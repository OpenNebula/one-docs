#!/usr/bin/env python3
"""Read GitHub milestone issues and match release-note issue URLs; never edit notes."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ISSUE_URL = re.compile(r'https?://github\.com/([\w.-]+/[\w.-]+)/issues/(\d+)(?!\d)', re.I)


def get_json(endpoint):
    headers = {'Accept': 'application/vnd.github+json', 'User-Agent': 'opennebula-release-review'}
    token = os.environ.get('GH_TOKEN') or os.environ.get('GITHUB_TOKEN')
    if token:
        headers['Authorization'] = 'Bearer ' + token
    request = Request('https://api.github.com/' + endpoint, headers=headers)
    with urlopen(request, timeout=60) as response:
        return json.load(response)


def pages(endpoint, fetch=get_json, **params):
    result = []
    page = 1
    while True:
        batch = fetch(endpoint + '?' + urlencode({**params, 'per_page': 100, 'page': page}))
        if not isinstance(batch, list):
            raise ValueError('Expected a paginated GitHub list')
        result.extend(batch)
        if len(batch) < 100:
            return result
        page += 1


def resolve_milestone(repo, title=None, number=None, fetch=get_json):
    if number is not None:
        return fetch(f'repos/{repo}/milestones/{number}')
    matches = [m for m in pages(f'repos/{repo}/milestones', fetch, state='all') if m['title'] == title]
    if len(matches) != 1:
        raise ValueError(f'Expected one exact milestone title {title!r}; found {len(matches)}. Use --milestone-number if necessary.')
    return matches[0]


def parse_notes(text):
    # Preserve line numbers while excluding comments, frontmatter, and fenced code.
    clean = re.sub(r'<!--.*?-->', lambda m: '\n' * m[0].count('\n'), text, flags=re.S)
    lines = clean.splitlines()
    refs = {}
    visible = []
    fence = None
    frontmatter = bool(lines and lines[0].strip() == '---')
    for number, line in enumerate(lines, 1):
        if frontmatter:
            if number > 1 and line.strip() == '---':
                frontmatter = False
            continue
        marker = re.match(r'^\s*(`{3,}|~{3,})', line)
        if marker:
            run = marker[1]
            if fence is None:
                fence = run
            elif run[0] == fence[0] and len(run) >= len(fence):
                fence = None
            continue
        if fence:
            continue
        definition = re.match(r'^\s*\[([^]]+)\]:\s*<?(https?://\S+?)>?(?:\s+.*)?$', line)
        if definition:
            refs[' '.join(definition[1].lower().split())] = definition[2]
            continue
        visible.append((number, line))
    entries = []
    section = 'Introduction / Highlights'
    block = []

    def flush():
        if not block:
            return
        body = '\n'.join(line for _, line in block)
        keys = set()
        for match in re.finditer(r'\[([^]]+)\](?:\[([^]]*)\])?', body):
            label = match[2] if match[2] else match[1]
            key = ' '.join(label.lower().split())
            if key in refs:
                keys.add(key)
        expanded = body + '\n' + '\n'.join(refs[k] for k in sorted(keys))
        identities = sorted({(m[1].lower(), int(m[2])) for m in ISSUE_URL.finditer(expanded)})
        entries.append({'id': f'entry-{block[0][0]}', 'section': section,
                        'start_line': block[0][0], 'end_line': block[-1][0], 'text': body,
                        'issue_urls': [f'https://github.com/{r}/issues/{n}' for r, n in identities]})
        block.clear()

    for number, line in visible:
        heading = re.match(r'^#{1,6}\s+(.+)', line)
        if heading:
            flush()
            section = heading[1].strip()
        elif not line.strip():
            flush()
        elif re.match(r'^\s*[-*+]\s+', line):
            flush()
            block.append((number, line))
        else:
            block.append((number, line))
    flush()
    return entries


def collect(repo, milestone, notes, fetch=get_json):
    entries = parse_notes(notes)
    records = pages(f'repos/{repo}/issues', fetch, state='closed', milestone=milestone['number'], sort='created', direction='asc')
    issues = []
    excluded_prs = []
    for item in records:
        if 'pull_request' in item:
            excluded_prs.append(item['html_url'])
            continue
        comments = pages(f'repos/{repo}/issues/{item["number"]}/comments', fetch) if item.get('comments', 0) else []
        url = f'https://github.com/{repo.lower()}/issues/{item["number"]}'
        matches = [e['id'] for e in entries if url in e['issue_urls']]
        issues.append({'number': item['number'], 'url': item['html_url'], 'title': item['title'],
                       'body': item.get('body'), 'state_reason': item.get('state_reason'),
                       'closed_at': item.get('closed_at'), 'updated_at': item.get('updated_at'),
                       'labels': [l['name'] for l in item.get('labels', [])],
                       'comments': [{'url': c['html_url'], 'body': c.get('body'), 'updated_at': c.get('updated_at')} for c in comments],
                       'matched_entry_ids': matches, 'match_status': 'url-match' if matches else 'needs-semantic-review'})
    known = {f'https://github.com/{repo.lower()}/issues/{i["number"]}' for i in issues}
    return {'repository': repo, 'milestone': {k: milestone.get(k) for k in ('number', 'title', 'state', 'html_url')},
            'collection_status': 'complete', 'collected_at': datetime.now(timezone.utc).isoformat(),
            'notes_sha256': hashlib.sha256(notes.encode()).hexdigest(), 'entries': entries, 'issues': issues,
            'excluded_pull_requests': excluded_prs,
            'references_outside_collected_set': sorted({u for e in entries for u in e['issue_urls']} - known),
            'limitations': ['Milestone membership and closure do not prove release inclusion.',
                            'Issue bodies and comments collected; PR diffs, timelines, Git history and backports not collected.',
                            'Markdown extraction is source-based; Hugo conditionals are not evaluated.',
                            'Collection is paginated but not an atomic snapshot of GitHub.']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', default='OpenNebula/one')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--milestone', help='Exact milestone title, e.g. 7.6.0 (not an inferred version)')
    group.add_argument('--milestone-number', type=int)
    parser.add_argument('--notes', type=Path, default=Path('content/software/release_information/release_notes/whats_new.md'))
    args = parser.parse_args()
    if not re.fullmatch(r'[\w.-]+/[\w.-]+', args.repo):
        parser.error('--repo must be owner/repository')
    try:
        notes = args.notes.read_text(encoding='utf-8')
        milestone = resolve_milestone(args.repo, args.milestone, args.milestone_number)
        report = collect(args.repo, milestone, notes)
        report['notes_path'] = str(args.notes)
    except (OSError, ValueError, KeyError, HTTPError, URLError) as exc:
        print(f'Collection failed; no complete report produced: {exc}', file=sys.stderr)
        return 1
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
