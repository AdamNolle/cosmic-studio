"""Portable capture-gate fixtures, not compositor runtime evidence."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch
import sys

spec = importlib.util.spec_from_file_location('studio_capture_gate', Path(__file__).resolve().parents[1]/'compositor/probes/capture_gate.py')
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


class PrivateX11Guards(unittest.TestCase):
    def load(self):
        path=Path(__file__).resolve().parents[1]/'compositor/probes/run-isolated.py'
        spec=importlib.util.spec_from_file_location('studio_private_harness',path)
        module=importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules,{'capture_gate':gate}):spec.loader.exec_module(module)
        return module

    def test_desktop_display_without_owned_server_proof_rejected(self):
        harness=self.load()
        for env in ({'DISPLAY':':0'}, {'DISPLAY':'localhost:0','STUDIO_PRIVATE_X11_PID':'42'}):
            with self.subTest(env=env), self.assertRaisesRegex(ValueError,'owned private'):
                harness.private_x11(env,Path('work/private'))

    def test_authorization_outside_owned_probe_tree_rejected(self):
        harness=self.load()
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);auth=root/'desktop.auth';auth.write_bytes(b'not a real credential')
            with self.assertRaisesRegex(ValueError,'inside the owned probe tree'):
                harness.private_x11({'DISPLAY':':4','STUDIO_PRIVATE_X11_PID':'42',
                                     'XAUTHORITY':str(auth)},root/'private'/'case')


class FixtureReadiness(unittest.TestCase):
    def load(self):
        return PrivateX11Guards().load()

    def test_ready_requires_all_callbacks_and_live_fixture(self):
        harness=self.load()
        with tempfile.TemporaryDirectory() as folder:
            log=Path(folder)/'fixture.log'
            log.write_text('STUDIO_FIXTURE_READY count=3 configured=3 callbacks=3\n')
            result=harness.wait_fixture_ready(Mock(poll=Mock(return_value=None)),log,3)
            self.assertEqual(result['initial_frame_callbacks'],3)
            self.assertIn('unproven',result['scope'])
            with self.assertRaisesRegex(RuntimeError,'exited'):
                harness.wait_fixture_ready(Mock(poll=Mock(return_value=0)),log,3)

    def test_old_or_partial_markers_timeout_without_capture(self):
        harness=self.load()
        with tempfile.TemporaryDirectory() as folder:
            log=Path(folder)/'fixture.log'
            for text in ('Native layer fixture: Panel+Dock, ext_background_effect_v1, SHM buffers ready\n',
                         'STUDIO_FIXTURE_READY count=3 configured=3 callbacks=2\n',
                         'STUDIO_FIXTURE_READY count=1 configured=1 callbacks=1\n'):
                log.write_text(text)
                with self.subTest(text=text),patch.object(harness.time,'monotonic',side_effect=[0,0,2]),patch.object(harness.time,'sleep'),self.assertRaisesRegex(RuntimeError,'capture not attempted'):
                    harness.wait_fixture_ready(Mock(poll=Mock(return_value=None)),log,3,timeout=1)

    def test_delayed_marker_background_only_and_log_limit(self):
        harness=self.load()
        with tempfile.TemporaryDirectory() as folder:
            log=Path(folder)/'fixture.log';log.write_text('Waiting for configure\n')
            with patch.object(harness.time,'sleep',side_effect=lambda _:log.write_text('STUDIO_FIXTURE_READY count=1 configured=1 callbacks=1\n')):
                result=harness.wait_fixture_ready(Mock(poll=Mock(return_value=None)),log,1)
                self.assertEqual(result['count'],1)
            log.write_bytes(b'x'*(2*1024*1024+1))
            with self.assertRaisesRegex(RuntimeError,'Oversized'):
                harness.wait_fixture_ready(Mock(poll=Mock(return_value=None)),log,1)

    def test_real_source_requests_callbacks_before_buffer_commit(self):
        source=(Path(__file__).resolve().parents[1]/'compositor/probes/fixture.c').read_text()
        callback=source.index('struct wl_callback *callback=wl_surface_frame(s->surface)')
        attach=source.index('wl_surface_attach(s->surface,s->buffers[0]')
        self.assertLess(callback,attach)
        self.assertIn('configured==count&&callbacks==count',source)
        self.assertIn('wl_callback_destroy(callback)',source)
        self.assertIn('return 4;',source)


class CaptureGuards(unittest.TestCase):
    def check(self, pixels, log='', header=b'P6\n16 16\n255\n'):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            (root/'frame.ppm').write_bytes(header+pixels)
            (root/'compositor.log').write_text(log)
            return gate.validate(root/'frame.ppm',root/'compositor.log')

    def test_blank_capture_rejected_despite_protocol_success(self):
        with self.assertRaisesRegex(ValueError,'Blank'):
            self.check(bytes([38,42,42])*256)

    def test_truncation_and_renderer_failures_rejected(self):
        pixels=b''.join(bytes([n,100,200]) for n in range(256))
        with self.assertRaisesRegex(ValueError,'Truncated'):
            self.check(pixels[:-1])
        for marker in ('Failed to render frame.', 'The context has been lost',
                       'Failed to submit buffer for display'):
            with self.subTest(marker=marker), self.assertRaisesRegex(ValueError,'rendering failed'):
                self.check(pixels,marker)

    def test_visible_fixture_pass_is_explicitly_limited(self):
        result=self.check(b''.join(bytes([n,100,200]) for n in range(256)))
        self.assertEqual((result['width'],result['height']),(16,16))
        self.assertIn('not optical quality',result['scope'])


if __name__=='__main__':
    unittest.main()
