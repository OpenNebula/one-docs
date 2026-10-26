"""Offline image comparisons and hash-bound substitution intentions. Never applies replacements."""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import tempfile
import threading

from .catalogue import build_catalogue


class ReviewError(ValueError):
    pass


def digest(path):
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(65536), b''):
            value.update(chunk)
    return value.hexdigest()


def image_info(path):
    from PIL import Image

    info = dict(exists=path.is_file(), sha256=None, width=None, height=None, error=None)
    if not info['exists']:
        return info
    info['sha256'] = digest(path)
    try:
        with Image.open(path) as image:
            info.update(width=image.width, height=image.height)
            if image.width * image.height > 24_000_000:
                raise ValueError('Image exceeds the 24 megapixel review limit.')
            image.verify()
    except (OSError, ValueError, Image.DecompressionBombError) as exc:
        info['error'] = str(exc).replace(str(path), path.name)
    return info


def compare_images(baseline_path, candidate_path):
    import numpy as np
    from PIL import Image
    from skimage.metrics import structural_similarity

    baseline, candidate = image_info(baseline_path), image_info(candidate_path)
    result = dict(baseline=baseline, candidate=candidate, dimensions_changed=False,
                  changed=False, ssim=None, change_percent=None, comparison_error=None)
    if not baseline['exists'] or not candidate['exists']:
        return result
    if baseline['error'] or candidate['error']:
        result['comparison_error'] = baseline['error'] or candidate['error']
        return result
    if (baseline['width'], baseline['height']) != (candidate['width'], candidate['height']):
        result['dimensions_changed'] = True
        return result
    try:
        with Image.open(baseline_path) as old, Image.open(candidate_path) as new:
            left, right = np.asarray(old.convert('RGBA')), np.asarray(new.convert('RGBA'))
        if np.array_equal(left, right):
            result.update(ssim=1.0, change_percent=0.0)
            return result
        result['changed'] = True
        window = min(7, left.shape[0], left.shape[1])
        if window % 2 == 0:
            window -= 1
        if window < 3:
            raise ValueError('Images smaller than 3 pixels cannot be compared with SSIM.')
        similarity = float(structural_similarity(left, right, channel_axis=2, data_range=255, win_size=window))
        result.update(ssim=similarity, change_percent=100 * (1 - max(0.0, min(1.0, similarity))))
    except (OSError, ValueError) as exc:
        result['comparison_error'] = str(exc)
    return result


def _json(path):
    data = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data, dict):
        raise ReviewError(f'Expected a JSON object: {path.name}')
    return data


def _contained(root, path):
    path = Path(path).resolve()
    if not path.is_relative_to(root):
        raise ReviewError('Path is outside the configured review directory.')
    return path


def _atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with tempfile.NamedTemporaryFile('w', encoding='utf-8', dir=path.parent, delete=False) as stream:
        temporary = Path(stream.name)
        try:
            json.dump(value, stream, indent=2, allow_nan=False)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        except BaseException:
            temporary.unlink(missing_ok=True)
            raise
    try:
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


class ReviewSession:
    def __init__(self, repo_root, run_dir, inventory, replacement_root=None, manifest=None):
        self.root = Path(repo_root).resolve()
        self.run_dir = Path(run_dir).resolve()
        if not self.run_dir.is_dir():
            raise ReviewError('Review requires an existing run directory.')
        self.inventory = Path(inventory).resolve()
        self.replacement_root = (Path(replacement_root).resolve() if replacement_root else self.run_dir
                                 if (self.run_dir / 'capture-results.json').is_file() else self.run_dir / 'screenshots')
        self.explicit_manifest = self._manifest_id(manifest) if manifest else None
        self.directory = _contained(self.run_dir, self.run_dir / 'review')
        self.selection_file = _contained(self.directory, self.directory / 'substitutions.json')
        self.lock = threading.RLock()
        self.paths = {}
        self.records = {}
        self.data = {}
        self.refresh()

    def _manifest_id(self, value):
        path = Path(value)
        target = (self.root / path).resolve()
        return _contained(self.root, target).relative_to(self.root).as_posix()

    def _run_records(self):
        records = {}
        notes = []

        def group(run, fallback=None):
            workflow = run / 'workflow.json'
            if workflow.is_file():
                saved = _json(workflow)
                group_id = saved.get('group')
                for page in saved.get('pages', []):
                    if isinstance(page, dict) and page.get('manifest'):
                        records[self._manifest_id(page['manifest'])] = dict(
                            status=page.get('status', 'unknown'), root=run / 'screenshots',
                            error=page.get('error'), expected_images=None)
                if group_id:
                    target = _contained(self.root, self.root / group_id)
                    for name in _json(target).get('manifests', []):
                        identity = self._manifest_id(target.parent / name)
                        records.setdefault(identity, dict(status='not_run', root=run / 'screenshots',
                                                         error=None, expected_images=None))
            elif fallback and fallback.get('group'):
                target = _contained(self.root, self.root / fallback['group'])
                if target.is_file():
                    for name in _json(target).get('manifests', []):
                        records[self._manifest_id(target.parent / name)] = dict(
                            status='failed' if fallback.get('status') == 'failed' else 'not_run',
                            root=run / 'screenshots', error=None, expected_images=None)
            captures = run / 'screenshots' / 'capture-results.json'
            if captures.is_file():
                for identity, record in _json(captures).get('manifests', {}).items():
                    record = dict(record, root=run / 'screenshots')
                    records[self._manifest_id(identity)] = record

        suite = self.run_dir / 'suite.json'
        try:
            if suite.is_file():
                for entry in _json(suite).get('groups', []):
                    child = _contained(self.run_dir, self.run_dir / entry['run_dir'])
                    group(child, entry)
            else:
                group(self.run_dir)
            capture_record = self.replacement_root / 'capture-results.json'
            if capture_record.is_file():
                for identity, record in _json(capture_record).get('manifests', {}).items():
                    records[self._manifest_id(identity)] = dict(record, root=self.replacement_root)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            notes.append(f'Run metadata could not be fully read: {exc}')
        if self.explicit_manifest:
            records.setdefault(self.explicit_manifest, dict(status='unknown', root=self.replacement_root,
                                                           expected_images=None, error=None))
        return records, notes

    def refresh(self):
        with self.lock:
            catalogue = build_catalogue(self.inventory, self.root)
            self.records, notes = self._run_records()
            self.paths = {}
            comparisons = {}
            documents = []
            shots_by_doc = {}
            for shot in catalogue['screenshots']:
                shots_by_doc.setdefault(shot['document'], []).append(shot)

            for doc in catalogue['documents']:
                shots = shots_by_doc.get(doc['id'], [])
                image_rows = []
                # Markdown order wins; old/moved docs still expose their manifest captures.
                references = [image for image in doc['images'] if image['coverage'] != 'unclassified']
                present = {(r['asset'], r['variant']) for r in references}
                for shot in shots:
                    for asset in shot['assets']:
                        pair = (asset['asset'], asset['variant'])
                        if pair not in present:
                            references.append(dict(asset=pair[0], variant=pair[1], line=None,
                                                   screenshots=[shot['id']], coverage='mapped'))
                            present.add(pair)
                for index, reference in enumerate(references):
                    shot = next((s for s in shots if s['id'] in reference['screenshots']), None)
                    if shot and shot['status'] == 'disabled':
                        continue
                    asset = reference['asset']
                    record = self.records.get(shot['manifest']) if shot else None
                    candidate_root = Path(record['root']) if record else self.replacement_root
                    baseline = _contained(self.root, self.root / asset)
                    candidate = _contained(candidate_root.resolve(), candidate_root / asset)
                    expected = bool(shot and record and record.get('status') != 'not_run')
                    selected = record.get('expected_images') if record else None
                    if selected is not None:
                        expected = expected and asset in selected
                    if not record and shot and not self.records:
                        expected = candidate.is_file()
                    relative_candidate = os.path.relpath(candidate, self.run_dir)
                    identity = hashlib.sha256(f'{asset}\0{relative_candidate}'.encode()).hexdigest()[:24]
                    if identity not in comparisons or expected and not comparisons[identity]['expected']:
                        consumers = comparisons[identity]['documents'] if identity in comparisons else []
                        compared = compare_images(baseline, candidate) if expected else dict(
                            baseline=image_info(baseline), candidate=dict(exists=False, sha256=None, width=None, height=None, error=None),
                            dimensions_changed=False, changed=False, ssim=None, change_percent=None, comparison_error=None)
                        compared.update(id=identity, asset=asset, replacement=relative_candidate,
                                        expected=expected, documents=consumers,
                                        can_substitute=bool(expected and compared['baseline']['exists'] and compared['candidate']['exists']
                                                            and not compared['baseline']['error'] and not compared['candidate']['error']))
                        comparisons[identity] = compared
                        self.paths[identity] = dict(baseline=baseline, candidate=candidate, candidate_root=candidate_root.resolve())
                    if doc['id'] not in comparisons[identity]['documents']:
                        comparisons[identity]['documents'].append(doc['id'])
                    image_rows.append(dict(id=identity, order=index + 1, variant=reference['variant'], line=reference.get('line'),
                                           title=shot['title'] if shot else Path(asset).name,
                                           manifest=shot['manifest'] if shot else None, recipe=shot['recipe'] if shot else None,
                                           capture=shot['capture'] if shot else None, coverage=reference['coverage']))
                states = [self.records[m]['status'] for m in doc['manifests'] if m in self.records]
                if 'failed' in states:
                    status = 'failed'
                elif 'running' in states:
                    status = 'running'
                elif states and all(s == 'complete' for s in states):
                    status = 'complete'
                elif 'not_run' in states:
                    status = 'not_run'
                elif states:
                    status = 'unknown'
                else:
                    status = 'outside_run' if doc['manifests'] else 'unmapped'
                if status == 'outside_run' and any(comparisons[row['id']]['expected'] for row in image_rows):
                    status = 'unknown'
                documents.append(dict(id=doc['id'], title=doc['title'], path=doc['doc'], section=doc['section'],
                                      exists=doc['exists'], manifests=doc['manifests'], status=status, images=image_rows,
                                      failure=next((self.records[m].get('error') for m in doc['manifests']
                                                    if m in self.records and self.records[m].get('error')), None)))
            # A later manifest may establish that a shared asset was captured for an earlier unmapped page.
            for document in documents:
                unique = [comparisons[i] for i in dict.fromkeys(r['id'] for r in document['images'])]
                document.update(changed=sum(i['changed'] for i in unique), dimensions=sum(i['dimensions_changed'] for i in unique),
                                missing_baseline=sum(not i['baseline']['exists'] for i in unique),
                                missing_candidate=sum(i['expected'] and not i['candidate']['exists'] for i in unique),
                                errors=sum(bool(i['comparison_error'] or i['baseline']['error'] or i['candidate']['error']) for i in unique),
                                max_change=max((i['change_percent'] for i in unique if i['change_percent'] is not None), default=None))
            self.data = dict(version=1, run=dict(id=self.run_dir.name, name=self.run_dir.name), documents=documents,
                             comparisons=comparisons, notes=notes, catalogue_diagnostics=catalogue['summary'],
                             selection_file='review/substitutions.json', metric='RGBA SSIM; change = 100 * (1 - max(0, SSIM)); no resizing')
            return self.view()

    def _load_selections(self):
        if not self.selection_file.exists():
            return dict(version=1, run=self.run_dir.name, selections=[])
        data = _json(self.selection_file)
        if data.get('version') != 1 or data.get('run') != self.run_dir.name or not isinstance(data.get('selections'), list):
            raise ReviewError('Saved substitutions do not match this run or format; refusing to overwrite them.')
        required = ('id', 'asset', 'replacement', 'baseline_sha256', 'candidate_sha256')
        if any(not isinstance(item, dict) or not all(isinstance(item.get(key), str) and item[key] for key in required)
               for item in data['selections']):
            raise ReviewError('Saved substitution entries are malformed; refusing to overwrite them.')
        return data

    def view(self):
        with self.lock:
            saved = self._load_selections()
            nominated, stale = [], []
            for record in saved['selections']:
                current = self.data['comparisons'].get(record['id'])
                if (current and current['can_substitute']
                        and current['baseline']['sha256'] == record['baseline_sha256']
                        and current['candidate']['sha256'] == record['candidate_sha256']):
                    nominated.append(record['id'])
                else:
                    stale.append(record['id'])
            summary = dict(documents=len(self.data['documents']), images=len(self.data['comparisons']),
                           changed=sum(i['changed'] for i in self.data['comparisons'].values()),
                           dimensions=sum(i['dimensions_changed'] for i in self.data['comparisons'].values()),
                           missing_baseline=sum(not i['baseline']['exists'] for i in self.data['comparisons'].values()),
                           missing_candidate=sum(i['expected'] and not i['candidate']['exists'] for i in self.data['comparisons'].values()),
                           failed=sum(d['status'] == 'failed' for d in self.data['documents']), selected=len(nominated), stale=len(stale))
            return dict(self.data, selected=nominated, stale=stale, summary=summary)

    @contextmanager
    def _selection_lock(self):
        import fcntl
        self.directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        with (self.directory / '.selection.lock').open('a') as stream:
            fcntl.flock(stream, fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(stream, fcntl.LOCK_UN)

    def nominate(self, identity, selected, baseline_sha256=None, candidate_sha256=None):
        with self.lock, self._selection_lock():
            if type(selected) is not bool:
                raise ReviewError('selected must be a boolean.')
            current = self.data['comparisons'].get(identity)
            if current is None:
                raise ReviewError('Unknown comparison.')
            saved = self._load_selections()
            entries = [s for s in saved['selections'] if s['id'] != identity]
            if selected:
                paths = self.paths[identity]
                baseline = _contained(self.root, paths['baseline'])
                candidate = _contained(paths['candidate_root'], paths['candidate'])
                if not current['can_substitute'] or not baseline.is_file() or not candidate.is_file():
                    raise ReviewError('Both images must exist and be readable before substitution can be nominated.')
                if (digest(baseline) != baseline_sha256 or digest(candidate) != candidate_sha256
                        or baseline_sha256 != current['baseline']['sha256'] or candidate_sha256 != current['candidate']['sha256']):
                    raise ReviewError('Image contents changed since comparison. Refresh and inspect them again.')
                if any(s['asset'] == current['asset'] for s in entries):
                    raise ReviewError('Another candidate for this repository asset is already nominated.')
                entries.append(dict(id=identity, asset=current['asset'], replacement=current['replacement'],
                                    baseline_sha256=baseline_sha256, candidate_sha256=candidate_sha256,
                                    baseline_dimensions=[current['baseline']['width'], current['baseline']['height']],
                                    candidate_dimensions=[current['candidate']['width'], current['candidate']['height']],
                                    documents=current['documents'], nominated_at=datetime.now(timezone.utc).isoformat()))
            saved.update(selections=entries, updated_at=datetime.now(timezone.utc).isoformat())
            _atomic_json(self.selection_file, saved)
            return self.view()

    def clear(self):
        with self.lock, self._selection_lock():
            saved = self._load_selections()
            saved.update(selections=[], updated_at=datetime.now(timezone.utc).isoformat())
            _atomic_json(self.selection_file, saved)
            return self.view()

    def image_path(self, identity, side):
        paths = self.paths.get(identity)
        if paths is None or side not in ('baseline', 'candidate'):
            raise ReviewError('Unknown image.')
        root = self.root if side == 'baseline' else paths['candidate_root']
        path = _contained(root, paths[side])
        info = self.data['comparisons'][identity][side]
        if not info['exists'] or info['error'] or not path.is_file():
            raise ReviewError('Image is missing or unreadable.')
        if digest(path) != info['sha256']:
            raise ReviewError('Image changed; refresh the comparison.')
        return path
