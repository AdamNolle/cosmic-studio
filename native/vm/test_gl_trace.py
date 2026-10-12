"""Source-only passive GL reviewer fixtures, never real rendering evidence."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('studio_gl_trace_review', ROOT/'native/compositor/probes/gl_trace_review.py')
gl = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gl)
BIND = '1 @0 eglMakeCurrent(dpy = 0x1, draw = 0x2, read = 0x2, ctx = 0x3) = EGL_TRUE\n'


class GlMetadata(unittest.TestCase):
    def test_read_draw_and_pbo_are_distinct(self):
        result = gl.review(BIND + '2 @0 glBindFramebuffer(target = GL_FRAMEBUFFER, framebuffer = 0)\n'
                           '3 @0 glBindFramebuffer(target = GL_DRAW_FRAMEBUFFER, framebuffer = 8)\n'
                           '4 @0 glBlitFramebuffer(mask = GL_COLOR_BUFFER_BIT)\n'
                           '5 @0 glBindFramebuffer(target = GL_READ_FRAMEBUFFER, framebuffer = 8)\n'
                           '6 @0 glBindBuffer(target = GL_PIXEL_PACK_BUFFER, buffer = 9)\n'
                           '7 @0 glReadBuffer(mode = GL_COLOR_ATTACHMENT0)\n'
                           '8 @0 glReadPixels(pixels = NULL)\n')
        blit, read = result['events']
        self.assertEqual((blit['gl']['read_fbo'], blit['gl']['draw_fbo']), ('0', '8'))
        self.assertEqual(read['gl']['pack_buffer'], '9')
        self.assertEqual(read['gl']['read_buffers'], {'8': 'GL_COLOR_ATTACHMENT0'})
        self.assertFalse(result['mapped_pixel_bytes_observed'])
        self.assertFalse(result['candidate_runtime_pass'])
        self.assertEqual(result['actual_gl_errors'], [])

    def test_context_state_survives_switch_without_thread_alias(self):
        result = gl.review(BIND + '2 @0 glBindFramebuffer(target = GL_FRAMEBUFFER, framebuffer = 7)\n'
                           '3 @1 eglMakeCurrent(dpy = 0x1, draw = NULL, read = NULL, ctx = 0x4) = EGL_TRUE\n'
                           '4 @1 glDrawArrays(count = 4)\n'
                           '5 @0 glDrawArrays(count = 4)\n')
        self.assertEqual(result['events'][0]['gl']['draw_fbo'], 'unknown')
        self.assertEqual(result['events'][1]['gl']['draw_fbo'], '7')

    def test_fake_calls_are_not_application_binding_evidence(self):
        result = gl.review(BIND + '2 @0 glBindFramebuffer(target = GL_FRAMEBUFFER, framebuffer = 0) // fake\n'
                           '3 @0 glDrawArrays(count = 4)\n')
        self.assertEqual(result['generated_fake_calls_excluded'], [2])
        self.assertEqual(result['events'][0]['gl']['draw_fbo'], 'unknown')

    def test_incomplete_raw_refused_and_prefix_boundaries_preserved(self):
        text = BIND + '2 @0 glDrawArrays(count = 4)\n3 @0 eglSwapBuffers(dpy = 0x1, surface = 0x2) // incomplete\nTAIL\n'
        with self.assertRaisesRegex(ValueError, 'whole stream refused'):
            gl.review(text)
        result = gl.review(text, completed_prefix=True)
        self.assertFalse(result['whole_metadata_stream_accepted'])
        self.assertTrue(result['completed_prefix_only'])
        self.assertEqual(result['first_excluded_line'], 3)
        self.assertEqual(result['excluded_tail_bytes'], len(text.splitlines(keepends=True)[2].encode()) + 5)
        self.assertFalse(result['native_window_lifetime_complete'])

    def test_actual_error_and_mapping_are_only_observations(self):
        result = gl.review(BIND + '2 @0 glGetError() = GL_INVALID_OPERATION\n'
                           '3 @0 glMapBufferRange(target = GL_PIXEL_PACK_BUFFER, offset = 0, length = 64) = 0x1234\n')
        self.assertEqual(result['actual_gl_errors'][0]['result'], 'GL_INVALID_OPERATION')
        self.assertFalse(result['mapped_pixel_bytes_observed'])

    def test_unknown_context_unthreaded_nonmonotonic_and_limits_refused(self):
        for text in ('2 @0 glDrawArrays(count = 4)\n', '2 glDrawArrays(count = 4)\n',
                     BIND + '1 @0 glDrawArrays(count = 4)\n', BIND + '2 @0 glDrawArrays(count = 4)',
                     'x' * (gl.MAX_BYTES + 1)):
            with self.subTest(text=text[:40]), self.assertRaises(ValueError):
                gl.review(text)


if __name__ == '__main__':
    unittest.main()
