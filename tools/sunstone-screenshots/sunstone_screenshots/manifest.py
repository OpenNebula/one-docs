from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable


class ManifestError(ValueError):
    """Raised when the screenshot manifest is malformed."""


def load_manifest(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ManifestError(f"{path}: invalid JSON: {exc}") from exc

    if not isinstance(data, dict):
        raise ManifestError(f"{path}: manifest root must be an object")
    if data.get("version") != 1:
        raise ManifestError(f"{path}: only manifest version 1 is supported")
    if not isinstance(data.get("screenshots"), list):
        raise ManifestError(f"{path}: screenshots must be a list")
    return data


def validate_manifest(manifest: dict[str, Any], repo_root: Path, manifest_path: Path) -> list[str]:
    errors: list[str] = []
    seen_ids: set[str] = set()
    manifest_dir = manifest_path.resolve().parent
    from .workflow import validate_commands
    hooks = manifest.get('hooks', {})
    if not isinstance(hooks, dict) or set(hooks) - {'setup', 'teardown'}:
        errors.append('hooks: expected setup/teardown command lists')
    else:
        for commands in hooks.values():
            try:
                validate_commands(commands, manifest_dir)
            except ManifestError as exc:
                errors.append(str(exc))
    group = manifest.get('group')
    if group is not None and (not isinstance(group, str) or not (manifest_dir / group).is_file()):
        errors.append('group: must reference an existing group JSON file')

    deferred = manifest.get('deferredScreenshots', [])
    if not isinstance(deferred, list):
        errors.append('deferredScreenshots: expected a list')
    else:
        for item in deferred:
            if (not isinstance(item, dict) or set(item) != {'image', 'reason'}
                    or not all(isinstance(v, str) and v.strip() for v in item.values())):
                errors.append('deferredScreenshots: each entry requires image and reason strings')
            elif not (repo_root / item['image']).is_file():
                errors.append(f'deferredScreenshots: image does not exist: {item["image"]}')

    for index, screenshot in enumerate(manifest.get("screenshots", []), start=1):
        prefix = f"screenshots[{index}]"
        if not isinstance(screenshot, dict):
            errors.append(f"{prefix}: must be an object")
            continue

        screenshot_id = screenshot.get("id")
        if not screenshot_id:
            errors.append(f"{prefix}: missing id")
        elif screenshot_id in seen_ids:
            errors.append(f"{prefix}: duplicate id {screenshot_id}")
        else:
            seen_ids.add(screenshot_id)

        for key in ("doc", "image", "recipe", "capture"):
            if not screenshot.get(key):
                errors.append(f"{prefix}: missing {key}")

        if 'sharedFrom' in screenshot:
            try:
                source_path, source, source_manifest = shared_source(screenshot, manifest_path)
                if source.get('sharedFrom') or source.get('status') == 'disabled':
                    raise ManifestError('sharedFrom must name an enabled, directly captured screenshot')
                for key in ('image', 'darkImage', 'capture'):
                    if screenshot.get(key) != source.get(key):
                        raise ManifestError(f'sharedFrom {key} differs from its source')
                if (manifest_dir / screenshot['recipe']).resolve() != (source_path.parent / source['recipe']).resolve():
                    raise ManifestError('sharedFrom recipe differs from its source')
                if manifest_defaults(manifest) != manifest_defaults(source_manifest):
                    raise ManifestError('sharedFrom defaults differ from its source')
            except (ManifestError, OSError, KeyError, TypeError) as exc:
                errors.append(f'{prefix}: {exc}')

        for key in ("doc", "image", "darkImage"):
            rel_path = screenshot.get(key)
            if rel_path and not (repo_root / rel_path).exists():
                errors.append(f"{prefix}: {key} does not exist: {rel_path}")

        recipe = screenshot.get("recipe")
        if recipe and not (manifest_dir / recipe).exists():
            errors.append(f"{prefix}: recipe does not exist: {recipe}")
        elif recipe:
            try:
                data = json.loads((manifest_dir / recipe).read_text())
                captures = data.get('captures', [])
                if screenshot.get('capture') not in [c.get('id') for c in captures]:
                    errors.append(f'{prefix}: capture not found in recipe')
                steps = list(data.get('setup', [])) + list(data.get('teardown', []))
                for capture in captures:
                    steps.extend(capture.get('steps', []))
                validate_commands([s for s in steps if s.get('action') == 'guestCommand'])
                if any('script' in s for s in steps if s.get('action') == 'guestCommand'):
                    errors.append(f'{prefix}: guestCommand recipe steps require inline command; script hooks belong in the manifest')
            except (ValueError, TypeError, AttributeError) as exc:
                errors.append(f'{prefix}: invalid recipe: {exc}')

    environments = manifest.get("environments", {})
    if environments and not isinstance(environments, dict):
        errors.append("environments: must be an object")

    environment_ids = set(environments) if isinstance(environments, dict) else set()
    for screenshot in manifest.get("screenshots", []):
        if not isinstance(screenshot, dict):
            continue
        environment = screenshot.get("environment")
        if environment and environment_ids and environment not in environment_ids:
            errors.append(f"{screenshot.get('id', '<unknown>')}: unknown environment {environment}")

    return errors


def shared_source(screenshot: dict[str, Any], manifest_path: Path) -> tuple[Path, dict[str, Any], dict[str, Any]]:
    reference = screenshot['sharedFrom']
    if (not isinstance(reference, dict) or set(reference) != {'manifest', 'id'}
            or not all(isinstance(value, str) and value.strip() for value in reference.values())):
        raise ManifestError('sharedFrom requires nonempty manifest and id strings')
    path = (manifest_path.resolve().parent / reference['manifest']).resolve()
    manifest = load_manifest(path)
    matches = [s for s in manifest['screenshots'] if isinstance(s, dict) and s.get('id') == reference['id']]
    if len(matches) != 1:
        raise ManifestError('sharedFrom must identify exactly one source screenshot')
    return path, matches[0], manifest


def screenshot_variants(screenshot: dict[str, Any]) -> Iterable[tuple[str, str]]:
    image = screenshot.get("image")
    if image:
        yield "light", image

    dark_image = screenshot.get("darkImage")
    if dark_image:
        yield "dark", dark_image


def manifest_defaults(manifest: dict[str, Any]) -> dict[str, Any]:
    defaults = manifest.get("defaults")
    return defaults if isinstance(defaults, dict) else {}
