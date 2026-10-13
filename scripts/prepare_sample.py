from settings import WORKSPACE, ARCHIVE_DIR
"""Create a reproducible stratified sample from the verified center-point inventory."""
import csv
import json
import random
import zipfile
from pathlib import Path

ROOT = WORKSPACE
DATA = ROOT / 'annotation'
SOURCE = ARCHIVE_DIR

def main():
    DATA.mkdir(exist_ok=True)
    if (DATA / 'sample.json').exists():
        raise SystemExit('Sample already exists; refusing to replace annotation inputs.')
    with (ROOT / 'inspection/center_point_filter_manifest.csv').open(encoding='utf-8-sig') as f:
        candidates = [r for r in csv.DictReader(f) if r['decision'] == 'keep']
    rng = random.Random(20261012)
    points = []
    for level, count in [(1, 13), (2, 13), (3, 12), (4, 12)]:
        pool = sorted([r for r in candidates if int(r['road_level']) == level], key=lambda r: r['point_id'])
        picked = rng.sample(pool, count)
        archive = picked[0]['archive']
        with zipfile.ZipFile(SOURCE / archive) as z:
            members = {i.filename.rsplit('/', 1)[-1]: i for i in z.infolist() if not i.is_dir() and not i.filename.startswith('__MACOSX/')}
            for row in picked:
                pid = row['point_id']
                images = []
                for angle in [0, 90, 180, 270]:
                    filename = f'{pid}_{angle}_0.png'
                    member = members[filename]
                    rel = f'images/{level}/{filename}'
                    dest = DATA / rel
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_bytes(z.read(member))
                    images.append({'angle': angle, 'filename': filename, 'archive_member': member.filename, 'url': '/' + rel})
                points.append({'id': f'{level}:{pid}', 'point_id': pid, 'road_level': level, 'archive': archive, 'images': images})
    rng.shuffle(points)
    payload = {'sample_id': 'center50-seed20261012-v1', 'seed': 20261012, 'counts': {'1': 13, '2': 13, '3': 12, '4': 12}, 'points': points}
    (DATA / 'sample.json').write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    print('Created 50 center points, 200 original images:', DATA)

if __name__ == '__main__':
    main()
