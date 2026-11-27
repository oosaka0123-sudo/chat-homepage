#!/usr/bin/env python3
"""One-off guarded SNS-only Kanto release. No JSON or other site changes."""
import re
import sys
import tempfile
from pathlib import Path

import kanto_model_sync as existing

SLUGS=['kugenuma','yuigahama','oarai-onuki','kashima-hirai','katakai','ichinomiya','taito','onjuku','kamogawa-maruki']
PAGES=['index.html']+['spots/'+s+'/index.html' for s in SLUGS]+['about/index.html','contact/index.html','privacy/index.html']
FILES=PAGES+['styles.css']
URL_IG=b'https://www.instagram.com/kanto_surfer_ks/'
URL_FB=b'https://www.facebook.com/kansaisurfer/'
CSS_MARK=b'/* Kanto SNS icons mirror Kansai Surfer:'
CSS_QUERY=re.compile(rb'(styles\.css\?v=)[a-f0-9]{12}')
SNS_NAVS=re.compile(rb'<nav class="(?:sns-buttons|footer-sns)"[^>]*>.*?</nav>',re.S)
assert len(FILES)==14 and len(set(FILES))==14

def nav_pattern(css_class):
    return re.compile(rb'<nav class="'+css_class+rb'"[^>]*>.*?</nav>',re.S)

def extract_nav(src,css_class):
    parts=nav_pattern(css_class).findall(src)
    if len(parts)!=1: raise ValueError('Source SNS navigation missing/duplicated: '+css_class.decode())
    if URL_IG not in parts[0] or URL_FB not in parts[0]:
        raise ValueError('Unexpected source Instagram/Facebook target')
    if parts[0].count(b'<svg')!=2:raise ValueError('Expected two accessible SNS icons')
    return parts[0]

def strip_for_comparison(data):
    data=SNS_NAVS.sub(b'',data)
    return CSS_QUERY.sub(rb'\1SAME_VERSION',data)

def patch_html(original,source,rel,style_ver):
    header=extract_nav(source,b'sns-buttons')
    footer=extract_nav(source,b'footer-sns')
    old=original
    for nav,cls in ((header,b'sns-buttons'),(footer,b'footer-sns')):
        p=nav_pattern(cls)
        ms=list(p.finditer(old))
        if len(ms)>1:raise ValueError('Multiple existing SNS blocks: '+rel)
        if ms:
            m=ms[0]
            old=old[:m.start()]+nav+old[m.end():]
        else:
            if cls==b'sns-buttons':
                start=old.find(b'<header class="site-header">')
                end=old.find(b'</header>',start)
                if start<0 or end<0:raise ValueError('Unexpected header layout: '+rel)
                at=old.find(b'<button class="menu-button"',start,end)
                if at<0:at=old.find(b'<nav class="site-menu"',start,end)
                if at<0:at=end
            else:
                at=old.find(b'<nav class="footer-spot-nav"')
                if at<0:raise ValueError('Footer spot navigation missing: '+rel)
            old=old[:at]+nav+old[at:]
    if len(CSS_QUERY.findall(old))!=1:
        raise ValueError('Expected exactly one versioned CSS link: '+rel)
    old=CSS_QUERY.sub(lambda m:m.group(1)+style_ver,old)
    if strip_for_comparison(original)!=strip_for_comparison(old):
        raise ValueError('Unexpected change outside SNS blocks/CSS query: '+rel)
    if len(nav_pattern(b'sns-buttons').findall(old))!=1 or len(nav_pattern(b'footer-sns').findall(old))!=1:
        raise ValueError('Invalid SNS blocks after patch: '+rel)
    grid=re.search(rb'<div class="footer-spot-grid">(.*?)</div>',old,re.S)
    if grid is None or grid.group(1).count(b'<a ')!=9:
        raise ValueError('Existing nine footer-spot links were changed: '+rel)
    if b'index,follow' not in old or b'rel="canonical"' not in old:
        raise ValueError('SEO markers lost: '+rel)
    return old

def main():
    source_run=existing.selected_build()
    if not source_run:
        raise RuntimeError('No fresh main-equivalent Pages build; refusing release')
    print('SNS source Pages run',source_run['id'],'commit',source_run['head_sha'][:12],flush=True)
    with existing.source_artifact(source_run) as artifact:
        source={f:existing.extract_member(artifact,f) for f in FILES}
    css=source['styles.css']
    idx=css.find(CSS_MARK)
    if idx<0 or css.find(CSS_MARK,idx+1)>=0:raise RuntimeError('Missing/duplicate source SNS CSS marker')
    css_snippet=css[idx:]
    v=CSS_QUERY.findall(source['index.html'])
    if len(v)!=1:raise RuntimeError('Source lacks versioned CSS link')
    v_match=CSS_QUERY.search(source['index.html'])
    style_ver=v_match.group(0).split(b'?v=')[1]
    # The source must contain two social links in both header and footer on 13 pages.
    for rel in PAGES:
        for cls in (b'sns-buttons',b'footer-sns'):
            extract_nav(source[rel],cls)
    with tempfile.TemporaryDirectory(prefix='kanto-sns-release-') as temp:
        root=Path(temp); backup=root/'backup'; stage=root/'stage'
        for file in FILES:
            (backup/file).parent.mkdir(parents=True,exist_ok=True)
            (stage/file).parent.mkdir(parents=True,exist_ok=True)
        existing.ftp(['get "/kanto/'+p+'" -o "'+str(backup/p)+'"' for p in FILES])
        if not all((backup/p).is_file() for p in FILES):
            raise RuntimeError('Incomplete 14-file backup: production untouched')
        for rel in PAGES:
            (stage/rel).write_bytes(patch_html((backup/rel).read_bytes(),source[rel],rel,style_ver))
        oldcss=(backup/'styles.css').read_bytes()
        if CSS_MARK in oldcss:
            old_idx=oldcss.index(CSS_MARK)
            if oldcss[old_idx:]!=css_snippet:
                raise RuntimeError('Existing SNS CSS differs; refusing unsafe replacement')
            newcss=oldcss
        else:
            newcss=oldcss.rstrip()+b'\n\n'+css_snippet
        (stage/'styles.css').write_bytes(newcss)
        for rel in FILES:
            if existing.live_fetch(rel,'sns_preflight')!=(backup/rel).read_bytes():
                raise RuntimeError('Concurrent public change detected: '+rel)
        changed=[rel for rel in FILES if (stage/rel).read_bytes()!=(backup/rel).read_bytes()]
        if not changed:
            print('PASS: all 14 SNS assets already match; no upload needed',flush=True)
            return
        print('SNS release, changing '+str(len(changed))+' of 14 files; backup complete',flush=True)
        try:
            existing.ftp(['put "'+str(stage/p)+'" -o "/kanto/'+p+'"' for p in changed])
            for rel in FILES:
                if existing.live_fetch(rel,'sns_verify')!=(stage/rel).read_bytes():
                    raise RuntimeError('Public byte verification mismatch: '+rel)
            print('PASS: all 13 pages show matching header/footer SNS and styles.css is verified',flush=True)
        except Exception:
            try:
                existing.ftp(['put "'+str(backup/p)+'" -o "/kanto/'+p+'"' for p in changed])
                print('ROLLBACK: restored pre-release files',file=sys.stderr,flush=True)
            except Exception:
                print('CRITICAL: SNS rollback failed; immediate manual inspection required',file=sys.stderr,flush=True)
            raise

if __name__=='__main__':main()
