#!/usr/bin/env python3
# Local stock scraper: Python standard library only, no API key, no accounts.
# Gets daily prices from Yahoo's public chart page and saves them on this Pi.
import json, sqlite3, sys, time, urllib.request, os, csv, datetime
HOME=os.path.expanduser("~/pi-stocks"); DB=f"{HOME}/data/stocks.db"
def fetch(sym, rng):
    url=f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?range={rng}&interval=1d"
    req=urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
    r=json.load(urllib.request.urlopen(req, timeout=20))["chart"]["result"][0]
    q=r["indicators"]["quote"][0]
    for i,ts in enumerate(r.get("timestamp",[])):
        if q["close"][i] is None: continue
        d=datetime.datetime.fromtimestamp(ts, datetime.timezone.utc).date().isoformat()
        yield (sym,d,q["open"][i],q["high"][i],q["low"][i],q["close"][i],q["volume"][i])
def main():
    os.makedirs(f"{HOME}/data",exist_ok=True)
    db=sqlite3.connect(DB)
    db.execute("create table if not exists daily(sym,date,open,high,low,close,volume,primary key(sym,date))")
    syms=[s.strip().upper() for s in open(f"{HOME}/watchlist.txt") if s.strip()]
    for s in syms:
        have=db.execute("select count(*) from daily where sym=?",(s,)).fetchone()[0]
        try:
            rows=list(fetch(s,"1y" if have==0 else "5d"))
            db.executemany("insert or replace into daily values(?,?,?,?,?,?,?)",rows)
            last=rows[-1]; print(f"{s:6} {last[1]} close {last[5]:.2f}  ({len(rows)} days saved)")
        except Exception as e: print(f"{s:6} FAILED: {e}")
        time.sleep(2)
    db.commit()
    if "--export" in sys.argv:
        out=f"{HOME}/export/stocks-{datetime.date.today()}.csv"; os.makedirs(f"{HOME}/export",exist_ok=True)
        w=csv.writer(open(out,"w",newline="")); w.writerow(["sym","date","open","high","low","close","volume"])
        w.writerows(db.execute("select * from daily order by sym,date")); print("Exported", out)
if __name__=="__main__": main()
