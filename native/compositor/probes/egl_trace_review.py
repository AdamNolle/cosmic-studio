#!/usr/bin/env python3
"""Bounded read-only review of EGL/native-window tracing; never certify rendering.

Input: apitrace dump --thread-ids=true --color=never --grep=^egl, plus
ltrace -L -f -ttt -x 'wl_egl_window_*+wl_proxy_destroy+wl_display_disconnect'.
Apitrace thread indices are NOT ltrace PIDs; keep their timelines separate.
GetError rows are actual caller-observed errors, not inferred ContextLost labels.
"""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import re

MAX_BYTES = 8 * 1024 * 1024
MAX_CALLS = 16384
CALL = re.compile(r'^(\d+) @(\d+) (egl\w+)\((.*)\) = (.+)$')
WINDOW = re.compile(r'^(\d+) (\d+\.\d+) (wl_egl_window_\w+|wl_proxy_destroy|wl_display_disconnect)(?:@([^\s(]+))?\((.*)\) = (.+)$')
FAULTS = {'EGL_BAD_SURFACE', 'EGL_BAD_ALLOC', 'EGL_CONTEXT_LOST', '0x300d', '0x3003', '0x300e'}
CREATE = {'eglCreateWindowSurface', 'eglCreatePlatformWindowSurface',
          'eglCreatePlatformWindowSurfaceEXT', 'eglCreatePlatformWindowSurfaceKHR',
          'eglCreatePbufferSurface', 'eglCreatePixmapSurface'}


def bounded(text):
    if len(text.encode('utf-8')) > MAX_BYTES:
        raise ValueError('Trace dump exceeds review limit; preserve original and collect bounded evidence.')
    return text.splitlines()


def review(egl_dump, native_dump):
    calls, windows, states, surfaces = [], [], {}, []
    previous = -1
    for line in bounded(egl_dump):
        if not line.strip():
            continue
        match = CALL.fullmatch(line)
        if not match:
            raise ValueError('Unknown/unthreaded EGL dump line; no guessed identities: '+line[:120])
        number, thread, name, raw, result = match.groups()
        number = int(number)
        if number <= previous or len(calls) >= MAX_CALLS:
            raise ValueError('Non-monotonic or oversized EGL call stream.')
        previous = number
        # Extract only scalar named arguments; arrays/strings are retained raw,
        # never interpreted as pointers or used to assert ownership.
        args = dict(re.findall(r'(\w+) = (NULL|EGL_\w+|0x[0-9a-fA-F]+|-?\d+)(?=,|$)', raw))
        state = states.setdefault(thread, {'dpy': 'unknown', 'ctx': 'unknown',
                                           'draw': 'unknown', 'read': 'unknown'})
        before = deepcopy(state)
        if name == 'eglMakeCurrent' and result == 'EGL_TRUE':
            state.update({key: args.get(key, 'unknown') for key in ('dpy', 'ctx', 'draw', 'read')})
        elif name == 'eglReleaseThread' and result == 'EGL_TRUE':
            state.update({key: 'NULL' for key in state})
        elif name == 'eglGetCurrentContext':
            state['ctx'] = result
        elif name == 'eglGetCurrentDisplay':
            state['dpy'] = result
        elif name == 'eglGetCurrentSurface':
            key = {'EGL_DRAW': 'draw', 'EGL_READ': 'read'}.get(args.get('readdraw'))
            if key:
                state[key] = result
        event = {'call': number, 'thread_index': thread, 'name': name, 'args': args,
                 'raw_args': raw, 'result': result, 'current_before': before,
                 'current_after': deepcopy(state)}
        calls.append(event)
        if name in CREATE:
            surfaces.append({'call': number, 'thread_index': thread, 'display': args.get('dpy', 'unknown'),
                             'native_window': args.get('win', args.get('native_window', 'unknown')),
                             'surface': result,
                             'creation_succeeded': bool(re.fullmatch(r'0x[0-9a-fA-F]+', result)) and int(result, 16) != 0})
    if not calls or not any(c['name'] == 'eglGetError' for c in calls):
        raise ValueError('EGL calls and actual caller-observed GetError records are required.')
    for line in bounded(native_dump):
        match = WINDOW.fullmatch(line)
        if match:
            pid, timestamp, name, library, args, result = match.groups()
            windows.append({'pid_or_tid': pid, 'epoch_seconds': timestamp, 'name': name,
                            'library': library, 'raw_args': args, 'result': result})
            if len(windows) > MAX_CALLS:
                raise ValueError('Native lifetime stream exceeds review limit.')
        elif any(name in line for name in ('wl_egl_window_', 'wl_proxy_destroy', 'wl_display_disconnect')):
            raise ValueError('Incomplete/unrecognized native lifetime call; do not infer ownership.')
    faults = [c for c in calls if c['name'] == 'eglGetError' and c['result'] in FAULTS]
    return {'scope': 'Observe-only API/lifetime diagnosis, not rendering/session certification',
            'status': 'target-error-observed' if faults else 'no-target-error-observed',
            'egl_call_count': len(calls), 'native_lifetime_call_count': len(windows),
            'first_target_error': faults[0] if faults else None,
            'actual_egl_context_lost': any(c['result'] in ('EGL_CONTEXT_LOST', '0x300e') for c in faults),
            'binding_scope': 'Last observed successful MakeCurrent/GetCurrent state; not object validity proof',
            'surface_creation': surfaces,
            'lifetime_events': [c for c in calls if c['name'] in CREATE or c['name'] in
                                ('eglGetDisplay', 'eglGetPlatformDisplay', 'eglGetPlatformDisplayEXT',
                                 'eglInitialize', 'eglTerminate', 'eglCreateContext', 'eglDestroyContext',
                                 'eglDestroySurface', 'eglMakeCurrent', 'eglReleaseThread')],
            'faults': faults, 'native_window_events': windows,
            'pid_to_apitrace_thread_mapping': 'unestablished; separate streams, no invented ordering',
            'native_window_lifetime_complete': False,
            'candidate_runtime_pass': False, 'final_desktop_complete': False}


def read_bounded(path):
    if path.stat().st_size > MAX_BYTES:
        raise ValueError('Oversized trace dump; original remains preserved.')
    return path.read_text(encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--egl-dump', required=True, type=Path)
    parser.add_argument('--native-dump', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    result = review(read_bounded(args.egl_dump), read_bounded(args.native_dump))
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(json.dumps({key: result[key] for key in ('status', 'egl_call_count',
                       'native_lifetime_call_count', 'actual_egl_context_lost', 'candidate_runtime_pass')}))


if __name__ == '__main__':
    main()
