set -eu
python3 - <<'PY'
import json
import os
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

def one(command):
    return ET.fromstring(subprocess.check_output(['su', '-', 'oneadmin', '-c', command], text=True))

name = 'docs-screenshot-alpine'
marker = Path('/root/screenshot-lab/alpine-workflow.json')
if marker.exists():
    raise SystemExit('Previous Alpine workflow marker exists; inspect and clean up that workflow first.')
vms = one('onevm list -x').findall('VM')
if any(v.findtext('NAME') == name and v.findtext('STATE') != '6' for v in vms):
    raise SystemExit('A VM named docs-screenshot-alpine already exists; refusing to reuse it.')
templates = [t for t in one('onetemplate list -x').findall('VMTEMPLATE')
             if (t.findtext('NAME') or '').lower().startswith('alpine')]
if len(templates) != 1:
    raise SystemExit('Expected exactly one existing Alpine template in this miniONE lab.')
marker.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
with marker.open('x') as stream:
    json.dump({'name': name, 'workflow_id': os.environ['SUNSTONE_WORKFLOW_ID'],
               'template_id': templates[0].findtext('ID'),
               'previous_ids': [v.findtext('ID') for v in vms]}, stream)
marker.chmod(0o600)
print('Alpine workflow prepared; no VM has been created yet.')
PY
