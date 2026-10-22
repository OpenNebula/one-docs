from __future__ import annotations

import html
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .manifest import screenshot_variants


def write_qa_report(
    manifest: dict[str, Any],
    repo_root: Path,
    replacement_root: Path,
    output: Path,
) -> None:
    repo_root = repo_root.resolve()
    replacement_root = replacement_root.resolve()
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    rows: list[str] = []
    missing_count = 0
    total = 0

    for screenshot in manifest.get("screenshots", []):
        if not isinstance(screenshot, dict) or screenshot.get("status") == "disabled":
            continue

        for variant, image_path in screenshot_variants(screenshot):
            total += 1
            current = repo_root / image_path
            replacement = replacement_root / image_path
            current_exists = current.exists()
            replacement_exists = replacement.exists()
            if not replacement_exists:
                missing_count += 1

            rows.append(
                _render_card(
                    screenshot=screenshot,
                    variant=variant,
                    image_path=image_path,
                    current=current,
                    replacement=replacement,
                    report_dir=output.parent,
                    current_exists=current_exists,
                    replacement_exists=replacement_exists,
                )
            )

    summary = {
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "total": total,
        "missing": missing_count,
        "replacementRoot": str(replacement_root),
        "deferred": manifest.get('deferredScreenshots', []),
    }

    output.write_text(_render_page(summary, rows), encoding="utf-8")


def _render_card(
    screenshot: dict[str, Any],
    variant: str,
    image_path: str,
    current: Path,
    replacement: Path,
    report_dir: Path,
    current_exists: bool,
    replacement_exists: bool,
) -> str:
    screenshot_id = str(screenshot.get("id", image_path))
    card_id = f"{screenshot_id}:{variant}"
    title = screenshot.get("title") or screenshot_id
    status = "ready" if replacement_exists else "missing replacement"
    status_class = "ready" if replacement_exists else "missing"

    current_img = _image_or_missing(current, report_dir, current_exists)
    replacement_img = _image_or_missing(replacement, report_dir, replacement_exists)

    meta = {
        "doc": screenshot.get("doc", ""),
        "line": screenshot.get("docLine", ""),
        "recipe": screenshot.get("recipe", ""),
        "capture": screenshot.get("capture", ""),
        "image": image_path,
    }

    return f"""
      <article class="card" data-card-id="{html.escape(card_id)}">
        <header>
          <div>
            <h2>{html.escape(str(title))}</h2>
            <p>{html.escape(screenshot_id)} · {html.escape(variant)}</p>
          </div>
          <span class="pill {status_class}">{html.escape(status)}</span>
        </header>
        <dl>
          {_meta_row("Doc", _doc_label(meta))}
          {_meta_row("Image", image_path)}
          {_meta_row("Recipe", f"{meta['recipe']}#{meta['capture']}")}
        </dl>
        <div class="compare">
          <figure>
            <figcaption>Current</figcaption>
            {current_img}
          </figure>
          <figure>
            <figcaption>Replacement</figcaption>
            {replacement_img}
          </figure>
        </div>
        <footer>
          <button type="button" data-verdict="approved">Approve</button>
          <button type="button" data-verdict="rejected">Reject</button>
          <span class="verdict" aria-live="polite"></span>
        </footer>
      </article>
    """


def _render_page(summary: dict[str, Any], rows: list[str]) -> str:
    summary_json = html.escape(json.dumps(summary, indent=2))
    deferred = summary.get('deferred', [])
    deferred_html = ''
    if deferred:
        items = ''.join(f'<li>{html.escape(item["image"])}: {html.escape(item["reason"])}</li>' for item in deferred)
        deferred_html = f'<section><h2>Deferred Screenshots</h2><ul>{items}</ul></section>'
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Sunstone Screenshot QA</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f7f8fa;
      --panel: #ffffff;
      --text: #1c2530;
      --muted: #607080;
      --border: #d9e0e7;
      --accent: #0b67c2;
      --ok: #146c43;
      --bad: #b42318;
      --warn-bg: #fff4d6;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font: 14px/1.45 system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}
    main {{
      max-width: 1600px;
      margin: 0 auto;
      padding: 24px;
    }}
    .topbar {{
      display: flex;
      align-items: end;
      justify-content: space-between;
      gap: 16px;
      margin-bottom: 18px;
    }}
    h1 {{
      margin: 0 0 6px;
      font-size: 24px;
      letter-spacing: 0;
    }}
    .topbar p {{
      margin: 0;
      color: var(--muted);
    }}
    details {{
      border: 1px solid var(--border);
      background: var(--panel);
      padding: 10px 12px;
      border-radius: 8px;
      margin-bottom: 18px;
    }}
    pre {{
      overflow: auto;
      margin: 10px 0 0;
      color: var(--muted);
    }}
    .grid {{
      display: grid;
      grid-template-columns: 1fr;
      gap: 18px;
    }}
    .card {{
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 16px;
      box-shadow: 0 1px 2px rgba(22, 34, 48, 0.06);
    }}
    .card header {{
      display: flex;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 12px;
    }}
    h2 {{
      margin: 0 0 3px;
      font-size: 16px;
      letter-spacing: 0;
    }}
    header p {{
      margin: 0;
      color: var(--muted);
      overflow-wrap: anywhere;
    }}
    .pill {{
      align-self: start;
      border-radius: 999px;
      border: 1px solid var(--border);
      padding: 3px 8px;
      white-space: nowrap;
      font-size: 12px;
      color: var(--muted);
    }}
    .pill.ready {{
      color: var(--ok);
      border-color: rgba(20, 108, 67, 0.3);
    }}
    .pill.missing {{
      color: var(--bad);
      border-color: rgba(180, 35, 24, 0.3);
      background: var(--warn-bg);
    }}
    dl {{
      display: grid;
      grid-template-columns: 80px 1fr;
      gap: 4px 10px;
      margin: 0 0 14px;
      color: var(--muted);
    }}
    dt {{ font-weight: 650; }}
    dd {{
      margin: 0;
      overflow-wrap: anywhere;
    }}
    .compare {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
    }}
    figure {{
      margin: 0;
      border: 1px solid var(--border);
      border-radius: 8px;
      overflow: hidden;
      background: #fdfefe;
      min-height: 240px;
    }}
    figcaption {{
      padding: 8px 10px;
      border-bottom: 1px solid var(--border);
      color: var(--muted);
      font-weight: 650;
    }}
    img {{
      display: block;
      width: 100%;
      height: auto;
    }}
    .missing-box {{
      display: grid;
      min-height: 220px;
      place-items: center;
      padding: 24px;
      color: var(--bad);
      text-align: center;
      overflow-wrap: anywhere;
    }}
    footer {{
      display: flex;
      align-items: center;
      gap: 8px;
      margin-top: 12px;
    }}
    button {{
      border: 1px solid var(--border);
      background: #fff;
      color: var(--text);
      border-radius: 6px;
      padding: 6px 10px;
      cursor: pointer;
    }}
    button:hover {{ border-color: var(--accent); }}
    .verdict {{
      color: var(--muted);
      margin-left: 4px;
    }}
    .card[data-verdict="approved"] {{
      border-color: rgba(20, 108, 67, 0.45);
    }}
    .card[data-verdict="rejected"] {{
      border-color: rgba(180, 35, 24, 0.45);
    }}
    @media (max-width: 900px) {{
      main {{ padding: 14px; }}
      .topbar {{ display: block; }}
      .compare {{ grid-template-columns: 1fr; }}
      dl {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <main>
    <section class="topbar">
      <div>
        <h1>Sunstone Screenshot QA</h1>
        <p>{summary["total"]} variants · {summary["missing"]} missing replacements · {len(deferred)} deferred · generated {html.escape(summary["generated"])}</p>
      </div>
    </section>
    <details>
      <summary>Run metadata</summary>
      <pre>{summary_json}</pre>
    </details>
    <section class="grid">
      {''.join(rows)}
    </section>
    {deferred_html}
  </main>
  <script>
    const keyPrefix = "sunstone-screenshot-qa:";
    for (const card of document.querySelectorAll(".card")) {{
      const key = keyPrefix + card.dataset.cardId;
      const verdict = card.querySelector(".verdict");
      const saved = localStorage.getItem(key);
      if (saved) {{
        card.dataset.verdict = saved;
        verdict.textContent = saved;
      }}
      for (const button of card.querySelectorAll("button[data-verdict]")) {{
        button.addEventListener("click", () => {{
          const value = button.dataset.verdict;
          localStorage.setItem(key, value);
          card.dataset.verdict = value;
          verdict.textContent = value;
        }});
      }}
    }}
  </script>
</body>
</html>
"""


def _image_or_missing(path: Path, report_dir: Path, exists: bool) -> str:
    if not exists:
        return f'<div class="missing-box">Missing<br>{html.escape(str(path))}</div>'
    src = os.path.relpath(path, report_dir)
    return f'<img src="{html.escape(src)}" alt="">'


def _meta_row(label: str, value: str) -> str:
    return f"<dt>{html.escape(label)}</dt><dd>{html.escape(value)}</dd>"


def _doc_label(meta: dict[str, Any]) -> str:
    line = meta.get("line")
    if line:
        return f"{meta.get('doc')}:{line}"
    return str(meta.get("doc"))
