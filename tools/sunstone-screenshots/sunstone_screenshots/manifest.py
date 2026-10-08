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
                validate_commands(commands)
            except ManifestError as exc:
                errors.append(str(exc))
    group = manifest.get('group')
    if group is not None and (not isinstance(group, str) or not (manifest_dir / group).is_file()):
        errors.append('group: must reference an existing group JSON file')

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

        for key in ("doc", "image", "darkImage"):
            rel_path = screenshot.get(key)
            if rel_path and not (repo_root / rel_path).exists():
                print(repo_root / rel_path)
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
                steps = list(data.get('setup', []))
                for capture in captures:
                    steps.extend(capture.get('steps', []))
                validate_commands([s for s in steps if s.get('action') == 'guestCommand'])
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
