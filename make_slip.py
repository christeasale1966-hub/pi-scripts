#!/usr/bin/env python3
"""Fill the Teasdale packing-slip template and render a letter-size PDF.

No prices are included. Signature, date-received, and initials lines stay blank.
"""

from __future__ import annotations

import argparse
import base64
import html
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

DIR = Path(__file__).resolve().parent
TEMPLATE = DIR / "packing-slip-template.html"
LOGO = DIR / "teasdale_logo.png"
MASTER_LOGO = Path("/workspace/accounting/assets/teasdale_logo.png")
OUT_DIR = DIR / "out"
TZ = ZoneInfo("America/Toronto")

DATE_FORMATS = ("%m/%d/%Y", "%Y-%m-%d", "%m/%d/%y", "%d/%m/%Y")


def parse_date(value: str | None) -> datetime:
    if not value:
        return datetime.now(TZ)
    text = value.strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).replace(tzinfo=TZ)
        except ValueError:
            continue
    raise SystemExit(
        f"Could not parse date {value!r}. Use MM/DD/YYYY or YYYY-MM-DD."
    )


def literal_newlines(text: str) -> str:
    """Turn shell-escaped \\n sequences into real line breaks."""
    return (text or "").replace("\\n", "\n")


def esc(text: str, multiline: bool = False) -> str:
    cleaned = html.escape(text or "", quote=True)
    if multiline:
        cleaned = cleaned.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "<br>")
    return cleaned


def logo_data_uri() -> str:
    """Embed the logo so the PDF renders it even if the temp HTML is moved."""
    path = LOGO if LOGO.exists() else MASTER_LOGO
    if not path.exists():
        raise SystemExit(f"Logo not found: {LOGO} or {MASTER_LOGO}")
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def safe_po(po: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", po).strip("-._")
    return cleaned or "slip"


def find_chrome() -> str | None:
    for name in (
        "google-chrome",
        "google-chrome-stable",
        "chromium",
        "chromium-browser",
    ):
        path = shutil.which(name)
        if path:
            return path
    return None


def find_wkhtml() -> str | None:
    return shutil.which("wkhtmltopdf")


def render_pdf(html_path: Path, pdf_path: Path) -> None:
    chrome = find_chrome()
    if chrome:
        html_uri = html_path.resolve().as_uri()
        commands = [
            [
                chrome,
                "--headless=new",
                "--disable-gpu",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--allow-file-access-from-files",
                "--no-pdf-header-footer",
                f"--print-to-pdf={pdf_path}",
                html_uri,
            ],
            [
                chrome,
                "--headless",
                "--disable-gpu",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--allow-file-access-from-files",
                "--no-pdf-header-footer",
                f"--print-to-pdf={pdf_path}",
                html_uri,
            ],
        ]
        last_error = ""
        for cmd in commands:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if pdf_path.exists() and pdf_path.stat().st_size > 0:
                return
            last_error = (result.stderr or result.stdout or "").strip()
        raise SystemExit(f"Chrome failed to write a PDF.\n{last_error}")

    wkhtml = find_wkhtml()
    if wkhtml:
        cmd = [
            wkhtml,
            "--page-size",
            "Letter",
            "--margin-top",
            "0",
            "--margin-bottom",
            "0",
            "--margin-left",
            "0",
            "--margin-right",
            "0",
            "--enable-local-file-access",
            "--print-media-type",
            "--disable-smart-shrinking",
            str(html_path),
            str(pdf_path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if pdf_path.exists() and pdf_path.stat().st_size > 0:
            return
        raise SystemExit(
            "wkhtmltopdf failed to write a PDF.\n"
            + (result.stderr or result.stdout or "").strip()
        )

    raise SystemExit(
        "Need Google Chrome, Chromium, or wkhtmltopdf to make a packing-slip PDF."
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create a Teasdale packing slip PDF with no prices."
    )
    parser.add_argument("--po", required=True, help="Purchase order number")
    parser.add_argument(
        "--desc",
        required=True,
        help="Item description, used exactly as given (not itemized)",
    )
    parser.add_argument("--qty", default="", help="Quantity (leave blank if not given)")
    parser.add_argument(
        "--date",
        default=None,
        help="Date as MM/DD/YYYY (default: today in America/Toronto)",
    )
    parser.add_argument(
        "--ship-to",
        default="",
        help="Ship-to address. Use \\n between lines.",
    )
    parser.add_argument("--slip", default="", help="Packing slip number")
    parser.add_argument(
        "--ship-via",
        default="Pick-up",
        help="How it ships (default: Pick-up)",
    )
    parser.add_argument("--notes", default="", help="Optional notes")
    parser.add_argument(
        "--sample",
        action="store_true",
        help="Mark the slip as SAMPLE (watermark). Not for a real shipment.",
    )
    parser.add_argument(
        "--out",
        default=None,
        help="Optional PDF path (default: out/PackingSlip_PO<po>_<date>.pdf)",
    )
    args = parser.parse_args()

    if not TEMPLATE.exists():
        raise SystemExit(f"Template not found: {TEMPLATE}")

    dt = parse_date(args.date)
    date_display = dt.strftime("%m/%d/%Y")
    date_file = dt.strftime("%Y-%m-%d")

    filled = (
        TEMPLATE.read_text(encoding="utf-8")
        .replace("{{LOGO_SRC}}", logo_data_uri())
        .replace("{{SAMPLE_CLASS}}", "sample" if args.sample else "")
        .replace("{{DATE}}", esc(date_display))
        .replace("{{PO_NUMBER}}", esc(args.po))
        .replace("{{SLIP_NUMBER}}", esc(args.slip))
        .replace("{{SHIP_TO}}", esc(literal_newlines(args.ship_to), multiline=True))
        .replace("{{DESCRIPTION}}", esc(literal_newlines(args.desc), multiline=True))
        .replace("{{QTY}}", esc(str(args.qty or "")))
        .replace("{{SHIP_VIA}}", esc(args.ship_via))
        .replace("{{NOTES}}", esc(literal_newlines(args.notes), multiline=True))
    )

    if args.out:
        pdf_path = Path(args.out).expanduser().resolve()
        pdf_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        pdf_path = OUT_DIR / f"PackingSlip_PO{safe_po(args.po)}_{date_file}.pdf"

    with tempfile.NamedTemporaryFile(
        "w",
        suffix=".html",
        dir=DIR,
        delete=False,
        encoding="utf-8",
    ) as handle:
        handle.write(filled)
        tmp_html = Path(handle.name)

    try:
        render_pdf(tmp_html, pdf_path)
    finally:
        tmp_html.unlink(missing_ok=True)

    print(pdf_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
