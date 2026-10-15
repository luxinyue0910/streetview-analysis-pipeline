"""Stream final selected images into one ZIP64 handoff without loose intermediate copies."""
import argparse
import csv
import hashlib
import io
import json
import shutil
import time
import zipfile
from collections import Counter
from pathlib import Path
from settings import WORKSPACE,ARCHIVE_DIR

def component(value):
    if not value or value in ['.','..'] or '/' in value or '\\' in value:raise ValueError('Invalid path component')
    return value

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--manifest',type=Path,default=WORKSPACE/'final_selection/final_selection_manifest.csv')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():raise SystemExit('Output already exists; refusing to overwrite.')
    args.output.parent.mkdir(parents=True,exist_ok=True)
    partial=args.output.with_suffix('.zip.partial')
    if partial.exists():raise SystemExit('A partial package already exists; inspect it before restarting.')
    raw_manifest=args.manifest.read_bytes()
    rows=list(csv.DictReader(io.StringIO(raw_manifest.decode('utf-8-sig'))))
    assert len({r['point_id'] for r in rows})==len(rows)
    assert all(r['status']=='selected' for r in rows)
    archives={};expected={};counts=Counter();image_bytes=0
    root='streetview_selected_images'
    try:
        for row in rows:
            archive=component(row['archive'])
            if archive not in archives:archives[archive]=zipfile.ZipFile(ARCHIVE_DIR/archive)
            for side in ['side_a','side_b']:
                filename=component(row[side+'_filename']);point=component(row['point_id']);level=component(row['road_level'])
                member=row[side+'_member'];info=archives[archive].getinfo(member)
                target=f'{root}/images/road_level_{level}/{point}/{filename}'
                assert target not in expected
                expected[target]=(archive,member,info.file_size,info.CRC);image_bytes+=info.file_size;counts[level]+=1
        estimate=image_bytes+len(raw_manifest)+len(expected)*300+100000
        free=shutil.disk_usage(args.output.parent).free
        if free<estimate+1024**3:raise SystemExit('Insufficient free space for the package plus a 1 GiB working margin.')
        manifest_sha=hashlib.sha256(raw_manifest).hexdigest()
        usage=f'''SELECTED STREET-VIEW IMAGES: TEAM HANDOFF

CONTENTS
{len(rows):,} center locations and {len(expected):,} selected images.
final_selection_manifest.csv: the unchanged final selection manifest.
images/road_level_1/ through road_level_4/: selected images grouped by road level,
then by coordinate-based point_id. Original image basenames are preserved.

FOLDER STRUCTURE AFTER EXTRACTION
streetview_selected_images/
  final_selection_manifest.csv
  USAGE.txt
  images/
    road_level_<road_level>/
      <point_id>/
        <original_image_filename>
        <other_original_image_filename>

HOW TO MATCH THE CSV TO THESE FILES
For each CSV row and each side (side_a or side_b), construct:
images/road_level_{{road_level}}/{{point_id}}/{{side_a_filename or side_b_filename}}
The archive and side_*_member columns still refer to the ORIGINAL source ZIPs.
They are retained for provenance; they are not paths inside this new package.
side_a and side_b do not denote physical left and right.

SELECTION POLICY
Model selections were retained, including previously flagged cases, with confirmed
human pair modifications applied and earlier human-confirmed selections preserved.
status=selected means accepted for downstream use, not individually human-verified.
prior_status, original_review_reasons, selection_source, and review_outcome preserve
the selection history. VLM scoring has not been performed.

IMAGE FORMAT AND INTEGRITY
The image bytes are copied unchanged from the original archives; no resizing or
re-encoding is performed. Filename extensions are also preserved. Some original
files ending in .png may actually contain JPEG data. Detect image encoding from
the bytes when constructing MIME types for a VLM API.
All selected output members are checked against the original byte lengths and CRCs.
This is a ZIP64 package, suitable for archives larger than 4 GiB. Use a ZIP64-capable
extractor. Allow enough storage for the ZIP and its extracted contents if unpacking.

Manifest SHA-256: {manifest_sha}
Project: https://github.com/luxinyue0910/streetview-analysis-pipeline
The source images are not published in the public repository. This package grants
no additional rights to redistribute the original image data.
'''
        start=time.perf_counter()
        with zipfile.ZipFile(partial,'w',compression=zipfile.ZIP_STORED,allowZip64=True) as target_zip:
            target_zip.writestr(root+'/final_selection_manifest.csv',raw_manifest)
            target_zip.writestr(root+'/USAGE.txt',usage.encode('utf-8'))
            for i,(target,(archive,member,size,crc)) in enumerate(expected.items(),1):
                with archives[archive].open(member) as source,target_zip.open(target,'w',force_zip64=True) as dest:
                    shutil.copyfileobj(source,dest,length=1024*1024)
                written=target_zip.getinfo(target)
                assert written.file_size==size and written.CRC==crc,'Image content mismatch'
                if i%1000==0 or i==len(expected):print(f'Packaged {i}/{len(expected)} images; {time.perf_counter()-start:.1f}s',flush=True)
        with zipfile.ZipFile(partial) as verify:
            assert len(verify.infolist())==len(expected)+2
            assert verify.read(root+'/final_selection_manifest.csv')==raw_manifest
            for target,(_,_,size,crc) in expected.items():
                info=verify.getinfo(target);assert info.file_size==size and info.CRC==crc
        partial.replace(args.output)
        summary={'points':len(rows),'images':len(expected),'images_by_road_level':dict(counts),'image_bytes':image_bytes,
                 'package_bytes':args.output.stat().st_size,'archive_entries':len(expected)+2,'manifest_sha256':manifest_sha,
                 'original_filenames_preserved':True,'all_image_sizes_and_crcs_verified':True,
                 'seconds':time.perf_counter()-start,'packaging':'Streaming ZIP64; no loose image duplicates or re-encoding'}
        args.output.with_suffix('.summary.json').write_text(json.dumps(summary,indent=2))
        print(json.dumps(summary,indent=2),flush=True)
    finally:
        for archive in archives.values():archive.close()

if __name__=='__main__':main()
