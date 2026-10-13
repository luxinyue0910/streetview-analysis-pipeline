from settings import WORKSPACE, ARCHIVE_DIR
"""Read selected images directly from original archives using an annotation CSV.

Usage: python3 read_selected.py annotation/annotations.csv --output selected_images
Without --output, validates all confirmed image references. Original archives stay intact.
"""
import argparse
import csv
import zipfile
from pathlib import Path

def iter_selected(manifest, archive_dir, include_auto=False, include_review=False):
    with open(manifest, encoding='utf-8-sig', newline='') as f:
        rows = list(csv.DictReader(f))
    archives = {}
    try:
        for row in rows:
            allowed = {'confirmed', 'selected'}
            if include_auto: allowed.add('auto_selected')
            if include_review: allowed.add('needs_review')
            if row['status'] not in allowed:
                continue
            name = row['archive']
            if Path(name).name != name:
                raise ValueError('Invalid archive name')
            if name not in archives:
                archives[name] = zipfile.ZipFile(Path(archive_dir) / name)
            for side in ['side_a', 'side_b']:
                member = row[side + '_member']
                if not member:
                    raise ValueError(f'Missing image reference: {row["point_id"]} {side}')
                yield row, side, archives[name].read(member)
    finally:
        for z in archives.values():
            z.close()

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('manifest')
    p.add_argument('--archive-dir', default=str(ARCHIVE_DIR))
    p.add_argument('--output', type=Path)
    p.add_argument('--include-auto', action='store_true', help='Also read model-selected images not manually reviewed')
    p.add_argument('--include-review', action='store_true', help='Also read provisional images flagged for review')
    args = p.parse_args()
    count = 0
    for row, side, data in iter_selected(args.manifest, args.archive_dir, args.include_auto, args.include_review):
        if args.output:
            directory = args.output / row['road_level'] / row['point_id']
            directory.mkdir(parents=True, exist_ok=True)
            (directory / (side + '.png')).write_bytes(data)
        count += 1
    print(f'Read {count} selected images successfully.')
