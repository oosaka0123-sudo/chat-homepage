#!/usr/bin/env python3
"""Synchronize only verified Kanto model articles and their public JSON to Lolipop.
No deletes. No LLM API calls. Restore backups if transfer/verification fails.
"""
import datetime as dt
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.request
import zipfile

REPO = 'oosaka0123-sudo/kanto-surfer-ks'
TARGET = 'https://kanto.rss7.net/'
SLUGS = ['kugenuma','yuigahama','oarai-onuki','kashima-hirai','katakai','ichinomiya','taito','onjuku','kamogawa-maruki']
IDS = ['kugenuma','yuigahama','oarai_onuki','kashima_hirai','katakai','ichinomiya','taito','onjuku','kamogawa_maruki']
PAGES = [('index.html','ranking')] + [(f'spots/{slug}/index.html',slug.replace('-','_')) for slug in SLUGS]
DATA = [f'data/{id}.json' for id in IDS] + ['data/index.json']
FILES = [rel for rel, _ in PAGES] + DATA
assert len(FILES) == 20 and len(set(FILES)) == 20
NOW = dt.datetime.now(dt.timezone.utc)
JST = dt.timezone(dt.timedelta(hours=9))
TOKEN = os.environ.get('GH_TOKEN', '')
FTP_USER = os.environ.get('FTP_USER', '')
FTP_PASSWORD = os.environ.get('FTP_PASSWORD', '')


def request(url, *, auth=False):
    headers={'User-Agent':'kanto-model-guarded-sync/1.0','Accept':'application/vnd.github+json' if auth else 'application/octet-stream'}
    if auth: headers['Authorization']='Bearer '+TOKEN
    else: headers.update({'Cache-Control':'no-cache, no-store','Pragma':'no-cache'})
    err=None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url,headers=headers),timeout=35) as r: return r.read()
        except Exception as ex:
            err=ex;time.sleep(2+3*attempt)
    raise RuntimeError(f'HTTP request failed: {url}') from err

def api(route):
    return json.loads(request('https://api.github.com/repos/'+REPO+'/'+route,auth=True))

def selected_build():
    latest=api('commits/main')['sha']
    tree=api('git/commits/'+latest)['tree']['sha']
    runs=api('actions/workflows/deploy-pages.yml/runs?per_page=30')['workflow_runs']
    valid=[]
    for r in runs:
        started=dt.datetime.fromisoformat(r['created_at'].replace('Z','+00:00'))
        if r['conclusion']=='success' and dt.timedelta(0)<=NOW-started<dt.timedelta(hours=5):
            valid.append(r)
    for r in valid:
        if r['head_sha']==latest and r['head_branch']=='main' and r['event']!='pull_request':
            return r
    # A verified PR Pages artifact may be used only if its git tree is byte-identical
    # to the current main tree. This survives a slow Open-Meteo build after a merge.
    for r in valid:
        if r['event']=='pull_request' and api('git/commits/'+r['head_sha'])['tree']['sha']==tree:
            print('SOURCE FALLBACK: exact same Git tree as current main; PR build independently verified')
            return r
    return None

def source_artifact(r):
    items=api(f'actions/runs/{r["id"]}/artifacts')['artifacts']
    items=[x for x in items if x['name']=='github-pages' and not x['expired']]
    if not items: raise RuntimeError('Pages artifact unavailable')
    url=f'https://api.github.com/repos/{REPO}/actions/artifacts/{items[0]["id"]}/zip'
    # curl intentionally strips GitHub Authorization on redirects to Azure artifact storage.
    dl=subprocess.run(['curl','-fsSL','--retry','3','--max-time','90','-H',
         'Authorization: Bearer '+TOKEN,'-H','Accept: application/vnd.github+json',url],
         capture_output=True,timeout=120)
    if dl.returncode:raise RuntimeError('Pages artifact download failed (curl exit '+str(dl.returncode)+')')
    with zipfile.ZipFile(io.BytesIO(dl.stdout)) as z:
        tar_data=z.read('artifact.tar')
    return tarfile.open(fileobj=io.BytesIO(tar_data),mode='r:*')

def extract_member(archive,rel):
    matches=[m for m in archive.getmembers() if m.name.lstrip('./')==rel and m.isfile()]
    if len(matches)!=1: raise RuntimeError('Missing or duplicate Pages artifact member: '+rel)
    return archive.extractfile(matches[0]).read()

def ensure_valid(source):
    model=json.loads(source['data/model-ranking.json'].decode('utf-8'))
    generated=dt.datetime.fromisoformat(model['generated_at'].replace('Z','+00:00'))
    if generated.tzinfo is None or not dt.timedelta(0)<=NOW-generated<dt.timedelta(hours=5):
        raise RuntimeError('Generated model timestamp is stale or future')
    today=NOW.astimezone(JST).date()
    if model['today']['date']!=today.isoformat() or model['tomorrow']['date']!=(today+dt.timedelta(days=1)).isoformat():
        raise RuntimeError('Date mismatch between website and model')
    for key in ('today','tomorrow'):
        d=model[key]
        if d['status']!='model_reference' or len(d['entries'])!=9:raise RuntimeError(key+' unavailable; keep last live edition')
        if sorted(x['rank'] for x in d['entries'])!=list(range(1,10)) or {x['id'] for x in d['entries']}!=set(IDS):
            raise RuntimeError('Invalid nine-spot rank coverage')
        for e in d['entries']:
            if not 90<=len(e['home'])<=120 or not 90<=len(e['detail'])<=120:
                raise RuntimeError('Short article character count invalid '+e['id'])
            surf=e.get('surf_size',{})
            if surf.get('status')!='experimental' or not surf.get('label') or surf.get('confidence')!='low':
                raise RuntimeError('Surf-size prediction missing its experimental label for '+e['id'])
    for id in IDS:
        d=json.loads(source[f'data/{id}.json'].decode('utf-8'))
        if d['spot']['id']!=id or d['generated_at']!=model['generated_at'] or d['daily']['rows'][0]['date']!=today.isoformat() or len(d['daily']['rows'])!=10:
            raise RuntimeError('Inconsistent model JSON '+id)
    json.loads(source['data/index.json'].decode('utf-8'))
    for rel,id in PAGES:
        p=marker_pattern(id)
        if len(p.findall(source[rel]))!=1:
            raise RuntimeError('Pages model marker missing: '+rel)
        if rel=='index.html':
            if any(token in source[rel] for token in (b'data-forecast',b'id="forecast-title"',b'id="daily-forecast"')):
                raise RuntimeError('Homepage must not contain default Kugenuma chart and 10-day table')
        elif b'data-forecast' not in source[rel] or b'id="daily-forecast"' not in source[rel]:
            raise RuntimeError('Individual spot must retain graph and 10-day table: '+rel)
    print('PASS: 9 model spots x 2 dates, 100-char articles, ten HTML, ten JSON, fresh source '+generated.isoformat())

def marker_pattern(id):
    raw=id.encode()
    return re.compile(rb'<!-- KS-MODEL:'+raw+rb':START -->.*?<!-- KS-MODEL:'+raw+rb':END -->',re.S)

def ftp(lines):
    common=['set cmd:fail-exit true','set ftp:ssl-force true','set ftp:ssl-protect-data true',
            'set ssl:verify-certificate true','set ftp:passive-mode true','set net:timeout 20','set net:max-retries 3',
            'open -u "'+FTP_USER+'","'+FTP_PASSWORD+'" ftp.lolipop.jp']
    p=subprocess.run(['lftp'],input='\n'.join(common+lines+['bye'])+'\n',text=True,capture_output=True,timeout=420)
    if p.returncode: raise RuntimeError('FTPS transfer failed (exit '+str(p.returncode)+')')

def live_fetch(rel,salt):
    p=rel.removesuffix('index.html') if rel=='index.html' or rel.endswith('/index.html') else rel
    return request(TARGET+p+'?model_sync='+str(salt)+'-'+str(time.time_ns()))

def generation_timestamp(raw, expected_id):
    data=json.loads(raw)
    if data.get('spot',{}).get('id')!=expected_id:
        raise ValueError('Forecast spot ID mismatch: '+expected_id)
    value=data.get('generated_at')
    if not isinstance(value,str):
        raise ValueError('Forecast generation timestamp missing: '+expected_id)
    timestamp=dt.datetime.fromisoformat(value.replace('Z','+00:00'))
    if timestamp.tzinfo is None:
        raise ValueError('Forecast generation timestamp has no timezone: '+expected_id)
    return timestamp

def verify_no_regression(source, previous):
    # A delayed or retried build must not replace any newer live spot snapshot.
    # Equal times are allowed for a verified editorial-only change.
    for spot in IDS:
        rel=f'data/{spot}.json'
        old=generation_timestamp(previous[rel],spot)
        new=generation_timestamp(source[rel],spot)
        if new<old:
            raise RuntimeError('Refusing older forecast for '+spot+
                               ': source '+new.isoformat()+' < live '+old.isoformat())

def self_test():
    def fixture(value):
        return {f'data/{spot}.json':json.dumps({'spot':{'id':spot},'generated_at':value}).encode() for spot in IDS}
    old=fixture('2026-11-28T08:00:00Z')
    fresh=fixture('2026-11-28T09:00:00Z')
    same=fixture('2026-11-28T17:00:00+09:00')
    verify_no_regression(fresh,old)
    verify_no_regression(same,old)
    def rejected(new,previous):
        try:
            verify_no_regression(new,previous)
        except (RuntimeError,ValueError,KeyError):
            return
        raise AssertionError('Unsafe snapshot was accepted')
    rejected(old,fresh)
    mixed=dict(fresh)
    mixed['data/taito.json']=fixture('2026-11-28T07:59:59Z')['data/taito.json']
    rejected(mixed,old)
    rejected(fresh,fixture('2026-11-28T09:00:00'))
    bad=dict(old)
    bad['data/onjuku.json']=b'{"spot":{"id":"taito"},"generated_at":"2026-11-28T08:00:00Z"}'
    rejected(fresh,bad)
    print('PASS: monotonic timestamp checks (new/equal/older/mixed/invalid timezone/wrong spot)')

def guarded_sync(source,tmp):
    backup=tmp/'backup';stage=tmp/'stage'
    for rel in FILES:
        (backup/rel).parent.mkdir(parents=True,exist_ok=True)
        (stage/rel).parent.mkdir(parents=True,exist_ok=True)
    ftp([f'get "/kanto/{rel}" -o "{backup/rel}"' for rel in FILES])
    if any(not (backup/p).is_file() for p in FILES):raise RuntimeError('Incomplete backup; production untouched')
    verify_no_regression(source,{rel:(backup/rel).read_bytes() for rel in DATA if rel!='data/index.json'})
    for rel,id in PAGES:
        old=(backup/rel).read_bytes()
        preserved=old
        if rel=='index.html':
            # One-time removal of legacy Kugenuma chart + ten-day block from homepage.
            # The old page contains no other content between forecast-title and </main>.
            begin=b'<section class="forecast-section" aria-labelledby="forecast-title">'
            if begin in old:
                if old.count(begin)!=1:raise RuntimeError('Duplicate homepage chart anchor')
                start=old.index(begin)
                end=old.find(b'</main>',start)
                if end<0:raise RuntimeError('Homepage closing main anchor missing')
                removed=old[start:end]
                if not all(tag in removed for tag in [b'id="daily-forecast"',b'data-forecast',b'id="forecast-title"']):
                    raise RuntimeError('Unexpected legacy section: not safe to delete')
                if b'KS-RESEARCH:' in removed or b'KS-MODEL:' in removed or b'<footer' in removed:
                    raise RuntimeError('Other homepage content inside old chart range; refusing removal')
                preserved=old[:start]+old[end:]
            if any(x in preserved for x in [b'data-forecast',b'id="daily-forecast"',b'id="forecast-title"']):
                raise RuntimeError('Unexpected extra homepage chart markup')
        new_model=marker_pattern(id).search(source[rel]).group()
        pat=marker_pattern(id)
        current=list(pat.finditer(preserved))
        if len(current)>1:raise RuntimeError('Production duplicate model marker '+rel)
        if current:
            m=current[0]
            new=preserved[:m.start()]+new_model+preserved[m.end():]
        else:
            anchor=b'<!-- KS-RESEARCH:'+id.encode()+b':START -->'
            at=preserved.find(anchor)
            if at<0:at=preserved.find(b'</main>') if rel=='index.html' else preserved.find(b'<section class="forecast-section"')
            if at<0:raise RuntimeError('No safe insertion point '+rel)
            new=preserved[:at]+new_model+preserved[at:]
        if pat.sub(b'',new)!=pat.sub(b'',preserved) or len(pat.findall(new))!=1:
            raise RuntimeError('Change outside model article section '+rel)
        if b'</main>' not in new or (rel!='index.html' and b'data-forecast' not in new):
            raise RuntimeError('Required forecast markup lost '+rel)
        if rel=='index.html' and (b'data-forecast' in new or b'id="daily-forecast"' in new):
            raise RuntimeError('Home chart not removed')
        (stage/rel).write_bytes(new)
    for rel in DATA:(stage/rel).write_bytes(source[rel])
    if len([p for p in stage.rglob('*') if p.is_file()])!=20:
        raise RuntimeError('Wrong number of files staged')
    for rel in FILES:
        if live_fetch(rel,'before')!=(backup/rel).read_bytes():
            raise RuntimeError('Live production differs from backup; refusing unsafe upload '+rel)
    changed=[rel for rel in FILES if (stage/rel).read_bytes()!=(backup/rel).read_bytes()]
    if not changed:
        print('PASS: all twenty public files are already current')
        return
    print(f'Uploading {len(changed)} of 20 files, with complete backup; no remote deletes')
    attempted=False
    try:
        attempted=True
        ftp([f'put "{stage/rel}" -o "/kanto/{rel}"' for rel in changed])
        for rel in FILES:
            if live_fetch(rel,'verify')!=(stage/rel).read_bytes():
                raise RuntimeError('Public byte verification failed for '+rel)
        print('PASS: 10 public HTML and 10 public model JSON files byte-identical on '+TARGET)
    except Exception:
        if attempted:
            try:
                ftp([f'put "{backup/rel}" -o "/kanto/{rel}"' for rel in changed])
                print('ROLLBACK: restored all affected HTML/JSON from pre-transfer backup',file=sys.stderr)
            except Exception:
                print('CRITICAL: rollback FAILED; inspect public Kanto site immediately',file=sys.stderr)
        raise

def main():
    self_test()
    if sys.argv[1:]==['--self-test']:
        return
    assert TOKEN and FTP_USER and FTP_PASSWORD, 'Existing action token and FTPS secrets required'
    r=selected_build()
    if r is None:
        print('::warning::SKIP: no successful main Pages build within five hours; prior production preserved')
        return
    print('Using exact verified source Pages run',r['id'],'commit',r['head_sha'][:12])
    with source_artifact(r) as archive:
        source={rel:extract_member(archive,rel) for rel in FILES}
        source['data/model-ranking.json']=extract_member(archive,'data/model-ranking.json')
    ensure_valid(source)
    with tempfile.TemporaryDirectory(prefix='kanto-model-lolipop-') as wd:
        guarded_sync(source,Path(wd))
if __name__=='__main__':main()
