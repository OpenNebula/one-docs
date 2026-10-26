from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg")

MARKDOWN_IMAGE_RE = re.compile(r"!\[([^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
SHORTCODE_IMAGE_RE = re.compile(r"{{<\s*image\b.*?>}}", re.DOTALL)
SHORTCODE_ATTR_RE = re.compile(r"([A-Za-z][A-Za-z0-9_-]*)\s*=\s*(?:\"([^\"]*)\"|'([^']*)'|([^\s>]+))")

SUNSTONE_TERMS = (
    "sunstone",
    "fireedge",
    "oneform",
    "oneprovision",
    "instantiate",
    "virtual network",
    "vm template",
    "vnc",
    "wizard",
)

CORE_CONTEXT_TERMS = (
    "sunstone",
    "fireedge",
    "oneform",
    "oneprovision",
)

SUNSTONE_PATH_TERMS = (
    "sunstone",
    "fireedge",
    "oneform",
    "oneprovision",
    "common_101_ui",
)


@dataclass(frozen=True)
class ImageVariant:
    role: str
    raw_path: str
    asset_path: str | None
    exists: bool


@dataclass(frozen=True)
class ImageReference:
    doc: str
    line: int
    kind: str
    alt: str
    variants: tuple[ImageVariant, ...]
    sunstone_candidate: bool
    reasons: tuple[str, ...]


def scan_content(repo_root: Path, content_dir: Path) -> list[ImageReference]:
    repo_root = repo_root.resolve()
    content_root = (repo_root / content_dir).resolve()
    references: list[ImageReference] = []

    for path in sorted(content_root.rglob("*.md")):
        references.extend(scan_document(repo_root, path))

    return sorted(references, key=lambda ref: (ref.doc, ref.line, ref.kind))


def scan_document(repo_root: Path, path: Path) -> list[ImageReference]:
    repo_root = repo_root.resolve()
    path = (repo_root / path).resolve()
    rel_doc = path.relative_to(repo_root).as_posix()
    text = path.read_text(encoding="utf-8")
    references = list(_scan_markdown_images(repo_root, rel_doc, text))
    references.extend(_scan_image_shortcodes(repo_root, rel_doc, text))
    return sorted(references, key=lambda ref: (ref.line, ref.kind))


def _scan_markdown_images(repo_root: Path, rel_doc: str, text: str) -> Iterable[ImageReference]:
    lines = text.splitlines()
    for match in MARKDOWN_IMAGE_RE.finditer(text):
        raw_path = _strip_image_target(match.group(2))
        if not _looks_like_image(raw_path):
            continue

        line = _line_number(text, match.start())
        variants = (_variant(repo_root, "image", raw_path),)
        candidate, reasons = _candidate_details(lines, line, variants, match.group(0))
        yield ImageReference(
            doc=rel_doc,
            line=line,
            kind="markdown",
            alt=match.group(1),
            variants=variants,
            sunstone_candidate=candidate,
            reasons=tuple(reasons),
        )


def _scan_image_shortcodes(repo_root: Path, rel_doc: str, text: str) -> Iterable[ImageReference]:
    lines = text.splitlines()
    for match in SHORTCODE_IMAGE_RE.finditer(text):
        attrs = _parse_shortcode_attrs(match.group(0))
        variants: list[ImageVariant] = []

        for role, attr in (("image", "path"), ("dark", "pathDark")):
            raw_path = attrs.get(attr)
            if raw_path and _looks_like_image(raw_path):
                variants.append(_variant(repo_root, role, raw_path))

        if not variants:
            continue

        line = _line_number(text, match.start())
        candidate, reasons = _candidate_details(lines, line, variants, match.group(0))
        yield ImageReference(
            doc=rel_doc,
            line=line,
            kind="hugo-image",
            alt=attrs.get("alt", ""),
            variants=tuple(variants),
            sunstone_candidate=candidate,
            reasons=tuple(reasons),
        )


def _parse_shortcode_attrs(shortcode: str) -> dict[str, str]:
    attrs: dict[str, str] = {}
    for match in SHORTCODE_ATTR_RE.finditer(shortcode):
        attrs[match.group(1)] = next(group for group in match.groups()[1:] if group is not None)
    return attrs


def _variant(repo_root: Path, role: str, raw_path: str) -> ImageVariant:
    asset_path = normalize_asset_path(raw_path)
    return ImageVariant(
        role=role,
        raw_path=raw_path,
        asset_path=asset_path,
        exists=bool(asset_path and (repo_root / asset_path).exists()),
    )


def normalize_asset_path(raw_path: str) -> str | None:
    path = _strip_image_target(raw_path)
    if not path or re.match(r"^[a-z][a-z0-9+.-]*:", path, re.IGNORECASE):
        return None

    if path.startswith("/images/"):
        return f"assets{path}"
    if path.startswith("images/"):
        return f"assets/{path}"
    if path.startswith("assets/images/"):
        return path
    if path.startswith("/assets/images/"):
        return path[1:]
    return path.lstrip("/")


def _strip_image_target(path: str) -> str:
    path = path.strip().strip("<>").strip("'\"")
    path = path.split("#", 1)[0].split("?", 1)[0]
    return path


def _looks_like_image(path: str) -> bool:
    clean = _strip_image_target(path).lower()
    return clean.endswith(IMAGE_EXTENSIONS)


def _line_number(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def _candidate_details(
    lines: list[str],
    line: int,
    variants: tuple[ImageVariant, ...],
    source: str,
) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    paths = " ".join((variant.asset_path or variant.raw_path).lower() for variant in variants)
    source_lower = source.lower()
    window = "\n".join(lines[max(0, line - 7) : min(len(lines), line + 6)]).lower()

    path_hits = [term for term in SUNSTONE_PATH_TERMS if term in paths]
    if path_hits:
        reasons.append(f"path:{','.join(path_hits)}")

    source_hits = [term for term in CORE_CONTEXT_TERMS if term in source_lower]
    if source_hits:
        reasons.append(f"markup:{','.join(source_hits)}")

    core_context_hits = [term for term in CORE_CONTEXT_TERMS if term in window]
    if core_context_hits:
        reasons.append(f"context-core:{','.join(core_context_hits)}")

    context_hits = [term for term in SUNSTONE_TERMS if term in window and term not in CORE_CONTEXT_TERMS]
    if (path_hits or source_hits or core_context_hits) and context_hits:
        reasons.append(f"context-nearby:{','.join(context_hits[:4])}")

    return bool(reasons), reasons
