from contextlib import redirect_stdout
from io import StringIO
import unittest
from unittest.mock import Mock, patch

from sunstone_screenshots import capture


class FailureDebugTests(unittest.TestCase):
    def test_steps_run_on_current_page_and_track_new_tabs(self):
        page, popup = Mock(), Mock()
        with patch('builtins.input', side_effect=['{"action":"click","opensPage":true}',
                                                '[{"action":"hover"},{"action":"defocus"}]', '']), \
                patch.object(capture, '_run_step', side_effect=[popup, popup, popup]) as run, \
                redirect_stdout(StringIO()):
            self.assertIs(capture._failure_debug_prompt(page), popup)
        self.assertIs(run.call_args_list[0].args[0], page)
        self.assertIs(run.call_args_list[1].args[0], popup)
        self.assertEqual(run.call_count, 3)

    def test_bad_input_and_failed_action_allow_further_testing(self):
        page = Mock()
        output = StringIO()
        with patch('builtins.input', side_effect=['bad json', '123', '[]',
                                                '{"action":"click"}', '{"action":"defocus"}', '']), \
                patch.object(capture, '_run_step', side_effect=[RuntimeError('not visible'), page]) as run, \
                redirect_stdout(output):
            self.assertIs(capture._failure_debug_prompt(page), page)
        self.assertEqual(run.call_count, 2)
        self.assertIn('not visible', output.getvalue())
        self.assertIn('Action completed: defocus', output.getvalue())

    def test_inspector_and_eof(self):
        page = Mock()
        with patch('builtins.input', side_effect=['inspect', EOFError]), redirect_stdout(StringIO()):
            self.assertIs(capture._failure_debug_prompt(page), page)
        page.pause.assert_called_once()
