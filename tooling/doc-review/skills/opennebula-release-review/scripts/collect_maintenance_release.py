#!/usr/bin/env python3
"""Collect all milestone issues and note references for a maintenance review."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.error import HTTPError

from collect_release_issues import get_json, pages, parse_notes, resolve_milestone, ISSUE_URL


def collect(repo, milestone, notes, fetch=get_json):
    entries = parse_notes(notes)
    for entry in entries:
        heading = entry['section'].strip().lower()
        entry['section_kind'] = ('backported_features' if heading == 'backported features' else
                                 'resolved_issues' if heading == 'resolved issues' else 'other')
    records = pages(f'repos/{repo}/issues', fetch, state='all', milestone=milestone['number'], sort='created', direction='asc')
    items = {}
    excluded = []
    for item in records:
        url = f'https://github.com/{repo.lower()}/issues/{item["number"]}'
        if 'pull_request' in item:
            excluded.append(item['html_url'])
        else:
            items[url] = (item, True)
    refs = sorted({url for entry in entries for url in entry['issue_urls']})
    unavailable = []
    for url in refs:
        if url in items:
            continue
        match = ISSUE_URL.fullmatch(url)
        try:
            item = fetch(f'repos/{match[1]}/issues/{match[2]}')
        except HTTPError as exc:
            if exc.code not in (403, 404, 410):
                raise
            unavailable.append({'url': url, 'http_status': exc.code,
                                'matched_entry_ids': [e['id'] for e in entries if url in e['issue_urls']]})
            continue
        if 'pull_request' in item:
            excluded.append(item['html_url'])
        else:
            items[url] = (item, False)
    issues = []
    groups = {k: [] for k in ('matched_issues', 'matched_backported_features',
                              'unmatched_issues', 'unmatched_backported_features', 'unclassified')}
    for url, (item, in_milestone) in sorted(items.items()):
        match = ISSUE_URL.fullmatch(url)
        comments = pages(f'repos/{match[1]}/issues/{match[2]}/comments', fetch) if item.get('comments') else []
        issue_type = item.get('type')
        type_name = issue_type.get('name') if isinstance(issue_type, dict) else None
        hint = {'feature': 'backported_features', 'bug': 'resolved_issues'}.get((type_name or '').lower(), 'unknown')
        matched = [e for e in entries if url in e['issue_urls']]
        sections = {e['section_kind'] for e in matched} - {'other'}
        # Existing placement routes matches; Type routes absent candidates. Neither is semantic truth.
        bucket = next(iter(sections)) if len(sections) == 1 else hint if not sections else 'unknown'
        prefix = 'matched_' if matched else 'unmatched_'
        group = prefix + ('backported_features' if bucket == 'backported_features' else 'issues') if bucket != 'unknown' else 'unclassified'
        groups[group].append(url)
        issues.append({'url': url, 'github_url': item['html_url'], 'number': item['number'],
                       'title': item['title'], 'body': item.get('body'), 'state': item['state'],
                       'state_reason': item.get('state_reason'), 'closed_at': item.get('closed_at'),
                       'updated_at': item.get('updated_at'), 'type': issue_type, 'type_name': type_name,
                       'labels': [label['name'] for label in item.get('labels', [])],
                       'milestone': item.get('milestone'), 'in_target_milestone': in_milestone,
                       'classification_hint': hint, 'provisional_group': group,
                       'type_section_conflict': bool(sections and hint != 'unknown' and sections != {hint}),
                       'matched_entry_ids': [e['id'] for e in matched],
                       'comments': [{'url': c['html_url'], 'body': c.get('body'), 'updated_at': c.get('updated_at')} for c in comments]})
    return {'mode': 'maintenance', 'repository': repo,
            'milestone': {k: milestone.get(k) for k in ('number', 'title', 'state', 'html_url')},
            'collected_at': datetime.now(timezone.utc).isoformat(),
            'collection_status': 'partial' if unavailable else 'complete',
            'notes_sha256': hashlib.sha256(notes.encode()).hexdigest(),
            'entries': entries, 'issues': issues, 'provisional_groups': groups,
            'provisional_counts': {k: len(v) for k,v in groups.items()},
            'matched_uncertainty_counts': None,
            'unavailable_references': unavailable, 'excluded_pull_requests': sorted(set(excluded)),
            'unlinked_entries': [e['id'] for e in entries if e['section_kind'] != 'other' and not e['issue_urls']],
            'limitations': ['URL matches are not confirmed semantic matches; uncertainty counts require agent review.',
                            'Feature/Bug Type is a hint, not proof of release inclusion or backport provenance.',
                            'All milestone issue states collected; open/not-planned issues are not automatically additions.',
                            'No branch, tag, PR timeline or shipped-change completeness audit performed.',
                            'Markdown/Hugo is inspected as source; conditionals are not rendered.',
                            'GitHub collection is not an atomic snapshot.']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', default='OpenNebula/one')
    selector = parser.add_mutually_exclusive_group(required=True)
    selector.add_argument('--milestone', help='Exact milestone title')
    selector.add_argument('--milestone-number', type=int)
    parser.add_argument('--notes', required=True, type=Path)
    args = parser.parse_args()
    if not re.fullmatch(r'[\w.-]+/[\w.-]+', args.repo):
        parser.error('--repo must be owner/repository')
    try:
        milestone = resolve_milestone(args.repo, args.milestone, args.milestone_number)
        result = collect(args.repo, milestone, args.notes.read_text(encoding='utf-8'))
        result['notes_path'] = str(args.notes)
    except (OSError, ValueError, KeyError) as exc:
        print(f'Collection failed: {exc}', file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 2 if result['collection_status'] == 'partial' else 0


if __name__ == '__main__':
    sys.exit(main())
