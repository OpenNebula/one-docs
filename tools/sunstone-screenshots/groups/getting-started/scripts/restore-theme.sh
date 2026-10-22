set -eu
python3 - <<'PY'
import json
import os
from pathlib import Path
import subprocess

marker = Path('/root/screenshot-lab/theme-workflow.json')
if not marker.exists():
    raise SystemExit(0)
state = json.loads(marker.read_text())
if state.get('workflow_id') != os.environ['SUNSTONE_WORKFLOW_ID']:
    print('Theme marker belongs to another invocation; leaving it untouched.')
    raise SystemExit(0)
subprocess.run(['su', '-', 'oneadmin', '-c', 'oneuser update 0'],
               input=state['template'], text=True, check=True)
marker.unlink()
print('Restored the original Sunstone user settings.')
PY
