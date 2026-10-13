from settings import WORKSPACE, ARCHIVE_DIR
"""Create a fresh, balanced validation sample, excluding all previous point IDs."""
import csv
import json
import random
import zipfile
from pathlib import Path

ROOT = WORKSPACE
OUT = ROOT / 'annotation100'

def main():
    OUT.mkdir(exist_ok=True)
    if (OUT / 'sample.json').exists():
        raise SystemExit('Existing sample retained; refusing to replace it.')
    old = json.loads((ROOT / 'annotation/sample.json').read_text())
    excluded = {p['point_id'] for p in old['points']}
    with (ROOT / 'inspection/center_point_filter_manifest.csv').open(encoding='utf-8-sig') as f:
        rows = [r for r in csv.DictReader(f) if r['decision'] == 'keep' and r['point_id'] not in excluded]
    rng = random.Random(20261013)
    points = []
    for level in [1,2,3,4]:
        selected = rng.sample(sorted([r for r in rows if int(r['road_level']) == level], key=lambda r:r['point_id']), 25)
        archive = selected[0]['archive']
        with zipfile.ZipFile(ARCHIVE_DIR / archive) as z:
            members = {i.filename.rsplit('/',1)[-1]:i for i in z.infolist() if not i.is_dir() and not i.filename.startswith('__MACOSX/')}
            for row in selected:
                images=[]
                for angle in [0,90,180,270]:
                    filename=f'{row["point_id"]}_{angle}_0.png';member=members[filename]
                    rel=f'images/{level}/{filename}';dest=OUT/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(z.read(member))
                    images.append({'angle':angle,'filename':filename,'archive_member':member.filename,'url':'/'+rel})
                points.append({'id':f'{level}:{row["point_id"]}','point_id':row['point_id'],'road_level':level,'archive':archive,'images':images})
    rng.shuffle(points)
    sample={'sample_id':'center100-seed20261013-v1','seed':20261013,'counts':{str(l):25 for l in [1,2,3,4]},'require_two_review':True,'points':points}
    (OUT/'sample.json').write_text(json.dumps(sample,ensure_ascii=False,indent=2))
    page=(ROOT/'annotation/index.html').read_text().replace('上海街景 · 侧向视角标注','上海街景 · 新100点位验证').replace('50 个随机点位 · 一级 13 / 二级 13 / 三级 12 / 四级 12','100 个新随机点位 · 四个道路等级各 25 个').replace('标记待复核并继续','勉强选这两张并继续').replace('确认两张并继续','确定选这两张并继续').replace('只有点击“确认两张”才记为已确认；看不准时标记待复核，可不选或保留候选。全部 50 个点位都会导出，未标注和待复核不会被当成已确认。','两种完成按钮都需要先选两张。明确时点击“确定选这两张”；拿不准时点击“勉强选这两张”，记录为待复核，可加备注。全部 100 个点位都会导出。模型预测在此页面隐藏，避免影响你的判断。').replace('center50_','center100_')
    (OUT/'index.html').write_text(page)
    js=(ROOT/'annotation/app.js').read_text().replace('/ 50','/ ${sample.points.length}').replace('50-confirmed-review','sample.points.length-confirmed-review').replace('confirmed/50*100','(confirmed+review)/sample.points.length*100').replace('index === 49','index === sample.points.length-1').replace('Math.min(49,target)','Math.min(sample.points.length-1,target)').replace('index<49','index<sample.points.length-1')
    js=js.replace("$('swap').disabled = l.selected.length !== 2;", "$('swap').disabled = l.selected.length !== 2; $('review').disabled = l.selected.length !== 2 || failed;")
    js=js.replace("if(status==='confirmed' && l.selected.length!==2) return;","if(l.selected.length!==2) return;")
    js=js.replace("$('confirm').disabled=labelFor(sample.points[index]).selected.length!==2;","$('confirm').disabled=labelFor(sample.points[index]).selected.length!==2; $('review').disabled=$('confirm').disabled;")
    js=js.replace("$('confirm').disabled=true;","$('confirm').disabled=true; $('review').disabled=true;")
    js=js.replace('已确认 ${confirmed}', '明确 ${confirmed}').replace('待复核 ${review}', '勉强选择 ${review}')
    (OUT/'app.js').write_text(js);(OUT/'style.css').write_bytes((ROOT/'annotation/style.css').read_bytes())
    assert len({p['point_id'] for p in points})==100 and not excluded & {p['point_id'] for p in points}
    print('100 new center points, 25 per road level; 400 original images; no old point IDs.')

if __name__=='__main__':main()
