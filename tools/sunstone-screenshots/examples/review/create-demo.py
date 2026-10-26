"""Create a disposable review example using copies of actual Sunstone captures."""

import argparse
import csv
import json
from pathlib import Path
import shutil
import shlex
import uuid


ROOT = Path(__file__).resolve().parents[4]


def create(output):
    output = Path(output).resolve()
    if output.exists():
        raise ValueError('Choose a new output directory; existing review data is never overwritten.')
    repo, run = output / 'repo', output / 'run'
    (repo / 'content').mkdir(parents=True)
    (repo / 'assets/images').mkdir(parents=True)
    (run / 'screenshots/assets/images').mkdir(parents=True)
    # Same-resolution wizard steps give a real, inspectable content change.
    frames = ROOT / '.sunstone-screenshots/labs/getting-started-20261022-120141/screenshots/assets/images/quickstart/light'
    assets = ROOT / 'assets/images/quickstart/light'
    wizard_before = frames / 'sunstone_instantiate_vm_1.png'
    wizard_after = frames / 'sunstone_instantiate_vm_2.png'
    if not wizard_before.is_file() or not wizard_after.is_file():
        wizard_before, wizard_after = assets / 'sunstone_instantiate_vm_1.png', assets / 'sunstone_instantiate_vm_2.png'
    cases = [
        ('login', assets / 'sunstone_login_page.png', assets / 'sunstone_login_page.png'),
        ('wizard', wizard_before, wizard_after),
        ('dimensions', assets / 'sunstone_dashboard.png', assets / 'sunstone_vm_templates_alpine.png'),
        ('missing-replacement', assets / 'sunstone_network_details.png', None),
        ('missing-baseline', None, assets / 'sunstone_vm_instances.png'),
        ('not-run', assets / 'sunstone_vm_templates.png', None),
    ]
    for name, baseline, candidate in cases:
        if baseline:
            shutil.copyfile(baseline, repo / f'assets/images/{name}.png')
        if candidate:
            shutil.copyfile(candidate, run / f'screenshots/assets/images/{name}.png')
    pages = [('minione', 'Deploy OpenNebula with miniONE', ['login', 'wizard', 'dimensions'], 'complete'),
             ('validation', 'Validate the OpenNebula environment', ['missing-replacement', 'missing-baseline'], 'failed'),
             ('templates', 'VM template configuration', ['not-run'], 'not_run')]

    def write(path, data):
        path.write_text(json.dumps(data, indent=2) + '\n')

    for name, title, images, _ in pages:
        (repo / f'content/{name}.md').write_text(f'# {title}\n\n' + '\n\n'.join(f'![Sunstone {image}](/images/{image}.png)' for image in images))
        write(repo / f'{name}.json', dict(version=1, group='group.json', screenshots=[
            dict(id=f'{name}.{image}', title=image.replace('-', ' ').title(), doc=f'content/{name}.md',
                 image=f'assets/images/{image}.png', recipe='recipe.json', capture=image) for image in images]))
    write(repo / 'recipe.json', dict(captures=[dict(id=name, steps=[]) for name, _, _ in cases]))
    write(repo / 'group.json', dict(version=1, provision='provision.json', manifests=[f'{name}.json' for name, _, _, _ in pages]))
    write(repo / 'provision.json', dict(example_only=True))
    write(run / 'workflow.json', dict(group='group.json', pages=[dict(manifest=f'{name}.json', status=status,
        **({'error': "Timed out waiting for a VM to reach RUNNING."} if status == 'failed' else {}))
        for name, _, _, status in pages if status != 'not_run']))
    with (repo / 'inventory.csv').open('w', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(['id', 'title', 'doc', 'group', 'manifest', 'automation_status', 'section'])
        for name, title, _, _ in pages:
            writer.writerow([name, title, f'content/{name}.md', 'group.json', f'{name}.json', 'draft', 'Getting Started'])
    print(f'Review fixture created at {output}')
    print(shlex.join(['tools/sunstone-screenshots/bin/sunstone-screenshots', '--repo-root', str(repo),
                      'review', '--inventory', str(repo / 'inventory.csv'), '--run-dir', str(run)]))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', default=f'.sunstone-screenshots/review-demo-{uuid.uuid4().hex[:8]}')
    args = parser.parse_args()
    create(args.output)
