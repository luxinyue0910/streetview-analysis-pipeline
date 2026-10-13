"""Review all provisional points in batches of 50, streaming original ZIP images locally."""
import argparse,csv,hashlib,io,json,os,threading,zipfile
from collections import Counter
from functools import lru_cache
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit,parse_qs
from settings import WORKSPACE,ARCHIVE_DIR,REPOSITORY

ROOT=Path(os.environ.get('STREETVIEW_REVIEW_DIR',WORKSPACE/'review_workspace'))
ROOT.mkdir(parents=True,exist_ok=True)
BASE=WORKSPACE/'full_selection'
with (BASE/'selection_manifest.csv').open(encoding='utf-8-sig') as f:
    reader=csv.DictReader(f);FIELDS=reader.fieldnames;ALL=list(reader)
QUEUE=[r for r in ALL if r['status']=='needs_review']
HASH=hashlib.sha256((BASE/'selection_manifest.csv').read_bytes()).hexdigest()
META=ROOT/'source.json'
if META.exists() and json.loads(META.read_text())['manifest_sha256']!=HASH:raise ValueError('Source manifest changed; use a new review directory.')
META.write_text(json.dumps({'manifest_sha256':HASH,'queue_points':len(QUEUE)}))
LABELS=ROOT/'labels.json';LOCK=threading.Lock()
ARCHIVES={name:zipfile.ZipFile(ARCHIVE_DIR/name) for name in {r['archive'] for r in QUEUE}}
MEMBERS={name:{i.filename.rsplit('/',1)[-1]:i.filename for i in z.infolist() if not i.is_dir() and not i.filename.startswith('__MACOSX/')} for name,z in ARCHIVES.items()}
IDS={f'{r["road_level"]}:{r["point_id"]}':i for i,r in enumerate(QUEUE)}

def load():return json.loads(LABELS.read_text()) if LABELS.exists() else {}

def point(i):
    r=QUEUE[i];images=[]
    for a in [0,90,180,270]:
        filename=f'{r["point_id"]}_{a}_0.png'
        images.append({'angle':a,'filename':filename,'archive_member':MEMBERS[r['archive']][filename],'url':f'/image/{i}/{a}'})
    return {'id':f'{r["road_level"]}:{r["point_id"]}','point_id':r['point_id'],'road_level':int(r['road_level']),
            'archive':r['archive'],'queue_index':i+1,'model_selected':list(map(int,r['classifier_pair'].split('/'))),
            'review_reasons':r['review_reasons'].split(';'),'pair_margin':float(r['classifier_margin']),'note':r['note'],'images':images}

def atomic(path,data):
    temp=path.with_suffix(path.suffix+'.tmp');temp.write_bytes(data);os.replace(temp,path)

def csv_bytes(rows,fields):
    f=io.StringIO(newline='');w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows);return ('\ufeff'+f.getvalue()).encode()

def export(labels):
    fields=['queue_index','point_id','road_level','archive','status','side_a_angle','side_a_filename','side_a_member','side_b_angle','side_b_filename','side_b_member','original_model_pair','note']
    rows=[];overrides={}
    for i,r in enumerate(QUEUE):
        p=point(i);l=labels.get(p['id']);selected=l['selected'] if l else p['model_selected'];status=l['status'] if l else 'unreviewed'
        record={'queue_index':i+1,'point_id':p['point_id'],'road_level':p['road_level'],'archive':p['archive'],'status':status,'original_model_pair':r['classifier_pair'],'note':l.get('note','') if l else ''}
        for idx,side in enumerate(['side_a','side_b']):
            im=next((im for im in p['images'] if idx<len(selected) and im['angle']==selected[idx]),None)
            for suffix,val in [('angle',im['angle'] if im else ''),('filename',im['filename'] if im else ''),('member',im['archive_member'] if im else '')]:record[side+'_'+suffix]=val
        rows.append(record)
        if l and status=='confirmed':
            updated=dict(r);updated['status']='confirmed';updated['selection_source']='human_review';updated['review_reasons']=''
            for side in ['side_a','side_b']:
                for suffix in ['angle','filename','member']:updated[side+'_'+suffix]=record[side+'_'+suffix]
            updated['note']=(r['note']+' | ' if r['note'] else '')+'Review: '+l.get('note','')
            overrides[p['id']]=updated
    atomic(ROOT/'review_results.csv',csv_bytes(rows,fields))
    final=[overrides.get(f'{r["road_level"]}:{r["point_id"]}',r) for r in ALL]
    atomic(ROOT/'selection_manifest_reviewed.csv',csv_bytes(final,FIELDS))
    return final

@lru_cache(maxsize=32)
def image(i,a):
    r=QUEUE[i];name=f'{r["point_id"]}_{a}_0.png';return ARCHIVES[r['archive']].read(MEMBERS[r['archive']][name])

class Handler(BaseHTTPRequestHandler):
    def send(self,data,kind='application/json; charset=utf-8',status=200):
        self.send_response(status);self.send_header('Content-Type',kind);self.send_header('Content-Length',str(len(data)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(data)
    def do_GET(self):
        url=urlsplit(self.path)
        if url.path=='/api/state':
            try:batch=int(parse_qs(url.query).get('batch',['1'])[0]);assert 1<=batch<=(len(QUEUE)+49)//50
            except (ValueError,AssertionError):return self.send(b'{}',status=400)
            with LOCK:labels=load()
            start=(batch-1)*50;points=[point(i) for i in range(start,min(start+50,len(QUEUE)))];counts=Counter(l['status'] for l in labels.values())
            payload={'sample':{'sample_id':'full-review-'+HASH[:12],'points':points,'batch':batch,'batch_count':(len(QUEUE)+49)//50,'queue_total':len(QUEUE),'confirmed_total':counts['confirmed'],'reviewed_uncertain_total':counts['needs_review']},'labels':{p['id']:labels[p['id']] for p in points if p['id'] in labels}}
            return self.send(json.dumps(payload,ensure_ascii=False).encode())
        if url.path in ['/api/export.csv','/api/export-updated.csv','/api/export.json']:
            with LOCK:
                labels=load();export(labels)
                data=json.dumps({'manifest_sha256':HASH,'labels':labels},ensure_ascii=False,indent=2).encode() if url.path.endswith('json') else (ROOT/('selection_manifest_reviewed.csv' if 'updated' in url.path else 'review_results.csv')).read_bytes()
            return self.send(data,'application/json; charset=utf-8' if url.path.endswith('json') else 'text/csv; charset=utf-8')
        if url.path.startswith('/image/'):
            try:
                _,_,i,a=url.path.split('/');i=int(i);a=int(a);assert 0<=i<len(QUEUE) and a in [0,90,180,270];data=image(i,a)
                return self.send(data,'image/jpeg' if data.startswith(b'\xff\xd8') else 'image/png')
            except (ValueError,AssertionError,KeyError):return self.send(b'Not found','text/plain',404)
        name={'/':'index.html','/index.html':'index.html','/app.js':'app.js','/style.css':'style.css'}.get(url.path)
        if not name:return self.send(b'Not found','text/plain',404)
        types={'index.html':'text/html; charset=utf-8','app.js':'text/javascript; charset=utf-8','style.css':'text/css; charset=utf-8'}
        return self.send((REPOSITORY/'web/review'/name).read_bytes(),types[name])
    def do_POST(self):
        if self.path!='/api/label':return self.send(b'{}',status=404)
        try:
            size=int(self.headers.get('Content-Length','0'));assert 0<size<20000
            value=json.loads(self.rfile.read(size));pid=value['id'];selected=value['selected'];status=value['status'];note=value.get('note','')
            assert pid in IDS and isinstance(selected,list) and len(selected)<=2 and len(set(selected))==len(selected)
            assert all(type(a) is int and a in [0,90,180,270] for a in selected)
            assert status in ['draft','confirmed','needs_review'] and (status=='draft' or len(selected)==2)
            assert isinstance(note,str) and len(note)<=2000
            with LOCK:
                labels=load();was_confirmed=labels.get(pid,{}).get('status')=='confirmed'
                labels[pid]={'selected':selected,'status':status,'note':note};atomic(LABELS,json.dumps(labels,ensure_ascii=False,indent=2).encode())
                if status=='confirmed' or was_confirmed:export(labels)
                counts=Counter(l['status'] for l in labels.values())
            return self.send(json.dumps({'ok':True,'confirmed_total':counts['confirmed'],'reviewed_uncertain_total':counts['needs_review']}).encode())
        except (AssertionError,ValueError,KeyError,TypeError):return self.send(b'{"error":"Invalid review selection"}',status=400)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8770);p.add_argument('--open-browser',action='store_true');args=p.parse_args()
    address=f'http://127.0.0.1:{args.port}/?batch=1'
    try:server=ThreadingHTTPServer(('127.0.0.1',args.port),Handler)
    except OSError:
        if args.open_browser:
            from urllib.request import urlopen
            import webbrowser
            with urlopen(f'http://127.0.0.1:{args.port}/api/state',timeout=2) as response:existing=json.load(response)
            if existing['sample']['sample_id']=='full-review-'+HASH[:12]:webbrowser.open(address);raise SystemExit(0)
        raise
    if args.open_browser:
        import webbrowser
        webbrowser.open(address)
    print(f'Review page: http://127.0.0.1:{args.port}/?batch=1 ({len(QUEUE)} points, first 50 shown)',flush=True)
    server.serve_forever()
