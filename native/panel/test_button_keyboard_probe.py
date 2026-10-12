import importlib.util
import os
from pathlib import Path
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('button_diagnostic',HERE/'probes/run_button_keyboard.py')
diagnostic=importlib.util.module_from_spec(spec);spec.loader.exec_module(diagnostic)

class ButtonKeyboardProbeTests(unittest.TestCase):
    def test_root_refused_before_process_or_files(self):
        with patch.object(os,'getuid',return_value=0,create=True), patch.object(diagnostic.subprocess,'check_output') as command:
            with self.assertRaisesRegex(ValueError,'non-root'):
                diagnostic.run(Path('/unapproved'),Path('/unused'))
            command.assert_not_called()

    def test_compiler_library_and_profile_overrides_refused(self):
        for name in ('LD_PRELOAD','LD_LIBRARY_PATH','RUSTFLAGS','RUSTC_WRAPPER','CARGO_PROFILE_TEST_OPT_LEVEL','CARGO_BUILD_RUSTFLAGS'):
            with self.subTest(name=name),patch.object(os,'getuid',return_value=1000,create=True),patch.dict(os.environ,{name:'forbidden'},clear=True),patch.object(diagnostic.subprocess,'check_output') as command:
                with self.assertRaisesRegex(ValueError,'override'):
                    diagnostic.run(Path('/unapproved'),Path('/unused'))
                command.assert_not_called()

    def test_wrong_prior_build_path_refused_before_process(self):
        with patch.object(os,'getuid',return_value=1000,create=True),patch.dict(os.environ,{},clear=True),patch.object(diagnostic.subprocess,'check_output') as command:
            with self.assertRaises(ValueError):
                diagnostic.run(Path('/unapproved'),Path('/unused'))
            command.assert_not_called()

    def test_real_widget_probe_is_not_mock_callback_or_grab(self):
        text=(HERE/'probes/overflow_button_keyboard.rs').read_text(encoding='utf-8')
        self.assertEqual(text.count('#[test]'),6)
        for required in ('cosmic::widget::button::custom(','.as_widget_mut().update(', 'focusable::focus::<()>', 'focusable::unfocus::<()>', 'Key::Character(" ".into())'):
            self.assertIn(required,text)
        for forbidden in ('impl Widget', 'WlKeyboard', 'last_pointer_press', 'SERIAL_COUNTER', '.grab(', 'unsafe ', 'Named::Space'):
            self.assertNotIn(forbidden,text)

    def test_driver_preserves_actual_feature_artifact_and_inputs(self):
        text=(HERE/'probes/run_button_keyboard.py').read_text(encoding='utf-8')
        for required in ('sorted(artifacts[0][\'features\']) != sorted(features)', "row['target']['kind'] == ['lib']", "dependency-inputs-before.json", "dependency-inputs-after.json", "before == after", "output.exists()", "'candidate_runtime_pass':False", "'final_desktop_complete':False"):
            self.assertIn(required,text)
        self.assertEqual(text.count('    validate_source_inputs()'),2)
        self.assertIn("report['source_inputs_unchanged'] = True",text)
        for forbidden in ("['cargo'", "['sudo'", "['flatpak'", "['git', 'apply'", 'unlink(', 'rmtree('):
            self.assertNotIn(forbidden,text)
