#!/usr/bin/env python3
"""Publish ONLY Kanto's contact acknowledgement and the success redirect script.

The current contact HTML is backed up and patched exclusively within the inline
contact JavaScript / scoped CSS. No PHP, emails, forecast data or other pages
are touched. Confirm exact public bytes and rollback on any mismatch.
"""
import re
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
import kanto_model_sync as base

CONTACT='contact/index.html'
THANKS='contact/thanks/index.html'
CONTENT_URL='https://kanto.rss7.net/contact/'
THANKS_URL='https://kanto.rss7.net/contact/thanks/'
CSS=re.compile(rb'<style id="ks-info-styles">.*?</style>',re.S)
HELPER=re.compile(rb'<script id="ks-contact-script">.*?</script>',re.S)

def require_single(pattern,html,label):
    parts=pattern.findall(html)
    if len(parts)!=1:raise RuntimeError('Expected exactly one '+label)
    return parts[0]

def verify_thanks(html,sitemap):
    required=[
      b'<!doctype html>',b'name="robots" content="noindex,follow"',
      b'href="https://kanto.rss7.net/contact/thanks/"',
      'お問い合わせありがとうございました。'.encode('utf-8'),
      b'id="ks-thankyou-confirmed" hidden',
      b'id="ks-thankyou-unverified" hidden',
      b'id="ks-thanks-script"',
      b'href="../../styles.css?v=',b'src="../../app.js?v=',
      b'href="../../about/"',b'href="../../privacy/"',
      b'https://www.facebook.com/profile.php?id=61595144364123',
      b'https://www.instagram.com/kanto_surfer_ks/',
      b'href="/"',b'href="/contact/"',
      b'footer-spot-grid'
    ]
    for item in required:
        if item not in html:raise RuntimeError('Thank-you source lacks required element')
    if b'/contact/thanks/' in sitemap:raise RuntimeError('Noindex route appears in sitemap')
    grid=re.search(rb'<div class="footer-spot-grid">([\s\S]*?)</div>',html)
    if grid is None or grid.group(1).count(b'<a ')!=9:raise RuntimeError('Nine footer spots are missing')

def verify_contact(html):
    required=[b'action="send.php"',b'id="ks-inquiry-form"',b'id="ks-contact-script"',
      b'id="ks-contact-token"',b'footer-spot-grid',
      b'https://www.facebook.com/profile.php?id=61595144364123']
    for item in required:
        if item not in html:raise RuntimeError('Contact source lacks expected backend or navigation')
    if b"window.location.assign(new URL('thanks/',window.location.href).href)" not in html:
        raise RuntimeError('Redirect on successful contact response is missing')
    if b"if(!response.ok||!data.success)throw" not in html:
        raise RuntimeError('Form may redirect before server success')
    require_single(CSS,html,'scoped contact CSS')
    require_single(HELPER,html,'contact form helper')

def get_existing_thanks():
    req=urllib.request.Request(THANKS_URL+'?release_probe=20261127',
      headers={'Cache-Control':'no-cache','User-Agent':'kanto-contact-thanks-release'})
    try:
        with urllib.request.urlopen(req,timeout=30) as r:
            if r.status==200:return True
            raise RuntimeError('Unexpected status on existing thank-you route: '+str(r.status))
    except urllib.error.HTTPError as e:
        if e.code==404:return False
        raise RuntimeError('Cannot inspect thank-you route safely: '+str(e.code))

def main():
    run=base.selected_build()
    if run is None:raise RuntimeError('No verified Kanto main-equivalent Pages artifact; no release')
    print('SOURCE KANTO RUN',run['id'],'SHA',run['head_sha'][:12],flush=True)
    with base.source_artifact(run) as a:
        source_contact=base.extract_member(a,CONTACT)
        source_thanks=base.extract_member(a,THANKS)
        sitemap=base.extract_member(a,'sitemap.xml')
    verify_thanks(source_thanks,sitemap)
    verify_contact(source_contact)
    with tempfile.TemporaryDirectory(prefix='kanto-thanks-release-') as tmp:
        root=Path(tmp)
        before=root/'before'
        stage=root/'stage'
        for rel in [CONTACT,THANKS]:
            (before/rel).parent.mkdir(parents=True,exist_ok=True)
            (stage/rel).parent.mkdir(parents=True,exist_ok=True)
        base.ftp([f'get "/kanto/{CONTACT}" -o "{before/CONTACT}"'])
        if not (before/CONTACT).is_file():raise RuntimeError('Missing contact backup')
        existing=get_existing_thanks()
        if existing:
            base.ftp([f'get "/kanto/{THANKS}" -o "{before/THANKS}"'])
            if not (before/THANKS).is_file():raise RuntimeError('Missing previous thank-you page backup')
        old=(before/CONTACT).read_bytes()
        # The only changes allowed to existing contact markup are scoped CSS and helper.
        new=CSS.sub(lambda _:require_single(CSS,source_contact,'new CSS'),old)
        new=HELPER.sub(lambda _:require_single(HELPER,source_contact,'new helper'),new)
        if CSS.sub(b'',HELPER.sub(b'',new))!=CSS.sub(b'',HELPER.sub(b'',old)):
            raise RuntimeError('Non-contact text would be modified; refusing deployment')
        verify_contact(new)
        (stage/CONTACT).write_bytes(new)
        (stage/THANKS).write_bytes(source_thanks)
        if base.live_fetch(CONTACT,'thanks_preflight')!=old:
            raise RuntimeError('Concurrent contact page change: refusing deployment')
        if existing and base.live_fetch(THANKS,'thanks_preflight')!=(before/THANKS).read_bytes():
            raise RuntimeError('Concurrent thank-you page change: refusing deployment')
        changed=[rel for rel in [CONTACT,THANKS] if not (before/rel).is_file()
                 or (stage/rel).read_bytes()!=(before/rel).read_bytes()]
        if not changed:
            print('PASS: thanks page and contact helper already published',flush=True)
            return
        print('UPLOAD',len(changed),'allowlisted HTML files (PHP and data untouched)',flush=True)
        try:
            base.ftp(['mkdir -p "/kanto/contact/thanks"']+
                [f'put "{stage/rel}" -o "/kanto/{rel}"' for rel in changed])
            for rel in [CONTACT,THANKS]:
                if base.live_fetch(rel,'thanks_verify')!=(stage/rel).read_bytes():
                    raise RuntimeError('Public byte mismatch: '+rel)
            verify_thanks(base.live_fetch(THANKS,'thanks_design'),sitemap)
            verify_contact(base.live_fetch(CONTACT,'thanks_form'))
            print('PASS: production contact and /contact/thanks/ are byte-verified; no real mail was sent',flush=True)
        except Exception:
            print('ERROR: restoring old contact pages',file=sys.stderr,flush=True)
            try:
                restore=[f'put "{before/rel}" -o "/kanto/{rel}"' for rel in changed if (before/rel).is_file()]
                if THANKS in changed and not existing:
                    restore.append(f'rm "/kanto/{THANKS}"')
                if restore:base.ftp(restore)
                print('ROLLBACK: restored original contact page and prior thank-you state',file=sys.stderr,flush=True)
            except Exception:
                print('CRITICAL: rollback incomplete; inspect contact and thanks pages',file=sys.stderr,flush=True)
            raise
if __name__=='__main__':main()
