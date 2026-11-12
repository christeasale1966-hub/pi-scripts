#!/bin/bash
# Stock scraper setup. Run: bash pi-stocks/setup.sh
set -e
mkdir -p ~/pi-stocks/data ~/pi-stocks/logs ~/pi-stocks/export
sudo timedatectl set-timezone America/Toronto
# Schedule: weekdays 4:30 PM Toronto time, after market close. The Pi runs it by itself.
( crontab -l 2>/dev/null | grep -v pi-stocks/scrape.py ; echo "30 16 * * 1-5 /usr/bin/python3 $HOME/pi-stocks/scrape.py >> $HOME/pi-stocks/logs/scrape.log 2>&1" ) | crontab -
echo "First scrape (1 year of history):"
python3 ~/pi-stocks/scrape.py
echo "STOCKS OK - runs weekdays 4:30 PM. Data stays in ~/pi-stocks/data."
