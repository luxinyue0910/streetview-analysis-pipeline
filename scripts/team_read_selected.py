"""Standalone standard-library reader for the team selection-manifest handoff.

Use --check-only to validate ZIP member references without decoding or extracting.
Without --output, selected bytes are read and checked but no images are written.
"""
import argparse
import csv
import zipfile
from pathlib import Path

def safe_component(value):
    if not value or value in ('.', '..') or '/' in value or '\\' in value:
        raise ValueError('Invalid path component in manifest')
    return value

def iter_selected(manifest, archive_dir, limit_points=0, check_only=False):
    archives={}
    required={'point_id','road_level','archive','status','side_a_member','side_b_member'}
    count=0
    try:
        with open(manifest,encoding='utf-8-sig',newline='') as f:
            reader=csv.DictReader(f)
            if not required.issubset(reader.fieldnames or []):raise ValueError('Missing required manifest columns')
            for row in reader:
                if row['status'] not in {'selected','confirmed'}:continue
                if limit_points and count>=limit_points:break
                name=safe_component(row['archive']);safe_component(row['point_id']);safe_component(row['road_level'])
                if name not in archives:archives[name]=zipfile.ZipFile(Path(archive_dir)/name)
                for side in ['side_a','side_b']:
                    member=row[side+'_member']
                    if not member or archives[name].getinfo(member).file_size<=0:raise ValueError('Missing or empty selected image member')
                    yield row,side,None if check_only else archives[name].read(member)
                count+=1
    finally:
        for archive in archives.values():archive.close()

def extension(data):
    if data.startswith(b'\xff\xd8'):return '.jpg'
    if data.startswith(b'\x89PNG\r\n\x1a\n'):return '.png'
    raise ValueError('Unsupported image encoding; expected JPEG or PNG')

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest',type=Path)
    parser.add_argument('--archive-dir',type=Path,required=True,help='Folder containing the original ZIP archives')
    parser.add_argument('--output',type=Path,help='Optional destination for selected images')
    parser.add_argument('--check-only',action='store_true',help='Validate references without reading image bytes')
    parser.add_argument('--limit-points',type=int,default=0,help='Limit to this many points; 0 means all')
    args=parser.parse_args()
    if args.limit_points<0:parser.error('--limit-points must be nonnegative')
    if args.check_only and args.output:parser.error('--check-only cannot be combined with --output')
    count=0
    for row,side,data in iter_selected(args.manifest,args.archive_dir,args.limit_points,args.check_only):
        if data is not None:
            ext=extension(data)
            if args.output:
                dest=args.output/row['road_level']/row['point_id'];dest.mkdir(parents=True,exist_ok=True)
                (dest/(side+ext)).write_bytes(data)
        count+=1
    print(f'{"Validated" if args.check_only else "Read"} {count} selected image references across {count//2} points.')

if __name__=='__main__':main()
