"""Configure private workspace and original archives without hard-coded local paths."""
import os
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[1]
WORKSPACE = Path(os.environ.get('STREETVIEW_WORKSPACE', REPOSITORY / 'workspace')).expanduser().resolve()
ARCHIVE_DIR = Path(os.environ.get('STREETVIEW_ARCHIVE_DIR', WORKSPACE / 'raw')).expanduser().resolve()
