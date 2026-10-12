import importlib.util
from pathlib import Path
import unittest

source = Path(__file__).resolve().parents[1]/'compositor/probes/egl_trace_review.py'
spec = importlib.util.spec_from_file_location('egl_trace_review', source)
review = importlib.util.module_from_spec(spec)
spec.loader.exec_module(review)


class EGLTraceReviewTests(unittest.TestCase):
    def test_current_draw_read_follow_only_successful_native_calls(self):
        text = '''0 @0 eglMakeCurrent(dpy = 0x10, draw = 0x20, read = 0x21, ctx = 0x30) = EGL_TRUE
2 @0 eglMakeCurrent(dpy = 0x40, draw = 0x50, read = 0x51, ctx = 0x60) = EGL_FALSE
3 @0 eglQuerySurface(dpy = 0x10, surface = 0x20, attribute = EGL_BUFFER_AGE_EXT, value = &0) = EGL_FALSE
4 @0 eglGetError() = EGL_BAD_SURFACE
5 @1 eglGetError() = EGL_CONTEXT_LOST
'''
        result = review.review(text, '')
        self.assertEqual(result['first_target_error']['current_before'],
                         {'dpy': '0x10', 'draw': '0x20', 'read': '0x21', 'ctx': '0x30'})
        self.assertTrue(result['actual_egl_context_lost'])
        self.assertEqual(result['faults'][1]['current_before']['ctx'], 'unknown')
        self.assertFalse(result['candidate_runtime_pass'])
        self.assertFalse(result['final_desktop_complete'])

    def test_qualified_native_symbols_and_no_invented_thread_mapping(self):
        native = '''123 1791688267.1 wl_egl_window_create@libwayland-egl.so.1(0x10, 1, 1) = 0x20
123 1791688267.2 wl_egl_window_resize@libwayland-egl.so.1(0x20, 2, 2, 0, 0) = <void>
123 1791688267.3 wl_egl_window_destroy@libwayland-egl.so.1(0x20) = <void>
123 1791688267.4 +++ exited (status 0) +++
'''
        result = review.review('0 @0 eglGetError() = EGL_BAD_ALLOC\n', native)
        self.assertEqual(result['native_lifetime_call_count'], 3)
        self.assertEqual(result['native_window_events'][0]['library'], 'libwayland-egl.so.1')
        self.assertFalse(result['actual_egl_context_lost'])
        self.assertFalse(result['native_window_lifetime_complete'])
        self.assertIn('unestablished', result['pid_to_apitrace_thread_mapping'])

    def test_surfaceless_swap_error_does_not_prove_destroyed_surface(self):
        # Source-only regression for the observed pristine trace pattern; not
        # replay, a renderer fixture or permission to accept interrupted tails.
        text = '''0 @0 eglCreatePlatformWindowSurfaceEXT(dpy = 0x10, config = 0x40, native_window = 0x50, attrib_list = {}) = 0x20
1 @0 eglMakeCurrent(dpy = 0x10, draw = 0x20, read = 0x20, ctx = 0x30) = EGL_TRUE
2 @0 eglSwapBuffersWithDamageKHR(dpy = 0x10, surface = 0x20, rects = {}, n_rects = 1) = EGL_TRUE
3 @0 eglMakeCurrent(dpy = 0x10, draw = NULL, read = NULL, ctx = 0x30) = EGL_TRUE
4 @0 eglSwapBuffers(dpy = 0x10, surface = 0x20) = EGL_FALSE
5 @0 eglGetError() = EGL_BAD_SURFACE
6 @0 eglCreatePlatformWindowSurfaceEXT(dpy = 0x10, config = 0x40, native_window = 0x50, attrib_list = {}) = NULL
7 @0 eglGetError() = EGL_BAD_ALLOC
8 @0 eglMakeCurrent(dpy = 0x10, draw = 0x20, read = 0x20, ctx = 0x30) = EGL_TRUE
9 @0 eglSwapBuffers(dpy = 0x10, surface = 0x20) = EGL_TRUE
'''
        result = review.review(text, '')
        self.assertEqual(result['first_target_error']['current_before']['draw'], 'NULL')
        self.assertEqual(result['first_target_error']['current_before']['ctx'], '0x30')
        self.assertEqual([s['creation_succeeded'] for s in result['surface_creation']], [True, False])
        self.assertFalse(result['actual_egl_context_lost'])
        self.assertFalse(result['native_window_lifetime_complete'])
        self.assertFalse(result['candidate_runtime_pass'])
        with self.assertRaises(ValueError):
            review.review(text+'10 @0 eglSwapBuffers(dpy = 0x10, surface = 0x20) // incomplete\n', '')

    def test_empty_unthreaded_truncated_nonmonotonic_or_oversized_evidence_is_refused(self):
        for text, native in [('', ''), ('0 eglGetError() = EGL_BAD_SURFACE', ''),
                             ('0 @0 eglGetError() = EGL_SUCCESS\n0 @0 eglGetError() = EGL_SUCCESS', ''),
                             ('0 @0 eglGetError() = EGL_SUCCESS', '123 wl_egl_window_create( <unfinished ...>')]:
            with self.subTest(text=text, native=native), self.assertRaises(ValueError):
                review.review(text, native)
        with self.assertRaises(ValueError):
            review.review('X'*(review.MAX_BYTES+1), '')


if __name__ == '__main__':
    unittest.main()
