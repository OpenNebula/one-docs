"""Run on the laptop to recover a group stopped during Alpine teardown."""

import argparse
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from sunstone_screenshots import provision as lab


GROUP = Path(__file__).resolve().parents[1]


def recover(run_dir):
    run_dir = Path(run_dir).resolve()
    result_path = run_dir / 'workflow.json'
    result = lab.load(result_path)
    pages = result.get('pages', [])
    if (result.get('group') != str(GROUP / 'group.json') or len(pages) != 1
            or pages[0].get('manifest') != str(GROUP / 'automated.json')
            or pages[0].get('status') != 'failed'):
        raise lab.ProvisionError('Recovery requires this group stopped on its first, Alpine workflow.')
    state = lab.load(run_dir / 'state.json')
    if state.get('phase') != 'ready':
        raise lab.ProvisionError('Recovery requires a ready lab.')
    vm = lab.owned_vm(lab.connect(state['config']), state)
    if int(vm.STATE) != 3 or int(vm.LCM_STATE) != 3:
        raise lab.ProvisionError('Recorded lab VM is not running.')

    marker = lab.ssh(state, run_dir, 'cat /root/screenshot-lab/alpine-workflow.json\n')
    if marker is None or marker.returncode:
        raise lab.ProvisionError('Cannot read the Alpine workflow marker; check SSH/sudo access.')
    marker = json.loads(marker.stdout)
    workflow_id = marker.get('workflow_id', '')
    if marker.get('name') != 'docs-screenshot-alpine' or not re.fullmatch('[0-9a-f]{32}', workflow_id):
        raise lab.ProvisionError('Unexpected Alpine workflow marker; refusing recovery.')
    archive = run_dir / f'workflow.failed-{workflow_id}.json'
    if archive.exists():
        raise lab.ProvisionError(f'Recovery archive already exists: {archive}')

    script = (GROUP / 'scripts/cleanup-alpine.sh').read_text()
    log_path = run_dir / 'guest-commands.log'
    log_path.touch(mode=0o600)
    with log_path.open('a') as log:
        log.write('\nRetrying Alpine cleanup with full VM metadata.\n')
        log.flush()
        cleanup = lab.ssh(state, run_dir, f'export SUNSTONE_WORKFLOW_ID={workflow_id}\n' + script,
                          timeout=240, log=log)
    if cleanup is None or cleanup.returncode:
        raise lab.ProvisionError(f'Alpine recovery failed; inspect {log_path}')
    verified = lab.ssh(state, run_dir, 'test ! -e /root/screenshot-lab/alpine-workflow.json\n')
    if verified is None or verified.returncode:
        raise lab.ProvisionError('Alpine marker remains after cleanup; refusing to reset the failed run.')
    result_path.rename(archive)
    print(f'Alpine cleanup completed; prior failed result retained at {archive}')
    print('The lab can now be retried with run-group --reuse.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir', required=True)
    args = parser.parse_args()
    try:
        recover(args.run_dir)
    except (lab.ProvisionError, OSError, ValueError, KeyError) as exc:
        print(f'error: {exc}', file=sys.stderr)
        sys.exit(1)
