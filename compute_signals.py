"""Compute price-based scorefeed fields from Alpaca daily bars (IEX feed).
Writes signals.json: {"generated":..., "rows": {TICKER: {h, v50, r52, rp, adx, d}}}
h = 52-week high, v50 = % above/below 50-day average, r52 = 52-week % return,
rp = % of the 52-week range, adx = ADX(14), d = date of latest bar."""
import json, os, sys, datetime, urllib.request, urllib.parse
KEY=os.environ["ALPACA_KEY"]; SEC=os.environ["ALPACA_SECRET"]
tick=[t.strip() for t in open("feed_tickers.txt") if t.strip()]
start=(datetime.date.today()-datetime.timedelta(days=420)).isoformat()
def alp(t): return t.replace("-",".")
def get(url):
    req=urllib.request.Request(url,headers={"APCA-API-KEY-ID":KEY,"APCA-API-SECRET-KEY":SEC})
    return json.load(urllib.request.urlopen(req,timeout=60))
bars={}
for i in range(0,len(tick),20):
    chunk=tick[i:i+20]; tok=None
    while True:
        q={"symbols":",".join(alp(t) for t in chunk),"timeframe":"1Day","start":start,
           "limit":10000,"feed":"iex","adjustment":"split"}
        if tok: q["page_token"]=tok
        d=get("https://data.alpaca.markets/v2/stocks/bars?"+urllib.parse.urlencode(q))
        for s,bl in (d.get("bars") or {}).items(): bars.setdefault(s,[]).extend(bl)
        tok=d.get("next_page_token")
        if not tok: break
def adx14(h,l,c,n=14):
    if len(c)<2*n+1: return None
    tr=[];pdm=[];mdm=[]
    for i in range(1,len(c)):
        up=h[i]-h[i-1]; dn=l[i-1]-l[i]
        pdm.append(up if up>dn and up>0 else 0.0); mdm.append(dn if dn>up and dn>0 else 0.0)
        tr.append(max(h[i]-l[i],abs(h[i]-c[i-1]),abs(l[i]-c[i-1])))
    atr=sum(tr[:n]);p=sum(pdm[:n]);m=sum(mdm[:n]);dx=[]
    for i in range(n,len(tr)+1):
        if i>n:
            atr=atr-atr/n+tr[i-1];p=p-p/n+pdm[i-1];m=m-m/n+mdm[i-1]
        if atr==0: continue
        pi=100*p/atr;mi=100*m/atr
        dx.append(100*abs(pi-mi)/(pi+mi) if pi+mi else 0.0)
    if len(dx)<n: return None
    a=sum(dx[:n])/n
    for x in dx[n:]: a=(a*(n-1)+x)/n
    return a
def calc(bl):
    bl=sorted(bl,key=lambda b:b["t"])
    if len(bl)<60: return None
    c=[b["c"] for b in bl];h=[b["h"] for b in bl];l=[b["l"] for b in bl]
    last=c[-1]; w=bl[-252:]
    hi=max(b["h"] for b in w);lo=min(b["l"] for b in w)
    out={"h":round(hi,2),"v50":round((last/(sum(c[-50:])/50)-1)*100,2),"d":bl[-1]["t"][:10]}
    if hi>lo: out["rp"]=round(max(0,min(100,(last-lo)/(hi-lo)*100)),1)
    if len(bl)>=240: out["r52"]=round((last/w[0]["c"]-1)*100,1)
    a=adx14(h,l,c)
    if a is not None: out["adx"]=round(a,1)
    return out
rows={}
for t in tick:
    r=calc(bars.get(alp(t),[]))
    if r: rows[t]=r
json.dump({"generated":datetime.datetime.utcnow().isoformat()+"Z","count":len(rows),"rows":rows},open("signals.json","w"))
print("signals for",len(rows),"of",len(tick),file=sys.stderr)
