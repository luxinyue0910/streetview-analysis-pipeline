"""Accept existing selections and apply only confirmed human pair modifications."""
import csv,hashlib,json,zipfile
from collections import Counter
from pathlib import Path
from settings import WORKSPACE,ARCHIVE_DIR

def main():
    source=WORKSPACE/'full_selection/selection_manifest.csv'
    label_path=WORKSPACE/'review_workspace/labels.json'
    labels=json.loads(label_path.read_text()) if label_path.exists() else {}
    with source.open(encoding='utf-8-sig') as f:reader=csv.DictReader(f);fields=reader.fieldnames;rows=list(reader)
    out=WORKSPACE/'final_selection';out.mkdir(exist_ok=True)
    fields=fields+['prior_status','original_review_reasons','review_outcome']
    archives={};members={};modified=[];unchanged=0;results=[]
    try:
        for original in rows:
            r=dict(original);pid=f'{r["road_level"]}:{r["point_id"]}';review=labels.get(pid)
            r['prior_status']=r['status'];r['original_review_reasons']=r['review_reasons'];r['review_reasons']='';r['status']='selected';r['review_outcome']='not_reviewed'
            if review and review['status']=='confirmed':
                selected=review['selected'];assert len(set(selected))==2 and all(a in [0,90,180,270] for a in selected)
                old=[int(r['side_a_angle']),int(r['side_b_angle'])]
                if sorted(selected)!=sorted(old):
                    name=r['archive']
                    if name not in archives:
                        archives[name]=zipfile.ZipFile(ARCHIVE_DIR/name)
                        members[name]={i.filename.rsplit('/',1)[-1]:i.filename for i in archives[name].infolist() if not i.is_dir() and not i.filename.startswith('__MACOSX/')}
                    for side,angle in zip(['side_a','side_b'],selected):
                        filename=f'{r["point_id"]}_{angle}_0.png';r[side+'_angle']=angle;r[side+'_filename']=filename;r[side+'_member']=members[name][filename]
                    r['selection_source']='human_review_modified';r['review_outcome']='modified';modified.append({'point_id':r['point_id'],'old':old,'new':selected})
                else:r['review_outcome']='confirmed_model_unchanged';unchanged+=1
                if review.get('note'):r['note']=(r['note']+' | ' if r['note'] else '')+'Review: '+review['note']
            elif review:r['review_outcome']=review['status']
            results.append(r)
        assert len({r['point_id'] for r in results})==len(results)
        for r in results:
            name=r['archive']
            if name not in archives:archives[name]=zipfile.ZipFile(ARCHIVE_DIR/name)
            assert r['side_a_filename']!=r['side_b_filename']
            for side in ['side_a','side_b']:
                assert archives[name].getinfo(r[side+'_member']).file_size>0
        path=out/'final_selection_manifest.csv';temp=path.with_suffix('.csv.tmp')
        with temp.open('w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(results)
        temp.replace(path)
        summary={'points':len(results),'image_references':2*len(results),'confirmed_review_modifications':len(modified),
                 'confirmed_review_unchanged':unchanged,'existing_human_confirmed_selections_retained':sum(r['selection_source']=='human_confirmed' for r in results),
                 'all_selected_members_verified':True,'selection_sources':dict(Counter(r['selection_source'] for r in results)),
                 'policy':'User accepted existing model choices including previously flagged points; only confirmed review pair changes applied. Existing earlier human-confirmed selections retained.',
                 'status_semantics':'selected means accepted for use under this policy, not individually human-verified.',
                 'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'review_labels_sha256':hashlib.sha256(label_path.read_bytes()).hexdigest() if label_path.exists() else None}
        (out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
        (out/'human_modifications.json').write_text(json.dumps(modified,ensure_ascii=False,indent=2))
        print(json.dumps(summary,ensure_ascii=False,indent=2))
    finally:
        for z in archives.values():z.close()

if __name__=='__main__':main()
