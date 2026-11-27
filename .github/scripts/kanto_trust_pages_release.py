#!/usr/bin/env python3
"""Guarded one-off release of Kanto's 3 trust pages only.

Downloads an exact-main-tree successful GitHub Pages artifact, backs up the three
Lolipop HTML files, and replaces only those files. No data or CSS uploads.
"""
import re
import sys
import tempfile
from pathlib import Path
import kanto_model_sync as base

PAGES=('about/index.html','privacy/index.html','contact/index.html')
REQUIRED={
    'about/index.html': (b'ABOUT KANTO SURFER KS', '波の恵みを'.encode(), '大切にする5つのこと'.encode()),
    'privacy/index.html': (b'PRIVACY &amp; TRUST','個人情報の取得と利用'.encode(),'2026年11月27日'.encode()),
    'contact/index.html': (b'id="ks-inquiry-form"',b'id="ks-contact-script"','送信機能はありません'.encode()),
}
FACEBOOK=b'https://www.facebook.com/profile.php?id=61595144364123'
INSTAGRAM=b'https://www.instagram.com/kanto_surfer_ks/'
assert len(PAGES)==3

def verify(rel,payload):
    if not payload.startswith(b'<!doctype html>'):
        raise ValueError(f'{rel}: document structure invalid')
    for token in REQUIRED[rel]:
        if token not in payload:
            raise ValueError(f'{rel}: required component missing: {token!r}')
    for token in (FACEBOOK,INSTAGRAM,b'<header class="site-header">',b'<footer class="site-footer">',
                  b'footer-spot-grid',b'id="ks-info-styles"',b'content="index,follow"',
                  ('href="https://kanto.rss7.net/'+rel.replace('index.html','')+'"').encode()):
        if token not in payload:
            raise ValueError(f'{rel}: missing required site feature: {token!r}')
    footer=re.search(rb'<div class="footer-spot-grid">(.*?)</div>',payload,re.S)
    if footer is None or footer.group(1).count(b'<a ')!=9:
        raise ValueError(f'{rel}: footer no longer has nine spots')
    if b'https://www.facebook.com/kansaisurfer/' in payload:
        raise ValueError(f'{rel}: stale Kansai Facebook link')
    if rel!='contact/index.html' and b'id="ks-contact-script"' in payload:
        raise ValueError(f'{rel}: unexpected contact JS')
    if rel=='contact/index.html' and re.search(rb'<form[^>]+\saction=',payload):
        raise ValueError('Contact form must not pretend to submit to a server')

def main():
    run=base.selected_build()
    if run is None:
        raise RuntimeError('No successful Kanto build with main-equivalent tree in the last five hours; production unchanged')
    print('TRUST_SOURCE run',run['id'],'sha',run['head_sha'][:12],flush=True)
    with base.source_artifact(run) as tar:
        pages={p:base.extract_member(tar,p) for p in PAGES}
    for path,data in pages.items():verify(path,data)
    print('PASS: all three generated pages satisfy sources, links, SEO, nine spots and contact safety',flush=True)

    with tempfile.TemporaryDirectory(prefix='kanto-trust-release-') as tmp:
        root=Path(tmp)
        before=root/'before'
        staged=root/'staged'
        for page in PAGES:
            (before/page).parent.mkdir(parents=True,exist_ok=True)
            (staged/page).parent.mkdir(parents=True,exist_ok=True)
            (staged/page).write_bytes(pages[page])
        base.ftp([f'get "/kanto/{rel}" -o "{before/rel}"' for rel in PAGES])
        if not all((before/rel).is_file() for rel in PAGES):
            raise RuntimeError('Incomplete backup; no upload attempted')
        for rel in PAGES:
            old=(before/rel).read_bytes()
            if base.live_fetch(rel,'trust_preflight')!=old:
                raise RuntimeError('Concurrent production update detected: '+rel)
            if b'<footer class="site-footer">' not in old:
                raise RuntimeError('Unexpected old HTML layout: '+rel)
        changed=[rel for rel in PAGES if pages[rel]!=(before/rel).read_bytes()]
        if not changed:
            print('PASS: three pages already current; nothing to transfer',flush=True)
            return
        print(f'TRUST_UPLOAD {len(changed)} of 3 HTML; backup complete; zero remote deletes',flush=True)
        try:
            base.ftp([f'put "{staged/rel}" -o "/kanto/{rel}"' for rel in changed])
            for rel in PAGES:
                public=base.live_fetch(rel,'trust_verify')
                if public != pages[rel]:
                    raise RuntimeError('Public byte mismatch: '+rel)
                verify(rel,public)
            print('PASS: 3/3 public information pages byte-identical and all requirements present',flush=True)
        except Exception:
            try:
                base.ftp([f'put "{before/rel}" -o "/kanto/{rel}"' for rel in changed])
                print('ROLLBACK: three old pages restored',file=sys.stderr,flush=True)
            except Exception:
                print('CRITICAL: rollback failed, check /kanto/about,privacy,contact',file=sys.stderr,flush=True)
            raise

if __name__=='__main__':
    main()
