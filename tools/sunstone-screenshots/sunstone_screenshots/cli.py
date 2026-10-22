from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from contextlib import nullcontext
from pathlib import Path

from .capture import CaptureError, _select_screenshots, capture_screenshots
from .docs_scan import ImageReference, scan_content
from .manifest import ManifestError, load_manifest, screenshot_variants, validate_manifest
from .qa_report import write_qa_report
from . import provision as lab
from . import workflow


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="sunstone-screenshots",
        description="Inventory, capture, and review Sunstone screenshots in the OpenNebula docs.",
    )
    parser.add_argument("--repo-root", default=".", help="Repository root. Defaults to the current directory.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    provision_parser = subparsers.add_parser("provision", help="Create a single-VM miniONE lab.")
    provision_parser.add_argument("config", help="Provisioning JSON configuration.")
    provision_parser.add_argument("--run-dir", required=True, help="New directory for state and logs.")
    provision_parser.add_argument("--check", action="store_true", help="Validate local configuration without allocating a VM.")
    for command in ("status", "destroy"):
        lab_parser = subparsers.add_parser(command, help=f"{command.title()} a provisioned lab run.")
        lab_parser.add_argument("--run-dir", required=True)

    scan_parser = subparsers.add_parser("scan", help="Scan markdown files for image references.")
    scan_parser.add_argument("--content-dir", default="content", help="Content directory relative to the repo root.")
    scan_parser.add_argument("--format", choices=("json", "csv"), default="json")
    scan_parser.add_argument("--only-sunstone", action="store_true", help="Only include likely Sunstone UI screenshots.")
    scan_parser.add_argument("--output", help="Write output to a file instead of stdout.")

    validate_parser = subparsers.add_parser("validate", help="Validate a screenshot manifest.")
    validate_parser.add_argument("manifest", help="Path to manifest JSON.")

    report_parser = subparsers.add_parser("qa-report", help="Create a visual old-vs-new screenshot QA report.")
    report_parser.add_argument("manifest", help="Path to manifest JSON.")
    report_parser.add_argument(
        "--replacement-root",
        required=True,
        help="Root containing newly captured files, preserving repo-relative asset paths.",
    )
    report_parser.add_argument("--output", default=".sunstone-screenshots/qa/index.html")

    capture_parser = subparsers.add_parser("capture", help="Run Playwright recipes and store replacement screenshots.")
    capture_parser.add_argument("manifest", help="Path to manifest JSON.")
    capture_parser.add_argument("--run-dir", help="Use Sunstone and credentials from a ready provisioned run.")
    capture_parser.add_argument("--output-root", default=".sunstone-screenshots/runs/local")
    capture_parser.add_argument("--id", action="append", dest="ids", help="Screenshot id to capture. Can be repeated.")
    capture_parser.add_argument("--tag", action="append", dest="tags", help="Capture screenshots with this tag. Can be repeated.")
    capture_parser.add_argument("--skip-hooks", action="store_true",
                                help="Debug with existing resources: skip manifest guest setup/teardown hooks, not recipe actions.")
    capture_parser.add_argument("--headed", action="store_true", help="Show the browser while recipes run.")
    capture_parser.add_argument("--browser", choices=("chromium", "firefox", "webkit"), default="chromium")
    capture_parser.add_argument("--debug", action="store_true", help="Show the browser, slow actions down, and print each recipe step.")
    capture_parser.add_argument("--slow-mo", type=int, default=0, help="Delay Playwright actions by this many milliseconds.")
    capture_parser.add_argument("--pause-before-step", action="store_true", help="Pause in Playwright Inspector before every recipe step.")
    capture_parser.add_argument("--pause-after-step", action="store_true", help="Pause in Playwright Inspector after every recipe step.")
    capture_parser.add_argument("--keep-open-on-failure", action="store_true", help="Leave the browser open if a recipe step fails.")

    group_parser = subparsers.add_parser('run-group', help='Provision once and capture an ordered group of pages.')
    group_parser.add_argument('group')
    group_parser.add_argument('--run-dir', required=True)
    group_parser.add_argument('--reuse', action='store_true', help='Explicitly reuse a ready lab with matching configuration.')
    group_parser.add_argument('--check', action='store_true', help='Validate group files without provisioning or SSH.')
    group_parser.add_argument('--debug', action='store_true')
    group_parser.add_argument('--keep-open-on-failure', action='store_true',
                              help='Keep the browser open at a failed recipe step until Enter is pressed, before cleanup.')
    group_parser.set_defaults(ids=None, tags=None, headed=False, browser='chromium', slow_mo=0,
                              pause_before_step=False, pause_after_step=False, keep_open_on_failure=False)

    suite_parser = subparsers.add_parser('run-suite', help='Run groups sequentially, each with a fresh disposable VM.')
    suite_parser.add_argument('suite', help='Suite JSON listing group files in order.')
    suite_parser.add_argument('--run-dir', required=True, help='New directory containing separate group run directories.')
    suite_parser.add_argument('--check', action='store_true', help='Validate all groups without contacting infrastructure.')
    suite_parser.add_argument('--debug', action='store_true')
    suite_parser.add_argument('--keep-open-on-failure', action='store_true',
                              help='Keep the browser open at a failed recipe step until Enter is pressed, before cleanup.')
    suite_parser.add_argument('--resume', action='store_true', help='Resume a suite stopped at readiness checks before screenshots started.')
    suite_parser.set_defaults(reuse=False, ids=None, tags=None, headed=False, browser='chromium', slow_mo=0,
                              pause_before_step=False, pause_after_step=False, keep_open_on_failure=False)

    for lab_parser in (provision_parser, capture_parser, group_parser, suite_parser):
        lab_parser.add_argument('--keep-sudo-alive', action='store_true',
                                help='Refresh existing sudo authorization while this command runs; run sudo -v first.')

    args = parser.parse_args(argv)
    repo_root = Path(args.repo_root).resolve()

    try:
        keep_sudo_alive = getattr(args, 'keep_sudo_alive', False) and not getattr(args, 'check', False)
        with lab.sudo_session(keep_sudo_alive):
            if args.command == 'run-suite':
                return _run_suite(args, repo_root)
            if args.command == 'run-group':
                return _run_group(args, repo_root)
            if args.command == "provision":
                if args.check:
                    lab.configuration(args.config)
                    print("Local provisioning configuration OK; no infrastructure contacted.")
                else:
                    lab.provision(args.config, args.run_dir)
                return 0
            if args.command in ("status", "destroy"):
                getattr(lab, args.command)(args.run_dir)
                return 0
            if args.command == "scan":
                return _scan(args, repo_root)
            if args.command == "validate":
                return _validate(args, repo_root)
            if args.command == "qa-report":
                return _qa_report(args, repo_root)
            if args.command == "capture":
                return _capture(args, repo_root)
    except (ManifestError, CaptureError, lab.ProvisionError, OSError, ValueError, KeyError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    parser.error(f"Unknown command: {args.command}")
    return 2


def _scan(args: argparse.Namespace, repo_root: Path) -> int:
    references = scan_content(repo_root, Path(args.content_dir))
    if args.only_sunstone:
        references = [reference for reference in references if reference.sunstone_candidate]

    if args.format == "json":
        payload = [_reference_to_dict(reference) for reference in references]
        text = json.dumps(payload, indent=2)
    else:
        text = _references_to_csv(references)

    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


def _validate(args: argparse.Namespace, repo_root: Path) -> int:
    manifest_path = Path(args.manifest)
    manifest = load_manifest(manifest_path)
    errors = validate_manifest(manifest, repo_root, manifest_path)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print(f"Manifest OK: {manifest_path}")
    return 0


def _qa_report(args: argparse.Namespace, repo_root: Path) -> int:
    manifest_path = Path(args.manifest)
    manifest = load_manifest(manifest_path)
    write_qa_report(
        manifest=manifest,
        repo_root=repo_root,
        replacement_root=Path(args.replacement_root),
        output=Path(args.output),
    )
    print(f"Wrote QA report: {args.output}")
    return 0


def _capture(args: argparse.Namespace, repo_root: Path) -> int:
    manifest_path = Path(args.manifest)
    manifest = load_manifest(manifest_path)
    errors = validate_manifest(manifest, repo_root, manifest_path)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    selected = _select_screenshots(manifest, set(args.ids) if args.ids else None, set(args.tags) if args.tags else None)
    shared = [s for s in selected if s.get('sharedFrom')]
    for screenshot in shared:
        for _, image in screenshot_variants(screenshot):
            if not (Path(args.output_root) / image).is_file():
                raise CaptureError(f'Shared replacement is missing: {image}. Run its producer manifest first in the same output directory.')
    if shared:
        manifest = dict(manifest, screenshots=[s for s in manifest['screenshots'] if not s.get('sharedFrom')])
        if not any(not s.get('sharedFrom') for s in selected):
            print(f'Reused {len(shared)} shared screenshots: {manifest_path}')
            return 0

    previous = {}
    if args.run_dir:
        environment = lab.capture_environment(args.run_dir)
        previous = {key: os.environ.get(key) for key in environment}
        os.environ.update(environment)
    try:
        with workflow.guest_session(args.run_dir) if args.run_dir else nullcontext():
            if getattr(args, 'skip_hooks', False):
                print('Skipping manifest guest setup/teardown hooks; required resources must already exist. Recipe actions still run.')
                _run_capture(args, repo_root, manifest_path, manifest)
            else:
                workflow.capture_with_hooks(manifest, lambda: _run_capture(args, repo_root, manifest_path, manifest), manifest_path)
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
    return 0


def _run_group(args, repo_root):
    config, manifests, destroy_on_success = workflow.load_group(args.group, repo_root)
    if args.check:
        policy = 'destroy lab after success' if destroy_on_success else 'retain lab'
        print(f'Group OK: {len(manifests)} page manifests; {policy}; no infrastructure contacted.')
        return 0
    run_dir = Path(args.run_dir).resolve()
    resuming = getattr(args, 'resume', False) and (run_dir / 'state.json').is_file()
    if resuming and (run_dir / 'workflow.json').exists():
        raise lab.ProvisionError('Resume refuses a group whose screenshot workflows have already started.')
    if args.reuse or resuming:
        previous_workflow = run_dir / 'workflow.json'
        if previous_workflow.exists() and any(p.get('status') != 'complete' for p in lab.load(previous_workflow).get('pages', [])):
            raise lab.ProvisionError('Previous workflow did not complete; use a fresh lab to avoid carrying dirty state.')
        state = lab.load(run_dir / 'state.json')
        expected = lab.configuration(config)
        actual = dict(state['config'])
        actual['minione_script'] = actual.get('installer_url', actual['minione_script'])
        if any(actual.get(k) != v for k, v in expected.items()):
            raise lab.ProvisionError('Recorded lab must match the group provisioning configuration.')
        if resuming:
            lab.resume_readiness(run_dir)
        elif state.get('phase') != 'ready':
            raise lab.ProvisionError('Reused lab must be ready and match the group provisioning configuration.')
    else:
        lab.provision(config, run_dir)
    output = run_dir / 'screenshots'
    summary = {'group': str(Path(args.group).resolve()), 'pages': [], 'lab_status': 'retained'}
    try:
        for index, path in enumerate(manifests, 1):
            entry = {'manifest': str(path), 'status': 'running'}
            summary['pages'].append(entry)
            lab.save(run_dir / 'workflow.json', summary)
            args.manifest = str(path)
            args.output_root = str(output)
            try:
                if _capture(args, repo_root):
                    raise ManifestError(f'Capture validation failed: {path}')
                report = run_dir / 'qa' / f'{index:03d}.html'
                write_qa_report(load_manifest(path), repo_root, output, report)
                entry.update(status='complete', report=str(report))
            except BaseException:
                entry['status'] = 'failed'
                raise
        if destroy_on_success:
            summary['lab_status'] = 'destroying'
            lab.save(run_dir / 'workflow.json', summary)
            try:
                lab.destroy(run_dir)
            except BaseException:
                summary['lab_status'] = 'destroy-failed'
                raise
            summary['lab_status'] = 'destroyed'
    finally:
        lab.save(run_dir / 'workflow.json', summary)
        status = 'destroyed' if summary['lab_status'] == 'destroyed' else 'retained'
        print(f'Lab {status}; workflow results: {run_dir / "workflow.json"}')
    return 0


def _run_suite(args, repo_root):
    groups = workflow.load_suite(args.suite, repo_root)
    run_dir = Path(args.run_dir).resolve()
    resuming = getattr(args, 'resume', False)
    summary = {'version': 1, 'suite': str(Path(args.suite).resolve()), 'groups': [
        {'group': str(group), 'run_dir': str(run_dir / f'{index:02d}-{group.parent.name}'), 'status': 'pending'}
        for index, group in enumerate(groups, 1)
    ]}
    suite_path = run_dir / 'suite.json'
    if resuming:
        summary = _validate_suite_resume(lab.load(suite_path), summary)
    if args.check:
        print(f'Suite OK: {len(groups)} groups; each lab destroyed before the next provision; no infrastructure contacted.')
        return 0
    if run_dir.exists() and not resuming:
        raise lab.ProvisionError('Suite run directory already exists; choose a fresh directory.')
    # Validate local credentials for every provision before creating the first VM.
    for group, entry in zip(groups, summary['groups']):
        if entry['status'] == 'complete':
            continue
        config, _, _ = workflow.load_group(group, repo_root)
        lab.configuration(config)
    if not resuming:
        run_dir.mkdir(parents=True, mode=0o700)
    lab.save(suite_path, summary)
    try:
        for entry in summary['groups']:
            if entry['status'] == 'complete':
                print(f'Skipping completed group: {entry["group"]}', flush=True)
                continue
            entry['status'] = 'running'
            lab.save(suite_path, summary)
            print(f'Starting group: {entry["group"]}', flush=True)
            group_args = argparse.Namespace(**vars(args))
            group_args.group = entry['group']
            group_args.run_dir = entry['run_dir']
            group_args.reuse = False
            try:
                if _run_group(group_args, repo_root):
                    raise lab.ProvisionError(f'Group failed: {entry["group"]}')
                state = lab.load(Path(entry['run_dir']) / 'state.json')
                if state.get('phase') != 'destroyed':
                    raise lab.ProvisionError('Group lab was not destroyed; refusing to provision the next group.')
                entry.update(status='complete', vm_id=state['vm_id'], lab_status='destroyed')
            except BaseException:
                entry['status'] = 'failed'
                raise
            lab.save(suite_path, summary)
    finally:
        lab.save(suite_path, summary)
        print(f'Suite results: {suite_path}')
    return 0


def _validate_suite_resume(saved, expected):
    if saved.get('version') != 1 or saved.get('suite') != expected['suite']:
        raise lab.ProvisionError('Saved suite does not match the requested suite.')
    entries = saved.get('groups')
    if not isinstance(entries, list) or len(entries) != len(expected['groups']):
        raise lab.ProvisionError('Saved suite group list does not match.')
    unfinished = False
    for entry, target in zip(entries, expected['groups']):
        if entry.get('group') != target['group'] or entry.get('run_dir') != target['run_dir']:
            raise lab.ProvisionError('Saved group paths/order do not match the suite; refusing resume.')
        path = Path(entry['run_dir'])
        status = entry.get('status')
        if status == 'complete':
            state = lab.load(path / 'state.json')
            if unfinished or state.get('phase') != 'destroyed' or state.get('vm_id') != entry.get('vm_id'):
                raise lab.ProvisionError('Completed group must have its recorded VM destroyed before resume.')
            continue
        unfinished = True
        if status not in ('pending', 'failed', 'running'):
            raise lab.ProvisionError('Unexpected group status in saved suite.')
        if (path / 'workflow.json').exists():
            raise lab.ProvisionError('Resume refuses groups whose screenshot workflows have already started.')
        state_path = path / 'state.json'
        if state_path.exists():
            lab.validate_readiness_resume(lab.load(state_path))
        elif path.exists():
            raise lab.ProvisionError('Group directory exists without VM state; inspect it before retrying.')
    return saved


def _run_capture(args, repo_root, manifest_path, manifest):
    capture_screenshots(
        manifest=manifest,
        manifest_path=manifest_path,
        repo_root=repo_root,
        output_root=Path(args.output_root),
        selected_ids=set(args.ids) if args.ids else None,
        selected_tags=set(args.tags) if args.tags else None,
        headed=args.headed,
        browser_name=args.browser,
        debug=args.debug,
        slow_mo=args.slow_mo,
        pause_before_step=args.pause_before_step,
        pause_after_step=args.pause_after_step,
        keep_open_on_failure=args.keep_open_on_failure,
    )


def _reference_to_dict(reference: ImageReference) -> dict[str, object]:
    return {
        "doc": reference.doc,
        "line": reference.line,
        "kind": reference.kind,
        "alt": reference.alt,
        "sunstoneCandidate": reference.sunstone_candidate,
        "reasons": list(reference.reasons),
        "images": [
            {
                "role": variant.role,
                "rawPath": variant.raw_path,
                "assetPath": variant.asset_path,
                "exists": variant.exists,
            }
            for variant in reference.variants
        ],
    }


def _references_to_csv(references: list[ImageReference]) -> str:
    from io import StringIO

    buffer = StringIO()
    writer = csv.DictWriter(
        buffer,
        fieldnames=[
            "doc",
            "line",
            "kind",
            "alt",
            "sunstone_candidate",
            "reasons",
            "roles",
            "raw_paths",
            "asset_paths",
            "exists",
        ],
    )
    writer.writeheader()
    for reference in references:
        writer.writerow(
            {
                "doc": reference.doc,
                "line": reference.line,
                "kind": reference.kind,
                "alt": reference.alt,
                "sunstone_candidate": str(reference.sunstone_candidate).lower(),
                "reasons": "|".join(reference.reasons),
                "roles": "|".join(variant.role for variant in reference.variants),
                "raw_paths": "|".join(variant.raw_path for variant in reference.variants),
                "asset_paths": "|".join(variant.asset_path or "" for variant in reference.variants),
                "exists": "|".join(str(variant.exists).lower() for variant in reference.variants),
            }
        )
    return buffer.getvalue().rstrip("\n")
