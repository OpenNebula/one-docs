from __future__ import annotations

import json
import os
import re
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

from .manifest import manifest_defaults, screenshot_variants


VARIABLE_RE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")


class CaptureError(RuntimeError):
    """Raised when a screenshot recipe cannot be executed."""


def capture_screenshots(
    manifest: dict[str, Any],
    manifest_path: Path,
    repo_root: Path,
    output_root: Path,
    selected_ids: set[str] | None = None,
    selected_tags: set[str] | None = None,
    headed: bool = False,
    browser_name: str = "chromium",
    debug: bool = False,
    slow_mo: int = 0,
    pause_before_step: bool = False,
    pause_after_step: bool = False,
    keep_open_on_failure: bool = False,
) -> None:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise CaptureError(
            "Python Playwright is not installed. Run "
            "`python3 -m pip install -r tools/sunstone-screenshots/requirements.txt` "
            "and then `python3 -m playwright install chromium`."
        ) from exc

    repo_root = repo_root.resolve()
    output_root = output_root.resolve()
    manifest_dir = manifest_path.resolve().parent
    selected = _select_screenshots(manifest, selected_ids, selected_tags)
    if not selected:
        raise CaptureError(_empty_selection_message(manifest, selected_ids, selected_tags))

    by_recipe: dict[Path, list[dict[str, Any]]] = defaultdict(list)
    for screenshot in selected:
        by_recipe[manifest_dir / screenshot["recipe"]].append(screenshot)

    defaults = manifest_defaults(manifest)
    viewport = defaults.get("viewport", {"width": 1440, "height": 1000})

    visual_debug = headed or debug or pause_before_step or pause_after_step or keep_open_on_failure
    effective_slow_mo = slow_mo if slow_mo > 0 else (500 if debug else 0)

    with sync_playwright() as playwright:
        browser_type = getattr(playwright, browser_name)
        browser = browser_type.launch(headless=not visual_debug, slow_mo=effective_slow_mo)
        try:
            for recipe_path, screenshots in by_recipe.items():
                recipe = _load_recipe(recipe_path)
                wanted_capture_ids = {screenshot["capture"] for screenshot in screenshots}
                screenshot_by_capture = defaultdict(list)
                for screenshot in screenshots:
                    screenshot_by_capture[screenshot["capture"]].append(screenshot)

                context = browser.new_context(
                    viewport={
                        "width": int(viewport.get("width", 1440)),
                        "height": int(viewport.get("height", 1000)),
                    },
                    device_scale_factor=float(viewport.get("deviceScaleFactor", 1)),
                    locale=str(defaults.get("locale", "en-US")),
                )
                page = context.new_page()
                try:
                    for step_index, step in enumerate(recipe.get("setup", []), start=1):
                        page = _run_debug_step(
                            page,
                            step,
                            {},
                            label=f"{recipe_path.name} setup step {step_index}",
                            debug=debug,
                            pause_before_step=pause_before_step,
                            pause_after_step=pause_after_step,
                        )

                    for capture in recipe.get("captures", []):
                        capture_id = capture.get("id")
                        if not capture_id:
                            raise CaptureError(f"{recipe_path}: capture is missing id")

                        env = {"SCREENSHOT_CAPTURE": str(capture_id)}
                        for step_index, step in enumerate(capture.get("steps", []), start=1):
                            page = _run_debug_step(
                                page,
                                step,
                                env,
                                label=f"{recipe_path.name} capture {capture_id} step {step_index}",
                                debug=debug,
                                pause_before_step=pause_before_step,
                                pause_after_step=pause_after_step,
                            )

                        if capture_id not in wanted_capture_ids:
                            continue

                        for screenshot in screenshot_by_capture[capture_id]:
                            for variant, image_path in screenshot_variants(screenshot):
                                variant_env = {
                                    "SCREENSHOT_CAPTURE": str(capture_id),
                                    "SCREENSHOT_ID": str(screenshot.get("id", "")),
                                    "SCREENSHOT_THEME": variant,
                                }
                                target = output_root / image_path
                                target.parent.mkdir(parents=True, exist_ok=True)
                                _prepare_screenshot_variant(
                                    page,
                                    recipe,
                                    capture,
                                    screenshot,
                                    variant,
                                    variant_env,
                                    debug=debug,
                                    pause_before_step=pause_before_step,
                                    pause_after_step=pause_after_step,
                                )
                                _take_screenshot(page, capture.get("screenshot", {}), target, variant_env)
                                print(f"captured {screenshot.get('id')} {variant}: {target.relative_to(repo_root) if target.is_relative_to(repo_root) else target}")
                except Exception as exc:
                    if keep_open_on_failure:
                        print(f"\nRecipe failed: {exc}")
                        print("Browser is still open for inspection.")
                        print("Press Enter here when finished to run teardown and close the browser.")
                        input()
                    raise
                finally:
                    try:
                        for step_index, step in enumerate(recipe.get('teardown', []), start=1):
                            page = _run_debug_step(
                                page, step, {}, label=f'{recipe_path.name} teardown step {step_index}',
                                debug=debug, pause_before_step=pause_before_step,
                                pause_after_step=pause_after_step,
                            )
                    finally:
                        context.close()
        finally:
            browser.close()


def _select_screenshots(
    manifest: dict[str, Any],
    selected_ids: set[str] | None,
    selected_tags: set[str] | None,
) -> list[dict[str, Any]]:
    screenshots: list[dict[str, Any]] = []
    for screenshot in manifest.get("screenshots", []):
        if not isinstance(screenshot, dict) or screenshot.get("status") == "disabled":
            continue

        screenshot_id = str(screenshot.get("id", ""))
        tags = {str(tag) for tag in screenshot.get("tags", [])}

        if selected_ids and screenshot_id not in selected_ids:
            continue
        if selected_tags and not tags.intersection(selected_tags):
            continue
        screenshots.append(screenshot)
    return screenshots


def _empty_selection_message(
    manifest: dict[str, Any],
    selected_ids: set[str] | None,
    selected_tags: set[str] | None,
) -> str:
    available_ids: list[str] = []
    available_tags: set[str] = set()

    for screenshot in manifest.get("screenshots", []):
        if not isinstance(screenshot, dict) or screenshot.get("status") == "disabled":
            continue
        if screenshot.get("id"):
            available_ids.append(str(screenshot["id"]))
        available_tags.update(str(tag) for tag in screenshot.get("tags", []))

    parts = ["No screenshots matched the selection."]
    if selected_ids:
        parts.append(f"Requested ids: {', '.join(sorted(selected_ids))}.")
    if selected_tags:
        parts.append(f"Requested tags: {', '.join(sorted(selected_tags))}.")
    if available_tags:
        parts.append(f"Available tags: {', '.join(sorted(available_tags))}.")
    if available_ids:
        parts.append(f"Available ids: {', '.join(sorted(available_ids))}.")
    return " ".join(parts)


def _load_recipe(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise CaptureError(f"Recipe does not exist: {path}")
    try:
        recipe = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise CaptureError(f"{path}: invalid JSON: {exc}") from exc
    if not isinstance(recipe.get("captures"), list):
        raise CaptureError(f"{path}: captures must be a list")
    return recipe


def _run_step(page: Any, step: dict[str, Any], variables: dict[str, str]) -> Any:
    action = step.get("action")
    if action == "guestCommand":
        from .workflow import run_guest
        run_guest(step)
        return page
    if not action:
        raise CaptureError(f"Recipe step is missing action: {step}")

    if action == "goto":
        page.goto(_expand(step["url"], variables), wait_until=step.get("waitUntil", "networkidle"))
        return page
    if action == "waitForSelector":
        _wait_for_selector(page, step, variables)
        return page
    if action == "waitForURL":
        page.wait_for_url(_expand(step["url"], variables), timeout=step.get("timeout", 30000))
        return page
    if action == "waitForLoadState":
        page.wait_for_load_state(step.get("state", "networkidle"))
        return page
    if action == "waitTime":
        page.wait_for_timeout(step.get("timeout", 5000))
        return page
    if action == "hover":
        _locator(page, step, variables).hover()
        return page
    if action == "moveMouse":
        x, y = _point_from_step(page, step, default_x_percent=50, default_y_percent=50)
        page.mouse.move(x, y)
        return page
    if action == "defocus":
        x, y = _point_from_step(page, step, default_x_percent=50, default_y_percent=50)
        page.mouse.move(x, y)
        return page
    if action == "setColorScheme":
        page.emulate_media(color_scheme=step.get("scheme", "light"))
        return page
    if action == "pause":
        page.pause()
        return page
    if action == "click":
        if step.get("opensPage"):
            return _run_action_that_opens_page(
                page,
                step,
                lambda: _locator(page, step, variables).click(),
            )
        _locator(page, step, variables).click()
        return page
    if action == "fill":
        _locator(page, step, variables).fill(_expand(step.get("value", ""), variables))
        return page
    if action == "press":
        _locator(page, step, variables).press(step["key"])
        return page
    if action == "evaluate":
        page.evaluate(_expand(step["script"], variables))
        return page
    if action == "switchToPage":
        return _switch_to_page(page, step)

    raise CaptureError(f"Unsupported recipe action: {action}")


def _wait_for_selector(page, step, variables):
    selector = _expand(step['selector'], variables)
    timeout = step.get('timeout', 30000)
    state = step.get('state', 'visible')
    if not step.get('refreshSelector'):
        page.wait_for_selector(selector, timeout=timeout, state=state)
        return
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

    deadline = time.monotonic() + timeout / 1000
    while True:
        remaining = int((deadline - time.monotonic()) * 1000)
        if remaining <= 0:
            raise CaptureError(f'Timed out waiting for selector: {selector}')
        try:
            page.wait_for_selector(selector, timeout=min(5000, remaining), state=state)
            return
        except PlaywrightTimeoutError:
            remaining = int((deadline - time.monotonic()) * 1000)
            if remaining <= 0:
                raise CaptureError(f'Timed out waiting for selector: {selector}')
            try:
                page.locator(_expand(step['refreshSelector'], variables)).first.click(timeout=min(5000, remaining))
            except PlaywrightTimeoutError:
                # A busy or rerendered refresh control must not shorten the overall wait.
                continue


def _run_debug_step(
    page: Any,
    step: dict[str, Any],
    variables: dict[str, str],
    label: str,
    debug: bool,
    pause_before_step: bool,
    pause_after_step: bool,
) -> Any:
    if debug:
        print(f"{label}: {_step_summary(step, variables)}")

    if pause_before_step or step.get("pauseBefore"):
        print(f"Paused before {label}. Resume in Playwright Inspector.")
        page.pause()

    try:
        page = _run_step(page, step, variables)
    except Exception as exc:
        raise CaptureError(f'{label}: {exc}') from exc

    if pause_after_step or step.get("pauseAfter"):
        print(f"Paused after {label}. Resume in Playwright Inspector.")
        page.pause()

    return page


def _step_summary(step: dict[str, Any], variables: dict[str, str]) -> str:
    action = step.get("action", "<missing action>")
    for key in ("selector", "dataCy", "role", "label", "text", "url", "scheme"):
        if key in step:
            return f"{action} {key}={_expand(str(step[key]), variables)!r}"
    return str(action)


def _run_action_that_opens_page(page: Any, step: dict[str, Any], action: Any) -> Any:
    timeout = int(step.get("timeout", 30000))
    with page.context.expect_page(timeout=timeout) as page_info:
        action()

    new_page = page_info.value
    wait_state = step.get("newPageWaitForLoadState", "domcontentloaded")
    if wait_state:
        new_page.wait_for_load_state(wait_state, timeout=timeout)
    new_page.bring_to_front()
    return new_page


def _switch_to_page(page: Any, step: dict[str, Any]) -> Any:
    pages = page.context.pages
    if not pages:
        raise CaptureError("No browser pages are open.")

    if "index" in step:
        next_page = pages[int(step["index"])]
    else:
        target = step.get("target", "last")
        if target == "last":
            next_page = pages[-1]
        elif target == "first":
            next_page = pages[0]
        elif target == "previous":
            current_index = pages.index(page) if page in pages else len(pages) - 1
            next_page = pages[max(current_index - 1, 0)]
        else:
            raise CaptureError(f"Unsupported switchToPage target: {target}")

    wait_state = step.get("waitForLoadState")
    if wait_state:
        next_page.wait_for_load_state(wait_state, timeout=step.get("timeout", 30000))
    next_page.bring_to_front()
    return next_page


def _prepare_screenshot_variant(
    page: Any,
    recipe: dict[str, Any],
    capture: dict[str, Any],
    screenshot: dict[str, Any],
    variant: str,
    variables: dict[str, str],
    debug: bool,
    pause_before_step: bool,
    pause_after_step: bool,
) -> None:
    color_scheme = "dark" if variant == "dark" else "light"
    page.emulate_media(color_scheme=color_scheme)

    for source_name, source in (
        ("recipe", recipe),
        ("capture", capture),
        ("screenshot", capture.get("screenshot", {})),
    ):
        for step_index, step in enumerate(_theme_steps(source, variant), start=1):
            page = _run_debug_step(
                page,
                step,
                variables,
                label=f"{source_name} {variant} theme step {step_index}",
                debug=debug,
                pause_before_step=pause_before_step,
                pause_after_step=pause_after_step,
            )


def _theme_steps(source: Any, variant: str) -> list[dict[str, Any]]:
    if not isinstance(source, dict):
        return []

    theme_steps = source.get("themeSteps")
    if not isinstance(theme_steps, dict):
        return []

    steps = theme_steps.get(variant, [])
    if not isinstance(steps, list):
        raise CaptureError(f"themeSteps.{variant} must be a list")
    return [step for step in steps if isinstance(step, dict)]


def _take_screenshot(page: Any, options: dict[str, Any], target: Path, variables: dict[str, str]) -> None:
    selector = options.get("selector")
    omit_background = bool(options.get("omitBackground", False))
    buffer = int(options.get("buffer", 0))
    clip = _clip_from_options(page, options)

    if clip:
        page.screenshot(
            path=str(target),
            omit_background=omit_background,
            clip=clip,
        )
        return

    if selector:
        if buffer > 0:
            box = page.locator(_expand(selector, variables)).first.bounding_box()
            if not box:
                raise CaptureError(f"Could not get bounding box for screenshot selector: {selector}")
            page.screenshot(
                path=str(target),
                omit_background=omit_background,
                clip={
                    "x": max(box["x"] - buffer, 0),
                    "y": max(box["y"] - buffer, 0),
                    "width": box["width"] + buffer * 2,
                    "height": box["height"] + buffer * 2,
                },)
            return
        page.locator(_expand(selector, variables)).first.screenshot(
            path=str(target),
            omit_background=omit_background,

        )
        return

    page.screenshot(
        path=str(target),
        full_page=bool(options.get("fullPage", False)),
        omit_background=omit_background,
    )


def _point_from_step(
    page: Any,
    step: dict[str, Any],
    default_x_percent: float,
    default_y_percent: float,
) -> tuple[float, float]:
    viewport = page.viewport_size or {"width": 1440, "height": 1000}
    width = float(viewport["width"])
    height = float(viewport["height"])

    if "x" in step:
        x = float(step["x"])
    else:
        x = width * float(step.get("xPercent", default_x_percent)) / 100

    if "y" in step:
        y = float(step["y"])
    else:
        y = height * float(step.get("yPercent", default_y_percent)) / 100

    return _clamp(x, 0, width - 1), _clamp(y, 0, height - 1)


def _clip_from_options(page: Any, options: dict[str, Any]) -> dict[str, float] | None:
    raw_clip = options.get("clip")
    if not isinstance(raw_clip, dict):
        return None

    viewport = page.viewport_size or {"width": 1440, "height": 1000}
    viewport_width = float(viewport["width"])
    viewport_height = float(viewport["height"])

    left = _bound_value(raw_clip, "left", viewport_width, 0)
    right = _bound_value(raw_clip, "right", viewport_width, viewport_width)
    top = _bound_value(raw_clip, "top", viewport_height, 0)
    bottom = _bound_value(raw_clip, "bottom", viewport_height, viewport_height)

    if right <= left:
        raise CaptureError(f"Screenshot clip right must be greater than left: {raw_clip}")
    if bottom <= top:
        raise CaptureError(f"Screenshot clip bottom must be greater than top: {raw_clip}")

    return {
        "x": _clamp(left, 0, viewport_width - 1),
        "y": _clamp(top, 0, viewport_height - 1),
        "width": _clamp(right - left, 1, viewport_width - _clamp(left, 0, viewport_width - 1)),
        "height": _clamp(bottom - top, 1, viewport_height - _clamp(top, 0, viewport_height - 1)),
    }


def _bound_value(bounds: dict[str, Any], name: str, viewport_size: float, default: float) -> float:
    percent_name = f"{name}Percent"
    if percent_name in bounds:
        return viewport_size * float(bounds[percent_name]) / 100
    if name in bounds:
        return float(bounds[name])
    return default


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(value, maximum))


def _locator(page: Any, step: dict[str, Any], variables: dict[str, str]) -> Any:
    if "selector" in step:
        return page.locator(_expand(step["selector"], variables)).first
    if "dataCy" in step:
        return page.locator(f"[data-cy={_css_string(_expand(step['dataCy'], variables))}]").first
    if "role" in step:
        name = step.get("name")
        return page.get_by_role(
            step["role"],
            name=_expand(name, variables) if name is not None else None,
            exact=bool(step.get("exact", False)),
        )
    if "label" in step:
        return page.get_by_label(_expand(step["label"], variables), exact=bool(step.get("exact", False)))
    if "text" in step:
        return page.get_by_text(_expand(step["text"], variables), exact=bool(step.get("exact", False)))
    raise CaptureError(f"Step needs selector, dataCy, role/name, label, or text: {step}")


def _expand(value: str, variables: dict[str, str]) -> str:
    def replace(match: re.Match[str]) -> str:
        name = match.group(1)
        if name in variables:
            return variables[name]
        return os.environ.get(name, match.group(0))

    return VARIABLE_RE.sub(replace, str(value))


def _css_string(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\a ")
    return f'"{escaped}"'
