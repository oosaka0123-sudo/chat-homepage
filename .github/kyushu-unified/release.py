"""One-off Kyushu preview replacement. Exact old/new public byte scope, FTPS and HTTPS verification."""
import datetime as dt
import ftplib, hashlib, io, json, os, ssl, sys, zipfile
from pathlib import Path, PurePosixPath
from urllib.request import Request, urlopen

HERE=Path(__file__).resolve().parent
URL="https://kyushu.rss7.net/"
DEST="/kyushu"
SLUGS="aoshima eguchihama hatsu hitotsuba ikuragahama kanegahama keya kizakihama koigaura mitoma okuragahama tategami umegahama".split()
EXPECTED={"index.html","robots.txt","about/index.html","privacy/index.html","contact/index.html","contact/thanks/index.html","assets/app.js","assets/base.css","assets/kyushu.css"}
EXPECTED|={f"spots/{s}/index.html" for s in SLUGS}|{f"data/{s}.json" for s in SLUGS}
def sha(b): return hashlib.sha256(b).hexdigest()
def require(ok, label):
    if not ok: raise ValueError(label)
def matches(raw, meta):
    return len(raw)==meta["bytes"] and sha(raw)==meta["sha256"]
def load():
    old=json.loads((HERE/"old-manifest.json").read_text("utf-8"))
    new=json.loads((HERE/"manifest.json").read_text("utf-8"))
    require(old["source_commit"]=="14ae3945ce7ec536c37325db031ae1ff2f6eeea4","old source")
    require(old["archive_sha256"]=="e2ed66594d1af0111591ec8b95257eb3a1f6cb00766a32e8ada97a6f49d2da19","old release")
    require(new["source_commit"]=="f2ccec52b1e9fce88539222ec31a5b45c00dd0a2","new source")
    require(new["archive_sha256"]=="afe24b58c458f62566088b69ee3d2687307d795a97f44d935e822bb90ef6bd5a","new release")
    for m in (old,new): require(m["target"]==URL and m["file_count"]==35 and set(m["files"])==EXPECTED,"manifest scope")
    archive=(HERE/"site.zip").read_bytes()
    require(sha(archive)==new["archive_sha256"],"ZIP digest")
    with zipfile.ZipFile(io.BytesIO(archive)) as z:
        require(len(z.namelist())==35 and set(z.namelist())==EXPECTED,"ZIP scope")
        payload={p:z.read(p) for p in sorted(EXPECTED)}
    stamps=set()
    for p,raw in payload.items():
        require(len(raw)<2_000_000 and matches(raw,new["files"][p]),"file digest")
        if p.endswith(".html"): require(b'content="noindex,nofollow"' in raw,"index guard")
        if p.startswith("data/"):
            d=json.loads(raw)
            require(d["id"]==PurePosixPath(p).stem and len(d["daytime_daily"])==10 and d["reference_tide"]["local_applicability_verified"] is False,"data contract")
            stamps.add(d["retrieved"])
    require(b"Disallow: /" in payload["robots.txt"],"robots guard")
    require(len(stamps)==1 and new["retrieved"] in stamps,"mixed generation")
    ts=dt.datetime.fromisoformat(stamps.pop());now=dt.datetime.now(dt.timezone(dt.timedelta(hours=9)))
    require(ts.tzinfo and dt.timedelta(0)<=now-ts<dt.timedelta(hours=5) and ts.astimezone(now.tzinfo).date()==now.date(),"stale release")
    changed={p for p in EXPECTED if old["files"][p]!=new["files"][p]}
    allowed={"assets/app.js","assets/kyushu.css"}|{f"spots/{s}/index.html" for s in SLUGS}|{f"data/{s}.json" for s in SLUGS}
    require(changed==allowed,"unexpected changed-file scope")
    print("PASS immutable 35-file payload; changed files",len(changed),flush=True)
    return old,new,payload,changed
def connect():
    ftp=ftplib.FTP_TLS(context=ssl.create_default_context(),timeout=25)
    ftp.connect("ftp.lolipop.jp",21);ftp.login(os.environ["KYUSHU_FTP_USER"],os.environ["KYUSHU_FTP_PASSWORD"]);ftp.prot_p()
    ftp.cwd(DEST);require(ftp.pwd().rstrip("/")==DEST,"destination")
    return ftp
def enter(ftp,p):
    parent=str(PurePosixPath(p).parent)
    dest=DEST if parent=="." else DEST+"/"+parent
    ftp.cwd(dest);require(ftp.pwd().rstrip("/")==dest,"path mismatch")
    return PurePosixPath(p).name
def read(ftp,p):
    name=enter(ftp,p);b=bytearray()
    def cb(chunk):
        require(len(b)+len(chunk)<2_000_000,"remote too large")
        b.extend(chunk)
    ftp.retrbinary("RETR "+name,cb)
    return bytes(b)
def public(p,meta):
    req=Request(URL+p+"?ks="+meta["sha256"][:16],headers={"Cache-Control":"no-cache","Accept-Encoding":"identity"})
    with urlopen(req,timeout=25) as r:
        require(r.status==200 and r.geturl().startswith(URL),"HTTP target")
        raw=r.read(meta["bytes"]+1)
    require(matches(raw,meta),"HTTP mismatch "+p)
def stage(ftp,p,raw):
    name=enter(ftp,p)
    tmp=".ks-kyushu-"+sha(raw)+"-"+name+".part"
    names={n for n,f in ftp.mlsd() if f.get("type")=="file"}
    require(tmp not in names,"unknown existing stage")
    ftp.storbinary("STOR "+tmp,io.BytesIO(raw))
    folder=str(PurePosixPath(p).parent)
    tmp_rel=tmp if folder=="." else folder+"/"+tmp
    require(read(ftp,tmp_rel)==raw,"stage verification")
    return tmp
def replace(ftp,p,tmp,expected_current):
    require(read(ftp,p)==expected_current,"concurrent write "+p)
    name=enter(ftp,p);ftp.rename(tmp,name)
def run():
    old,new,payload,changed=load()
    if "--publish" not in sys.argv: return
    require(os.environ.get("CONFIRM_KYUSHU")=="kyushu.rss7.net","confirmation")
    backup={}; staged={}; touched=[]
    order=sorted(changed,key=lambda p:(p=="assets/app.js",not p.startswith("data/"),p))
    with connect() as ftp:
        for p in sorted(EXPECTED):
            raw=read(ftp,p);require(matches(raw,old["files"][p]),"old FTPS mismatch "+p)
            public(p,old["files"][p]);backup[p]=raw
        print("PASS old 35 files verified over FTPS and HTTPS; no new writes yet",flush=True)
        try:
            for p in order: staged[p]=stage(ftp,p,payload[p])
            for p in order:
                touched.append(p)
                replace(ftp,p,staged[p],backup[p])
                require(read(ftp,p)==payload[p],"rename mismatch "+p)
                print("Published "+p,flush=True)
            for p in sorted(EXPECTED): public(p,new["files"][p])
            print("PASS all 35 public file hashes",flush=True)
        except Exception:
            print("STOP; restoring changed final paths from verified backup",flush=True)
            try:
                with connect() as restore:
                    for p in reversed(touched):
                        actual=read(restore,p)
                        if actual==backup[p]: continue
                        require(actual==payload[p],"rollback concurrent write "+p)
                        tmp=stage(restore,p,backup[p])
                        replace(restore,p,tmp,actual)
                        require(read(restore,p)==backup[p],"restore mismatch")
                    for p in sorted(EXPECTED): public(p,old["files"][p])
                    print("PASS previous public file hashes restored; staging leftovers may require inspection",flush=True)
            except Exception:
                print("CRITICAL: rollback not verified; inspect before retry",flush=True)
            raise
if __name__=="__main__":
    try: run()
    except Exception as e:
        print("Stopped:",type(e).__name__,file=sys.stderr);sys.exit(1)
