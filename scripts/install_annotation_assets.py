"""Copy versioned UI assets into a private workspace, without changing labels or samples."""
import shutil
from settings import REPOSITORY, WORKSPACE

for name in ['annotation', 'annotation100', 'annotation30']:
    destination = WORKSPACE / name
    destination.mkdir(parents=True, exist_ok=True)
    for file in ['index.html', 'style.css', 'app.js']:
        shutil.copyfile(REPOSITORY / 'web' / name / file, destination / file)
print('Annotation assets installed; labels and sample files preserved.')
