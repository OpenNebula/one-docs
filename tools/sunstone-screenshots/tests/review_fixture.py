"""Small raster fixtures for review model and real-browser integration tests."""

import json
from pathlib import Path


def create_review_fixture(root):
    from PIL import Image, ImageDraw

    root = Path(root)
    run = root / 'run'
    (root / 'content').mkdir(parents=True)
    (root / 'assets/images').mkdir(parents=True)
    (run / 'screenshots/assets/images').mkdir(parents=True)
    for name in ('same', 'changed', 'resized', 'missing-new', 'missing-old', 'not-run'):
        old = Image.new('RGB', (96, 64), '#f1f4f3')
        draw = ImageDraw.Draw(old)
        draw.rectangle((0, 0, 95, 12), fill='#177d84')
        draw.rectangle((6, 20, 30, 57), fill='#d7e7e1')
        draw.rectangle((38, 23, 87, 28), fill='#687c77')
        draw.rectangle((38, 36, 72, 40), fill='#a7bab0')
        if name != 'missing-old':
            old.save(root / f'assets/images/{name}.png')
        if name in ('missing-new', 'not-run'):
            continue
        if name == 'resized':
            old = Image.new('RGB', (80, 60), '#e1ece5')
        elif name == 'changed':
            ImageDraw.Draw(old).rectangle((40, 23, 82, 40), fill='#c4544f')
        old.save(run / f'screenshots/assets/images/{name}.png')

    def write(name, value):
        (root / name).write_text(json.dumps(value))

    docs = [('first', ['same', 'changed', 'resized']), ('second', ['missing-new', 'missing-old']), ('third', ['not-run'])]
    for doc, images in docs:
        (root / f'content/{doc}.md').write_text('# Sunstone\n\n' + '\n\n'.join(f'![Sunstone {name}](/images/{name}.png)' for name in images))
        write(f'{doc}.json', dict(version=1, group='group.json', screenshots=[
            dict(id=f'{doc}.{name}', title=f'Sunstone {name}', doc=f'content/{doc}.md', image=f'assets/images/{name}.png',
                 recipe='recipe.json', capture=name) for name in images]))
    write('recipe.json', dict(captures=[dict(id=name, steps=[]) for _, images in docs for name in images]))
    write('group.json', dict(version=1, provision='provision.json', manifests=[f'{d}.json' for d, _ in docs]))
    write('provision.json', {'offline': True})
    (root / 'inventory.csv').write_text('id,title,doc,group,manifest,automation_status,section\n'
        + '\n'.join(f'{name},Sunstone {name},content/{name}.md,group.json,{name}.json,draft,Getting Started' for name, _ in docs) + '\n')
    write('run/workflow.json', dict(group='group.json', lab_status='retained', pages=[
        dict(manifest='first.json', status='complete'),
        dict(manifest='second.json', status='failed', error="waitForSelector: VM did not reach RUNNING")]))
    return run
