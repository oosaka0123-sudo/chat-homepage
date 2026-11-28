"""Manual Kyushu-only noindex preview upload; never remove server files."""
import argparse
import datetime as dt
import io
import re
import ftplib
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import ssl
import sys
from urllib.parse import quote
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "build/site"
HOST = "ftp.lolipop.jp"
DEST = "/kyushu"
URL = "https://kyushu.rss7.net/"


def bundle():
    spots = json.loads((ROOT / "config/representative-spots.json").read_text(encoding="utf-8"))["spots"]
    slugs = {s["slug"] for s in spots}
    if len(slugs) != 13:
        raise ValueError("Unexpected spot count")
    expected = {"index.html", "robots.txt", "about/index.html", "privacy/index.html",
                "contact/index.html", "contact/thanks/index.html",
                "assets/app.js", "assets/base.css", "assets/kyushu.css"}
    expected.update(f"spots/{slug}/index.html" for slug in slugs)
    expected.update(f"data/{slug}.json" for slug in slugs)
    actual = {p.relative_to(SITE).as_posix() for p in SITE.rglob("*") if p.is_file()}
    if actual != expected:
        raise ValueError("Unexpected or missing build files")
    for relative in sorted(expected):
        p = SITE / relative
        if p.is_symlink() or not p.resolve().is_relative_to(SITE.resolve()):
            raise ValueError("Unexpected file location")
        if relative.endswith(".html") and 'content="noindex,nofollow"' not in p.read_text(encoding="utf-8"):
            raise ValueError("Search indexing must remain disabled for preview")
        if relative.startswith("data/"):
            record = json.loads(p.read_text(encoding="utf-8"))
            if record["id"] != p.stem:
                raise ValueError("Forecast ID mismatch")
    if "Disallow: /" not in (SITE / "robots.txt").read_text(encoding="utf-8"):
        raise ValueError("Preview robots guard missing")
    # Publish the home page last.
    return sorted(expected, key=lambda s: (s == "index.html", s.endswith(".html"), s))


def remote_bytes(ftp, name, limit=2_000_000):
    chunks = bytearray()
    def receive(chunk):
        if len(chunks) + len(chunk) > limit:
            raise ValueError("Remote file exceeds allowed size")
        chunks.extend(chunk)
    ftp.retrbinary("RETR " + name, receive)
    return bytes(chunks)


def staged_name(relative, raw):
    # A retry of exactly the same payload uses the same staging name.
    return ".ks-kyushu-" + hashlib.sha256(raw).hexdigest() + "-" + PurePosixPath(relative).name + ".part"


def forecast_stamp(raw, expected_id):
    record = json.loads(raw)
    if record["id"] != expected_id:
        raise ValueError("Forecast ID mismatch")
    stamp = dt.datetime.fromisoformat(record["retrieved"])
    if stamp.tzinfo is None:
        raise ValueError("Forecast timestamp has no offset")
    return stamp


def upload(files, refresh=False):
    user, password = os.environ.get("KYUSHU_FTP_USER"), os.environ.get("KYUSHU_FTP_PASSWORD")
    if not user or not password:
        raise ValueError("Kyushu FTPS credentials are not configured")
    payloads = {rel: (SITE / rel).read_bytes() for rel in files}
    if not payloads or any(len(raw) > 2_000_000 for raw in payloads.values()):
        raise ValueError("Invalid payload size")
    allowed = set(payloads)
    if refresh:
        if len(allowed) != 13 or any(not re.fullmatch(r"data/[a-z0-9-]+\.json", rel) for rel in allowed):
            raise ValueError("Refresh must contain exactly 13 forecast files")
        stamps = {forecast_stamp(raw, PurePosixPath(rel).stem) for rel, raw in payloads.items()}
        now = dt.datetime.now(dt.timezone(dt.timedelta(hours=9)))
        if len(stamps) != 1:
            raise ValueError("Mixed forecast generation")
        stamp = next(iter(stamps))
        if not dt.timedelta(0) <= now - stamp < dt.timedelta(hours=5) or stamp.astimezone(now.tzinfo).date() != now.date():
            raise ValueError("Forecast snapshot stale or future")
    stages = {str(PurePosixPath(rel).with_name(staged_name(rel, raw))): rel for rel, raw in payloads.items()}
    directories = {str(parent) for name in allowed for parent in PurePosixPath(name).parents if str(parent) != "."}
    existing = set()
    with ftplib.FTP_TLS(context=ssl.create_default_context(), timeout=25) as ftp:
        ftp.connect(HOST, 21)
        ftp.login(user, password)
        ftp.prot_p()

        def enter(folder=""):
            remote = DEST + ("/" + folder if folder else "")
            ftp.cwd(remote)
            if ftp.pwd().rstrip("/") != remote:
                raise ValueError("Unexpected remote folder")

        def scan(folder=""):
            enter(folder)
            for name, facts in list(ftp.mlsd()):
                kind = facts.get("type", "")
                if kind in ("cdir", "pdir") or name in (".", ".."):
                    continue
                if not name or "/" in name or chr(92) in name or chr(13) in name or chr(10) in name:
                    raise ValueError("Unexpected remote entry")
                relative = folder + "/" + name if folder else name
                if kind == "dir" and relative in directories:
                    scan(relative)
                    enter(folder)
                elif kind == "file" and relative in allowed:
                    old = remote_bytes(ftp, name)
                    if old == payloads[relative]:
                        existing.add(relative)
                    elif refresh:
                        if forecast_stamp(old, PurePosixPath(relative).stem) >= stamp:
                            raise ValueError("Existing forecast newer or conflicting")
                    else:
                        raise ValueError("Existing remote file differs; upload refused")
                elif kind == "file" and relative in stages:
                    # Only our exact content-addressed staging file is resumable.
                    old = remote_bytes(ftp, name)
                    if not payloads[stages[relative]].startswith(old):
                        raise ValueError("Staging bytes differ; upload refused")
                else:
                    raise ValueError("Unexpected remote entry; upload refused")

        # For refresh, do not inspect or touch unrelated HTML or other directories.
        scan("data" if refresh else "")
        if refresh:
            enter("data")
            live = {name for name, facts in ftp.mlsd() if facts.get("type") == "file" and "data/" + name in allowed}
            if len(live) != len(allowed):
                raise ValueError("Initial publication incomplete")
        for relative in files:
            if relative in existing:
                continue
            part = PurePosixPath(relative)
            if part.is_absolute() or ".." in part.parts:
                raise ValueError("Unsafe path")
            enter()
            for segment in part.parts[:-1]:
                try:
                    ftp.cwd(segment)
                except ftplib.error_perm:
                    if refresh:
                        raise
                    ftp.mkd(segment)
                    ftp.cwd(segment)
            directory = str(PurePosixPath(DEST) / part.parent)
            if ftp.pwd().rstrip("/") != directory.rstrip("/"):
                raise ValueError("Remote path mismatch")
            name = staged_name(relative, payloads[relative])
            # Never expose a partial JSON or HTML at its final URL.
            with io.BytesIO(payloads[relative]) as local:
                ftp.storbinary("STOR " + name, local)
            if remote_bytes(ftp, name) != payloads[relative]:
                raise ValueError("Staging verification failed")
            current = {n for n, facts in ftp.mlsd() if facts.get("type") == "file"}
            if part.name in current:
                old = remote_bytes(ftp, part.name)
                if old == payloads[relative]:
                    # A concurrent identical writer is safe, but leave staging for manual reconciliation.
                    raise ValueError("Concurrent identical upload; reconcile staging")
                if not refresh or forecast_stamp(old, part.stem) >= stamp:
                    raise ValueError("Concurrent write detected; upload refused")
            elif refresh:
                raise ValueError("Published forecast disappeared")
            ftp.rename(name, part.name)
            if remote_bytes(ftp, part.name) != payloads[relative]:
                raise ValueError("Published bytes differ after rename")
            print("Uploaded " + relative, flush=True)


def verify(files):
    for relative in files:
        local = (SITE / relative).read_bytes()
        digest = hashlib.sha256(local).hexdigest()
        endpoint = URL + quote(relative, safe="/") + "?v=" + digest[:12]
        request = Request(endpoint, headers={"Cache-Control": "no-cache", "Accept-Encoding": "identity"})
        with urlopen(request, timeout=25) as response:
            if not response.geturl().startswith(URL) or response.status != 200:
                raise ValueError("Unexpected HTTPS target/status")
            remote = response.read(len(local) + 1)
        if hashlib.sha256(remote).hexdigest() != digest:
            raise ValueError("Published content differs: " + relative)
        print("Verified " + relative, flush=True)
    with urlopen(URL, timeout=25) as response:
        if response.geturl() != URL or response.status != 200:
            raise ValueError("Unexpected homepage target/status")
        if b'content="noindex,nofollow"' not in response.read():
            raise ValueError("Preview homepage guard missing")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument("--refresh", action="store_true", help="Update only the 13 forecast JSON files")
    args = parser.parse_args()
    files = bundle()
    if args.refresh:
        files = [rel for rel in files if rel.startswith("data/")]
    if args.verify_only:
        verify(files)
    else:
        upload(files, refresh=args.refresh)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        # Do not print raw server replies, which may contain credential details.
        print("Deployment stopped: " + type(error).__name__, file=sys.stderr)
        sys.exit(1)
