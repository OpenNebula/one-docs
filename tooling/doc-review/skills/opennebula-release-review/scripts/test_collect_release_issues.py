import unittest
from collect_release_issues import collect, pages, parse_notes, resolve_milestone


class CollectorTests(unittest.TestCase):
    def test_pagination_and_exact_title(self):
        calls = []
        def fetch(url):
            calls.append(url)
            return [{'title': 'old', 'number': i} for i in range(100)] if url.endswith('&page=1') else [{'title': '7.6', 'number': 101}]
        self.assertEqual(resolve_milestone('OpenNebula/one', title='7.6', fetch=fetch)['number'], 101)
        self.assertEqual(len(calls), 2)
        self.assertIn('state=all', calls[0])
        with self.assertRaises(ValueError):
            resolve_milestone('OpenNebula/one', title='7.6.0', fetch=lambda _: [])

    def test_url_identity_and_source_context(self):
        notes = '''---
title: Test
---
<!-- https://github.com/OpenNebula/one/issues/999 -->
## Core
- Added capability [#12](https://github.com/OpenNebula/one/issues/12#issuecomment-5).
  Continued description.
- Related [issue][ref].
- Other https://github.com/other/repo/issues/12 and https://github.com/OpenNebula/one/pull/12
```text
https://github.com/OpenNebula/one/issues/998
```
[ref]: https://github.com/OPENNEBULA/ONE/issues/12?x=1
'''
        entries = parse_notes(notes)
        self.assertEqual(len(entries), 3)
        self.assertEqual(entries[0]['start_line'], 6)
        self.assertEqual(entries[0]['end_line'], 7)
        self.assertEqual(entries[0]['section'], 'Core')
        self.assertEqual(entries[0]['issue_urls'], entries[1]['issue_urls'])
        self.assertEqual(entries[2]['issue_urls'], ['https://github.com/other/repo/issues/12'])

    def test_closed_issues_comments_and_multiple_matches(self):
        def fetch(url):
            if '/comments?' in url:
                return [{'html_url': 'comment', 'body': 'Declined', 'updated_at': 'today'}]
            return [{'number': 1, 'title': 'Request', 'html_url': 'https://github.com/O/R/issues/1', 'state_reason': 'not_planned', 'comments': 1},
                    {'number': 2, 'title': 'Feature', 'html_url': 'https://github.com/O/R/issues/2'},
                    {'number': 3, 'html_url': 'pr', 'pull_request': {}}]
        notes = '- https://github.com/O/R/issues/1\n- https://github.com/O/R/issues/1\n- https://github.com/other/repo/issues/1'
        data = collect('O/R', {'number': 4}, notes, fetch)
        self.assertEqual(len(data['issues']), 2)
        self.assertEqual(len(data['issues'][0]['matched_entry_ids']), 2)
        self.assertEqual(data['issues'][0]['state_reason'], 'not_planned')
        self.assertEqual(data['issues'][0]['comments'][0]['body'], 'Declined')
        self.assertEqual(data['issues'][1]['match_status'], 'needs-semantic-review')
        self.assertEqual(data['excluded_pull_requests'], ['pr'])
        self.assertEqual(data['references_outside_collected_set'], ['https://github.com/other/repo/issues/1'])

    def test_failure_does_not_become_empty_success(self):
        def fail(_):
            raise OSError('rate limited')
        with self.assertRaises(OSError):
            pages('repos/O/R/issues', fail)


if __name__ == '__main__':
    unittest.main()
