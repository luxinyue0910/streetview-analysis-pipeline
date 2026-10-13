"""Random blind audit of unflagged auto selections; exclude previous annotated images."""
import csv,hashlib,json,random,zipfile
from collections import Counter
from pathlib import Path
from settings import WORKSPACE,ARCHIVE_DIR,REPOSITORY

def main():
    out=WORKSPACE/'annotation_auto50';out.mkdir(exist_ok=True)
    if (out/'sample.json').exists():raise SystemExit('Existing audit sample retained.')
    excluded=set();hashes=set()
    for name in ['annotation','annotation100','annotation30']:
        s=json.loads((WORKSPACE/name/'sample.json').read_text());excluded.update(p['point_id'] for p in s['points'])
        for file in (WORKSPACE/name/'images').rglob('*.png'):hashes.add(hashlib.sha256(file.read_bytes()).hexdigest())
    review=WORKSPACE/'review_workspace/labels.json'
    if review.exists():excluded.update(k.split(':',1)[1] for k in json.loads(review.read_text()))
    with (WORKSPACE/'full_selection/selection_manifest.csv').open(encoding='utf-8-sig') as f:
        pool=[r for r in csv.DictReader(f) if r['status']=='auto_selected' and r['point_id'] not in excluded]
    rng=random.Random(202610130501);pool=sorted(pool,key=lambda r:(r['archive'],r['point_id']));rng.shuffle(pool)
    archives={};members={};points=[];predictions=[];rejected=0
    try:
        for row in pool:
            name=row['archive']
            if name not in archives:
                archives[name]=zipfile.ZipFile(ARCHIVE_DIR/name)
                members[name]={i.filename.rsplit('/',1)[-1]:i.filename for i in archives[name].infolist() if not i.is_dir() and not i.filename.startswith('__MACOSX/')}
            raw=[]
            for angle in [0,90,180,270]:
                filename=f'{row["point_id"]}_{angle}_0.png';member=members[name][filename];data=archives[name].read(member)
                raw.append((angle,filename,member,data,hashlib.sha256(data).hexdigest()))
            if any(h in hashes for a,n,m,d,h in raw):rejected+=1;continue
            images=[];level=int(row['road_level']);pid=f'{level}:{row["point_id"]}'
            for a,n,m,d,h in raw:
                path=f'images/{level}/{n}';dest=out/path;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(d);hashes.add(h)
                images.append({'angle':a,'filename':n,'archive_member':m,'url':'/'+path})
            points.append({'id':pid,'point_id':row['point_id'],'road_level':level,'archive':name,'images':images})
            predictions.append({'id':pid,'point_id':row['point_id'],'road_level':level,'predicted':list(map(int,row['classifier_pair'].split('/'))),'scores':{str(a):float(row['score_'+str(a)]) for a in [0,90,180,270]},'pair_margin':float(row['classifier_margin'])})
            if len(points)==50:break
    finally:
        for z in archives.values():z.close()
    assert len(points)==50
    sample={'sample_id':'auto50-blindaudit-seed202610130501-v1','seed':202610130501,'counts':dict(Counter(p['road_level'] for p in points)),
            'require_two_review':True,'population':'Unflagged auto_selected center points','excluded_seen_points':len(excluded),'eligible_points':len(pool),'duplicate_image_rejections':rejected,'points':points}
    (out/'sample.json').write_text(json.dumps(sample,ensure_ascii=False,indent=2))
    evaluation=WORKSPACE/'evaluation_auto50';evaluation.mkdir(exist_ok=True)
    (evaluation/'predictions_before_labels.json').write_text(json.dumps({'sample_id':sample['sample_id'],'predictions':predictions,'source_manifest_sha256':hashlib.sha256((WORKSPACE/'full_selection/selection_manifest.csv').read_bytes()).hexdigest(),'labels_read':False},ensure_ascii=False,indent=2))
    template=REPOSITORY/'web/annotation100'
    page=(template/'index.html').read_text().replace('新100点位验证','普通自动选择点位盲测').replace('100 个新随机点位 · 四个道路等级各 25 个','50 个随机点位 · 来自未标记待复核的自动选择集').replace('全部 100 个点位','全部 50 个点位').replace('center100_','auto50_')
    page=page.replace('选择道路两侧的照片','验证普通自动选择点位')
    (out/'index.html').write_text(page)
    for name in ['style.css','app.js']:(out/name).write_bytes((template/name).read_bytes())
    print('Prepared 50 unflagged center points:',sample['counts'],'; 200 images; model answers hidden.')

if __name__=='__main__':main()
