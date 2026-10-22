set -eu
python3 - <<'PY'
import json
import os
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

def pool(command, tag):
    return ET.fromstring(subprocess.check_output(['su', '-', 'oneadmin', '-c', command], text=True)).findall(tag)

marker = Path('/root/screenshot-lab/wordpress-workflow.json')
if marker.exists():
    raise SystemExit('Previous WordPress marker exists; inspect that workflow before retrying.')
resources = {
    'vms': pool('onevm list -x', 'VM'),
    'templates': pool('onetemplate list -x', 'VMTEMPLATE'),
    'images': pool('oneimage list -x', 'IMAGE'),
}
names = {'vms': 'docs-screenshot-wordpress', 'templates': 'Service WordPress - KVM', 'images': 'Service WordPress - KVM'}
for kind, records in resources.items():
    if any(r.findtext('NAME') == names[kind] and (kind != 'vms' or r.findtext('STATE') != '6') for r in records):
        raise SystemExit('WordPress ' + kind + ' already exist; refusing to reuse them.')
marker.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
with marker.open('x') as stream:
    json.dump({'workflow_id': os.environ['SUNSTONE_WORKFLOW_ID'], 'names': names,
               'previous_ids': {kind: [r.findtext('ID') for r in records] for kind, records in resources.items()}}, stream)
marker.chmod(0o600)
print('WordPress baseline recorded; the browser will import and deploy the appliance.')
PY
