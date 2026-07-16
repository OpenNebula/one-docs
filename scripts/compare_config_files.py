#!/usr/bin/env python3
"""Compare installed OpenNebula files with entries in config_files.csv.

The script only uses the Python standard library, so it can be copied to an
OpenNebula host and run there. By default it looks for config_files.csv next to
the script, then in the current directory, and finally in this repository's
assets/tables directory.
"""

from __future__ import annotations

import argparse
import csv
import fnmatch
import os
import sys
from functools import lru_cache
from pathlib import Path, PurePosixPath
from typing import Iterable, Sequence


LISTED_ETC_ROOT = PurePosixPath("/etc/one")
LISTED_REMOTES_ROOT = PurePosixPath("/var/lib/one/remotes")
LISTED_ROOTS = (LISTED_ETC_ROOT, LISTED_REMOTES_ROOT)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Compare every file below the OpenNebula /etc/one and "
            "/var/lib/one/remotes directories with the Filename patterns in "
            "config_files.csv."
        )
    )
    parser.add_argument(
        "csv_file",
        nargs="?",
        type=Path,
        help=(
            "path to config_files.csv (default: look next to the script, in "
            "the current directory, and in ../assets/tables)"
        ),
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path("/etc/one"),
        help="/etc/one directory to inspect (default: /etc/one)",
    )
    parser.add_argument(
        "--remotes-root",
        type=Path,
        default=Path("/var/lib/one/remotes"),
        help=(
            "/var/lib/one/remotes directory to inspect "
            "(default: /var/lib/one/remotes)"
        ),
    )
    return parser.parse_args(argv)


def find_csv(explicit_path: Path | None) -> Path:
    if explicit_path is not None:
        return explicit_path

    script_dir = Path(__file__).resolve().parent
    candidates = (
        script_dir / "config_files.csv",
        Path.cwd() / "config_files.csv",
        script_dir.parent / "assets" / "tables" / "config_files.csv",
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate

    locations = ", ".join(str(path) for path in candidates)
    raise FileNotFoundError(f"config_files.csv not found; checked: {locations}")


def clean_filename(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value.startswith("`") and value.endswith("`"):
        value = value[1:-1].strip()
    return value


def load_patterns(
    csv_path: Path,
) -> tuple[dict[PurePosixPath, list[PurePosixPath]], int]:
    patterns = {root: [] for root in LISTED_ROOTS}
    ignored = 0

    with csv_path.open(newline="", encoding="utf-8-sig") as csv_file:
        reader = csv.DictReader(csv_file)
        if reader.fieldnames is None or "Filename" not in reader.fieldnames:
            raise ValueError("CSV must have a 'Filename' column")

        for line_number, row in enumerate(reader, start=2):
            filename = clean_filename(row.get("Filename") or "")
            if not filename:
                continue

            listed_path = PurePosixPath(filename)
            listed_root = None
            for root in LISTED_ROOTS:
                try:
                    listed_path.relative_to(root)
                except ValueError:
                    continue
                listed_root = root
                break
            if listed_root is None:
                ignored += 1
                continue

            relative_pattern = listed_path.relative_to(listed_root)
            if relative_pattern == PurePosixPath("."):
                raise ValueError(
                    f"line {line_number}: Filename must identify a file below "
                    f"{listed_root}"
                )
            patterns[listed_root].append(relative_pattern)

    return patterns, ignored


def pattern_matches(pattern: PurePosixPath, path: PurePosixPath) -> bool:
    """Match glob syntax without allowing '*' to cross directory boundaries."""

    pattern_parts = pattern.parts
    path_parts = path.parts

    @lru_cache(maxsize=None)
    def match(pattern_index: int, path_index: int) -> bool:
        if pattern_index == len(pattern_parts):
            return path_index == len(path_parts)

        part = pattern_parts[pattern_index]
        if part == "**":
            return match(pattern_index + 1, path_index) or (
                path_index < len(path_parts)
                and match(pattern_index, path_index + 1)
            )

        return (
            path_index < len(path_parts)
            and fnmatch.fnmatchcase(path_parts[path_index], part)
            and match(pattern_index + 1, path_index + 1)
        )

    return match(0, 0)


def list_files(root: Path) -> list[PurePosixPath]:
    files: list[PurePosixPath] = []
    walk_errors: list[OSError] = []

    def record_error(error: OSError) -> None:
        walk_errors.append(error)

    for directory, _, filenames in os.walk(root, onerror=record_error):
        directory_path = Path(directory)
        for filename in filenames:
            relative_path = (directory_path / filename).relative_to(root)
            files.append(PurePosixPath(relative_path.as_posix()))

    if walk_errors:
        details = "; ".join(str(error) for error in walk_errors)
        raise OSError(f"could not inspect every directory below {root}: {details}")

    return sorted(files, key=str)


def display_paths(title: str, paths: Iterable[PurePosixPath], root: Path) -> int:
    paths = list(paths)
    print(f"\n{title} ({len(paths)}):")
    if not paths:
        print("  none")
        return 0

    for path in paths:
        print(f"  {root / Path(path.as_posix())}")
    return len(paths)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    targets = (
        (LISTED_ETC_ROOT, args.root.resolve()),
        (LISTED_REMOTES_ROOT, args.remotes_root.resolve()),
    )

    try:
        csv_path = find_csv(args.csv_file).resolve()
        patterns_by_root, ignored_rows = load_patterns(csv_path)
        for _, root in targets:
            if not root.is_dir():
                raise NotADirectoryError(
                    f"configuration root is not a directory: {root}"
                )
    except (OSError, csv.Error, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    print(f"CSV file: {csv_path}")
    roots_description = " or ".join(str(root) for root in LISTED_ROOTS)
    print(f"CSV rows outside {roots_description} ignored: {ignored_rows}")

    differences = 0
    total_files = 0
    for listed_root, root in targets:
        try:
            installed_files = list_files(root)
        except OSError as error:
            print(f"error: {error}", file=sys.stderr)
            return 2

        patterns = patterns_by_root[listed_root]
        covered_files: set[PurePosixPath] = set()
        unmatched_patterns: list[PurePosixPath] = []
        for pattern in patterns:
            matches = [
                path for path in installed_files if pattern_matches(pattern, path)
            ]
            if matches:
                covered_files.update(matches)
            else:
                unmatched_patterns.append(pattern)

        undocumented_files = [
            path for path in installed_files if path not in covered_files
        ]
        total_files += len(installed_files)

        print(f"\nConfiguration root: {root} (CSV prefix: {listed_root})")
        print(f"Installed files inspected: {len(installed_files)}")
        print(f"CSV patterns: {len(patterns)}")
        differences += display_paths(
            "Installed files not covered by the CSV", undocumented_files, root
        )
        differences += display_paths(
            "CSV patterns that matched no installed file", unmatched_patterns, root
        )

    print(f"\nTotal installed files inspected: {total_files}")

    if differences:
        print("\nResult: differences found")
        return 1

    print("\nResult: all installed files and CSV patterns match")
    return 0


if __name__ == "__main__":
    sys.exit(main())
