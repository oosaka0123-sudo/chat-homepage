#!/usr/bin/env python3
"""One-off Kanto email contact deployment, using Kansai's verified mail addresses.
No third-party APIs, no GitHub-stored recipient addresses, no unrelated files changed.
"""
import base64
import datetime
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from http.cookiejar import CookieJar
from urllib.parse import urlencode
from urllib.request import HTTPCookieProcessor, Request, build_opener
import kanto_model_sync as base

BACKEND=('common.php','challenge.php','send.php')
HTML=('contact/index.html','privacy/index.html')
ALL=HTML+tuple('contact/'+x for x in BACKEND)
EXPECTED_DOM='rss7.net'

def safe_emails(php):
    result={}
    for key in ('TO_EMAIL','FROM_EMAIL'):
        matches=re.findall(
            r'(?m)^\s*\$'+key+r'\s*=\s*([\'"])([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+)\1\s*;',
            php)
        if len(matches)!=1:
            raise RuntimeError('Kansai mail variable declaration not identifiable: '+key)
        address=matches[0][1]
        if not re.fullmatch(r'[A-Za-z0-9._%+-]+@rss7\.net',address,re.I):
            raise RuntimeError('Kansai email domain unexpectedly differs from verified rss7.net')
        result[key]=address
    return result

def from_repo(commit,path):
    record=base.api('contents/'+path+'?ref='+commit)
    if record.get('type')!='file' or record.get('encoding')!='base64':
        raise RuntimeError('Invalid GitHub source file '+path)
    return base64.b64decode(record['content'])

def php_lint(path):
    result=subprocess.run(['php','-l',str(path)],capture_output=True,text=True,timeout=20)
    if result.returncode:
        raise RuntimeError('PHP syntax check failed '+path.name)

def ftp_names():
    lines=[
       'set cmd:fail-exit true',
       'set ftp:ssl-force true','set ftp:ssl-protect-data true',
       'set ssl:verify-certificate true','set ftp:passive-mode true',
       'set net:timeout 20','set net:max-retries 3',
       'open -u "'+base.FTP_USER+'","'+base.FTP_PASSWORD+'" ftp.lolipop.jp',
       'cls -1 "/kanto/contact"','bye'
    ]
    r=subprocess.run(['lftp'],input='\n'.join(lines)+'\n',
                     text=True,capture_output=True,timeout=90)
    if r.returncode:
        raise RuntimeError('Could not inspect target directory; aborting without upload')
    return {x.strip().split('/')[-1] for x in r.stdout.splitlines() if x.strip()}

def verify_html(p,s):
    mandatory=(
        b'<html lang="ja">',
        b'footer-spot-grid',
        b'https://www.instagram.com/kanto_surfer_ks/',
        b'https://www.facebook.com/profile.php?id=61595144364123',
        b'<link rel="canonical" href="https://kanto.rss7.net/'+
           p.removesuffix('index.html').encode()+b'"',
    )
    for item in mandatory:
        if item not in s: raise RuntimeError('Required HTML element missing: '+p)
    if p.startswith('contact'):
        for token in (b'action="send.php"',b'name="purpose"',b'name="email"',
                      b'name="captcha"',b'id="ks-contact-token"',
                      b'id="ks-contact-script"',b'challenge.php'):
            if token not in s: raise RuntimeError('Contact markup is incomplete '+repr(token))
        if b'ks-inquiry-copy' in s:raise RuntimeError('Legacy copy-only contact form still rendered')
    else:
        for token in ('お問い合わせフォーム'.encode(),'セッションCookie'.encode(),'自動返信'.encode()):
            if token not in s:raise RuntimeError('New privacy notice missing '+repr(token))
    return True

def smoke_live(from_address):
    import urllib.error
    from urllib.request import urlopen
    invalid=Request('https://kanto.rss7.net/contact/send.php',data=b'purpose=other',
        method='POST',headers={'Content-Type':'application/x-www-form-urlencoded','Origin':'https://kanto.rss7.net'})
    try:
        urlopen(invalid,timeout=20)
        raise RuntimeError('A POST without CAPTCHA was unexpectedly accepted')
    except urllib.error.HTTPError as e:
        if e.code!=422:raise RuntimeError('Missing CAPTCHA request returned unexpected HTTP '+str(e.code))
    agent=build_opener(HTTPCookieProcessor(CookieJar()))
    start=agent.open(Request('https://kanto.rss7.net/contact/challenge.php',
                            headers={'Accept':'application/json','Cache-Control':'no-cache'}),timeout=30)
    obj=json.load(start)
    if not obj.get('success') or not re.fullmatch(r'\d+ \+ \d+ = \?',obj.get('question','')) or len(obj.get('token',''))!=48:
        raise RuntimeError('Real server CAPTCHA could not be started')
    a,b=map(int,re.findall(r'\d+',obj['question']))
    time.sleep(2.3)
    values={
        'purpose':'other',
        'name':'KS システム疎通テスト',
        'email':from_address,
        'phone':'',
        'message':'【関東サーファーKS 本番送信検査】新しいお問い合わせフォームのメール送信テストです。これは運用確認用のテスト送信です。',
        'website':'',
        'token':obj['token'],
        'captcha':str(a+b),
    }
    body=urlencode(values).encode('utf-8')
    request=Request('https://kanto.rss7.net/contact/send.php',data=body,method='POST',
        headers={'Content-Type':'application/x-www-form-urlencoded','Origin':'https://kanto.rss7.net'})
    try:
        with agent.open(request,timeout=35) as r:
            j=json.load(r)
            if r.status!=200 or not j.get('success'):
                raise RuntimeError('Production PHP did not accept a valid form POST')
    except urllib.error.HTTPError as e:
        # No body, sender details or other information are printed.
        raise RuntimeError('Production mail transport rejected the test (HTTP '+str(e.code)+')')
    print('PASS: real server CAPTCHA + one mail-acceptance test completed (delivery to mailbox not independently verified)',flush=True)

def main():
    run=base.selected_build()
    if not run:raise RuntimeError('No verified successful Kanto main-equivalent build; no deployment')
    sha=run['head_sha']
    print('SOURCE VERIFIED KANTO PAGES RUN',run['id'],'SHA',sha[:12],flush=True)
    with base.source_artifact(run) as artifact:
        html={p:base.extract_member(artifact,p) for p in HTML}
    for p,s in html.items():verify_html(p,s)
    templates={p:from_repo(sha,'backend/contact/'+p) for p in BACKEND}

    with tempfile.TemporaryDirectory(prefix='ks-kanto-real-contact-') as dirname:
        root=Path(dirname)
        before=root/'before';stage=root/'stage'
        for p in ALL:
            (before/p).parent.mkdir(parents=True,exist_ok=True)
            (stage/p).parent.mkdir(parents=True,exist_ok=True)

        # This existing source is used ONLY to copy administrator mail settings.
        kansai=root/'kansai-contact.php'
        base.ftp([f'get "/kansai/contact.php" -o "{kansai}"'])
        php=kansai.read_text(encoding='utf-8')
        emails=safe_emails(php)
        kansai.unlink()
        print('PASS: verified Kansai sender/recipient reused, without printing their values',flush=True)

        for p,c in html.items():(stage/p).write_bytes(c)
        for file,original in templates.items():
            content=original.decode('utf-8')
            if file=='send.php':
                for key,placeholder in (('TO_EMAIL','__KS_CONTACT_TO__'),('FROM_EMAIL','__KS_CONTACT_FROM__')):
                    sentinel="'"+placeholder+"'"
                    if content.count(sentinel)!=1:raise RuntimeError('Mail address substitution count not one')
                    content=content.replace(sentinel,"'"+emails[key]+"'")
            elif '__KS_CONTACT_TO__' in content or '__KS_CONTACT_FROM__' in content:
                raise RuntimeError('Mail placeholder in unexpected backend file')
            if file=='send.php' and ('__KS_CONTACT_TO__' in content or '__KS_CONTACT_FROM__' in content):
                raise RuntimeError('Mail template still contains placeholders')
            target=stage/'contact'/file
            target.write_text(content,encoding='utf-8')
            php_lint(target)

        # Preflight: only the two HTML pages and three exact PHP filenames may change.
        filenames=ftp_names()
        existing_php=[f for f in BACKEND if f in filenames]
        for p in HTML:
            base.ftp([f'get "/kanto/{p}" -o "{before/p}"'])
            if base.live_fetch(p,'before_contact')!=(before/p).read_bytes():
                raise RuntimeError('Concurrent change to '+p)
        for f in existing_php:
            base.ftp([f'get "/kanto/contact/{f}" -o "{before/"contact"/f}"'])
            if (before/'contact'/f).read_bytes()!=(stage/'contact'/f).read_bytes():
                raise RuntimeError('Unexpected pre-existing backend differs: '+f)

        changed=[p for p in HTML if (stage/p).read_bytes()!=(before/p).read_bytes()]
        for f in BACKEND:
            if f not in existing_php:changed.append('contact/'+f)
        if not changed:
            print('PASS: backend and pages already match; no upload needed',flush=True)
            return
        print('UPLOAD: '+str(len(changed))+' allowlisted files, backed up all existing files',flush=True)
        try:
            base.ftp([f'put "{stage/p}" -o "/kanto/{p}"' for p in changed])
            for p in HTML:
                if base.live_fetch(p,'verify_contact')!=(stage/p).read_bytes():
                    raise RuntimeError('Public contact/privacy HTML bytes do not match: '+p)
            for f in BACKEND:
                downloaded=root/('confirm-'+f)
                base.ftp([f'get "/kanto/contact/{f}" -o "{downloaded}"'])
                if downloaded.read_bytes()!=(stage/'contact'/f).read_bytes():
                    raise RuntimeError('FTPS PHP verification mismatch for '+f)
                downloaded.unlink()
            print('PASS: HTML and PHP source verified on Lolipop',flush=True)
            smoke_live(emails['FROM_EMAIL'])
            print('PASS: Kanto contact form published and one true mail acceptance test succeeded',flush=True)
        except Exception:
            print('ERROR: form release failed; restoring old HTML and backend',file=sys.stderr,flush=True)
            try:
                commands=[f'put "{before/p}" -o "/kanto/{p}"' for p in changed if (before/p).is_file()]
                commands.extend(f'rm "/kanto/contact/{f}"' for f in BACKEND if f not in existing_php and ('contact/'+f) in changed)
                if commands:base.ftp(commands)
                print('ROLLBACK: previous contact/prvacy HTML restored and newly created PHP deleted',file=sys.stderr,flush=True)
            except Exception:
                print('CRITICAL: rollback failed, inspect Kanto /contact immediately',file=sys.stderr,flush=True)
            raise

if __name__=='__main__':main()
