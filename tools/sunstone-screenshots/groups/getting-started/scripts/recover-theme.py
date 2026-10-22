"""Recover saved settings and guarded resources for interrupted getting-started captures."""

import argparse
import json
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from sunstone_screenshots import provision as lab


GROUP = Path(__file__).resolve().parents[1]
MARKER = '/root/screenshot-lab/theme-workflow.json'
ALPINE_MARKER = '/root/screenshot-lab/alpine-workflow.json'
WORDPRESS_MARKER = '/root/screenshot-lab/wordpress-workflow.json'
WORDPRESS_GUARD = f'test ! -e {WORDPRESS_MARKER}\n'
RESOURCE_GUARDS = f'test ! -e {ALPINE_MARKER}\n' + WORDPRESS_GUARD
USER_COMMAND = "su - oneadmin -c 'oneuser show 0 -x'\n"


def template_shape(template):
    text = template.text or ''
    if len(template) and not text.strip():
        text = ''
    return (template.tag, text, tuple(sorted(template.attrib.items())),
            tuple(sorted(template_shape(child) for child in template)))


def user_template(result):
    if result is None or result.returncode:
        raise lab.ProvisionError('Cannot verify the lab user settings; check SSH/sudo access.')
    user = ET.fromstring(result.stdout)
    template = user.find('TEMPLATE')
    if user.findtext('ID') != '0' or template is None:
        raise lab.ProvisionError('Expected the lab oneadmin user and its template.')
    return template


def valid_ids(value):
    return isinstance(value, list) and all(isinstance(item, str) and re.fullmatch('[0-9]+', item) for item in value)


def recover(run_dir, include_alpine=False, include_wordpress=False, workflow_record=None):
    with lab.run_lock(run_dir):
        return _recover(run_dir, include_alpine, include_wordpress, workflow_record)


def _recover(run_dir, include_alpine, include_wordpress, workflow_record):
    include_alpine = include_alpine or include_wordpress
    run_dir = Path(run_dir).resolve()
    result_path = run_dir / 'workflow.json'
    record_path = result_path
    if workflow_record is not None:
        record_path = Path(workflow_record).resolve()
        if (not include_wordpress or record_path.parent != run_dir
                or not re.fullmatch(r'workflow\.failed-wordpress-[0-9a-f]{32}\.json', record_path.name)):
            raise lab.ProvisionError('workflow-record must be an archived WordPress workflow in this run directory.')
        if result_path.exists():
            raise lab.ProvisionError('workflow.json still exists; recover that active failed record without --workflow-record.')
    workflow_result = lab.load(record_path)
    pages = workflow_result.get('pages', [])
    if include_wordpress:
        names = ('deploy_opennebula_onprem_with_minione.json', 'deploy_opennebula_on_aws.json',
                 'deploy_opennebula_onprem_with_poc_iso.json', 'validate_the_environment.json')
        if (workflow_result.get('group') != str(GROUP / 'group.json') or workflow_result.get('lab_status') != 'retained'
                or [page.get('manifest') for page in pages] != [str(GROUP / name) for name in names]
                or [page.get('status') for page in pages] != ['complete', 'complete', 'complete', 'failed']):
            raise lab.ProvisionError('WordPress recovery requires this group stopped on its validation page after three completed pages.')
    elif (workflow_result.get('group') != str(GROUP / 'group.json') or workflow_result.get('lab_status') != 'retained'
          or len(pages) != 1 or pages[0].get('status') != 'failed'
          or pages[0].get('manifest') != str(GROUP / 'deploy_opennebula_onprem_with_minione.json')):
        raise lab.ProvisionError('Recovery requires this group stopped on its first page.')
    if not include_alpine and any(p.is_file() for p in (run_dir / 'screenshots').rglob('*')):
        raise lab.ProvisionError('Screenshots already exist; refusing theme-only recovery.')
    log_path = run_dir / 'guest-commands.log'
    if not include_alpine:
        log_text = log_path.read_text()
        if 'oneuser update 0 /dev/stdin' not in log_text or 'argument 1 must be one of file' not in log_text:
            raise lab.ProvisionError('Guest log does not identify the /dev/stdin theme-hook failure.')
    state = lab.load(run_dir / 'state.json')
    if state.get('phase') != 'ready':
        raise lab.ProvisionError('Recovery requires a ready lab.')
    address = lab.running_address(lab.connect(state['config']), state)
    if not address or address != state.get('address'):
        raise lab.ProvisionError('Recorded VM is not running at its saved address; refusing recovery.')

    guards = '' if include_wordpress else WORDPRESS_GUARD if include_alpine else RESOURCE_GUARDS
    theme_command = (f'if test -e {MARKER}; then cat {MARKER}; else printf null; fi\n'
                     if include_wordpress else f'cat {MARKER}\n')
    marker = lab.ssh(state, run_dir, 'set -e\n' + guards + theme_command)
    if marker is None or marker.returncode:
        detail = getattr(marker, 'stderr', '').strip() if marker is not None else 'SSH command timed out'
        scope = 'WordPress' if include_wordpress else 'miniONE' if include_alpine else 'theme-only'
        raise lab.ProvisionError(f'Cannot verify a {scope} guest state; check resource markers and SSH/sudo access.'
                                 + (' ' + detail[-2000:] if detail else ''))
    marker = json.loads(marker.stdout)
    if not isinstance(marker, dict) and not (marker is None and include_wordpress):
        raise lab.ProvisionError('Unexpected theme snapshot; refusing recovery.')
    workflow_id = None
    if marker is not None:
        workflow_id = marker.get('workflow_id', '')
        if not isinstance(workflow_id, str) or not re.fullmatch('[0-9a-f]{32}', workflow_id):
            raise lab.ProvisionError('Unexpected theme workflow ID; refusing recovery.')
        original = ET.fromstring(marker['template'])
        if original.tag != 'TEMPLATE':
            raise lab.ProvisionError('Unexpected theme snapshot; refusing recovery.')

    alpine = None
    if include_alpine:
        result = lab.ssh(state, run_dir, 'set -e\n' + ('' if include_wordpress else WORDPRESS_GUARD)
                         + f'if test -e {ALPINE_MARKER}; then cat {ALPINE_MARKER}; else printf null; fi\n')
        if result is None or result.returncode:
            raise lab.ProvisionError('Cannot inspect the Alpine marker; check SSH/sudo access.')
        alpine = json.loads(result.stdout)
        if alpine is not None and (
                not isinstance(alpine, dict)
                or (workflow_id is not None and alpine.get('workflow_id') != workflow_id)
                or alpine.get('name') != 'docs-screenshot-alpine'
                or not isinstance(alpine.get('template_id'), str)
                or not re.fullmatch('[0-9]+', alpine['template_id'])
                or not valid_ids(alpine.get('previous_ids'))):
            raise lab.ProvisionError('Alpine marker does not identify the same workflow; refusing recovery.')

    wordpress = None
    if include_wordpress:
        result = lab.ssh(state, run_dir,
                         f'if test -e {WORDPRESS_MARKER}; then cat {WORDPRESS_MARKER}; else printf null; fi\n')
        if result is None or result.returncode:
            raise lab.ProvisionError('Cannot inspect the WordPress marker; check SSH/sudo access.')
        wordpress = json.loads(result.stdout)
        names = {'vms': 'docs-screenshot-wordpress', 'templates': 'Service WordPress - KVM',
                 'images': 'Service WordPress - KVM'}
        if marker is None:
            if not isinstance(wordpress, dict):
                raise lab.ProvisionError('No theme or WordPress marker identifies an interrupted workflow; refusing recovery.')
            workflow_id = wordpress.get('workflow_id', '')
            if not isinstance(workflow_id, str) or not re.fullmatch('[0-9a-f]{32}', workflow_id):
                raise lab.ProvisionError('Unexpected WordPress workflow ID; refusing recovery.')
        if wordpress is not None and (
                not isinstance(wordpress, dict) or wordpress.get('workflow_id') != workflow_id
                or wordpress.get('names') != names or not isinstance(wordpress.get('previous_ids'), dict)
                or set(wordpress['previous_ids']) != set(names)
                or any(not valid_ids(ids) for ids in wordpress['previous_ids'].values())):
            raise lab.ProvisionError('WordPress marker does not identify the same workflow; refusing recovery.')
        if alpine is not None and alpine.get('workflow_id') != workflow_id:
            raise lab.ProvisionError('Alpine marker does not identify the same workflow; refusing recovery.')

    kind = 'wordpress' if include_wordpress else 'theme'
    archive = run_dir / f'workflow.failed-{kind}-{workflow_id}.json'
    if archive.exists():
        raise lab.ProvisionError(f'Recovery archive already exists: {archive}')

    current = user_template(lab.ssh(state, run_dir, USER_COMMAND))
    if marker is None:
        # Theme teardown already finished; preserve current settings without guessing a snapshot.
        original = current
    else:
        expected = ET.fromstring(marker['template'])
        fireedge = expected.find('FIREEDGE')
        if fireedge is None:
            fireedge = ET.SubElement(expected, 'FIREEDGE')
        scheme = fireedge.find('SCHEME')
        if scheme is None:
            scheme = ET.SubElement(fireedge, 'SCHEME')
        scheme.text = 'system'
        if template_shape(current) not in (template_shape(original), template_shape(expected)):
            raise lab.ProvisionError('User settings changed outside the theme hook; refusing to overwrite them.')

    cleanups = []
    if wordpress is not None:
        cleanups.append(('WordPress', GROUP / 'scripts/cleanup-wordpress.sh', 360))
    if alpine is not None:
        cleanups.append(('Alpine', GROUP.parent / 'single-node/scripts/cleanup-alpine.sh', 240))
    if marker is not None:
        cleanups.append(('Theme', GROUP / 'scripts/restore-theme.sh', 30))
    log_path.touch(mode=0o600)
    with log_path.open('a') as log:
        for label, script, timeout in cleanups:
            log.write(f'\nRetrying guarded {label} cleanup for the interrupted page.\n')
            log.flush()
            cleanup = lab.ssh(state, run_dir, f'export SUNSTONE_WORKFLOW_ID={workflow_id}\n' + script.read_text(),
                              timeout=timeout, log=log)
            if cleanup is None or cleanup.returncode:
                raise lab.ProvisionError(f'{label} recovery failed; inspect {log_path}')
    restored = user_template(lab.ssh(state, run_dir, 'set -e\n' + RESOURCE_GUARDS + f'test ! -e {MARKER}\n' + USER_COMMAND))
    if template_shape(restored) != template_shape(original):
        raise lab.ProvisionError('User settings differ after recovery; retaining the failed workflow.')
    if record_path == result_path:
        result_path.rename(archive)
    else:
        # Preserve the previous recovery's evidence when cleaning a later standalone capture.
        lab.save(archive, workflow_result)
    status = 'Theme settings restored' if marker is not None else 'Workflow resources cleaned; user settings left unchanged'
    print(f'{status}; prior failed workflow retained at {archive}')
    print('Retry the page capture or run-group --reuse; miniONE will not be reinstalled.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir', required=True)
    parser.add_argument('--include-alpine', action='store_true',
                        help='Recover an interrupted first-page capture, including guarded termination of its Alpine VM.')
    parser.add_argument('--include-wordpress', action='store_true',
                        help='Recover the failed validation page, including WordPress, Alpine and theme teardown.')
    parser.add_argument('--keep-sudo-alive', action='store_true',
                        help='Refresh existing sudo authorization until recovery exits; run sudo -v first.')
    parser.add_argument('--workflow-record',
                        help='Archived WordPress group record to use for a later standalone capture after workflow.json was archived.')
    args = parser.parse_args()
    try:
        with lab.sudo_session(args.keep_sudo_alive):
            recover(args.run_dir, include_alpine=args.include_alpine, include_wordpress=args.include_wordpress,
                    workflow_record=args.workflow_record)
    except (lab.ProvisionError, OSError, ValueError, KeyError, TypeError, ET.ParseError) as exc:
        print(f'error: {exc}', file=sys.stderr)
        sys.exit(1)
