set -eu
python3 - <<'PY'
import json
import os
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

marker = Path('/root/screenshot-lab/theme-workflow.json')
if marker.exists():
    raise SystemExit('Previous theme marker exists; inspect that workflow before retrying.')
user = ET.fromstring(subprocess.check_output(['su', '-', 'oneadmin', '-c', 'oneuser show 0 -x'], text=True))
template = user.find('TEMPLATE')
if user.findtext('ID') != '0' or template is None:
    raise SystemExit('Expected the lab oneadmin user and its template.')
original = ET.tostring(template, encoding='unicode')
marker.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
with marker.open('x') as stream:
    json.dump({'workflow_id': os.environ['SUNSTONE_WORKFLOW_ID'], 'template': original}, stream)
marker.chmod(0o600)
fireedge = template.find('FIREEDGE')
if fireedge is None:
    fireedge = ET.SubElement(template, 'FIREEDGE')
scheme = fireedge.find('SCHEME')
if scheme is None:
    scheme = ET.SubElement(fireedge, 'SCHEME')
scheme.text = 'system'
# Omit the optional filename so the CLI reads stdin instead of validating a file.
subprocess.run(['su', '-', 'oneadmin', '-c', 'oneuser update 0'],
               input=ET.tostring(template, encoding='unicode'), text=True, check=True)
print('Sunstone follows the browser color scheme for this page workflow.')
PY
