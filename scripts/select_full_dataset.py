"""Select two side-view references per center point, with resumable local inference."""
import argparse
import csv
import hashlib
import io
import json
import sqlite3
import time
import zipfile
from collections import Counter
from pathlib import Path

import numpy as np
import torch
from PIL import Image, ImageOps
from transformers import CLIPModel, CLIPProcessor
from evaluate_clip import SIDE, ALONG
from settings import WORKSPACE, ARCHIVE_DIR

FIELDS=['point_id','road_level','archive','status','selection_source','review_reasons',
        'side_a_angle','side_a_filename','side_a_member','side_b_angle','side_b_filename','side_b_member',
        'classifier_pair','baseline_pair','classifier_margin','score_0','score_90','score_180','score_270',
        'classifier_sha256','note']

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def annotations():
    decisions={};fingerprints={}
    certainty_file=WORKSPACE/'annotation/explicit_certainty.json'
    legacy_certain=set(json.loads(certainty_file.read_text())) if certainty_file.exists() else set()
    if certainty_file.exists():fingerprints['explicit_legacy_certainty']=digest(certainty_file)
    for name in ['annotation','annotation100','annotation30']:
        path=WORKSPACE/name/'labels.json'
        if not path.exists():continue
        fingerprints[name]=digest(path)
        for pid,label in json.loads(path.read_text()).items():
            chosen=label.get('selected',[])
            if len(chosen)!=2:continue
            status=label.get('status')
            # First round did not systematically record certainty. One explicit correction was confirmed later.
            if name=='annotation':
                certain=pid in legacy_certain
                reason='legacy_annotation_certainty_not_recorded'
            else:
                certain=status=='confirmed';reason='human_uncertain' if status=='needs_review' else 'human_draft'
            decisions[pid]={'selected':chosen,'certain':certain,'reason':reason,'note':label.get('note',''),'round':name}
    return decisions,fingerprints

def export(db,out,meta,total,started):
    rows=[json.loads(p[0]) for p in db.execute('SELECT payload FROM points ORDER BY road_level,point_id')]
    dest=out/'selection_manifest.csv';temp=out/'selection_manifest.csv.tmp'
    with temp.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(rows)
    temp.replace(dest)
    with (out/'review_manifest.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(r for r in rows if r['status']=='needs_review')
    counts=Counter(r['status'] for r in rows);reasons=Counter(reason for r in rows for reason in r['review_reasons'].split(';') if reason)
    summary={'total_center_points':total,'processed_points':len(rows),'selected_image_references':2*len(rows),
             'complete':len(rows)==total,'status_counts':dict(counts),'review_reason_counts':dict(reasons),
             'selection_sources':dict(Counter(r['selection_source'] for r in rows)),
             'by_level':{str(l):dict(Counter(r['status'] for r in rows if int(r['road_level'])==l)) for l in [1,2,3,4]},
             'runtime_seconds_this_invocation':time.perf_counter()-started,'configuration':meta,
             'note':'auto_selected is an unreviewed model selection, not a human confirmation. Margin threshold is a review heuristic, not calibrated confidence. Scores use frozen classifier; human-confirmed choices override model results.'}
    (out/'run_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
    return summary

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=WORKSPACE/'full_selection')
    p.add_argument('--review-margin',type=float,default=0.3);p.add_argument('--limit',type=int,default=0,help='Smoke-test only: process at most this many new points')
    args=p.parse_args();out=args.output;out.mkdir(parents=True,exist_ok=True);started=time.perf_counter()
    manifest=WORKSPACE/'inspection/center_point_filter_manifest.csv'
    with manifest.open(encoding='utf-8-sig') as f:points=sorted([r for r in csv.DictReader(f) if r['decision']=='keep'],key=lambda r:(int(r['road_level']),r['point_id']))
    assert len({r['point_id'] for r in points})==len(points)
    weights=WORKSPACE/'classifier_trial/classifier_all84.npz';linear=np.load(weights)
    assert linear['classes'].tolist()==[0,1]
    human,fingerprints=annotations()
    meta={'classifier_sha256':digest(weights),'center_manifest_sha256':digest(manifest),'annotation_sha256':fingerprints,
          'review_margin':args.review_margin,'compare_zero_shot':True,'preprocess':'224 gray letterbox, full image',
          'prompts_sha256':hashlib.sha256(json.dumps(SIDE+ALONG).encode()).hexdigest(),'encoder':'openai/clip-vit-base-patch32'}
    db=sqlite3.connect(out/'checkpoint.sqlite');db.execute('CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY,value TEXT)')
    db.execute('CREATE TABLE IF NOT EXISTS images (sha TEXT PRIMARY KEY, score REAL, baseline REAL)')
    db.execute('CREATE TABLE IF NOT EXISTS points (point_id TEXT PRIMARY KEY, road_level INTEGER,payload TEXT)')
    old=db.execute('SELECT value FROM metadata WHERE key="configuration"').fetchone()
    if old and json.loads(old[0])!=meta:raise ValueError('Checkpoint configuration changed. Use a new output directory to avoid mixing results.')
    db.execute('INSERT OR IGNORE INTO metadata VALUES (?,?)',('configuration',json.dumps(meta)));db.commit()
    finished={r[0] for r in db.execute('SELECT point_id FROM points')};pending=[r for r in points if r['point_id'] not in finished]
    if args.limit:pending=pending[:args.limit]
    archives={};members={}
    for name in sorted({r['archive'] for r in points}):
        z=zipfile.ZipFile(ARCHIVE_DIR/name);archives[name]=z
        members[name]={i.filename.rsplit('/',1)[-1]:i.filename for i in z.infolist() if not i.is_dir() and not i.filename.startswith('__MACOSX/')}
    device='mps' if torch.backends.mps.is_available() else 'cpu';torch.set_num_threads(4)
    print(f'Start: {len(finished)}/{len(points)} done; {len(pending)} pending; device={device}',flush=True)
    encoder=CLIPModel.from_pretrained(WORKSPACE/'models/clip-vit-base-patch32',use_safetensors=True,local_files_only=True).to(device).eval()
    processor=CLIPProcessor.from_pretrained(WORKSPACE/'models/clip-vit-base-patch32',local_files_only=True,use_fast=False)
    with torch.inference_mode():
        text=encoder.get_text_features(**processor(text=SIDE+ALONG,return_tensors='pt',padding=True).to(device));text=text/text.norm(dim=-1,keepdim=True)
    last=started
    try:
        for begin in range(0,len(pending),16):
            chunk=pending[begin:begin+16];references=[];new_images={};cache={}
            for row in chunk:
                refs=[]
                for angle in [0,90,180,270]:
                    filename=f'{row["point_id"]}_{angle}_0.png';member=members[row['archive']][filename];data=archives[row['archive']].read(member)
                    sha=hashlib.sha256(data).hexdigest();refs.append({'angle':angle,'filename':filename,'member':member,'sha':sha})
                    existing=db.execute('SELECT score,baseline FROM images WHERE sha=?',(sha,)).fetchone()
                    if existing:cache[sha]=existing
                    elif sha not in new_images:
                        with Image.open(io.BytesIO(data)) as original:new_images[sha]=ImageOps.pad(original.convert('RGB'),(224,224),method=Image.Resampling.LANCZOS,color=(127,127,127))
                references.append(refs)
            keys=list(new_images)
            with torch.inference_mode():
                for b in range(0,len(keys),16):
                    batch=keys[b:b+16]
                    f=encoder.get_image_features(**processor(images=[new_images[k] for k in batch],return_tensors='pt').to(device));f=f/f.norm(dim=-1,keepdim=True)
                    features=f.cpu().numpy();score=(features@linear['coef'].T+linear['intercept']).ravel();sim=f@text.T
                    base=(sim[:,:len(SIDE)].mean(1)-sim[:,len(SIDE):].mean(1)).cpu().numpy()
                    for k,a,c in zip(batch,score,base):cache[k]=(float(a),float(c));db.execute('INSERT OR IGNORE INTO images VALUES (?,?,?)',(k,float(a),float(c)))
            for row,refs in zip(chunk,references):
                values=[cache[i['sha']][0] for i in refs];bases=[cache[i['sha']][1] for i in refs]
                delta=values[0]+values[2]-values[1]-values[3];bd=bases[0]+bases[2]-bases[1]-bases[3]
                chosen=[0,180] if delta>=0 else [90,270];baseline=[0,180] if bd>=0 else [90,270];reasons=[]
                if abs(delta)<args.review_margin:reasons.append('low_classifier_margin')
                if chosen!=baseline:reasons.append('classifier_baseline_disagreement')
                status='needs_review' if reasons else 'auto_selected';source='classifier';note=''
                annotation=human.get(f'{row["road_level"]}:{row["point_id"]}')
                if annotation:
                    note=annotation['note']
                    if annotation['certain']:
                        selected=annotation['selected'];status='confirmed';source='human_confirmed';reasons=[]
                    else:
                        selected=chosen;status='needs_review';reasons.append(annotation['reason']);source='classifier_with_human_candidate'
                        note=(note+' | ' if note else '')+'Human candidate: '+','.join(map(str,annotation['selected']))
                else:selected=chosen
                selected_refs=[next(i for i in refs if i['angle']==a) for a in selected]
                record={'point_id':row['point_id'],'road_level':int(row['road_level']),'archive':row['archive'],'status':status,'selection_source':source,
                        'review_reasons':';'.join(sorted(set(reasons))),'classifier_pair':'/'.join(map(str,chosen)),
                        'baseline_pair':'/'.join(map(str,baseline)),'classifier_margin':abs(delta),'classifier_sha256':meta['classifier_sha256'],'note':note}
                for side,im in zip(['side_a','side_b'],selected_refs):
                    record[side+'_angle']=im['angle'];record[side+'_filename']=im['filename'];record[side+'_member']=im['member']
                for angle,score in zip([0,90,180,270],values):record['score_'+str(angle)]=score
                db.execute('INSERT INTO points VALUES (?,?,?)',(row['point_id'],int(row['road_level']),json.dumps(record,ensure_ascii=False)))
            db.commit()
            now=time.perf_counter()
            if now-last>=30 or begin+16>=len(pending):
                count=db.execute('SELECT COUNT(*) FROM points').fetchone()[0]
                print(f'Progress {count}/{len(points)}; elapsed {now-started:.1f}s; unique images {db.execute("SELECT COUNT(*) FROM images").fetchone()[0]}',flush=True)
                export(db,out,meta,len(points),started);last=now
    finally:
        db.rollback();summary=export(db,out,meta,len(points),started)
        for z in archives.values():z.close()
        db.close()
    print(json.dumps(summary,ensure_ascii=False,indent=2),flush=True)

if __name__=='__main__':main()
