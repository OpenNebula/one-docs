"""Shared single-VM groups and trusted guest commands."""

from contextlib import contextmanager
from contextvars import ContextVar
import json
from pathlib import Path

from . import provision as lab
from .manifest import ManifestError, load_manifest, validate_manifest


guest_runner = ContextVar('guest_runner', default=None)


def validate_commands(commands):
    if not isinstance(commands, list):
        raise ManifestError('Guest hooks must be lists.')
    for command in commands:
        if not isinstance(command, dict) or not isinstance(command.get('command'), str) or not command['command'].strip():
            raise ManifestError('Guest commands require a nonempty command string.')
        if type(command.get('timeout', 120)) is not int or command.get('timeout', 120) <= 0:
            raise ManifestError('Guest command timeout must be a positive integer.')


def load_group(path, repo_root):
    path = Path(path).resolve()
    group = json.loads(path.read_text())
    if not isinstance(group, dict) or group.get('version') != 1:
        raise ManifestError('Group must be a version 1 object.')
    config = group.get('provision')
    if not isinstance(config, str) or not (path.parent / config).is_file():
        raise ManifestError('Group provision must reference an existing configuration file.')
    manifests = group.get('manifests')
    if not isinstance(manifests, list) or not manifests:
        raise ManifestError('Group requires an ordered, nonempty manifests list.')
    resolved = []
    assets = set()
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
            for key in ('image', 'darkImage'):
                asset = screenshot.get(key)
                if asset:
                    if asset in assets:
                        raise ManifestError(f'Duplicate output asset across group: {asset}')
                    assets.add(asset)
        resolved.append(target)
    return (path.parent / config).resolve(), resolved


@contextmanager
def guest_session(run_dir):
    run_dir = Path(run_dir).resolve()
    state = lab.load(run_dir / 'state.json')
    if state.get('phase') != 'ready':
        raise lab.ProvisionError('Guest commands require a ready lab.')

    def execute(command):
        validate_commands([command])
        log_path = run_dir / 'guest-commands.log'
        log_path.touch(mode=0o600)
        with log_path.open('a') as log:
            result = lab.ssh(state, run_dir, 'set -e\n' + command['command'] + '\n',
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


def capture_with_hooks(manifest, capture):
    hooks = manifest.get('hooks', {})
    try:
        for command in hooks.get('setup', []):
            run_guest(command)
        capture()
    finally:
        failures = []
        for command in hooks.get('teardown', []):
            try:
                run_guest(command)
            except Exception as exc:
                failures.append(str(exc))
        if failures:
            raise lab.ProvisionError('Teardown failed: ' + '; '.join(failures))
