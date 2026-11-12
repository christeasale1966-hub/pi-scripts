# Script manifest — Chris T / Teasdale Cutting Tools

This file is the access layer for any assistant working on Chris T's setup. It inventories the runnable scripts and related tools that already exist. Read this first. Do not assume a script is on the Raspberry Pi just because a copy exists on the assistant's server. Do not modify, run, move, or delete a script unless the current task asks you to. This manifest itself is documentation only.

**Owner:** Chris T, Teasdale Cutting Tools Ltd., Toronto. Time zone is America/Toronto (Eastern). He trades US stocks in USD through Questrade. Assistants have no Questrade login and must not ask for it. Information only — no bot places trades.

## Where things live

| Place | What it is | Typical paths |
|---|---|---|
| Assistant server ("the box") | The Linux machine assistants use. **This is not the Pi.** Files here survive across assistant sessions. | `/workspace/...` (shared scratch and project files); `/home/box/compass-scraper/` (Compass Form 4 poller, survives box restarts) |
| Raspberry Pi | Raspberry Pi 5, likely 4 GB, Debian 13 (trixie), user `sensor`, IP `192.168.2.61` on the home (Bell) Wi-Fi. Assistants cannot SSH to it directly. | Home directory `~` = `/home/sensor`. Installed projects: `~/pi-pitch` (confirmed), `~/pi-scripts-sync.sh` (confirmed), `~/pi-scripts` (listener drop folder). `~/pi-stocks` was built but **install on the Pi is not confirmed**. |
| GitHub | Public repo that the Pi listener mirrors. Download only; the listener never executes what it pulls. | [https://github.com/christeasale1966-hub/pi-scripts](https://github.com/christeasale1966-hub/pi-scripts) → lands in `~/pi-scripts` on the Pi |
| Windows PC (TCTWork) | The hop between the assistant box and the Pi. Chris pastes `scp` in PowerShell. | `C:\Users\chris\` |

**How a new project gets onto the Pi (tarball method):** an assistant builds a `.tar.gz` under `/workspace`, copies it to the Windows PC, Chris runs `scp <file> sensor@192.168.2.61:~`, then on the Pi: `tar xzf <file> && bash <dir>/setup.sh`.

**How a script in `pi-scripts` gets onto the Pi (listener method):** commit the file to `christeasale1966-hub/pi-scripts` on branch `main`. Within about 15 minutes, `~/pi-scripts-sync.sh` copies it to `~/pi-scripts`. The listener does not run the file.

**Pi hardware notes already confirmed:** a CMTECK USB mic appears as ALSA card 2 (`plughw:2,0`). The default `arecord` format is 8-bit / 8 kHz; record with `-f S16_LE -r 48000`.

## Status legend

| Status | Meaning |
|---|---|
| **on Pi** | Installed and confirmed on the Raspberry Pi (`sensor@192.168.2.61`). A source copy may also exist on the assistant server. |
| **on assistant server only** | Lives on the box (`/workspace` or `/home/box`). Runnable there (or invoked by a bot routine). Not installed on the Pi, or Pi install has not been confirmed. |
| **idle or expired** | Built but not running, never installed, or a one-off watch whose end date or trigger window has passed. The file is still on disk. |

Most Yahoo-price scripts need no API key (they use the public chart URL with a browser User-Agent). If a script needs a key, this file says so and names the path — it never stores the value. Do not put keys, tokens, or passwords in this file or in chat.

Schedules below are in America/Toronto. A "routine" is a scheduled assistant/bot job, not a Pi cron line, unless cron is named.

---

## 1. Pi

These are the Raspberry Pi projects and the path that delivers scripts to it.

| Name | What it does | Exact command | Location | Schedule | Status |
|---|---|---|---|---|---|
| `pi-scripts-sync.sh` (the listener) | Mirrors the public `pi-scripts` repo into `~/pi-scripts`. Download only; it never runs the files it pulls. Log: `~/pi-scripts-sync.log`. | On the Pi: `~/pi-scripts-sync.sh` (cron already calls it). Reinstall from the box copy: after copying `pi-listener.tar.gz` to the Pi, `tar xzf pi-listener.tar.gz && bash pi-listener/setup.sh` | Pi: `~/pi-scripts-sync.sh`. Source installer: `/workspace/pi-listener/setup.sh` | Cron on the Pi: `*/15 * * * *` (every 15 minutes) | **on Pi** (LISTENER OK confirmed 2026-11-12). As of that run the GitHub repo was still empty, so nothing had been downloaded yet. |
| `setup.sh` (listener installer) | Writes `~/pi-scripts-sync.sh`, installs git if needed, adds the 15-minute cron line, and runs one sync. | `bash /workspace/pi-listener/setup.sh` (on the Pi, from the unpacked tarball: `bash pi-listener/setup.sh`) | `/workspace/pi-listener/setup.sh` | Run once | **on assistant server only** (already used to install the listener) |
| `test.sh` | Tiny smoke test for the listener path: prints a hello line and the date. Intended to land at `~/pi-scripts/test/test.sh` after a GitHub commit. | Once it is on the Pi: `bash ~/pi-scripts/test/test.sh` | Box: `/workspace/test/test.sh`. Also seen on the Windows PC at `C:\Users\chris\test.sh`. Target on the Pi: `~/pi-scripts/test/test.sh` | None. The listener only downloads it; someone still has to run it. | **on assistant server only**. As of the afternoon of 2026-11-12 it was not yet confirmed on GitHub, so the Pi may not have it. |
| `pitch.py` | Autocorrelation pitch detector. Reads a WAV file or the USB mic. | On the Pi, after setup: `~/pi-pitch/venv/bin/python ~/pi-pitch/src/pitch.py --file ~/pi-pitch/samples/test_440.wav`  ·  live mic: `~/pi-pitch/venv/bin/python ~/pi-pitch/src/pitch.py --mic`  ·  optional: `--device` | Pi: `~/pi-pitch/src/pitch.py`. Source: `/workspace/pi-pitch/src/pitch.py` | None (manual) | **on Pi** (SETUP OK; a 440 Hz test tone read as 440.4 Hz, A4) |
| `make_test_tone.py` | Writes a 2-second 440 Hz WAV so pitch detection can be tested with no mic. | `~/pi-pitch/venv/bin/python ~/pi-pitch/src/make_test_tone.py`  (writes `~/pi-pitch/samples/test_440.wav`) | Pi: `~/pi-pitch/src/make_test_tone.py`. Source: `/workspace/pi-pitch/src/make_test_tone.py` | None (setup already ran it once) | **on Pi** |
| `setup.sh` (pitch installer) | Installs apt packages and a venv, builds the test tone, and runs pitch.py on it. | `bash pi-pitch/setup.sh` (on the Pi, from the unpacked tarball) | `/workspace/pi-pitch/setup.sh` | Run once | **on assistant server only** (already used to install pitch on the Pi) |
| `scrape.py` (Pi stock scraper) | Pulls daily OHLCV for the watchlist from Yahoo's public chart API (standard library only, no key) and stores it in SQLite. Watchlist source: `~/pi-stocks/watchlist.txt` (currently SPY, QQQ, NVDA, CEG). Database: `~/pi-stocks/data/stocks.db`. | On the Pi, after install: `python3 ~/pi-stocks/scrape.py`  ·  export a CSV: `python3 ~/pi-stocks/scrape.py --export` (writes `~/pi-stocks/export/stocks-YYYY-MM-DD.csv`). Then from the Windows PC: `scp sensor@192.168.2.61:pi-stocks/export/*.csv .` | Box source: `/workspace/pi-stocks/`. Intended on the Pi: `~/pi-stocks/` | Cron *would* be weekdays 4:30 PM: `30 16 * * 1-5` → `python3 ~/pi-stocks/scrape.py >> ~/pi-stocks/logs/scrape.log 2>&1` (added only if `setup.sh` is run on the Pi) | **idle or expired** — built, **not confirmed installed on the Pi** |
| `setup.sh` (stock scraper installer) | Sets timezone to America/Toronto, creates data/log/export folders, installs the weekday 4:30 PM cron job, and runs a first 1-year scrape. | `bash pi-stocks/setup.sh` (on the Pi, from the unpacked tarball) | `/workspace/pi-stocks/setup.sh` | Run once | **idle or expired** (install not confirmed) |
| `grok` / `grok_text.py` (Pi text starter) | One-shot cloud text prompt via the xAI API. Not voice, not a command-running agent, not the Grok Bot app. **Needs a key**, stored at `~/.config/grok-bot/api-key` (chmod 600) or in the `XAI_API_KEY` environment variable — never in this file or in chat. Optional model override: `XAI_MODEL`. | After install on the Pi: `~/grok-bot/grok "Your question here"`  or `~/grok-bot/grok` (prompts for a question). Source check only: `python3 /workspace/pi-grok-starter/grok_text.py` | Box: `/workspace/pi-grok-starter/`. Intended on the Pi: `/home/sensor/grok-bot/` | None | **idle or expired** — packaged, not installed or tested on the Pi |
| `install.sh` (Pi text starter installer) | Copies the client to `~/grok-bot`, makes a venv, installs `xai-sdk`. Makes no API request. Refuses to overwrite existing files. Run as `sensor`, not root. | On the Pi, from the unpacked folder: `bash install.sh` | `/workspace/pi-grok-starter/install.sh` | Run once | **idle or expired** |

---

## 2. Investing (Compass, insider, earnings, fear, scanners)

Yahoo chart scripts below need no API key. Run them from their own folder when they use relative paths (`seen.json`, `data/`, `results.csv`, and similar).

### 2a. Live Compass Form 4 poller

This is a long-running process on the **assistant server**, not the Pi. It never messages anyone; Compass (and other bots) read the inbox it writes. As of 2026-11-12 ~4:21 PM America/Toronto it was **running** (watchdog + scraper). This box has no cron and no systemd-as-PID-1, so a user-level watchdog relaunches the scraper and `start.sh` is hooked from `~/.bashrc`, `~/.profile`, and a desktop autostart file.

| Name | What it does | Exact command | Location | Schedule | Status |
|---|---|---|---|---|---|
| `scraper.py` | Polls the SEC EDGAR latest Form 4 feed, downloads XML only for issuers on the watchlist (from `/workspace/compass-team/registry.csv` plus a fixed medical/AI list), and appends open-market buys (code P) and sales (code S) as JSONL. Dedupes in SQLite. | Start via the wrapper, not by hand, unless debugging: `/home/box/compass-scraper/start.sh`  ·  one-shot poll: `python3 /home/box/compass-scraper/scraper.py --once`  ·  parse local XML fixtures only (writes nothing to the inbox): `python3 /home/box/compass-scraper/scraper.py --test`  or `python3 /home/box/compass-scraper/scraper.py --test /path/to/file.xml`  ·  unit tests: `python3 /home/box/compass-scraper/tests/test_parser.py` | `/home/box/compass-scraper/scraper.py`. Inbox: `/workspace/compass-team/inbox/insider.jsonl` (buys), `insider_sales.jsonl` (sales), `scraper-status.json` (heartbeat). State/logs/cache: `/home/box/compass-scraper/{state,logs,cache}` | Weekdays 6:00 AM–10:15 PM America/Toronto, every 75 seconds; sleeps outside that window. One catch-up poll on process start. | **on assistant server only** (running) |
| `start.sh` | Idempotent: starts the watchdog if it is not already running. | `/home/box/compass-scraper/start.sh` | `/home/box/compass-scraper/start.sh` | Hooked after login / desktop start | **on assistant server only** |
| `watchdog.sh` | Holds a lock and relaunches `scraper.py` if it exits. Checks every 15 seconds. | Started by `start.sh`. Do not launch a second copy. | `/home/box/compass-scraper/watchdog.sh` | Continuous while the box is up | **on assistant server only** (running) |
| `stop.sh` | Stops the watchdog and scraper. | `/home/box/compass-scraper/stop.sh` | `/home/box/compass-scraper/stop.sh` | Manual | **on assistant server only** |

Shared Compass files (not scripts): `/workspace/compass-team/registry.csv` (holdings and watchlist), `alerts-sent.csv` (dedup log), `README.md` (team lanes). Team bots — Fed Watch, Data Day, Earnings Watch, Sector Pulse, My Stocks, Thesis Break, Dividend Income, Options Flow, Macro Dashboard — are bots with lanes in that README, not scripts in this inventory. None of those nine have a saved schedule until Chris approves one in that bot's own chat.

### 2b. Insider, fear, earnings

| Name | What it does | Exact command | Location | Schedule | Status |
|---|---|---|---|---|---|
| `watch.py` | Daily SEC Form 4 sweep for today's new filings; writes `run_parsed.json` and a pending `seen.json`. Uses relative paths — run it from its folder. | `cd /workspace/insider-watch && python3 watch.py` | `/workspace/insider-watch/watch.py` (`seen.json`, `alerts-log.csv` in the same folder) | Grok Bot routine, weekdays around 6:00 PM America/Toronto | **on assistant server only** |
| `hist.py` | For one or more CIKs, sums Form 4 buys/sells since 2025-11-04 from the SEC submissions JSON and filing XML. | `python3 /workspace/insider-watch/hist.py <CIK> [CIK...]` | `/workspace/insider-watch/hist.py` | Manual | **on assistant server only** |
| `ft.py` (fear tracker) | Pulls a year of daily prices for SPY, QQQ, VIX, VIX3M, HYG, IEF, LQD, RSP, XLU, XLP, XLK and prints fear-style ratios (VIX/VIX3M, credit, defensive/XLK, 50-day and 150-day, SPY volume). No flags. | `python3 /workspace/fear/ft.py` | `/workspace/fear/ft.py` | Grok Bot routine around 4:40 PM America/Toronto | **on assistant server only** |
| `dates.md` (earnings calendar) | **Not a script.** Maintained markdown of confirmed and unconfirmed earnings dates for holdings and the watchlist. Updated by assistants / Earnings Watch, not by a cron job. | Open `/workspace/earnings-watch/dates.md` | `/workspace/earnings-watch/dates.md` (last updated morning of 2026-11-12) | Maintained file; warn Chris with lead time — his rule is to sell before earnings | **on assistant server only** |

A Friday insider-summary routine also exists as a bot job (not a file in this inventory). Last week's run failed; treat it as unreliable until it is repaired.

### 2c. Price quotes, moving-average checks, entry labels

| Name | What it does | Exact command | Location | Schedule | Status |
|---|---|---|---|---|---|
| `yq.py` | One-line Yahoo quote per ticker: last close, premarket, 50-day and 150-day, volume, 5-day high/low. | `python3 /workspace/yq.py TICKER [TICKER...]` | `/workspace/yq.py` | Manual | **on assistant server only** |
| `pull.py` (pre-open) | Same idea as `yq.py`, plus whether the last seven closes were below the 50-day. Prints a dict per ticker. | `python3 /workspace/preopen/pull.py TICKER [TICKER...]` | `/workspace/preopen/pull.py` | Used by pre-open brief work | **on assistant server only** |
| `ma50.py` | 50-day line, 5-day slope, and "touched near MA" check for a fixed list (AMD, MU, SOXL, BRK-B, HOOD, SPCX, ARM, SMCI, TQQQ, PLTR, TSLA, EOG, XLV, COIN). | `python3 /workspace/ma50.py` | `/workspace/ma50.py` | Manual / routine | **on assistant server only** |
| `ma_lines.py` | Daily 50-day and 150-day check for a longer tracking list, including crosses and 60-day highs. | `python3 /workspace/ma_lines.py` | `/workspace/ma_lines.py` | Manual / routine (50-day and 150-day signal jobs) | **on assistant server only** |
| `entry_check.py` | Labels each ticker NO-GO / WAIT / STRETCHED / READY / CAUTION from the 50/100/150-day lines. Info only. Default list is TMO, VEEV, IQV, CRWD, MA, CRBG. | `python3 /workspace/entry-tool/entry_check.py`  ·  or `python3 /workspace/entry-tool/entry_check.py TICKER [TICKER...]` | `/workspace/entry-tool/entry_check.py` | Manual | **on assistant server only** |
| `sector_scoreboard.py` | "Where is money flowing" scoreboard for US sector and industry ETFs (3-month and 1-month return vs 50-day and 150-day). | `python3 /workspace/sector_scoreboard.py` | `/workspace/sector_scoreboard.py` | Manual | **on assistant server only** |
| `build.py` (Chris scoreboard workbook) | Builds `chris_scoreboard.xlsx` from saved Yahoo JSON under `scoreboard/data/`, scoring past rule-based trades. Historical snapshot, not a live feed. | `cd /workspace/scoreboard && python3 build.py` | `/workspace/scoreboard/build.py` | None | **idle or expired** (saved snapshot) |

### 2d. Scanners and charts

| Name | What it does | Exact command | Location | Schedule | Status |
|---|---|---|---|---|---|
| `scan.py` | Prints last price, day change, 50-day, 150-day, 6-month change, and volume for the tickers you pass in. | `python3 /workspace/scan.py TICKER [TICKER...]` | `/workspace/scan.py` | Manual / Compass scanner routine | **on assistant server only** |
| `scan1151_1104.py` | Latest broad holdings-and-watchlist scan: 50/150-day rising and price above both → `BUYOK`, sorted by 6-month gain. | `python3 /workspace/scan1151_1104.py` | `/workspace/scan1151_1104.py` | Manual / routine | **on assistant server only** |
| `nonai_scan.py` | Screens a non-AI / non-tech list for price above a rising 50-day and 150-day, modest extension (−1% to +5% over the 50-day), and an up-day volume spike. Prints only the matches. | `python3 /workspace/nonai_scan.py` | `/workspace/nonai_scan.py` | Manual | **on assistant server only** |
| `scan_now.py`, `scan_full.py`, `scan_close.py`, `scan_mid.py`, `scan_vol.py` | Shorter variants of the same Yahoo 50/150-day scan idea (now / full universe / close / midday / volume). No flags. | `python3 /workspace/scan_now.py` (and the same pattern for `_full`, `_close`, `_mid`, `_vol`) | `/workspace/` (five files) | Manual | **on assistant server only** |
| `screen.py` (Saturday screen) | Pulls the Nasdaq screener, keeps US-listed names above $2B, and keeps those with rising 50-day and 150-day, price ≥ $10, and enough dollar volume. Writes `screen.json`. | `cd /workspace/satscan && python3 screen.py` | `/workspace/satscan/screen.py` | Saturday review work | **on assistant server only** |
| `tells.py` (Saturday tells) | One-line trend/volume snapshot for indexes, sectors, and a core list. Writes `tells.json`. | `cd /workspace/satscan && python3 tells.py` | `/workspace/satscan/tells.py` | Saturday review work | **on assistant server only** |
| Dated one-off scanners and briefs | Timestamped copies used on a given morning or close (names include the time and date). Same general job as `scan1151_1104.py` or `brief.py`. Prefer the latest named tool above unless you are reproducing a past run. | `python3 /workspace/<filename>.py` | `/workspace/scan0953_1104.py`, `scan1216.py`, `scan1521_1030.py`, `scan1521_1103.py`, `scan1527_1104.py`, `scan_1000_1029.py`, `scan_1026b.py`, `scan_1155_1028.py`, `brief.py`, `brief1102.py`, `brief1104.py`, `echo1104.py`, `hu.py`, `hu1023.py`, `hu1027.py`, `hu1027b.py`, `hu1028pm.py`, `hu1029pm.py`, `hu1030pm.py`, `hu1102am.py`, `hu1102pm.py`, `hu1103am.py`, `hu1103pm.py`, `hu1104am.py`, `hu1104pm.py`, `s1103a.py`, `s1154.py`, `s1521.py`, `s1530.py`, `r1154.py`, `rank.py`, `rank1031.py`, plus `/workspace/sat/`, `/workspace/sat1024/`, `/workspace/tells/`, `/workspace/tells1017/`, `/workspace/mkt/`, `/workspace/brief/`, `/workspace/all/es.py` | One-off | **idle or expired** (kept as dated copies) |
| `chart_all.py` | One PNG of AMD, MU, SPCX, ARM with price, 50-day, 150-day, volume, and support/resistance bands. Writes `all_in_one_chart.png` in the current directory. | `python3 /workspace/chart_all.py` | `/workspace/chart_all.py` | Manual | **on assistant server only** |
| `chart_lines.py`, `chart_sr.py`, `teva_chart.py`, `idx_chart.py`, `idx2.py`, `idx5.py` | Related chart helpers (moving-average lines, support/resistance, TEVA, index charts). | `python3 /workspace/chart_lines.py` (and the same pattern for the others) | `/workspace/` | Manual | **on assistant server only** |

### 2e. Intraday watches (mostly expired)

| Name | What it does | Exact command | Location | Schedule | Status |
|---|---|---|---|---|---|
| `fill_watch.py` | Loops until the regular-session close, watching TEVA ≤ $40.50 or SNOW ≤ $355. | `python3 /workspace/fill_watch.py` | `/workspace/fill_watch.py` | Intraday loop; exits at 4:00 PM | **idle or expired** (one-off fill watch; levels are stale) |
| `asts_watch.py` | Loops until 4:00 PM, triggers if ASTS ≤ $47.50 or ≥ $50.75. | `python3 /workspace/asts_watch.py` | `/workspace/asts_watch.py` | Intraday loop | **idle or expired** |
| `mu_sell_watch.py` | MU sell-alert checker; prints new ALERT lines only. State: `mu_watch_state.json`. | `cd /workspace/narrative && python3 mu_sell_watch.py` | `/workspace/narrative/mu_sell_watch.py` | Manual / watch | **idle or expired** (MU position watch; confirm it is still wanted before running) |
| `swing8.py` | "Swing 8" narrative-velocity snapshot for the last 24 hours, hourly, Eastern time. Logs `swing8_log.csv`. | `cd /workspace/narrative && python3 swing8.py` | `/workspace/narrative/swing8.py` | Manual | **on assistant server only** |
| `track.py` | Narrative velocity for one symbol vs a keyword regex and a news query; appends `narrative_log.csv`. | `cd /workspace/narrative && python3 track.py SYMBOL "keyword regex" "news query"` | `/workspace/narrative/track.py` | Manual | **on assistant server only** |

### 2f. Backtests and research (runnable, not live)

Run from the folder so relative `data/` paths work. These use saved Yahoo JSON under each folder, or fetch fresh prices, and write CSVs or charts. They are research tools, not a live feed.

| Name | What it does | Exact command | Location | Schedule | Status |
|---|---|---|---|---|---|
| `backtest/` (folder) | Rule backtests on saved daily bars (trend, pullback, market light, earnings filter). Main entry points: `bt.py` (full), `simple.py` (simpler Felix-style rules), `earnings_filter.py` (those rules plus an earnings filter), `tease.py`, `fetch.py` (refresh price JSON), `fetch_earnings.py`. | `cd /workspace/backtest && python3 simple.py`  ·  `python3 bt.py`  ·  `python3 earnings_filter.py`  ·  `python3 tease.py`  ·  `python3 fetch.py`  ·  `python3 fetch_earnings.py` | `/workspace/backtest/` (`data/`, `data_hot/`) | None | **on assistant server only** (snapshot / research) |
| `swing/` (folder) | Swing-review and "scare" (sharp-drop) research: fetch, review, write-up, calibration, extra stats, and `scare/scan.py` plus parse/detail helpers. Notes in `dip-rules-found.md` and `stocks-handoff.md`. | `cd /workspace/swing && python3 fetch.py`  ·  `python3 review.py`  ·  `python3 write.py`  ·  `python3 calib.py`  ·  `python3 extra.py`  ·  `cd /workspace/swing/scare && python3 scan.py` | `/workspace/swing/` | None (a weekly review from 2026-09-25 is saved) | **idle or expired** as a live review; scripts still runnable |
| `early-signals/bt.py` | Tests early-entry signals (RSI, stretch below 50-day, 3-down-then-up, MACD, bounce off a rising 150-day) on a 25-name list. Writes `results.csv`. | `cd /workspace/early-signals && python3 bt.py` | `/workspace/early-signals/bt.py` | None | **on assistant server only** |
| `independent-backtest/bt.py` | Separate backtest using `px.pkl` in the same folder. | `cd /workspace/independent-backtest && python3 bt.py` | `/workspace/independent-backtest/bt.py` | None | **on assistant server only** |
| `paper/middle-entry-backtest/bt.py` | Middle-entry experiment; see `/workspace/paper/README.md`. | `cd /workspace/paper/middle-entry-backtest && python3 bt.py` | `/workspace/paper/middle-entry-backtest/bt.py` | None | **on assistant server only** |
| Other research helpers | Extra backtest and correlation one-offs at the workspace root and in `/workspace/bt/`. | `python3 /workspace/bt.py`  ·  `python3 /workspace/bt2.py`  ·  `python3 /workspace/bt3.py`  ·  `python3 /workspace/bt4.py`  ·  `python3 /workspace/bt_blend.py`  ·  `python3 /workspace/bt/bt.py`  ·  `python3 /workspace/corr.py`  ·  `python3 /workspace/lv.py TICKER [...]`  ·  `python3 /workspace/q.py TICKER [...]` | `/workspace/` and `/workspace/bt/` | One-off | **idle or expired** |

### 2g. Data folders (no scripts)

| Folder | What it is | Status |
|---|---|---|
| `/workspace/yf_data/` | Saved Yahoo chart and earnings JSON snapshots for many tickers. Input for research, not a live scrape. | **idle or expired** |
| `/workspace/polymarket/` | CSV logs of Polymarket readings (`log.csv`, `swing_log.csv`). No scraper script lives in the folder. The READY app design mentions S&P odds from here. | **idle or expired** (logs only) |
| `/workspace/midterm-watch/` | Saved `spy.json` and `state.json` for a midterm / SPY watch. No script in the folder. | **idle or expired** |

### 2h. Scheduled bot routines that are not files

These run as Grok Bot / Compass jobs. They often call the scripts above, or read Yahoo / the Compass inbox / `dates.md`, but they are not themselves scripts on disk:

- Compass Morning Read — weekdays 9:20 AM America/Toronto.
- Red-light (market light) warning, stock scanner, 50-day and 150-day signals, pre-open brief, BRK.B watches, Saturday reviews.
- Daily insider check (`watch.py`) around 6:00 PM weekdays; fear tracker (`ft.py`) around 4:40 PM.
- Friday insider summary (failed last week).
- Email-side, not scripts: Questrade IQ price/volume alerts and Seeking Alpha arrive in Gmail; Benzinga alerts have been landing in Spam.

Compass only advises. No bot places or changes trades.

---

## 3. SPCX

SpaceX / SPCX desk tools. The Pulse dashboard and the READY checklist were designed and their source or rebuild prompts were saved; **neither is running** as a live app. Library TypeScript under `src/lib` is vendored app code and is not listed file-by-file.

| Name | What it does | Exact command | Location | Schedule | Status |
|---|---|---|---|---|---|
| `spcx-pulse` (app folder) | SPCX Pulse trading-desk dashboard source (and a copy under `orig-src`). Fix notes in `FIX_NOTES.md`. Not a one-file CLI. | No supported one-line CLI was found. Treat this as source for a web desk app, not a daily command. Rebuild notes also live in `/workspace/spcx/`. | `/workspace/spcx-pulse/` | None | **idle or expired** |
| `spcx-tc` (app folder) | Another TypeScript Pulse/desk variant with its own `package.json`. | Use only if you are rebuilding that app; check `/workspace/spcx-tc/package.json` first. Do not invent a start command from memory. | `/workspace/spcx-tc/` | None | **idle or expired** |
| `spcx-harness` (app folder) | Local harness / stub around the same desk code. `run.mjs` launches a Puppeteer pass. | `node /workspace/spcx-harness/run.mjs` (from that folder if it expects local paths). Supporting TS is under `src/` and `stub/`. | `/workspace/spcx-harness/` | None | **idle or expired** |
| `ready-tool` (READY checklist) | How-to and rebuild prompts for the READY! / WAIT! / NO-GO! checklist app (50/100/150-day labels, suggested bid, 8% GTC stop reminder, optional Polymarket caution). **No runnable app in the folder.** | There is nothing to execute. Read `/workspace/ready-tool/HOW-TO-USE.md` and `READY-rebuild-prompt.txt` if rebuilding. The closest runnable check on disk is `entry_check.py` in section 2c. | `/workspace/ready-tool/` | None | **idle or expired** |
| `spcx_watch.py` | Intraday loop that triggered if SPCX traded at or below $149, and ended at the 2026-10-09 close. | `python3 /workspace/spcx_watch.py` — do not run; the end date is in the past. | `/workspace/spcx_watch.py` | Ended 2026-10-09 4:01 PM | **idle or expired** |
| `/workspace/spcx/` notes | Saved Pulse rebuild prompt, an AI-dip backtest CSV, and rotation-tracker notes. No runnable script. | Read the markdown/CSV in `/workspace/spcx/` | `/workspace/spcx/` | None | **idle or expired** |

---

## 4. Other

Shop, music, drawing, and scratch tools on the assistant server. Big folders are one entry each. None of these are on the Pi.

| Name | What it does | Exact command | Location | Schedule | Status |
|---|---|---|---|---|---|
| `make_slip.py` | Builds a Teasdale-format packing-slip PDF (no prices). Template is in the same folder. | `python3 /workspace/packing-slips/make_slip.py --po PO_NUMBER --desc "item description"`  ·  optional: `--qty`, `--date MM/DD/YYYY` (default today, America/Toronto), `--ship-to` (use `\n` between lines), `--slip`, `--ship-via` (default `Pick-up`), `--notes` | `/workspace/packing-slips/make_slip.py` (output under `/workspace/packing-slips/out/`) | Manual, when Chris asks for a packing slip | **on assistant server only** |
| `quote/build.py` | One-off ReportLab quote PDF (hard-coded output name in the file). Not a general CLI. | `python3 /workspace/quote/build.py` (review and edit the hard-coded paths first) | `/workspace/quote/build.py` | One-off | **idle or expired** |
| `drawing-watch/` (folder) | Image-cleanup helpers for customer drawings (`clean.py`, `clean_emjac.py`, `clean_mr.py`, `clean_t7365.py`). Several expect local PGM/PNG names in the current directory. | `python3 /workspace/drawing-watch/clean.py` (and the sibling `clean_*.py` files). Check the hard-coded filenames before running. | `/workspace/drawing-watch/` | One-off | **idle or expired** |
| `music/` (folder) | Church / lead-sheet tools: batch render, song list, handouts, ChordPro-style lead sheets, transpose. | `python3 /workspace/music/leadsheet.py OUT.pdf song1.txt [song2.txt ...]`  ·  `python3 /workspace/music/transpose.py` (see the file for `infile` / semitone args)  ·  also `batch.py`, `create_song_list.py`, `handouts.py`, `make.py`, `make_open_eyes.py` | `/workspace/music/` | Manual | **on assistant server only** |
| `mobilesheets/` (folder) | Build, crop, parse, and make helpers for MobileSheets music PDFs. | `python3 /workspace/mobilesheets/build.py` (and `crop.py`, `mk.py`, `parse.py` in the same folder) | `/workspace/mobilesheets/` | Manual | **on assistant server only** |
| `mel.py`, `songs.py`, `rec/tr.py` | Melody / song / recording helpers (transpose or detect a key from audio). `mel.py` takes name, query, tonic, and mode. | `python3 /workspace/mel.py NAME QUERY TONIC maj` (or `min`)  ·  `python3 /workspace/songs.py`  ·  `python3 /workspace/rec/tr.py` | `/workspace/mel.py`, `/workspace/songs.py`, `/workspace/rec/tr.py` | Manual | **on assistant server only** |
| `bank-statements/scan.py` | One-off OpenCV pass over specific bank-statement page images. Hard-coded input paths. | Do not treat this as a general tool. If reused, edit the paths in `/workspace/bank-statements/scan.py` first. | `/workspace/bank-statements/scan.py` | One-off | **idle or expired** |
| Drawing / CNC one-offs | Short image and drawing editors used for specific jobs (broaches, GT pages, V-series profile overlays, Estwork, and similar). | See the file named for that job, for example `/workspace/dwg10383/edit.py`, `/workspace/b10lab/`, `/workspace/gt/`, `/workspace/v2.py`–`v11.py`, `/workspace/estwork/make.py`, `/workspace/ehw/`. | Scattered under `/workspace/` | One-off | **idle or expired** |
| Scratch one-letter scripts | Short unnamed experiments (`a.py`, `b.py`, `c.py`, and similar). Not an API. Open the file before using it. | `python3 /workspace/<name>.py` | `/workspace/` | One-off | **idle or expired** |

Other `/workspace` folders are documents, invoices, drawings, or images, not scripts: `inv/`, `po/`, `remit/`, `cmp/`, `dahl/`, `drive-filing/`, `pi-build-log/` (captions for Pi screenshots), and similar. Skip vendored trees (`node_modules`, venvs including `/workspace/pi-grok-test-venv/`, `site-packages`, `src/lib` inside the SPCX apps).

---

## Counts

Look-only inventory on 2026-11-12. "Underlying scripts" are `.py` / `.sh` / `.mjs` files found under `/workspace` (vendored library trees skipped) plus the Compass poller files under `/home/box/compass-scraper/` and the Pi-only listener script. Manifest entries are the table rows in the sections above (a dated-copy group or an app folder counts as one entry).

| Group | Manifest entries | Underlying runnable scripts |
|---|---:|---:|
| Pi | 10 | 10 source files on the box (`/workspace/pi-*`, `/workspace/test/test.sh`). The installed `~/pi-scripts-sync.sh` on the Pi is generated by setup (11 if you count that copy separately). |
| Investing | 38 | About **120** investing scripts on disk: 4 Compass poller files, 2 insider, 1 fear, first-class quote/scan/chart/watch/narrative tools, 6 backtest, 10 swing, 3 other backtests, and ~70 dated one-off scan/brief/hu/sat/tells/mkt variants. Also 1 maintained data file (`dates.md`, not a script) and 3 data-only folders. |
| SPCX | 6 | 2 runnable files (`spcx_watch.py`, `spcx-harness/run.mjs`) plus 3 app source trees, 1 prompt folder, and notes. TypeScript under `src/lib` is not counted as separate scripts. |
| Other | 9 | **57** shop, music, drawing, and scratch scripts under `/workspace` (packing slip, quotes, music, MobileSheets, drawing cleanup, and one-letter scratch files). |
| **Total** | **63 manifest entries** | **189** scripts under `/workspace` + **5** under `/home/box/compass-scraper/` (`scraper.py`, `start.sh`, `stop.sh`, `watchdog.sh`, `tests/test_parser.py`) + **1** Pi-only sync script ≈ **195** runnable files in scope |

| Status | How to read it | Rough script/entry mix |
|---|---|---|
| **on Pi** | Listener sync script, pitch detector, and test-tone writer are confirmed installed. | 3 confirmed Pi programs (plus the two installers already used, whose source remains on the box) |
| **on assistant server only** | Most investing tools, the running Compass poller, packing-slip and music tools, and source/installers. | The Compass poller is the only long-running investing process. Fear and insider `watch.py` are routine-invoked, not daemons. |
| **idle or expired** | Pi stock scraper and Pi text starter (not installed on the Pi); SPCX Pulse / READY apps; expired price watches (`spcx_watch.py` ended 2026-10-09; `fill_watch.py`, `asts_watch.py`); dated scanners; saved backtest/scoreboard snapshots; most shop one-offs. | Do not install or restart these unless the current task asks. |

**Not searched from this box:** the live filesystem of the Pi (except what Chris has confirmed in photos and chat), Questrade itself, and the Windows PC beyond files already copied into `/workspace` or noted above.

**If you are a new assistant:** start here. For Pi work, ship files through the tarball or `pi-scripts` listener path; do not assume you can SSH in. For investing work, prefer the named first-class scripts in section 2 over dated copies. For insider buys already polled today, read `/workspace/compass-team/inbox/` and `scraper-status.json` before launching another scraper. Never record a secret in this file.
