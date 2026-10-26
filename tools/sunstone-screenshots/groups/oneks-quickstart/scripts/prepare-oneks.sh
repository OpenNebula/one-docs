set -eu
if [ -e /root/screenshot-lab/oneks-workflow.json ]; then
    echo 'Previous OneKS workflow marker exists; inspect that workflow before retrying.' >&2
    exit 1
fi
install -d -m 700 /root/screenshot-lab
umask 077
cat > /root/screenshot-lab/oneks-workflow.py <<'PY'
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

MARKER = Path('/root/screenshot-lab/oneks-workflow.json')
PRIVATE = 'private-k8s'
CLUSTER = 'docs-screenshot-oneks'
WORKER = 'worker1'
DNS = '1.1.1.1'


def one(*args, input=None):
    result = subprocess.run(['su', '-', 'oneadmin', '-c', shlex.join(args)],
                            input=input, capture_output=True, text=True, timeout=60)
    if result.returncode:
        raise SystemExit('Guest CLI command failed: ' + shlex.join(args) + '\n' + result.stderr.strip())
    return result.stdout


def nets():
    return ET.fromstring(one('onevnet', 'list', '-x')).findall('VNET')


def clusters():
    data = json.loads(one('oneks', 'list', 'clusters', '--json'))
    if not isinstance(data, list) or any(not isinstance(item, dict) for item in data):
        raise SystemExit('Unexpected OneKS JSON pool; refusing to guess resource ownership.')
    return data


def body(document):
    value = document.get('TEMPLATE', {}).get('CLUSTER_BODY')
    if not isinstance(value, dict):
        raise SystemExit('Unexpected OneKS cluster body; inspect the installed build.')
    return value


def save(state):
    temporary = MARKER.with_suffix('.tmp')
    temporary.write_text(json.dumps(state, indent=2) + '\n')
    temporary.chmod(0o600)
    temporary.replace(MARKER)


def read_state():
    state = json.loads(MARKER.read_text())
    if state.get('version') != 1 or state.get('workflow_id') != os.environ['SUNSTONE_WORKFLOW_ID']:
        raise SystemExit('OneKS marker belongs to another invocation; leaving its resources untouched.')
    return state


def public_network(state):
    current = ET.fromstring(one('onevnet', 'show', state['public_id'], '-x'))
    if (current.findtext('ID') != state['public_id'] or current.findtext('NAME') != 'vnet'
            or current.findtext('UID') != '0' or current.find('TEMPLATE') is None):
        raise SystemExit('Public vnet identity changed; refusing cleanup.')
    if current.findtext('TEMPLATE/DNS') not in (state['original_dns'], DNS):
        raise SystemExit('Public vnet DNS changed outside this workflow; refusing to overwrite it.')
    return current


def private_network(state):
    records = nets()
    tracked = state.get('private_id')
    matches = [r for r in records if (r.findtext('ID') == tracked if tracked else
               r.findtext('NAME') == PRIVATE and r.findtext('ID') not in state['previous_networks'])]
    if len(matches) > 1:
        raise SystemExit('Multiple new private-k8s networks; refusing ambiguous cleanup.')
    if not matches:
        return None
    current = ET.fromstring(one('onevnet', 'show', str(int(matches[0].findtext('ID'))), '-x'))
    if (current.findtext('ID') in state['previous_networks'] or current.findtext('UID') != '0'
            or current.findtext('NAME') != PRIVATE):
        raise SystemExit('Private network identity changed; refusing cleanup.')
    return current


def cluster_document(state, private):
    tracked = state.get('cluster_id')
    matches = [r for r in clusters() if (str(r.get('ID')) == tracked if tracked else
               r.get('NAME') == CLUSTER and str(r.get('ID')) not in state['previous_clusters'])]
    if len(matches) > 1:
        raise SystemExit('Multiple new screenshot clusters; refusing ambiguous cleanup.')
    if not matches:
        return None
    identity = str(int(matches[0]['ID']))
    current = json.loads(one('oneks', 'show', 'cluster', identity, '--json'))
    if (str(current.get('ID')) != identity or identity in state['previous_clusters']
            or current.get('NAME') != CLUSTER or str(current.get('UID')) != '0'):
        raise SystemExit('OneKS cluster identity changed; refusing cleanup.')
    deployment = body(current).get('deployment', {})
    networks = deployment.get('networks', {})
    private_id = private.findtext('ID') if private is not None else state.get('private_id')
    if (str(networks.get('public', {}).get('id')) != state['public_id'] or private_id is None
            or str(networks.get('private', {}).get('id')) != private_id
            or str(deployment.get('cluster', {}).get('id')) != '0'):
        raise SystemExit('OneKS deployment no longer matches the workflow networks/cluster; refusing cleanup.')
    return current


def ensure_oneks_ready():
    deadline = time.monotonic() + 300
    next_restart = 0
    restarts = 0
    service_error = ''
    while True:
        try:
            return clusters()
        except SystemExit as exc:
            # A running unit can still have no API after the miniONE startup race.
            if 'connection refused' not in str(exc).lower() and 'econnrefused' not in str(exc).lower():
                raise
            api_error = str(exc)
        now = time.monotonic()
        if now >= deadline:
            raise SystemExit('OneKS API did not become ready within 300 seconds after '
                             + str(restarts) + ' restart attempts. Inspect journalctl -u opennebula-ks '
                             'and /var/log/one/oneks.log.\n' + api_error
                             + ('\nLast restart diagnostic: ' + service_error if service_error else ''))
        if restarts < 3 and now >= next_restart:
            restarts += 1
            print(f'OneKS API unavailable; restarting opennebula-ks ({restarts}/3)...', flush=True)
            try:
                result = subprocess.run(['systemctl', 'restart', 'opennebula-ks'],
                                        capture_output=True, text=True, timeout=min(30, deadline - now))
                service_error = (result.stderr.strip() or result.stdout.strip()) if result.returncode else ''
            except subprocess.TimeoutExpired:
                service_error = 'systemctl restart timed out; waiting for the service/API to settle.'
            next_restart = time.monotonic() + 60
        time.sleep(min(3, max(0, deadline - time.monotonic())))


def prepare():
    if MARKER.exists():
        raise SystemExit('Previous OneKS marker exists; inspect it before retrying.')
    memory = next(int(line.split()[1]) for line in Path('/proc/meminfo').read_text().splitlines()
                  if line.startswith('MemTotal:'))
    cpus = os.cpu_count() or 0
    if memory < 12 * 1024 * 1024 or cpus < 4:
        raise SystemExit('OneKS lab needs at least 12 GiB RAM and 4 vCPUs; '
                         f'guest reports {memory // 1024} MiB RAM and {cpus} vCPUs. '
                         'Use vm_resources overrides or a larger outer VM template.')
    if not os.access('/dev/kvm', os.R_OK | os.W_OK):
        raise SystemExit('OneKS needs working nested KVM inside the lab VM.')
    if shutil.disk_usage('/var/lib/one/datastores').free < 30 * 1024**3:
        raise SystemExit('OneKS lab needs at least 30 GiB free datastore space; use a larger outer VM disk.')
    subprocess.run(['systemctl', 'is-active', '--quiet', 'opennebula-gate'], check=True)
    previous_clusters = ensure_oneks_ready()
    networks = nets()
    public = [r for r in networks if r.findtext('NAME') == 'vnet' and r.findtext('UID') == '0']
    if (len(public) != 1 or any(r.findtext('NAME') == PRIVATE for r in networks)
            or any(r.get('NAME') == CLUSTER for r in previous_clusters)):
        raise SystemExit('Expected one public vnet and no existing workflow network/cluster; refusing to reuse resources.')
    public_id = str(int(public[0].findtext('ID')))
    current = ET.fromstring(one('onevnet', 'show', public_id, '-x'))
    if current.find('TEMPLATE') is None:
        raise SystemExit('Public vnet template is missing.')
    save(dict(version=1, workflow_id=os.environ['SUNSTONE_WORKFLOW_ID'], public_id=public_id,
              original_dns=current.findtext('TEMPLATE/DNS'),
              previous_networks=[r.findtext('ID') for r in networks],
              previous_clusters=[str(r['ID']) for r in previous_clusters], private_id=None, cluster_id=None))
    print('OneKS baseline recorded; the browser will create private-k8s and the screenshot cluster.')


def checkpoint(stage):
    state = read_state()
    public = public_network(state)
    private = private_network(state)
    if stage == 'private':
        if private is None:
            raise SystemExit('Browser did not create private-k8s.')
        if '0' not in [r.text for r in private.findall('CLUSTERS/ID')]:
            raise SystemExit('private-k8s is not assigned to OpenNebula cluster 0.')
        state['private_id'] = private.findtext('ID')
    elif stage == 'dns':
        if public.findtext('TEMPLATE/DNS') != DNS:
            raise SystemExit('Browser did not apply the requested public vnet DNS.')
    elif stage == 'cluster':
        cluster = cluster_document(state, private)
        if cluster is None:
            raise SystemExit('Browser did not create the OneKS cluster.')
        state['cluster_id'] = str(cluster['ID'])
    else:
        raise SystemExit('Unknown OneKS checkpoint.')
    save(state)
    print('OneKS checkpoint verified: ' + stage)


def wait_for(stage, timeout):
    if stage not in ('cluster', 'worker'):
        raise SystemExit('Unknown OneKS wait stage.')
    state = read_state()
    deadline = time.monotonic() + timeout
    while True:
        cluster = cluster_document(state, private_network(state))
        if cluster is None:
            raise SystemExit('Workflow cluster disappeared while waiting.')
        data = body(cluster)
        status = data.get('state')
        if status == 'ERROR' or str(status).endswith('_FAILURE'):
            raise SystemExit('OneKS cluster failed (' + str(status) + '); inspect its lifecycle logs.')
        if stage == 'cluster' and status == 'RUNNING':
            print('OneKS cluster is RUNNING.')
            return
        if stage == 'worker':
            workers = [g for g in data.get('node_groups', []) if g and g.get('name') == WORKER]
            if len(workers) > 1:
                raise SystemExit('Ambiguous worker1 node groups.')
            if workers:
                worker = workers[0]
                if worker.get('state') == 'ERROR' or str(worker.get('state')).endswith('_FAILURE'):
                    raise SystemExit('OneKS worker1 provisioning failed; inspect its lifecycle logs.')
                if worker.get('state') == 'RUNNING' and len(worker.get('vms', [])) == 1:
                    print('OneKS worker1 is RUNNING with one VM.')
                    return
        if time.monotonic() >= deadline:
            raise SystemExit('Timed out waiting for OneKS ' + stage + '; inspect the retained lab.')
        time.sleep(5)


def cleanup():
    if not MARKER.exists():
        print('No OneKS marker; nothing to clean up.')
        return
    state = read_state()
    # Verify the complete ownership chain before requesting any deletion.
    public_network(state)
    private = private_network(state)
    cluster = cluster_document(state, private)
    if private is not None:
        state['private_id'] = private.findtext('ID')
    if cluster is not None:
        state['cluster_id'] = str(cluster['ID'])
    save(state)
    if cluster is not None:
        if body(cluster).get('state') != 'DEPROVISIONING':
            one('oneks', 'delete', 'cluster', state['cluster_id'])
        deadline = time.monotonic() + 900
        while True:
            current = cluster_document(state, private)
            if current is None:
                break
            if body(current).get('state') == 'DEPROVISIONING_FAILURE':
                raise SystemExit('OneKS deprovisioning failed; marker retained. No forced deletion was attempted.')
            if time.monotonic() >= deadline:
                raise SystemExit('Timed out waiting for OneKS deletion; marker and networks retained.')
            time.sleep(5)
    private = private_network(state)
    if private is not None:
        identity = private.findtext('ID')
        vms = ET.fromstring(one('onevm', 'list', '-x')).findall('VM')
        if (int(private.findtext('USED_LEASES', '0')) != 0
                or any(vm.findtext('STATE') != '6' and any(n.findtext('NETWORK_ID') == identity
                       for n in vm.findall('TEMPLATE/NIC')) for vm in vms)):
            raise SystemExit('Private network still has leases or attached VMs; refusing to delete it.')
        one('onevnet', 'delete', identity)
        if private_network(state) is not None:
            raise SystemExit('Private network deletion did not complete; marker retained.')
    public = public_network(state)
    template = public.find('TEMPLATE')
    for entry in template.findall('DNS'):
        template.remove(entry)
    if state['original_dns'] is not None:
        ET.SubElement(template, 'DNS').text = state['original_dns']
    one('onevnet', 'update', state['public_id'], input=ET.tostring(template, encoding='unicode'))
    if public_network(state).findtext('TEMPLATE/DNS') != state['original_dns']:
        raise SystemExit('Could not verify original DNS restoration; marker retained.')
    MARKER.unlink()
    print('OneKS cluster removed, private network deleted and original public DNS restored.')


if __name__ == '__main__':
    stage = sys.argv[1]
    if stage == 'prepare':
        prepare()
    elif stage == 'cleanup':
        cleanup()
    elif stage.startswith('wait-'):
        wait_for(stage[5:], 1800 if stage == 'wait-cluster' else 1200)
    else:
        checkpoint(stage)
PY
python3 /root/screenshot-lab/oneks-workflow.py prepare
