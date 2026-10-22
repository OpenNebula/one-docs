set -eu
python3 - <<'PY'
import json
import os
from pathlib import Path
import subprocess
import time

def one(command):
    return subprocess.check_output(['su', '-', 'oneadmin', '-c', command], text=True)

def templates():
    values = json.loads(one('oneflow-template list -j'))['DOCUMENT_POOL'].get('DOCUMENT') or []
    return [values] if isinstance(values, dict) else values

marker = Path('/root/screenshot-lab/oneslurm-workflow.json')
if not marker.exists():
    print('No OneSlurm workflow marker; nothing to remove.')
    raise SystemExit(0)
state = json.loads(marker.read_text())
if state.get('workflow_id') != os.environ['SUNSTONE_WORKFLOW_ID']:
    print('OneSlurm marker belongs to another invocation; leaving it untouched.')
    raise SystemExit(0)
matches = [t for t in templates() if t['NAME'] == state['name']
           and str(t['ID']) not in state['previous_ids']]
if len(matches) > 1:
    raise SystemExit('Multiple new OneSlurm templates found; refusing ambiguous cleanup.')
for template in matches:
    template_id = str(int(template['ID']))
    current = json.loads(one('oneflow-template show ' + template_id + ' -j'))['DOCUMENT']
    if str(current['ID']) != template_id or current['NAME'] != state['name']:
        raise SystemExit('OneSlurm service template identity changed; refusing cleanup.')
    # Delete only the new service template. The group VM owns the imported role assets.
    one('oneflow-template delete ' + template_id)
    deadline = time.monotonic() + 60
    while any(str(t['ID']) == template_id for t in templates()):
        if time.monotonic() >= deadline:
            raise SystemExit('Timed out waiting for OneSlurm template deletion.')
        time.sleep(2)
    print('Deleted workflow OneSlurm service template ' + template_id)
marker.unlink()
PY
