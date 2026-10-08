"""Import the historical screenshot spreadsheet without treating notes as commands."""

import argparse
import csv
from pathlib import Path
from urllib.parse import urlparse


def import_inventory(source, output, repo_root):
    fields = ['title', 'source_page', 'doc', 'group', 'manifest', 'automation_status',
              'section', 'priority', 'assigned', 'manual_status', 'comments', 'sunstone_errors']
    rows = []
    section = ''
    with Path(source).open(newline='', encoding='utf-8-sig') as stream:
        for row in csv.DictReader(stream):
            title = row['Title'].strip()
            if not title:
                continue
            if not row['Page'].strip() and not row['Priority'].strip():
                section = title
                continue
            page = row['Page'].strip()
            url = urlparse(page)
            doc = ''
            status = 'needs-path'
            if url.hostname == 'docs.opennebula.io':
                parts = url.path.strip('/').split('/')[1:]
                base = Path('content').joinpath(*parts)
                for candidate in (base.with_suffix('.md'), base / '_index.md', base / 'index.md'):
                    if (repo_root / candidate).is_file():
                        doc, status = candidate.as_posix(), 'pending'
                        break
            elif url.hostname:
                status = 'external'
            rows.append(dict(zip(fields, [title, page, doc, '', '', status, section,
                row['Priority'], row['Assigned'], row['Status'], row['Comments'], row['Any Sunstone Errors?']])))
    # Never overwrite curated mappings on a later import.
    with Path(output).open('x', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    return rows


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source')
    parser.add_argument('output')
    parser.add_argument('--repo-root', type=Path, default=Path('.'))
    args = parser.parse_args()
    rows = import_inventory(args.source, args.output, args.repo_root)
    print(f'Imported {len(rows)} documentation entries.')
