from settings import WORKSPACE, ARCHIVE_DIR
"""Local-only annotation server; saves selections atomically and exports image references."""
import argparse
import csv
import io
import json
import os
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(os.environ.get('STREETVIEW_ANNOTATION_DIR', WORKSPACE / 'annotation'))
LOCK = threading.Lock()
SAMPLE = json.loads((ROOT / 'sample.json').read_text())
POINTS = {p['id']: p for p in SAMPLE['points']}
IMAGE_URLS = {i['url'] for p in SAMPLE['points'] for i in p['images']}
LABELS = ROOT / 'labels.json'

def load_labels():
    return json.loads(LABELS.read_text()) if LABELS.exists() else {}

def csv_export(labels):
    f = io.StringIO(newline='')
    w = csv.writer(f)
    w.writerow(['sample_id', 'point_id', 'road_level', 'archive', 'status', 'side_a_angle', 'side_a_filename', 'side_a_member', 'side_b_angle', 'side_b_filename', 'side_b_member', 'note'])
    for p in SAMPLE['points']:
        label = labels.get(p['id'], {})
        chosen = label.get('selected', [])
        sides = []
        for idx in range(2):
            im = next((i for i in p['images'] if idx < len(chosen) and i['angle'] == chosen[idx]), None)
            sides.extend([im['angle'], im['filename'], im['archive_member']] if im else ['', '', ''])
        w.writerow([SAMPLE['sample_id'], p['point_id'], p['road_level'], p['archive'], label.get('status', 'unlabeled'), *sides, label.get('note', '')])
    return ('\ufeff' + f.getvalue()).encode('utf-8')

class Handler(SimpleHTTPRequestHandler):
    def send_data(self, data, kind='application/json; charset=utf-8', status=200):
        self.send_response(status)
        self.send_header('Content-Type', kind)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == '/api/predictions':
            configured = os.environ.get('STREETVIEW_PREDICTIONS_FILE')
            if not configured:
                return self.send_data(b'{}', status=404)
            return self.send_data(Path(configured).read_bytes())
        if path == '/api/state':
            with LOCK:
                labels = load_labels()
            return self.send_data(json.dumps({'sample': SAMPLE, 'labels': labels}, ensure_ascii=False).encode())
        if path == '/api/export.csv':
            with LOCK:
                data = csv_export(load_labels())
                (ROOT / 'annotations.csv').write_bytes(data)
            return self.send_data(data, 'text/csv; charset=utf-8')
        if path == '/api/export.json':
            with LOCK:
                data = json.dumps({'sample_id': SAMPLE['sample_id'], 'labels': load_labels()}, ensure_ascii=False, indent=2).encode()
            return self.send_data(data)
        # Serve only page assets and sample images, never filesystem state.
        if path not in ['/', '/index.html', '/app.js', '/style.css'] and path not in IMAGE_URLS:
            return self.send_data(b'Not found', 'text/plain', 404)
        return super().do_GET()

    def do_POST(self):
        if self.path != '/api/label':
            return self.send_data(b'{}', status=404)
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if not 0 < size < 20000:
                raise ValueError('Invalid request size')
            value = json.loads(self.rfile.read(size))
            pid, selected, status = value['id'], value['selected'], value['status']
            if pid not in POINTS or not isinstance(selected, list) or len(selected) > 2 or len(set(selected)) != len(selected):
                raise ValueError('Invalid point or selection')
            if any(type(a) is not int or a not in [0, 90, 180, 270] for a in selected):
                raise ValueError('Invalid angle')
            if status not in ['draft', 'confirmed', 'needs_review'] or status == 'confirmed' and len(selected) != 2:
                raise ValueError('Confirm requires exactly two images')
            if SAMPLE.get('require_two_review') and status == 'needs_review' and len(selected) != 2:
                raise ValueError('Uncertain selection also requires exactly two images')
            note = value.get('note', '')
            if not isinstance(note, str) or len(note) > 2000:
                raise ValueError('Invalid note')
            with LOCK:
                labels = load_labels()
                labels[pid] = {'selected': selected, 'status': status, 'note': note}
                temp = LABELS.with_suffix('.tmp')
                temp.write_text(json.dumps(labels, ensure_ascii=False, indent=2))
                os.replace(temp, LABELS)
                csv_temp = ROOT / 'annotations.csv.tmp'
                csv_temp.write_bytes(csv_export(labels))
                os.replace(csv_temp, ROOT / 'annotations.csv')
            self.send_data(b'{"ok":true}')
        except (KeyError, ValueError, TypeError) as e:
            self.send_data(json.dumps({'error': str(e)}).encode(), status=400)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--open-browser', action='store_true')
    args = parser.parse_args()
    try:
        server = ThreadingHTTPServer(('127.0.0.1', args.port), partial(Handler, directory=str(ROOT)))
    except OSError:
        if args.open_browser:
            from urllib.request import urlopen
            import webbrowser
            try:
                with urlopen(f'http://127.0.0.1:{args.port}/api/state', timeout=2) as response:
                    existing = json.load(response)
                if existing['sample']['sample_id'] == SAMPLE['sample_id']:
                    webbrowser.open(f'http://127.0.0.1:{args.port}')
                    raise SystemExit(0)
            except (OSError, KeyError, ValueError):
                pass
        raise
    print(f'Annotation page: http://127.0.0.1:{args.port}', flush=True)
    if args.open_browser:
        import webbrowser
        webbrowser.open(f'http://127.0.0.1:{args.port}')
    server.serve_forever()
