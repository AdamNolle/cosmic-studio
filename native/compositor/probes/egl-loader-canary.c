/* EGL API-only canary: no display initialization, surface, context or renderer.
 * Exercise the exact dlopen/dlsym + eglGetProcAddress loading pattern used by
 * pinned Smithay. Native-window calls, when requested, use ONLY a named mock
 * library supplied by the test; they are not Wayland/protocol validation. */
#include <EGL/egl.h>
#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void *symbol(void *library, const char *name) {
    void *address = dlsym(library, name);
    if (!address) { fprintf(stderr, "missing canary API: %s\n", name); exit(2); }
    return address;
}

int main(int argc, char **argv) {
    void *library = dlopen("libEGL.so.1", RTLD_NOW | RTLD_LOCAL);
    if (!library) { fprintf(stderr, "libEGL unavailable\n"); return 2; }
    PFNEGLQUERYSURFACEPROC query = (PFNEGLQUERYSURFACEPROC)symbol(library, "eglQuerySurface");
    PFNEGLGETERRORPROC error = (PFNEGLGETERRORPROC)symbol(library, "eglGetError");
    PFNEGLGETPROCADDRESSPROC get = (PFNEGLGETPROCADDRESSPROC)symbol(library, "eglGetProcAddress");
    PFNEGLMAKECURRENTPROC current = (PFNEGLMAKECURRENTPROC)symbol(library, "eglMakeCurrent");
    PFNEGLGETCURRENTCONTEXTPROC context = (PFNEGLGETCURRENTCONTEXTPROC)symbol(library, "eglGetCurrentContext");
    PFNEGLGETCURRENTDISPLAYPROC display = (PFNEGLGETCURRENTDISPLAYPROC)symbol(library, "eglGetCurrentDisplay");
    PFNEGLGETCURRENTSURFACEPROC surface = (PFNEGLGETCURRENTSURFACEPROC)symbol(library, "eglGetCurrentSurface");
    EGLint value = 0;
    EGLBoolean first = query(EGL_NO_DISPLAY, EGL_NO_SURFACE, EGL_WIDTH, &value);
    EGLint first_error = error();
    query = (PFNEGLQUERYSURFACEPROC)get("eglQuerySurface");
    if (!query) return 3;
    EGLBoolean second = query(EGL_NO_DISPLAY, EGL_NO_SURFACE, EGL_HEIGHT, &value);
    EGLint second_error = error();
    EGLBoolean made_current = current(EGL_NO_DISPLAY, EGL_NO_SURFACE, EGL_NO_SURFACE, EGL_NO_CONTEXT);
    EGLint current_error = error();
    int empty = context() == EGL_NO_CONTEXT && display() == EGL_NO_DISPLAY
                && surface(EGL_DRAW) == EGL_NO_SURFACE && surface(EGL_READ) == EGL_NO_SURFACE;
    if (argc == 2) {
        if (!strstr(argv[1], "libstudio_window_mock.so")) return 4;
        void *mock = dlopen(argv[1], RTLD_NOW | RTLD_LOCAL);
        if (!mock) return 4;
        void *(*create)(void *, int, int) = symbol(mock, "wl_egl_window_create");
        void (*resize)(void *, int, int, int, int) = symbol(mock, "wl_egl_window_resize");
        void (*destroy)(void *) = symbol(mock, "wl_egl_window_destroy");
        void *window = create(NULL, 1, 1);
        resize(window, 2, 2, 0, 0);
        destroy(window);
        dlclose(mock);
    } else if (argc != 1) return 4;
    if (first != EGL_FALSE || second != EGL_FALSE || made_current != EGL_FALSE
        || first_error != EGL_BAD_DISPLAY || second_error != EGL_BAD_DISPLAY
        || current_error != EGL_BAD_DISPLAY || !empty) return 5;
    puts("EGL_API_CANARY_PASS: dlopen/dlsym and getProcAddress preserve BAD_DISPLAY; no renderer initialized");
    dlclose(library);
    return 0;
}
