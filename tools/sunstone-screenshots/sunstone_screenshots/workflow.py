"""Shared single-VM groups and trusted guest commands."""

from contextlib import contextmanager
from contextvars import ContextVar
import json
from pathlib import Path
import uuid

from . import provision as lab
from .manifest import ManifestError, load_manifest, shared_source, validate_manifest


guest_runner = ContextVar('guest_runner', default=None)


def validate_commands(commands, base_dir=None):
    if not isinstance(commands, list):
        raise ManifestError('Guest hooks must be lists.')
    for command in commands:
        if not isinstance(command, dict) or len({'command', 'script'} & command.keys()) != 1:
            raise ManifestError('Guest hooks require exactly one of command or script.')
        value = command.get('command', command.get('script'))
        if not isinstance(value, str) or not value.strip():
            raise ManifestError('Guest command or script must be a nonempty string.')
        if 'script' in command and base_dir is not None and not (base_dir / value).is_file():
            raise ManifestError(f'Guest script does not exist: {value}')
        if type(command.get('timeout', 120)) is not int or command.get('timeout', 120) <= 0:
            raise ManifestError('Guest command timeout must be a positive integer.')


def load_group(path, repo_root):
    path = Path(path).resolve()
    group = json.loads(path.read_text())
    if not isinstance(group, dict) or group.get('version') != 1:
        raise ManifestError('Group must be a version 1 object.')
    if type(group.get('destroyOnSuccess', False)) is not bool:
        raise ManifestError('Group destroyOnSuccess must be a boolean.')
    config = group.get('provision')
    if not isinstance(config, str) or not (path.parent / config).is_file():
        raise ManifestError('Group provision must reference an existing configuration file.')
    manifests = group.get('manifests')
    if not isinstance(manifests, list) or not manifests:
        raise ManifestError('Group requires an ordered, nonempty manifests list.')
    resolved = []
    assets = {}
    for name in manifests:
        if not isinstance(name, str):
            raise ManifestError('Group manifest paths must be strings.')
        target = (path.parent / name).resolve()
        if target in resolved:
            raise ManifestError(f'Duplicate manifest: {target}')
        manifest = load_manifest(target)
        errors = validate_manifest(manifest, repo_root, target)
        if errors:
            raise ManifestError('\n'.join(errors))
        if not manifest.get('group') or (target.parent / manifest['group']).resolve() != path:
            raise ManifestError(f'{target}: group must link back to {path}')
        docs = {s['doc'] for s in manifest['screenshots']}
        if len(docs) != 1:
            raise ManifestError(f'{target}: grouped manifests must contain one documentation page.')
        for screenshot in manifest['screenshots']:
            source_identity = None
            if screenshot.get('sharedFrom'):
                source_path, source, _ = shared_source(screenshot, target)
                if source_path not in resolved:
                    raise ManifestError('sharedFrom producer must appear earlier in the same group.')
                source_identity = (source_path, source['id'])
            for key in ('image', 'darkImage'):
                asset = screenshot.get(key)
                if asset:
                    if source_identity:
                        if assets.get(asset) != source_identity:
                            raise ManifestError(f'sharedFrom does not match the producer of {asset}')
                    elif asset in assets:
                        raise ManifestError(f'Duplicate output asset across group: {asset}')
                    else:
                        assets[asset] = (target, screenshot['id'])
        resolved.append(target)
    return (path.parent / config).resolve(), resolved, group.get('destroyOnSuccess', False)


def load_suite(path, repo_root):
    path = Path(path).resolve()
    suite = json.loads(path.read_text())
    if not isinstance(suite, dict) or suite.get('version') != 1:
        raise ManifestError('Suite must be a version 1 object.')
    groups = suite.get('groups')
    if not isinstance(groups, list) or not groups:
        raise ManifestError('Suite requires an ordered, nonempty groups list.')
    resolved = []
    for name in groups:
        if not isinstance(name, str) or not name.strip():
            raise ManifestError('Suite group paths must be nonempty strings.')
        group = (path.parent / name).resolve()
        if group in resolved:
            raise ManifestError(f'Duplicate group in suite: {group}')
        _, _, destroy_on_success = load_group(group, repo_root)
        if not destroy_on_success:
            raise ManifestError(f'{group}: suite groups require destroyOnSuccess=true.')
        resolved.append(group)
    return resolved


@contextmanager
def guest_session(run_dir):
    run_dir = Path(run_dir).resolve()
    with lab.run_lock(run_dir):
        state = lab.load(run_dir / 'state.json')
        if state.get('phase') != 'ready':
            raise lab.ProvisionError('Guest commands require a ready lab.')
        workflow_id = uuid.uuid4().hex

        def execute(command):
            validate_commands([command])
            log_path = run_dir / 'guest-commands.log'
            log_path.touch(mode=0o600)
            with log_path.open('a') as log:
                result = lab.ssh(state, run_dir, f'set -e\nexport SUNSTONE_WORKFLOW_ID={workflow_id}\n' + command['command'] + '\n',
                                 timeout=command.get('timeout', 120), log=log)
            if result.returncode:
                raise lab.ProvisionError(f'Guest command failed; inspect {log_path}')

        token = guest_runner.set(execute)
        try:
            yield
        finally:
            guest_runner.reset(token)


def run_guest(command):
    execute = guest_runner.get()
    if execute is None:
        raise lab.ProvisionError('Guest commands require capture --run-dir or run-group.')
    execute(command)


def archive_workflow_markers(manifest):
    """Abandon known setup markers without adopting or deleting their resources."""
    markers_by_script = {
        'prepare-theme.sh': 'theme-workflow.json',
        'prepare-alpine.sh': 'alpine-workflow.json',
        'prepare-wordpress.sh': 'wordpress-workflow.json',
        'prepare-oneks.sh': 'oneks-workflow.json',
    }
    markers = sorted({markers_by_script[Path(hook['script']).name]
                      for hook in manifest.get('hooks', {}).get('setup', [])
                      if 'script' in hook and Path(hook['script']).name in markers_by_script})
    if not markers:
        raise lab.ProvisionError('--force-workflow found no supported marker-based setup hooks in this manifest.')
    command = '''import os
from pathlib import Path
root = Path('/root/screenshot-lab')
names = MARKER_NAMES
paths = [root / name for name in names]
for path in paths:
    if path.is_symlink() or (path.exists() and not path.is_file()):
        raise SystemExit('Refusing to archive non-regular marker: ' + str(path))
existing = [path for path in paths if path.exists()]
if existing:
    archive = root / ('abandoned-' + os.environ['SUNSTONE_WORKFLOW_ID'])
    archive.mkdir(mode=0o700)
    for path in existing:
        path.rename(archive / path.name)
        print('Archived stale marker: ' + str(archive / path.name), flush=True)
else:
    print('No selected workflow markers to archive.', flush=True)
'''.replace('MARKER_NAMES', repr(markers))
    run_guest({'command': "python3 - <<'SUNSTONE_ARCHIVE'\n" + command + 'SUNSTONE_ARCHIVE', 'timeout': 30})


def capture_with_hooks(manifest, capture, manifest_path=None):
    hooks = manifest.get('hooks', {})
    def execute(command, stage, index):
        label = command.get('script', 'inline command')
        if 'script' in command:
            if manifest_path is None:
                raise ManifestError('Script hooks require the manifest path.')
            command = dict(command)
            command['command'] = (Path(manifest_path).resolve().parent / command.pop('script')).read_text()
        try:
            run_guest(command)
        except lab.ProvisionError as exc:
            raise lab.ProvisionError(f'Guest {stage} hook {index} ({label}): {exc}') from exc

    primary_error = None
    try:
        for index, command in enumerate(hooks.get('setup', []), 1):
            execute(command, 'setup', index)
        capture()
    except BaseException as exc:
        primary_error = exc
        raise
    finally:
        failures = []
        for index, command in enumerate(hooks.get('teardown', []), 1):
            try:
                execute(command, 'teardown', index)
            except Exception as exc:
                failures.append(str(exc))
        if failures:
            detail = 'Teardown failed: ' + '; '.join(failures)
            if primary_error is not None:
                detail = f'Workflow failed: {primary_error}. ' + detail
            raise lab.ProvisionError(detail) from primary_error
