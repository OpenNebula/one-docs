import unittest
from urllib.error import HTTPError
from collect_maintenance_release import collect


def issue(n, kind=None, state='closed'):
    return {'number': n, 'html_url': f'https://github.com/O/R/issues/{n}', 'title': f'Issue {n}',
            'state': state, 'type': {'name': kind} if kind else None}


class MaintenanceTests(unittest.TestCase):
    def test_all_states_types_external_refs_and_repeated_matches(self):
        calls = []
        def fetch(url):
            calls.append(url)
            if url.startswith('repos/o/r/issues/9'):
                return issue(9, 'Bug')
            return [issue(1, 'Feature'), issue(2, 'Bug', 'open'), issue(3), issue(4, 'Feature'),
                    {**issue(5), 'pull_request': {}}]
        notes = '## Backported Features\n- Feature https://github.com/O/R/issues/1\n- Again https://github.com/O/R/issues/1\n## Resolved Issues\n- External https://github.com/O/R/issues/9\n'
        result = collect('O/R', {'number': 94}, notes, fetch)
        self.assertIn('state=all', calls[0])
        self.assertEqual(len(result['issues']), 5)
        self.assertEqual(result['provisional_counts'], {'matched_issues': 1, 'matched_backported_features': 1,
                         'unmatched_issues': 1, 'unmatched_backported_features': 1, 'unclassified': 1})
        self.assertIsNone(result['matched_uncertainty_counts'])
        self.assertEqual(len(result['issues'][0]['matched_entry_ids']), 2)
        self.assertFalse(result['issues'][-1]['in_target_milestone'])

    def test_conflicting_type_and_cross_section(self):
        notes = '## Backported Features\n- https://github.com/O/R/issues/1\n## Resolved Issues\n- https://github.com/O/R/issues/1'
        result = collect('O/R', {'number': 1}, notes, lambda _: [issue(1, 'Bug')])
        self.assertEqual(result['provisional_counts']['unclassified'], 1)
        self.assertTrue(result['issues'][0]['type_section_conflict'])

    def test_inaccessible_reference_retained(self):
        def fetch(url):
            if '?' in url:
                return []
            raise HTTPError(url, 404, 'missing', {}, None)
        result = collect('O/R', {'number': 1}, '## Resolved Issues\n- https://github.com/O/R/issues/8', fetch)
        self.assertEqual(result['collection_status'], 'partial')
        self.assertEqual(len(result['unavailable_references']), 1)

    def test_comments_and_failures(self):
        def fetch(url):
            if '/comments?' in url:
                return [{'html_url': 'comment', 'body': 'Backport pending'}]
            return [{**issue(1, 'Feature'), 'comments': 1}]
        result = collect('O/R', {'number': 1}, '', fetch)
        self.assertEqual(result['issues'][0]['comments'][0]['body'], 'Backport pending')
        with self.assertRaises(OSError):
            collect('O/R', {'number': 1}, '', lambda _: (_ for _ in ()).throw(OSError('network failure')))


if __name__ == '__main__':
    unittest.main()
