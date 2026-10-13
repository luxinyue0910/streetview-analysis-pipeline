from settings import WORKSPACE, ARCHIVE_DIR
"""Fresh final-test sample, excluding earlier coordinates and identical images."""
import csv,json,random,zipfile,hashlib
from pathlib import Path
ROOT=WORKSPACE
OUT=ROOT/'annotation30'

def main():
    OUT.mkdir(exist_ok=True)
    if (OUT/'sample.json').exists():raise SystemExit('Existing sample retained.')
    excluded=set();hashes=set()
    for directory in ['annotation','annotation100']:
        old=json.loads((ROOT/directory/'sample.json').read_text());excluded.update(p['point_id'] for p in old['points'])
        hashes.update(hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/directory/'images').rglob('*.png'))
    assert len(excluded)==150
    with (ROOT/'inspection/center_point_filter_manifest.csv').open(encoding='utf-8-sig') as f:rows=[r for r in csv.DictReader(f) if r['decision']=='keep' and r['point_id'] not in excluded]
    rng=random.Random(20261013030);points=[];counts={1:8,2:8,3:7,4:7};duplicate_rejections=0
    for level,count in counts.items():
        pool=sorted([r for r in rows if int(r['road_level'])==level],key=lambda r:r['point_id']);rng.shuffle(pool);archive=pool[0]['archive']
        with zipfile.ZipFile(ARCHIVE_DIR/archive) as z:
            members={i.filename.rsplit('/',1)[-1]:i for i in z.infolist() if not i.is_dir() and not i.filename.startswith('__MACOSX/')}
            accepted=0
            for row in pool:
                raw=[]
                for angle in [0,90,180,270]:
                    name=f'{row["point_id"]}_{angle}_0.png';m=members[name];b=z.read(m);raw.append((angle,name,m.filename,b,hashlib.sha256(b).hexdigest()))
                if any(h in hashes for a,n,m,b,h in raw):duplicate_rejections+=1;continue
                images=[]
                for a,n,m,b,h in raw:
                    rel=f'images/{level}/{n}';dest=OUT/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(b);hashes.add(h)
                    images.append({'angle':a,'filename':n,'archive_member':m,'url':'/'+rel})
                points.append({'id':f'{level}:{row["point_id"]}','point_id':row['point_id'],'road_level':level,'archive':archive,'images':images})
                accepted+=1
                if accepted==count:break
            assert accepted==count
    rng.shuffle(points)
    sample={'sample_id':'center30-finaltest-seed20261013030-v1','seed':20261013030,'counts':counts,'require_two_review':True,'excluded_previous_points':150,'duplicate_image_rejections':duplicate_rejections,'points':points}
    (OUT/'sample.json').write_text(json.dumps(sample,ensure_ascii=False,indent=2))
    page=(ROOT/'annotation100/index.html').read_text().replace('新100点位验证','新30点位验证').replace('100 个新随机点位 · 四个道路等级各 25 个','30 个新随机点位 · 一级 8 / 二级 8 / 三级 7 / 四级 7').replace('全部 100 个点位','全部 30 个点位').replace('center100_','center30_')
    (OUT/'index.html').write_text(page)
    for name in ['style.css','app.js']:(OUT/name).write_bytes((ROOT/'annotation100'/name).read_bytes())
    assert len(points)==30 and not excluded&{p['point_id'] for p in points}
    print('30 new points; 120 original images; earlier 150 coordinates and identical images excluded.')

if __name__=='__main__':main()
