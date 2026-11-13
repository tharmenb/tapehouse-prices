import json, os, sys, urllib.request, datetime
KEY=os.environ["ALPACA_KEY"]; SEC=os.environ["ALPACA_SECRET"]
tick=[t.strip() for t in open("tickers.txt") if t.strip()]
def alp(t): return t.replace("-",".")          # BRK-B -> BRK.B
out={}
for i in range(0,len(tick),100):
    chunk=tick[i:i+100]
    url="https://data.alpaca.markets/v2/stocks/snapshots?feed=iex&symbols="+",".join(alp(t) for t in chunk)
    req=urllib.request.Request(url,headers={"APCA-API-KEY-ID":KEY,"APCA-API-SECRET-KEY":SEC})
    data=json.load(urllib.request.urlopen(req,timeout=60))
    for t in chunk:
        s=data.get(alp(t))
        if not s: continue
        px=(s.get("latestTrade") or {}).get("p") or (s.get("dailyBar") or {}).get("c")
        prev=(s.get("prevDailyBar") or {}).get("c")
        if not px or px<=0 or not prev: continue
        out[t]={"price":round(px,2),"chgPct":round((px/prev-1)*100,2),
                "at":(s.get("latestTrade") or {}).get("t")}
json.dump({"generated":datetime.datetime.utcnow().isoformat()+"Z","count":len(out),"prices":out},
          open("prices.json","w"),indent=0)
print("wrote",len(out),"of",len(tick),file=sys.stderr)
