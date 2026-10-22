set -eu
python3 - <<'PY'
import json
import os
from pathlib import Path
import subprocess

name = 'docs-screenshot-oneslurm'
marker = Path('/root/screenshot-lab/oneslurm-workflow.json')
if marker.exists():
    raise SystemExit('Previous OneSlurm workflow marker exists; inspect that workflow before retrying.')
output = subprocess.check_output(['su', '-', 'oneadmin', '-c', 'oneflow-template list -j'], text=True)
templates = json.loads(output)['DOCUMENT_POOL'].get('DOCUMENT') or []
if isinstance(templates, dict):
    templates = [templates]
if any(t['NAME'] == name for t in templates):
    raise SystemExit('The test OneSlurm service template already exists; refusing to reuse it.')
marker.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
with marker.open('x') as stream:
    json.dump({'name': name, 'workflow_id': os.environ['SUNSTONE_WORKFLOW_ID'],
               'previous_ids': [str(t['ID']) for t in templates]}, stream)
marker.chmod(0o600)
print('OneSlurm workflow prepared; the browser will import the service template.')
PY
