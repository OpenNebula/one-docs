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

marker = Path('/root/screenshot-lab/wordpress-workflow.json')
if not marker.exists():
    print('No WordPress marker; nothing to remove.')
    raise SystemExit(0)
state = json.loads(marker.read_text())
if state.get('workflow_id') != os.environ['SUNSTONE_WORKFLOW_ID']:
    print('WordPress marker belongs to another invocation; leaving it untouched.')
    raise SystemExit(0)

commands = {'vms': ('onevm', 'VM'), 'templates': ('onetemplate', 'VMTEMPLATE'), 'images': ('oneimage', 'IMAGE')}
owned = {}
# Validate the complete dependency chain before issuing any destructive command.
for kind, (command, tag) in commands.items():
    records = ET.fromstring(one(command + ' list -x')).findall(tag)
    matches = [r for r in records if r.findtext('NAME') == state['names'][kind]
               and r.findtext('ID') not in state['previous_ids'][kind]
               and (kind != 'vms' or r.findtext('STATE') != '6')]
    if len(matches) > 1:
        raise SystemExit('Multiple new WordPress ' + kind + '; refusing ambiguous cleanup.')
    if not matches:
        continue
    resource_id = str(int(matches[0].findtext('ID')))
    current = ET.fromstring(one(command + ' show ' + resource_id + ' -x'))
    if (current.findtext('ID') != resource_id or current.findtext('NAME') != state['names'][kind]
            or current.findtext('UID') != '0'):
        raise SystemExit('WordPress ' + kind + ' identity changed; refusing cleanup.')
    owned[kind] = current

if 'vms' in owned:
    expected = owned['templates'].findtext('ID') if 'templates' in owned else None
    if expected is None or owned['vms'].findtext('TEMPLATE/TEMPLATE_ID') != expected:
        raise SystemExit('WordPress VM template does not match the imported template; refusing cleanup.')
if 'templates' in owned:
    disks = owned['templates'].findall('TEMPLATE/DISK')
    expected = owned['images'].findtext('ID') if 'images' in owned else None
    if expected is None or not disks or any(d.findtext('IMAGE_ID') != expected for d in disks):
        raise SystemExit('WordPress template image does not match the import; refusing cleanup.')

if 'vms' in owned:
    vm_id = owned['vms'].findtext('ID')
    one('onevm terminate --hard ' + vm_id)
    deadline = time.monotonic() + 180
    while ET.fromstring(one('onevm show ' + vm_id + ' -x')).findtext('STATE') != '6':
        if time.monotonic() >= deadline:
            raise SystemExit('Timed out waiting for WordPress VM to reach DONE.')
        time.sleep(2)
if 'templates' in owned:
    one('onetemplate delete ' + owned['templates'].findtext('ID'))
if 'images' in owned:
    image_id = owned['images'].findtext('ID')
    deadline = time.monotonic() + 120
    delete_requested = False
    waiting_reported = False
    while True:
        records = ET.fromstring(one('oneimage list -x')).findall('IMAGE')
        current = next((r for r in records if r.findtext('ID') == image_id), None)
        if current is None:
            break
        if current.findtext('NAME') != state['names']['images'] or current.findtext('UID') != '0':
            raise SystemExit('WordPress image identity changed while waiting; refusing cleanup.')
        image_state = current.findtext('STATE')
        # Imports and disk releases are asynchronous; never force-delete their image.
        if image_state in ('1', '3', '5') and not delete_requested:
            one('oneimage delete ' + image_id)
            delete_requested = True
        elif image_state not in tuple(str(i) for i in range(11)):
            raise SystemExit('Unknown WordPress image state; refusing cleanup.')
        elif not delete_requested and not waiting_reported:
            print('Waiting for WordPress image ' + image_id + ' operation to finish (STATE=' + image_state + ').', flush=True)
            waiting_reported = True
        if time.monotonic() >= deadline:
            raise SystemExit('Timed out waiting for WordPress image ' + image_id + ' cleanup (STATE=' + image_state
                             + '). Marker retained; inspect the import/datastore operation before retrying recovery.')
        time.sleep(2)
marker.unlink()
print('Removed the workflow WordPress VM, template and image; existing resources were preserved.')
PY
