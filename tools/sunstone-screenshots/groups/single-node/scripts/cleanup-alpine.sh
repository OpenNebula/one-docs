set -eu
python3 - <<'PY'
import json
import os
from pathlib import Path
import subprocess
import time
import xml.etree.ElementTree as ET

def one(command):
    return subprocess.check_output(['su', '-', 'oneadmin', '-c', command], text=True)

marker = Path('/root/screenshot-lab/alpine-workflow.json')
if not marker.exists():
    print('No Alpine workflow marker; nothing to remove.')
    raise SystemExit(0)
state = json.loads(marker.read_text())
if state.get('workflow_id') != os.environ['SUNSTONE_WORKFLOW_ID']:
    print('Marker belongs to another invocation; leaving its VM and marker untouched.')
    raise SystemExit(0)
matches = [v for v in ET.fromstring(one('onevm list -x')).findall('VM')
           if v.findtext('NAME') == state['name']
           and v.findtext('ID') not in state['previous_ids']
           and v.findtext('STATE') != '6']
if len(matches) > 1:
    raise SystemExit('Multiple new workflow VMs found; refusing ambiguous cleanup.')
for vm in matches:
    vm_id = str(int(vm.findtext('ID')))
    # Pool records omit TEMPLATE_ID; verify ownership using the full VM record.
    current = ET.fromstring(one('onevm show ' + vm_id + ' -x'))
    if current.findtext('ID') != vm_id or current.findtext('NAME') != state['name']:
        raise SystemExit('Workflow VM identity changed; refusing cleanup.')
    template_id = current.findtext('TEMPLATE/TEMPLATE_ID')
    if template_id != state['template_id']:
        raise SystemExit(f'Workflow VM {vm_id} template does not match '
                         f'(expected {state["template_id"]}, found {template_id}); refusing cleanup.')
    one('onevm terminate --hard ' + vm_id)
    deadline = time.monotonic() + 180
    while True:
        current = ET.fromstring(one('onevm show ' + vm_id + ' -x'))
        if current.findtext('STATE') == '6':
            break
        if time.monotonic() >= deadline:
            raise SystemExit('Timed out waiting for Alpine VM to reach DONE.')
        time.sleep(2)
    print('Terminated workflow Alpine VM ' + vm_id)
marker.unlink()
PY
