"""Build an offline, document-first index from the versioned CSV and JSON files."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

from .docs_scan import scan_content, scan_document
from .manifest import ManifestError, load_manifest, screenshot_variants, validate_manifest


def build_catalogue(inventory: Path, repo_root: Path, discover: bool = False) -> dict:
    return _Catalogue(inventory, repo_root).build(discover)


class _Catalogue:
    def __init__(self, inventory, repo_root):
        self.root = Path(repo_root).resolve()
        self.inventory = Path(inventory).resolve()
        if not self.inventory.is_relative_to(self.root):
            raise ManifestError('Catalogue inventory must be inside --repo-root.')
        self.documents = {}
        self.documents_by_path = {}
        self.manifests = {}
        self.recipes = {}
        self.screenshots = {}
        self.assets = {}
        self.groups = {}
        self.diagnostics = []

    def issue(self, code, message, source, severity='error'):
        message = str(message).replace(str(self.root) + '/', '')
        item = dict(severity=severity, code=code, source=source, message=message)
        if item not in self.diagnostics:
            self.diagnostics.append(item)

    def relative(self, path):
        return path.relative_to(self.root).as_posix()

    def path(self, base, value, source):
        if not isinstance(value, str) or not value.strip() or Path(value).is_absolute():
            self.issue('path.invalid', 'Expected a nonempty relative path.', source)
            return None
        target = (base / value).resolve()
        if not target.is_relative_to(self.root):
            self.issue('path.outside-repository', f'Path escapes the repository: {value}', source)
            return None
        return target

    def file_info(self, path):
        if not path.is_file():
            return dict(exists=False, sha256=None)
        digest = hashlib.sha256()
        with path.open('rb') as stream:
            for chunk in iter(lambda: stream.read(65536), b''):
                digest.update(chunk)
        return dict(exists=True, sha256=digest.hexdigest())

    def read_json(self, path, kind):
        try:
            data = json.loads(path.read_text(encoding='utf-8'))
            if not isinstance(data, dict):
                raise ValueError('Expected a JSON object.')
            return data
        except (OSError, ValueError) as exc:
            message = exc.strerror if isinstance(exc, OSError) else str(exc)
            self.issue(f'{kind}.invalid', message, self.relative(path))
            return None

    def document(self, doc_path, row=None, row_number=None, origin='dependency'):
        row = row or {}
        path_id = self.relative(doc_path) if doc_path else None
        identity = row.get('id') or path_id or row.get('source_page') or f"unresolved:{row.get('title', '')}"
        if identity in self.documents or (path_id and path_id in self.documents_by_path):
            self.issue('document.duplicate', f'Duplicate document identity or path: {identity}', self.relative(self.inventory))
            return None
        node = dict(id=identity, title=row.get('title') or (doc_path.stem if doc_path else identity),
                    doc=path_id, source_page=row.get('source_page', ''), section=row.get('section', ''),
                    automation_status=row.get('automation_status') or ('pending' if origin == 'inventory' else origin), origin=origin,
                    inventory_row=row_number, group=None, manifests=[], images=[])
        node.update(self.file_info(doc_path) if doc_path else dict(exists=False, sha256=None))
        self.documents[identity] = node
        if path_id:
            self.documents_by_path[path_id] = node
            if not node['exists']:
                self.issue('document.missing', f'Document does not exist: {path_id}', identity)
        else:
            self.issue('document.unresolved', 'No local document path; external or unresolved inventory entry.', identity, 'warning')
        return node

    def group(self, path):
        identity = self.relative(path)
        if identity in self.groups:
            return identity
        node = dict(id=identity, path=identity, manifests=[], provision=None, provision_sha256=None,
                    **self.file_info(path))
        self.groups[identity] = node
        data = self.read_json(path, 'group')
        if data is None:
            return identity
        if data.get('version') != 1 or not isinstance(data.get('manifests'), list) or not data['manifests']:
            self.issue('group.invalid', 'Expected version 1 and a nonempty manifests list.', identity)
            return identity
        for value in data['manifests']:
            target = self.path(path.parent, value, identity)
            if target:
                member = self.relative(target)
                if member in node['manifests']:
                    self.issue('group.duplicate-manifest', f'Duplicate group manifest: {member}', identity)
                node['manifests'].append(member)
                if not target.is_file():
                    self.issue('group.missing-manifest', f'Manifest does not exist: {member}', identity)
        provision = self.path(path.parent, data.get('provision'), identity)
        if provision:
            node['provision'] = self.relative(provision)
            node['provision_sha256'] = self.file_info(provision)['sha256']
            self.read_json(provision, 'provision')
        return identity

    def recipe(self, path):
        identity = self.relative(path)
        if identity in self.recipes:
            return identity
        node = dict(id=identity, path=identity, setup_steps=0, teardown_steps=0, captures=[], **self.file_info(path))
        self.recipes[identity] = node
        data = self.read_json(path, 'recipe')
        if data is None:
            return identity
        captures = data.get('captures')
        if not isinstance(captures, list):
            self.issue('recipe.invalid', 'captures must be a list.', identity)
            return identity
        for stage in ('setup', 'teardown'):
            steps = data.get(stage, [])
            if not isinstance(steps, list):
                self.issue('recipe.invalid', f'{stage} must be a list.', identity)
            else:
                node[stage + '_steps'] = len(steps)
        seen = set()
        for capture in captures:
            if (not isinstance(capture, dict) or not isinstance(capture.get('id'), str) or not capture['id']
                    or not isinstance(capture.get('steps', []), list)):
                self.issue('recipe.invalid', 'Each capture needs a string id and a steps list.', identity)
                continue
            if capture['id'] in seen:
                self.issue('recipe.duplicate-capture', f"Duplicate capture: {capture['id']}", identity)
            seen.add(capture['id'])
            node['captures'].append(dict(id=capture['id'], step_count=len(capture.get('steps', [])), screenshots=[]))
        return identity

    def asset(self, path):
        identity = self.relative(path)
        if identity not in self.assets:
            self.assets[identity] = dict(id=identity, path=identity, documents=[], screenshots=[], **self.file_info(path))
        return identity

    def manifest(self, path):
        identity = self.relative(path)
        if identity in self.manifests:
            return identity
        node = dict(id=identity, path=identity, documents=[], group=None, recipes=[], screenshots=[],
                    deferred_screenshots=[], **self.file_info(path))
        self.manifests[identity] = node
        try:
            data = load_manifest(path)
            references = []
            if data.get('group') is not None:
                references.append((path.parent, data['group']))
            hooks = data.get('hooks', {})
            if isinstance(hooks, dict):
                for commands in hooks.values():
                    if isinstance(commands, list):
                        references.extend((path.parent, c['script']) for c in commands if isinstance(c, dict) and 'script' in c)
            deferred = data.get('deferredScreenshots', [])
            if isinstance(deferred, list):
                references.extend((self.root, d.get('image')) for d in deferred if isinstance(d, dict))
            for shot in data['screenshots']:
                if not isinstance(shot, dict):
                    continue
                references.extend((self.root, shot[key]) for key in ('doc', 'image', 'darkImage') if key in shot)
                if 'recipe' in shot:
                    references.append((path.parent, shot['recipe']))
                if isinstance(shot.get('sharedFrom'), dict):
                    references.append((path.parent, shot['sharedFrom'].get('manifest')))
            safe_paths = [self.path(base, value, identity) is not None for base, value in references]
            # Run existing format/hook/shared-source checks without executing any commands.
            if all(safe_paths):
                for error in validate_manifest(data, self.root, path):
                    self.issue('manifest.invalid', error, identity)
        except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
            message = exc.strerror if isinstance(exc, OSError) else str(exc).replace(str(path), identity)
            self.issue('manifest.invalid', message, identity)
            return identity
        if data.get('group'):
            group = self.path(path.parent, data['group'], identity)
            if group:
                node['group'] = self.group(group)
                if identity not in self.groups[node['group']]['manifests']:
                    self.issue('group.missing-membership', 'Manifest is not listed in its group.', identity)
        for item in deferred if isinstance(deferred, list) else []:
            if not isinstance(item, dict):
                continue
            target = self.path(self.root, item.get('image'), identity)
            if target:
                node['deferred_screenshots'].append(dict(asset=self.asset(target), reason=item.get('reason', '')))
        for shot in data['screenshots']:
            if not isinstance(shot, dict):
                continue
            if not all(isinstance(shot.get(key), str) and shot[key] for key in ('id', 'doc', 'recipe', 'capture', 'image')):
                self.issue('screenshot.invalid', 'Screenshot id, doc, recipe, capture and image must be nonempty strings.', identity)
                continue
            key = f"{identity}#{shot['id']}"
            if key in self.screenshots:
                continue
            doc = self.path(self.root, shot['doc'], key)
            recipe = self.path(path.parent, shot['recipe'], key)
            record = dict(id=key, screenshot_id=shot['id'], title=shot.get('title', shot['id']), manifest=identity,
                          doc=self.relative(doc) if doc else None, document=None,
                          recipe=self.recipe(recipe) if recipe else None, capture=shot['capture'],
                          status=shot.get('status', 'draft'), assets=[], shared_from=None)
            self.screenshots[key] = record
            node['screenshots'].append(key)
            if record['recipe']:
                if record['recipe'] not in node['recipes']:
                    node['recipes'].append(record['recipe'])
                matches = [c for c in self.recipes[record['recipe']]['captures'] if c['id'] == shot['capture']]
                if not matches:
                    self.issue('capture.missing', f"Recipe has no capture {shot['capture']!r}.", key)
                for capture in matches:
                    capture['screenshots'].append(key)
            for variant, image in screenshot_variants(shot):
                target = self.path(self.root, image, key)
                if target:
                    record['assets'].append(dict(variant=variant, asset=self.asset(target)))
            shared = shot.get('sharedFrom')
            if isinstance(shared, dict) and isinstance(shared.get('id'), str):
                source = self.path(path.parent, shared.get('manifest'), key)
                if source:
                    source_id = self.manifest(source)
                    record['shared_from'] = f"{source_id}#{shared['id']}"
                    if record['shared_from'] not in self.screenshots:
                        self.issue('shared-source.missing', 'Shared source screenshot does not exist.', key)
        return identity

    def read_inventory(self):
        with self.inventory.open(newline='', encoding='utf-8-sig') as stream:
            reader = csv.DictReader(stream)
            required = {'title', 'doc', 'manifest', 'automation_status'}
            if not required.issubset(reader.fieldnames or []):
                raise ManifestError('Catalogue CSV requires title, doc, manifest and automation_status columns.')
            for number, row in enumerate(reader, 2):
                if None in row or any(value is None for value in row.values()):
                    self.issue('inventory.invalid-row', f'CSV row {number} has the wrong number of columns.', self.relative(self.inventory))
                    continue
                row = {key: value.strip() for key, value in row.items()}
                doc = self.path(self.root, row['doc'], f'row {number}') if row['doc'] else None
                entry = self.document(doc, row, number, 'inventory')
                if entry is None:
                    continue
                group = self.path(self.inventory.parent, row['group'], entry['id']) if row.get('group') else None
                group_id = self.group(group) if group else None
                entry['group'] = group_id
                if row['manifest']:
                    target = self.path(self.inventory.parent, row['manifest'], entry['id'])
                    if target:
                        manifest_id = self.manifest(target)
                        entry['manifests'].append(manifest_id)
                        node = self.manifests[manifest_id]
                        if group_id and node['group'] != group_id:
                            self.issue('group.mismatch', 'Inventory and manifest point to different groups.', entry['id'])
                        if doc and any(self.screenshots[s]['doc'] != entry['doc'] for s in node['screenshots']):
                            self.issue('manifest.document-mismatch', 'Manifest contains screenshots for a different document.', entry['id'])
                        elif not doc:
                            self.issue('manifest.document-mismatch', 'Assign a local document path before linking a manifest.', entry['id'])
                        node['documents'].append(entry['id'])
                elif doc:
                    self.issue('document.unmapped', 'No manifest assigned yet.', entry['id'], 'warning')

    def connect_documents(self):
        for shot in self.screenshots.values():
            if not shot['doc']:
                continue
            document = self.documents_by_path.get(shot['doc'])
            if document is None:
                document = self.document(self.root / shot['doc'])
                if document is None:
                    continue
                self.issue('document.dependency', 'Document included through a shared manifest dependency, not the inventory.', document['id'], 'warning')
            shot['document'] = document['id']
            manifest = self.manifests[shot['manifest']]
            if document['group'] is None:
                document['group'] = manifest['group']
            if shot['manifest'] not in document['manifests']:
                document['manifests'].append(shot['manifest'])
            if document['id'] not in manifest['documents']:
                manifest['documents'].append(document['id'])

    def check_shared_order(self):
        for shot in self.screenshots.values():
            source = self.screenshots.get(shot['shared_from'])
            if source is None:
                continue
            group = self.manifests[shot['manifest']]['group']
            source_group = self.manifests[source['manifest']]['group']
            if group is not None:
                if source_group != group:
                    self.issue('shared-source.group-mismatch', 'Shared producer must belong to the same group.', shot['id'])
                    continue
                members = self.groups[group]['manifests']
                if source['manifest'] in members and shot['manifest'] in members:
                    if members.index(source['manifest']) >= members.index(shot['manifest']):
                        self.issue('shared-source.order', 'Shared producer must run before its consumer.', shot['id'])

    def connect_images(self, document, references):
        mapped = {}
        for shot in self.screenshots.values():
            if shot['document'] == document['id']:
                for variant in shot['assets']:
                    mapped.setdefault((variant['asset'], variant['variant']), []).append(shot['id'])
        deferred = {item['asset']: item['reason'] for name in document['manifests']
                    for item in self.manifests[name]['deferred_screenshots']}
        referenced = set()
        for reference in references:
            for variant in reference.variants:
                if variant.asset_path is None:
                    continue
                target = self.path(self.root, variant.asset_path, document['id'])
                if target is None:
                    continue
                asset_id = self.asset(target)
                theme = 'dark' if variant.role == 'dark' else 'light'
                referenced.add((asset_id, theme))
                shots = mapped.get((asset_id, theme), [])
                active = [s for s in shots if self.screenshots[s]['status'] != 'disabled']
                coverage = ('mapped' if active else 'disabled' if shots else 'deferred' if asset_id in deferred
                            else 'unmapped' if reference.sunstone_candidate else 'unclassified')
                document['images'].append(dict(asset=asset_id, variant=theme, line=reference.line, kind=reference.kind,
                                               sunstone_candidate=reference.sunstone_candidate, coverage=coverage,
                                               screenshots=shots, deferred_reason=deferred.get(asset_id)))
                if document['id'] not in self.assets[asset_id]['documents']:
                    self.assets[asset_id]['documents'].append(document['id'])
                if coverage == 'unmapped':
                    self.issue('image.unmapped', f'Likely Sunstone image has no capture mapping: {asset_id}', document['id'], 'warning')
                if not self.assets[asset_id]['exists']:
                    self.issue('asset.missing', f'Image does not exist: {asset_id}', document['id'])
        for (asset_id, theme), shots in mapped.items():
            for shot in shots:
                if shot not in self.assets[asset_id]['screenshots']:
                    self.assets[asset_id]['screenshots'].append(shot)
                if document['id'] not in self.assets[asset_id]['documents']:
                    self.assets[asset_id]['documents'].append(document['id'])
                if document['exists'] and (asset_id, theme) not in referenced:
                    self.issue('screenshot.not-referenced', f'{theme} image is not referenced by this document: {asset_id}', shot)
            if asset_id in deferred:
                self.issue('image.conflicting-coverage', f'Image is both mapped and deferred: {asset_id}', document['id'])

    def build(self, discover):
        self.read_inventory()
        references = {}
        if discover:
            for reference in scan_content(self.root, Path('content')):
                references.setdefault(reference.doc, []).append(reference)
            for doc, items in sorted(references.items()):
                if doc not in self.documents_by_path and any(r.sunstone_candidate for r in items):
                    document = self.document(self.root / doc, origin='discovered')
                    self.issue('document.untracked', 'Likely Sunstone page is missing from the inventory.', document['id'], 'warning')
        self.connect_documents()
        self.check_shared_order()
        for document in self.documents.values():
            if document['exists']:
                items = references.get(document['doc'])
                if items is None:
                    items = scan_document(self.root, Path(document['doc']))
                self.connect_images(document, items)
            else:
                self.connect_images(document, [])
        for asset in self.assets.values():
            producers = [s for s in asset['screenshots'] if self.screenshots[s]['shared_from'] is None
                         and self.screenshots[s]['status'] != 'disabled']
            if len(producers) > 1:
                self.issue('asset.multiple-producers', 'Multiple capture producers; use sharedFrom for intentional reuse.', asset['id'])
        entities = dict(documents=list(self.documents.values()), manifests=list(self.manifests.values()),
                        recipes=list(self.recipes.values()), screenshots=list(self.screenshots.values()),
                        assets=list(self.assets.values()), groups=list(self.groups.values()))
        summary = {name: len(items) for name, items in entities.items()}
        summary.update(errors=sum(d['severity'] == 'error' for d in self.diagnostics),
                       warnings=sum(d['severity'] == 'warning' for d in self.diagnostics))
        return dict(version=1, inventory=self.relative(self.inventory), valid=summary['errors'] == 0,
                    summary=summary, **entities, diagnostics=self.diagnostics)
