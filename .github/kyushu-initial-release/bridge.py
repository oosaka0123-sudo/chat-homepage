"""Validate an immutable public-only Kyushu bundle, then optionally upload and verify."""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import tempfile
import zipfile
import deploy_kyushu_preview as deploy

HERE = Path(__file__).resolve().parent
SOURCE = "ee58be54baf9d64afe098e3cc1ca15c14dd639eb"
ARCHIVE = "8e1d48f113f364d2f93d3e7ddf97936dc93d14870694d8aa656a051db11a588d"
SLUGS = "aoshima eguchihama hatsu hitotsuba ikuragahama kanegahama keya kizakihama koigaura mitoma okuragahama tategami umegahama".split()
EXPECTED = {"index.html","robots.txt","about/index.html","privacy/index.html","contact/index.html","contact/thanks/index.html","assets/app.js","assets/base.css","assets/kyushu.css"}
EXPECTED |= {f"spots/{slug}/index.html" for slug in SLUGS}
EXPECTED |= {f"data/{slug}.json" for slug in SLUGS}

def digest(data):
    return hashlib.sha256(data).hexdigest()

def prepare(target, require_fresh):
    manifest=json.loads((HERE/"manifest.json").read_text("utf-8"))
    archive=HERE/"site.zip"
    assert manifest["source_commit"]==SOURCE
    assert manifest["target"]=="https://kyushu.rss7.net/"
    assert manifest["archive_sha256"]==ARCHIVE==digest(archive.read_bytes())
    assert manifest["file_count"]==len(EXPECTED)==35
    assert set(manifest["files"])==EXPECTED
    stamps=set()
    with zipfile.ZipFile(archive) as z:
        assert len(z.infolist())==len(EXPECTED) and set(z.namelist())==EXPECTED
        for rel in sorted(EXPECTED):
            entry=z.getinfo(rel)
            declared=manifest["files"][rel]
            assert entry.file_size==declared["bytes"] and entry.file_size<2_000_000
            raw=z.read(rel)
            assert digest(raw)==declared["sha256"]
            if rel.endswith(".html"):
                assert b'content="noindex,nofollow"' in raw
            if rel=="robots.txt":
                assert b"Disallow: /" in raw
            if rel.startswith("data/"):
                obj=json.loads(raw)
                assert obj["id"]==Path(rel).stem
                stamps.add(obj["retrieved"])
            path=target/rel
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_bytes(raw)
    assert len(stamps)==1
    ts=dt.datetime.fromisoformat(stamps.pop())
    now=dt.datetime.now(dt.timezone(dt.timedelta(hours=9)))
    if require_fresh:
        assert ts.tzinfo and dt.timedelta(0)<=now-ts<dt.timedelta(hours=5)
        assert ts.astimezone(now.tzinfo).date()==now.date()
    print("PASS: exact 35-file public payload, pinned archive, noindex, per-file hashes")
    return sorted(EXPECTED,key=lambda s:(s=="index.html",s.endswith(".html"),s))

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--upload",action="store_true")
    args=p.parse_args()
    with tempfile.TemporaryDirectory() as tmp:
        deploy.SITE=Path(tmp)
        files=prepare(deploy.SITE,True)
        if args.upload:
            assert os.environ.get("CONFIRM_KYUSHU")=="kyushu.rss7.net"
            assert deploy.HOST=="ftp.lolipop.jp" and deploy.DEST=="/kyushu"
            for rel in files:
                assert digest((deploy.SITE/rel).read_bytes())==json.loads((HERE/"manifest.json").read_text("utf-8"))["files"][rel]["sha256"]
            deploy.upload(files)
            deploy.verify(files)

if __name__=="__main__":
    main()
