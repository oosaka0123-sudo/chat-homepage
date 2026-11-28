"""Kyushu public forecast maintenance: public data only, fixed FTPS destination.
No dependency on private repositories, no credential logging, no HTML writes.
"""
import datetime as dt
import concurrent.futures
import ftplib
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
import ssl
import sys
from urllib.parse import urlencode
from urllib.request import Request, urlopen

TOKYO=dt.timezone(dt.timedelta(hours=9))
HOST="ftp.lolipop.jp"
DEST="/kyushu/data"
PUBLIC="https://kyushu.rss7.net/data/"
# Public map and offshore grid coordinates; candidate JMA ports (not local measurements).
SPOTS=[
 ("kizakihama",31.8296,131.453,31.79166,131.62502,"MG"),
 ("okuragahama",32.3938889,131.6366667,32.29166,131.70836,"Z6"),
 ("keya",33.5907,130.134,33.625,130.04167,"KA"),
 ("aoshima",31.8037,131.47,31.79166,131.62502,"MG"),
 ("eguchihama",31.6586,130.316,31.625,130.29167,"ZJ"),
 ("koigaura",31.412265,131.343592,31.375,131.37502,"AB"),
 ("kanegahama",32.3628,131.626,32.29166,131.70836,"Z6"),
 ("hitotsuba",31.9238,131.473,31.95834,131.62502,"MG"),
 ("hatsu",33.8816,130.568,33.95834,130.54167,"QF"),
 ("ikuragahama",32.1944,131.556,32.20834,131.70836,"MG"),
 ("mitoma",33.7022,130.416,33.79166,130.37502,"QF"),
 ("tategami",33.5282,129.95,33.54166,129.95836,"KA"),
 ("umegahama",31.5799,131.412,31.45834,131.45836,"AB")]
PORTS={"MG":"宮崎","Z6":"細島","AB":"油津","KA":"唐津","QF":"博多","ZJ":"阿久根"}
FEEDS={
 "marine":("https://marine-api.open-meteo.com/v1/marine",{"hourly":"wave_height,wave_period","daily":"wave_height_max","cell_selection":"sea"}),
 "weather":("https://api.open-meteo.com/v1/forecast",{"hourly":"wind_speed_10m,wind_direction_10m,weather_code,temperature_2m,precipitation,precipitation_probability","daily":"weather_code,wind_speed_10m_max,wind_direction_10m_dominant","wind_speed_unit":"ms"})}
LIMIT=2_000_000
IDS={s[0] for s in SPOTS}
def require(ok,message):
    if not ok: raise ValueError(message)
def get(url,limit=LIMIT):
    with urlopen(Request(url,headers={"User-Agent":"KyushuSurferKS/1.0","Cache-Control":"no-cache","Accept-Encoding":"identity"}),timeout=40) as response:
        require(response.geturl()==url,"unexpected redirect")
        raw=response.read(limit+1)
    require(len(raw)<=limit,"response too large")
    return raw
def finite(v): return type(v) in (int,float) and math.isfinite(v)
def expected_times(start,hourly):
    return [(start+(dt.timedelta(hours=i) if hourly else dt.timedelta(days=i))).strftime("%Y-%m-%dT%H:00" if hourly else "%Y-%m-%d") for i in range(240 if hourly else 10)]
def validate_feed(kind,records,start):
    require(isinstance(records,list) and len(records)==13,"location count")
    vars=FEEDS[kind][1]
    for i,(s,r) in enumerate(zip(SPOTS,records)):
        require(r.get("location_id",0)==i and r.get("utc_offset_seconds")==32400,"location/timezone")
        lat,lon=(s[3],s[4]) if kind=="marine" else (s[1],s[2])
        tol=.01 if kind=="marine" else .25
        require(all(finite(r.get(k)) for k in ("latitude","longitude")) and max(abs(r["latitude"]-lat),abs(r["longitude"]-lon))<=tol,"grid "+s[0])
        for group in ("hourly","daily"):
            sec=r[group]; times=expected_times(start,group=="hourly"); n=len(times)
            require(sec["time"][:n]==times,"dates "+s[0])
            keys=vars[group].split(",")
            for key in keys:
                arr=sec[key][:n]
                require(len(arr)==n and all(v is None or finite(v) for v in arr),"values "+key)
                if key in ("wave_height","wave_period","wave_height_max","wind_speed_10m","wind_speed_10m_max","precipitation"):
                    require(all(v is None or v>=0 for v in arr),"negative "+key)
                if "direction" in key: require(all(v is None or 0<=v<=360 for v in arr),"wind direction")
                if key=="precipitation_probability": require(all(v is None or 0<=v<=100 for v in arr),"rain probability")
            r[group]={key:sec[key][:n] for key in ["time",*keys]}
    return records
def fetch(kind,start):
    endpoint,params=FEEDS[kind]
    query={**params,"timezone":"Asia/Tokyo","forecast_days":10,"latitude":",".join(str(s[1]) for s in SPOTS),"longitude":",".join(str(s[2]) for s in SPOTS)}
    return validate_feed(kind,json.loads(get(endpoint+"?"+urlencode(query))),start)
def daily_rows(marine,weather):
    rows=[]
    for i,date in enumerate(marine["daily"]["time"]):
        window=slice(i*24+5,i*24+18)
        w=marine["hourly"]["wave_height"][window]
        s=weather["hourly"]["wind_speed_10m"][window]
        d=weather["hourly"]["wind_direction_10m"][window]
        w_ok=len(w)==13 and all(finite(v) for v in w)
        s_ok=len(s)==13 and all(finite(v) for v in s)
        direction=None
        if s_ok and len(d)==13 and all(finite(v) for v in d):
            x=sum(v*math.cos(math.radians(a)) for v,a in zip(s,d));y=sum(v*math.sin(math.radians(a)) for v,a in zip(s,d))
            if math.hypot(x,y)>1e-8: direction=math.degrees(math.atan2(y,x))%360
        rows.append({"date":date,"wave_min":min(w) if w_ok else None,"wave_max":max(w) if w_ok else None,
                     "wind_mean":sum(s)/13 if s_ok else None,"wind_dir":direction,"weather_code":weather["hourly"]["weather_code"][i*24+11]})
    return rows
def integer(v):
    require(re.fullmatch(r"-?\d+",v.strip()) is not None,"invalid tide number")
    return int(v.strip())
def parse_tide(raw,station,year):
    days={}
    for line in raw.decode("ascii").splitlines():
        if not line.strip(): continue
        require(len(line)==136 and line[78:80]==station and integer(line[72:74])==year%100,"JMA row")
        date=dt.date(year,integer(line[74:76]),integer(line[76:78])).isoformat()
        require(date not in days,"duplicate JMA day")
        hourly=[integer(line[i:i+3]) for i in range(0,72,3)]
        require(999 not in hourly,"missing JMA level")
        row={"date":date,"hourly_cm":hourly,"high":[],"low":[]}
        for key,offset in (("high",80),("low",108)):
            for i in range(offset,offset+28,7):
                t=line[i:i+4].replace(" ","0");level=integer(line[i+4:i+7])
                if t=="9999" and level==999: continue
                require(re.fullmatch(r"\d{4}",t) and int(t[:2])<24 and int(t[2:])<60 and level!=999,"JMA event")
                row[key].append({"time":t[:2]+":"+t[2:],"height_cm":level})
        days[date]=row
    first=dt.date(year,1,1);n=(dt.date(year+1,1,1)-first).days
    require(set(days)=={(first+dt.timedelta(days=i)).isoformat() for i in range(n)},"incomplete JMA year")
    return days
def reference_tides(start):
    dates=[start.date()+dt.timedelta(days=i) for i in range(3)]
    tables={}
    for station in PORTS:
        for year in {d.year for d in dates}:
            try:
                url=f"https://www.data.jma.go.jp/kaiyou/data/db/tide/suisan/txt/{year}/{station}.txt"
                tables[station,year]=parse_tide(get(url,128*1024),station,year)
            except (OSError,ValueError):
                print("JMA reference unavailable:",station,year,flush=True);tables[station,year]={}
    return {s[0]:{"station":s[5],"name":PORTS[s[5]],"status":"candidate_reference_only","datum":"気象庁潮位表基準面",
                 "local_applicability_verified":False,"source":"https://www.data.jma.go.jp/kaiyou/db/tide/suisan/suisan.php?stn="+s[5],
                 "days":[tables[s[5],d.year][d.isoformat()] for d in dates if d.isoformat() in tables[s[5],d.year]]} for s in SPOTS}
def stamp(raw,id):
    obj=json.loads(raw)
    require(obj["id"]==id,"forecast ID")
    t=dt.datetime.fromisoformat(obj["retrieved"])
    require(t.utcoffset() is not None,"timezone missing")
    return t
def prepare(folder):
    now=dt.datetime.now(TOKYO);start=now.replace(hour=0,minute=0,second=0,microsecond=0)
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        feeds=dict(zip(FEEDS,pool.map(lambda k:fetch(k,start),FEEDS)))
    tides=reference_tides(start)
    require(dt.datetime.now(TOKYO).date()==start.date(),"date changed during fetch")
    folder.mkdir(parents=True,exist_ok=False)
    for i,s in enumerate(SPOTS):
        item={"id":s[0],"retrieved":now.isoformat(timespec="seconds")}
        for k,r in feeds.items():item[k]={f:r[i][f] for f in ("latitude","longitude","hourly","daily")}
        item["daytime_daily"]=daily_rows(item["marine"],item["weather"])
        item["reference_tide"]=tides[s[0]]
        (folder/(s[0]+".json")).write_text(json.dumps(item,ensure_ascii=True,separators=(",",":"),allow_nan=False),encoding="utf-8")
    print("PASS actual forecasts: 13 locations; 240 hours; 10 days; JST",now.isoformat(timespec="seconds"),flush=True)
    print("JMA available days:",sum(len(t["days"]) for t in tides.values()),"/39",flush=True)
def payload(folder):
    require({p.name for p in folder.iterdir()}=={i+".json" for i in IDS},"payload scope")
    data={i:(folder/(i+".json")).read_bytes() for i in sorted(IDS)}
    stamps={stamp(raw,i) for i,raw in data.items()}
    require(len(stamps)==1,"mixed timestamp")
    t=next(iter(stamps));now=dt.datetime.now(TOKYO)
    require(dt.timedelta(0)<=now-t<dt.timedelta(hours=1) and t.astimezone(TOKYO).date()==now.date(),"stale payload")
    for i,raw in data.items():
        require(len(raw)<LIMIT,"payload too large")
        d=json.loads(raw);date=t.astimezone(TOKYO).date().isoformat()
        require(d["marine"]["daily"]["time"][0]==date and d["weather"]["daily"]["time"][0]==date and len(d["daytime_daily"])==10,"daily contract")
        require(d["reference_tide"]["local_applicability_verified"] is False,"tide contract")
    return data,t
def read_remote(ftp,name):
    raw=bytearray()
    def cb(chunk):
        require(len(raw)+len(chunk)<LIMIT,"remote too large");raw.extend(chunk)
    ftp.retrbinary("RETR "+name,cb)
    return bytes(raw)
def publish(folder):
    data,t=payload(folder)
    require(os.environ.get("CONFIRM_KYUSHU")=="kyushu.rss7.net","confirmation")
    with ftplib.FTP_TLS(context=ssl.create_default_context(),timeout=25) as ftp:
        ftp.connect(HOST,21);ftp.login(os.environ["KYUSHU_FTP_USER"],os.environ["KYUSHU_FTP_PASSWORD"]);ftp.prot_p()
        ftp.cwd(DEST);require(ftp.pwd().rstrip("/")==DEST,"destination")
        files={name for name,f in ftp.mlsd() if f.get("type")=="file"}
        require({i+".json" for i in IDS}<=files,"initial files missing")
        old={}
        for i in data:
            raw=read_remote(ftp,i+".json");old[i]=raw
            old_stamp=stamp(raw,i)
            require(old_stamp<t or raw==data[i],"newer or conflicting forecast")
        print("PASS existing 13 forecast files; oldest/newest:",min(stamp(v,i) for i,v in old.items()).isoformat(),max(stamp(v,i) for i,v in old.items()).isoformat(),flush=True)
        for i,raw in data.items():
            if raw==old[i]:continue
            tmp=".ks-hourly-"+i+".part";name=i+".json"
            # Fixed maintenance-owned staging name; no other files or directories touched.
            require(ftp.pwd().rstrip("/")==DEST,"destination changed")
            ftp.storbinary("STOR "+tmp,io.BytesIO(raw))
            require(read_remote(ftp,tmp)==raw,"stage verification")
            require(read_remote(ftp,name)==old[i],"concurrent write")
            require(dt.datetime.now(TOKYO).date()==t.astimezone(TOKYO).date(),"date changed")
            ftp.rename(tmp,name)
            require(read_remote(ftp,name)==raw,"rename verification")
            print("Published",name,flush=True)
    for i,raw in data.items():
        digest=hashlib.sha256(raw).hexdigest()
        require(get(PUBLIC+i+".json?v="+digest[:16])==raw,"public verification "+i)
    print("PASS 13/13 public forecasts verified; generation",t.isoformat(),flush=True)
def self_test():
    start=dt.datetime(2026,11,29,tzinfo=TOKYO)
    def fixture(kind):
        records=[]
        for i,s in enumerate(SPOTS):
            lat,lon=(s[3],s[4]) if kind=="marine" else (s[1],s[2])
            row={"location_id":i,"latitude":lat,"longitude":lon,"utc_offset_seconds":32400}
            for group in ("hourly","daily"):
                times=expected_times(start,group=="hourly")
                row[group]={"time":times,**{k:[1]*len(times) for k in FEEDS[kind][1][group].split(",")}}
            records.append(row)
        return records
    m=validate_feed("marine",fixture("marine"),start)[0];w=validate_feed("weather",fixture("weather"),start)[0]
    m["hourly"]["wave_height"][5]=.4;m["hourly"]["wave_height"][17]=2;m["hourly"]["wave_height"][18]=9
    assert daily_rows(m,w)[0]["wave_min"]==.4 and daily_rows(m,w)[0]["wave_max"]==2
    m["hourly"]["wave_height"][8]=None;assert daily_rows(m,w)[0]["wave_max"] is None
    for kind,key,value in [("marine","location_id",9),("weather","utc_offset_seconds",0),("marine","latitude",0)]:
        r=fixture(kind);r[0][key]=value
        try: validate_feed(kind,r,start)
        except ValueError: pass
        else: raise AssertionError("bad input accepted")
    r=fixture("marine");r[0]["hourly"]["time"][0]="2026-11-28T00:00"
    try:validate_feed("marine",r,start)
    except ValueError:pass
    else:raise AssertionError("wrong date accepted")
    print("PASS offline checks: 13 spots, date, grid, timezone, daily aggregation and missing data")
if __name__=="__main__":
    try:
        mode=sys.argv[1]
        if mode=="test":self_test()
        elif mode=="prepare":prepare(Path(sys.argv[2]))
        elif mode=="publish":publish(Path(sys.argv[2]))
        else:raise ValueError("unknown mode")
    except Exception as error:
        print("Kyushu maintenance stopped:",type(error).__name__,file=sys.stderr)
        if isinstance(error,ValueError): print(str(error),file=sys.stderr)
        sys.exit(1)
