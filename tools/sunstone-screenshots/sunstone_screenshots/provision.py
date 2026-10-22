"""Single-VM lab provisioning. Outer-cloud credentials never enter the guest."""

import hashlib
import ipaddress
import json
from contextlib import contextmanager
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import threading
import time
import uuid
from urllib.request import urlopen
from urllib.parse import urlparse


class ProvisionError(RuntimeError):
    pass


_SUDO_REFRESH_INTERVAL = 60


@contextmanager
def sudo_session(enabled=False):
    if not enabled:
        yield
        return

    def refresh():
        try:
            result = subprocess.run(['sudo', '-n', '-v'], capture_output=True, text=True, timeout=10)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise ProvisionError(f'Could not refresh sudo authorization: {exc}') from exc
        if result.returncode:
            raise ProvisionError('Cannot refresh cached sudo authorization. Run sudo -v in this terminal first. '
                                 + result.stderr.strip())

    refresh()
    stopped = threading.Event()

    def keep_alive():
        while not stopped.wait(_SUDO_REFRESH_INTERVAL):
            try:
                refresh()
            except ProvisionError as exc:
                print(f'warning: {exc} Subsequent guest commands and cleanup may fail.', file=sys.stderr, flush=True)
                return

    worker = threading.Thread(target=keep_alive, name='sunstone-sudo-keepalive', daemon=True)
    print('Keeping cached sudo authorization active until this command exits.', flush=True)
    worker.start()
    try:
        yield
    finally:
        stopped.set()
        worker.join()


def save(path, state):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(state, indent=2) + '\n')
    temporary.chmod(0o600)
    temporary.replace(path)


def load(path):
    return json.loads(Path(path).read_text())


@contextmanager
def run_lock(run_dir):
    import fcntl

    path = Path(run_dir).resolve() / '.capture.lock'
    path.touch(mode=0o600)
    with path.open('r+') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ProvisionError(f'Another capture or recovery is using {path.parent}. '
                                 'Finish any paused run before retrying.') from exc
        try:
            yield
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def configuration(path):
    path = Path(path).resolve()
    cfg = load(path)
    if not isinstance(cfg, dict):
        raise ProvisionError('Provisioning configuration must be a JSON object.')
    if type(cfg.get('minione_force', False)) is not bool:
        raise ProvisionError('minione_force must be a boolean.')
    if type(cfg.get('disable_automatic_updates', False)) is not bool:
        raise ProvisionError('disable_automatic_updates must be a boolean.')
    password = cfg.get('minione_password')
    if password is not None and (not isinstance(password, str) or not password
                                 or any(c in password for c in '\x00\r\n')):
        raise ProvisionError('minione_password must be a nonempty single-line string or null.')
    endpoint = urlparse(cfg.get('endpoint', ''))
    if endpoint.scheme not in ('http', 'https') or not endpoint.hostname or endpoint.username:
        raise ProvisionError('Set endpoint to an HTTP(S) XML-RPC URL without embedded credentials.')
    if not shutil.which('ssh'):
        raise ProvisionError('OpenSSH client (ssh) is required on the runner.')
    if type(cfg.get('template_id')) is not int or cfg['template_id'] < 0:
        raise ProvisionError('Set template_id to a local OpenNebula OS template ID.')
    if not re.fullmatch(r'[a-z_][a-z0-9_-]*', cfg.get('ssh_user', '')):
        raise ProvisionError('Set a valid ssh_user.')
    local_user = cfg.get('ssh_local_user')
    if local_user is not None:
        if not isinstance(local_user, str) or not re.fullmatch(r'[a-z_][a-z0-9_-]*', local_user):
            raise ProvisionError('Set a valid ssh_local_user.')
        if not shutil.which('sudo'):
            raise ProvisionError('sudo is required for ssh_local_user.')
        for key in ('ssh_key', 'ssh_known_hosts'):
            if not isinstance(cfg.get(key), str) or not Path(cfg[key]).is_absolute():
                raise ProvisionError(f'{key} must be an absolute path when ssh_local_user is set.')
        result = subprocess.run(['sudo', '-n', '-H', '-u', local_user, '--',
                                 'test', '-r', cfg['ssh_key']],
                                capture_output=True, text=True, timeout=30)
        if result.returncode:
            raise ProvisionError(f'Cannot read ssh_key as {local_user} using sudo -n. '
                                 'Check the key path and sudo authorization. ' + result.stderr.strip())
    source = cfg.get('minione_script')
    if not isinstance(source, str) or not source.strip():
        raise ProvisionError('Set minione_script to a local path or HTTP(S) URL.')
    source_url = urlparse(source)
    remote_script = source_url.scheme in ('http', 'https')
    if source_url.scheme and (not remote_script or not source_url.hostname or source_url.username):
        raise ProvisionError('minione_script URL must use HTTP(S) without embedded credentials.')
    file_keys = ('auth_file', 'ssh_key') if remote_script else ('auth_file', 'ssh_key', 'minione_script')
    for key in file_keys:
        if key == 'ssh_key' and local_user is not None:
            continue
        value = Path(cfg[key]).expanduser()
        candidate = value if value.is_absolute() else path.parent / value
        try:
            candidate = candidate.resolve()
            cfg[key] = str(candidate)
            if not candidate.is_file():
                raise ProvisionError(f'{key} does not exist: {candidate}')
            with candidate.open('rb'):
                pass
        except PermissionError as exc:
            hint = (' Use a private key readable by the user running this command; '
                    'its public key must be authorized for ssh_user in the VM template.'
                    if key == 'ssh_key' else ' Use a file readable by the user running this command.')
            raise ProvisionError(f'{key} is not readable: {candidate}.{hint}') from exc
    for key, default in (('boot_timeout', 600), ('install_timeout', 1800), ('sunstone_port', 80)):
        cfg[key] = int(cfg.get(key, default))
        if cfg[key] <= 0:
            raise ProvisionError(f'{key} must be positive')
    if cfg['sunstone_port'] > 65535:
        raise ProvisionError('Invalid sunstone_port')
    if not cfg.get('opennebula_version'):
        raise ProvisionError('Set opennebula_version.')
    if type(cfg.get('management_nic_id', 0)) is not int or cfg.get('management_nic_id', 0) < 0:
        raise ProvisionError('management_nic_id must be a nonnegative integer.')
    if not remote_script:
        cfg['installer_sha256'] = hashlib.sha256(Path(cfg['minione_script']).read_bytes()).hexdigest()
    return cfg


def prepare_installer(cfg, run_dir):
    source = cfg['minione_script']
    if urlparse(source).scheme not in ('http', 'https'):
        return
    print('Downloading miniONE installer...', flush=True)
    try:
        with urlopen(source, timeout=60) as response:
            script = response.read(10 * 1024 * 1024 + 1)
    except OSError as exc:
        raise ProvisionError(f'Could not download miniONE: {exc}') from exc
    if not script or len(script) > 10 * 1024 * 1024:
        raise ProvisionError('miniONE download is empty or exceeds 10 MiB.')
    destination = run_dir / 'minione'
    destination.write_bytes(script)
    destination.chmod(0o600)
    cfg['installer_url'] = source
    cfg['minione_script'] = str(destination)
    cfg['installer_sha256'] = hashlib.sha256(script).hexdigest()


def connect(cfg):
    try:
        import pyone
    except ImportError as exc:
        raise ProvisionError('Install requirements-provision.txt to use provisioning.') from exc
    return pyone.OneServer(cfg['endpoint'], session=Path(cfg['auth_file']).read_text().strip(), timeout=30)


def wait_for(check, timeout, description, diagnostic=None):
    deadline = time.monotonic() + timeout
    while True:
        result = check()
        if result:
            return result
        if time.monotonic() >= deadline:
            detail = f': {diagnostic()}' if diagnostic else ''
            raise ProvisionError(f'Timed out waiting for {description}{detail}')
        time.sleep(3)


def owned_vm(one, state):
    vm = one.vm.info(state['vm_id'])
    if vm.NAME != state['vm_name']:
        raise ProvisionError('VM name no longer matches the recorded run; refusing operation.')
    return vm


def running_address(one, state):
    vm = owned_vm(one, state)
    if int(vm.STATE) == 6:
        raise ProvisionError('Lab VM has terminated.')
    if int(vm.STATE) != 3 or int(vm.LCM_STATE) != 3:
        return None
    nics = dict(vm.TEMPLATE).get('NIC', [])
    if isinstance(nics, dict):
        nics = [nics]
    for nic in nics:
        if int(nic.get('NIC_ID', -1)) == int(state['config'].get('management_nic_id', 0)) and nic.get('IP'):
            return str(ipaddress.ip_address(nic['IP']))
    return None


def ssh(state, run_dir, script, timeout=30, log=None):
    cfg = state['config']
    address = str(ipaddress.ip_address(state['address']))
    local_user = cfg.get('ssh_local_user')
    known_hosts = cfg['ssh_known_hosts'] if local_user else run_dir / 'known_hosts'
    command = ['ssh', '-T', '-i', cfg['ssh_key'], '-o', 'BatchMode=yes',
               '-o', 'IdentitiesOnly=yes', '-o', 'ConnectTimeout=10',
               '-o', 'StrictHostKeyChecking=accept-new',
               '-o', f'UserKnownHostsFile={known_hosts}',
               f'{cfg["ssh_user"]}@{address}',
               'bash -se' if cfg['ssh_user'] == 'root' else 'sudo -n bash -se']
    if state.get('host_key_alias'):
        command[1:1] = ['-o', f'HostKeyAlias={state["host_key_alias"]}',
                        '-o', 'CheckHostIP=no']
    if local_user:
        command = ['sudo', '-n', '-H', '-u', local_user, '--'] + command
    try:
        return subprocess.run(command, input=script, text=True, timeout=timeout,
                              stdout=log or subprocess.PIPE, stderr=log or subprocess.PIPE)
    except subprocess.TimeoutExpired:
        if log:
            raise ProvisionError('Remote command timed out; guest processes may still be running.')
        return None


def guest_ready(state, run_dir):
    result = ssh(state, run_dir, 'true\n')
    if result is not None and result.returncode == 0:
        state.pop('ssh_error', None)
        return True
    state['ssh_error'] = (result.stderr.strip()[-2000:] if result is not None
                          else 'SSH command timed out') or 'SSH command failed without stderr'
    return False


def install(state, run_dir):
    cfg = state['config']
    script = Path(cfg['minione_script']).read_bytes()
    if hashlib.sha256(script).hexdigest() != cfg['installer_sha256']:
        raise ProvisionError('miniONE script changed since this run was created.')
    # Stage via stdin: no dependency on SCP/SFTP configuration in the guest.
    import base64
    encoded = base64.b64encode(script).decode('ascii')
    args = ['--yes', '--version', str(cfg['opennebula_version']),
            '--sunstone-port', str(cfg['sunstone_port'])]
    if cfg.get('repo_base'):
        args += ['--repo-base', cfg['repo_base']]
    if cfg.get('minione_force', False):
        args.append('--force')
    if cfg.get('minione_password') is not None:
        args += ['--password', cfg['minione_password']]
    update_guard = ''
    if cfg.get('disable_automatic_updates', False):
        update_guard = (Path(__file__).parent / 'guest/pause-apt-updates.sh').read_text() + '\n'
    remote = (
        'test -c /dev/kvm || { echo "Nested KVM unavailable"; exit 1; }\n'
        'if command -v cloud-init >/dev/null; then cloud-init status --wait; fi\n'
    ) + update_guard + (
        'install -d -m 700 /root/screenshot-lab\n'
        f'printf %s {shlex.quote(encoded)} | base64 -d > /root/screenshot-lab/minione\n'
        f'bash /root/screenshot-lab/minione {shlex.join(args)}\n'
        'if command -v dpkg-query >/dev/null; then dpkg-query -W "opennebula*"; '
        'else rpm -qa "opennebula*"; fi\n'
    )
    log_path = run_dir / 'install.log'
    log_path.touch(mode=0o600)
    with log_path.open('a') as log:
        result = ssh(state, run_dir, remote, timeout=cfg['install_timeout'], log=log)
    if result.returncode:
        raise ProvisionError(f'miniONE installation failed; inspect {log_path}')


def services_ready(state, run_dir):
    result = ssh(state, run_dir,
                 "su - oneadmin -c 'oneuser show 0 >/dev/null && onehost list -x'\n")
    if result is None:
        state['services_error'] = 'SSH timed out while checking the inner API and host pool.'
        return False
    if result.returncode:
        detail = result.stderr.strip()[-2000:] or 'No stderr returned.'
        state['services_error'] = f'Inner readiness command failed (exit {result.returncode}): {detail}'
        return False
    import xml.etree.ElementTree as ET
    try:
        hosts = ET.fromstring(result.stdout)
    except ET.ParseError as exc:
        state['services_error'] = f'Inner API command returned invalid host XML: {exc}'
        return False
    if hosts.tag != 'HOST_POOL':
        state['services_error'] = f'Expected HOST_POOL XML, received {hosts.tag}.'
        return False
    entries = hosts.findall('HOST')
    if any(h.findtext('STATE') == '2' and h.findtext('VM_MAD') == 'kvm' for h in entries):
        state.pop('services_error', None)
        return True
    descriptions = []
    for host in entries:
        description = (f'#{host.findtext("ID", "?")} {host.findtext("NAME", "?")} '
                       f'(STATE={host.findtext("STATE", "?")}, VM_MAD={host.findtext("VM_MAD", "?")})')
        error = host.findtext('TEMPLATE/ERROR')
        if error:
            description += ': ' + error[-600:]
        descriptions.append(description)
    state['services_error'] = ('Inner API responds, but no KVM host is MONITORED (STATE=2). '
                               + ('Hosts: ' + '; '.join(descriptions) if entries else 'No hosts registered.'))
    return False


def http_ready(url):
    try:
        with urlopen(url, timeout=10) as response:
            return response.status == 200
    except OSError:
        return False


def check_services(state, run_dir):
    cfg = state['config']
    state_path = run_dir / 'state.json'
    state['phase'] = 'checking-services'
    save(state_path, state)
    wait_for(lambda: services_ready(state, run_dir), cfg['boot_timeout'], 'inner API and monitored KVM host',
             diagnostic=lambda: state.get('services_error', 'No inner readiness diagnostic available.'))
    host = state['address']
    if ':' in host:
        host = f'[{host}]'
    state['sunstone_url'] = f'http://{host}:{cfg["sunstone_port"]}'
    wait_for(lambda: http_ready(state['sunstone_url']), cfg['boot_timeout'], 'Sunstone from this runner')
    state['phase'] = 'ready'
    state.pop('failed_phase', None)
    state.pop('services_error', None)
    save(state_path, state)
    print(f'Ready: {state["sunstone_url"]} (state: {state_path})')


def validate_readiness_resume(state):
    phase = state.get('phase')
    if not (phase in ('checking-services', 'ready') or
            (phase == 'failed' and state.get('failed_phase') == 'checking-services')):
        raise ProvisionError('Resume only supports completed installations stopped at readiness checks.')
    if state.get('vm_id') is None or not state.get('address'):
        raise ProvisionError('Readiness resume requires a recorded VM ID and management address.')


def resume_readiness(run_dir):
    run_dir = Path(run_dir).resolve()
    state_path = run_dir / 'state.json'
    state = load(state_path)
    validate_readiness_resume(state)
    address = running_address(connect(state['config']), state)
    if address != state['address']:
        raise ProvisionError('Recorded VM is not running at its saved address; refusing readiness resume.')
    print(f'Rechecking installed lab VM {state["vm_id"]}; miniONE will not be reinstalled.', flush=True)
    try:
        check_services(state, run_dir)
    except BaseException:
        state['failed_phase'] = state['phase']
        state['phase'] = 'failed'
        save(state_path, state)
        raise


def provision(config_path, run_dir):
    cfg = configuration(config_path)
    one = connect(cfg)
    run_dir = Path(run_dir).resolve()
    run_dir.mkdir(parents=True, exist_ok=False, mode=0o700)
    state_path = run_dir / 'state.json'
    state = {'version': 1, 'config': cfg, 'vm_name': 'docs-lab-' + uuid.uuid4().hex,
             'phase': 'preparing-installer', 'vm_id': None}
    state['host_key_alias'] = state['vm_name']
    save(state_path, state)
    try:
        prepare_installer(cfg, run_dir)
        state['phase'] = 'allocating'
        save(state_path, state)
        print('Instantiating lab VM...', flush=True)
        state['vm_id'] = int(one.template.instantiate(cfg['template_id'], state['vm_name']))
        state['phase'] = 'booting'
        save(state_path, state)
        state['address'] = wait_for(lambda: running_address(one, state), cfg['boot_timeout'], 'VM and management IP')
        save(state_path, state)
        wait_for(lambda: guest_ready(state, run_dir), cfg['boot_timeout'], 'SSH and sudo',
                 diagnostic=lambda: state.get('ssh_error', 'No SSH diagnostic available'))
        state['phase'] = 'installing'
        save(state_path, state)
        print('Installing miniONE; output is in install.log...', flush=True)
        install(state, run_dir)
        check_services(state, run_dir)
    except BaseException:
        state['failed_phase'] = state['phase']
        state['phase'] = 'failed'
        save(state_path, state)
        print(f'Run retained for inspection/cleanup: {state_path}', flush=True)
        raise


def status(run_dir):
    state = load(Path(run_dir) / 'state.json')
    result = {'phase': state['phase'], 'vm_id': state['vm_id'], 'vm_name': state['vm_name']}
    if state['vm_id'] is not None:
        vm = owned_vm(connect(state['config']), state)
        result.update(vm_state=int(vm.STATE), lcm_state=int(vm.LCM_STATE))
    print(json.dumps(result, indent=2))


def destroy(run_dir):
    path = Path(run_dir) / 'state.json'
    state = load(path)
    if state['phase'] == 'destroyed':
        print('Already destroyed.')
        return
    if state['vm_id'] is None:
        raise ProvisionError('No recorded VM ID. Check outer cloud for the recorded vm_name before cleanup.')
    one = connect(state['config'])
    vm = owned_vm(one, state)
    if int(vm.STATE) != 6:
        one.vm.action('terminate-hard', state['vm_id'])
        state['phase'] = 'terminating'
        save(path, state)
        wait_for(lambda: int(owned_vm(one, state).STATE) == 6, 300, 'VM termination')
    state['phase'] = 'destroyed'
    save(path, state)
    print('Lab VM destroyed; local logs and screenshots retained.')


def capture_environment(run_dir):
    run_dir = Path(run_dir).resolve()
    state = load(run_dir / 'state.json')
    if state['phase'] != 'ready':
        raise ProvisionError('Provisioned run is not ready.')
    vm = owned_vm(connect(state['config']), state)
    if int(vm.STATE) != 3 or int(vm.LCM_STATE) != 3:
        raise ProvisionError('Lab VM is not running.')
    result = ssh(state, run_dir, 'cat /var/lib/one/.one/one_auth\n')
    if result is None or result.returncode or ':' not in result.stdout:
        raise ProvisionError('Could not retrieve inner OpenNebula credentials over SSH.')
    username, password = result.stdout.strip().split(':', 1)
    return {'SUNSTONE_URL': state['sunstone_url'], 'SUNSTONE_USER': username, 'SUNSTONE_PASSWORD': password}
