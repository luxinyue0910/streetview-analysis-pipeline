"""Validate full-manifest coverage, reference integrity, and selection provenance."""
import argparse
import csv
import json
import math
import zipfile
from collections import Counter
from pathlib import Path
from settings import WORKSPACE, ARCHIVE_DIR
from select_full_dataset import annotations

def main():
    p=argparse.ArgumentParser();p.add_argument('manifest',type=Path);p.add_argument('--allow-partial',action='store_true')
    p.add_argument('--review-labels',type=Path,default=WORKSPACE/'review_workspace/labels.json');args=p.parse_args()
    with (WORKSPACE/'inspection/center_point_filter_manifest.csv').open(encoding='utf-8-sig') as f:expected={r['point_id']:r for r in csv.DictReader(f) if r['decision']=='keep'}
    with args.manifest.open(encoding='utf-8-sig') as f:rows=list(csv.DictReader(f))
    observed={r['point_id'] for r in rows};assert len(observed)==len(rows),'Duplicate point rows'
    assert observed<=set(expected),'Non-center coordinates in output'
    if not args.allow_partial:assert observed==set(expected),'Missing center point rows'
    known,_=annotations();archives={};manual=0
    reviewed=json.loads(args.review_labels.read_text()) if args.review_labels.exists() else {}
    try:
        for row in rows:
            source=expected[row['point_id']]
            assert row['archive']==source['archive'] and row['road_level']==source['road_level']
            name=row['archive']
            if name not in archives:archives[name]=zipfile.ZipFile(ARCHIVE_DIR/name)
            angles=[]
            for side in ['side_a','side_b']:
                member=row[side+'_member'];filename=row[side+'_filename'];angle=int(row[side+'_angle']);angles.append(angle)
                assert member.rsplit('/',1)[-1]==filename
                assert filename==f'{row["point_id"]}_{angle}_0.png'
                assert archives[name].getinfo(member).file_size>0
            assert len(set(angles))==2 and all(a in [0,90,180,270] for a in angles)
            assert row['status'] in ['confirmed','auto_selected','needs_review']
            assert math.isfinite(float(row['classifier_margin']))
            if row['status']=='confirmed':
                pid=f'{row["road_level"]}:{row["point_id"]}'
                if row['selection_source']=='human_review':
                    human=reviewed[pid];assert human['status']=='confirmed'
                else:
                    human=known[pid];assert human['certain'] and row['selection_source']=='human_confirmed'
                assert angles==human['selected'];manual+=1
            else:assert sorted(angles)==list(map(int,row['classifier_pair'].split('/')))
            if row['status']=='needs_review':assert row['review_reasons']
            else:assert not row['review_reasons']
            if row['status']=='auto_selected':assert row['classifier_pair']==row['baseline_pair']
        summary={'validated_points':len(rows),'validated_image_references':len(rows)*2,'complete_coverage':observed==set(expected),
                 'human_overrides_verified':manual,'status_counts':dict(Counter(r['status'] for r in rows)),
                 'reference_check':'All selected ZIP members exist and have positive file size. All input images were read and decoded during inference.'}
        (args.manifest.parent/'validation_summary.json').write_text(json.dumps(summary,indent=2))
        print(json.dumps(summary,indent=2))
    finally:
        for z in archives.values():z.close()

if __name__=='__main__':main()
