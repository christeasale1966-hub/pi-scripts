#!/usr/bin/env python3
"""One text prompt per request; no microphone, tools, or command execution."""
import os
import stat
import sys
from pathlib import Path

DEFAULT_MODEL = "grok-4.7"

def load_key():
    key = os.environ.get("XAI_API_KEY", "").strip()
    if key:
        return key
    path = Path.home() / ".config" / "grok-bot" / "api-key"
    try:
        # Refuse symlinks and files readable by other users. Never execute config.
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    except FileNotFoundError:
        return ""
    with os.fdopen(fd, "r") as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
            raise ValueError("API key file must be owned by you and have permissions 600.")
        return stream.read(16384).strip()

def main():
    try:
        key = load_key()
    except (OSError, ValueError):
        print("Cannot safely read API key file. Check owner and chmod 600; see README.md.", file=sys.stderr)
        return 2
    if not key:
        print("Missing XAI_API_KEY. Set it privately or configure ~/.config/grok-bot/api-key; see README.md.", file=sys.stderr)
        return 2
    prompt = " ".join(sys.argv[1:]).strip()
    if not prompt:
        try:
            prompt = input("Your question: ").strip()
        except (EOFError, KeyboardInterrupt):
            return 0
    if not prompt:
        print("No question entered.", file=sys.stderr)
        return 2
    try:
        from xai_sdk import Client
        from xai_sdk.chat import user
    except ImportError:
        print("xai-sdk is missing. Run install.sh, then use the grok wrapper.", file=sys.stderr)
        return 2
    try:
        client = Client(api_key=key, timeout=120)
        chat = client.chat.create(model=os.environ.get("XAI_MODEL") or DEFAULT_MODEL, store_messages=False)
        chat.append(user(prompt))
        print(chat.sample().content)
    except KeyboardInterrupt:
        print("Cancelled.", file=sys.stderr)
        return 130
    except Exception:
        # Do not dump SDK exceptions, which could contain sensitive request details.
        print("Request failed. Check internet, API credits/key, model access, and SDK version. No secrets logged.", file=sys.stderr)
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
