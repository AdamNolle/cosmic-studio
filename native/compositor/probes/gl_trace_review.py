#!/usr/bin/env python3
"""Passive GL/EGL metadata review, not pixel, object-validity or runtime proof.

Dump selected GL calls and EGL with explicit apitrace thread indices. Never
inject getters, errors, fences or readback; never replay. Incomplete originals
are refused. --completed-prefix explicitly excludes and hashes an entire tail.
"""
import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re

MAX_BYTES = 8 * 1024 * 1024
MAX_CALLS = 16384
CALL = re.compile(r'^(\d+) @(\d+) ((?:egl|gl)\w+)\((.*)\)(?: = (.*))?$')
SCALAR = re.compile(r'(\w+) = (NULL|(?:EGL|GL)_\w+|0x[\da-fA-F]+|-?\d+)(?=,|$)')


def review(text, *, completed_prefix=False):
    raw = text.encode('utf-8')
    if not raw or len(raw) > MAX_BYTES:
        raise ValueError('Empty/oversized GL metadata stream; preserve original.')
    if not text.endswith('\n'):
        raise ValueError('Unterminated GL metadata stream; preserve original.')
    lines = text.splitlines(keepends=True)
    boundary = next((i for i, line in enumerate(lines) if '// incomplete' in line), None)
    if boundary is not None and not completed_prefix:
        raise ValueError('Incomplete GL/EGL call; whole stream refused.')
    prefix = lines if boundary is None else lines[:boundary]
    excluded = '' if boundary is None else ''.join(lines[boundary:])
    threads, contexts, counts, events, fake = {}, {}, Counter(), [], []
    previous = -1
    for line in prefix:
        line = line.rstrip('\n\r')
        if not line.strip():
            continue
        generated = line.endswith(' // fake')
        parsed = line[:-8] if generated else line
        match = CALL.fullmatch(parsed)
        if not match:
            raise ValueError('Unknown/unthreaded GL metadata line: '+line[:120])
        number, thread, name, args_raw, result = match.groups()
        number = int(number)
        if number <= previous or sum(counts.values()) + len(fake) >= MAX_CALLS:
            raise ValueError('Non-monotonic/oversized GL call stream.')
        previous = number
        if generated:
            fake.append(number)  # apitrace-generated initial state, not caller proof
            continue
        args = dict(SCALAR.findall(args_raw))
        counts[name] += 1
        binding = threads.setdefault(thread, dict(dpy='unknown', ctx='unknown', draw='unknown', read='unknown'))
        if name == 'eglMakeCurrent' and result == 'EGL_TRUE':
            binding.update({k: args.get(k, 'unknown') for k in binding})
        elif name == 'eglReleaseThread' and result == 'EGL_TRUE':
            binding.update({k: 'NULL' for k in binding})
        elif name in ('eglGetCurrentContext', 'eglGetCurrentDisplay'):
            binding['ctx' if name.endswith('Context') else 'dpy'] = result
        elif name == 'eglGetCurrentSurface':
            key = {'EGL_DRAW': 'draw', 'EGL_READ': 'read'}.get(args.get('readdraw'))
            if key:
                binding[key] = result
        if name.startswith('egl'):
            if name.startswith('eglSwapBuffers') or name in ('eglGetError', 'eglQuerySurface'):
                events.append(dict(call=number, thread_index=thread, name=name,
                                   result=result, raw_args=args_raw, egl=deepcopy(binding)))
            continue
        # Never combine unknown contexts or equate a trace index with an OS TID.
        key = (binding['dpy'], binding['ctx'])
        if any(v in ('unknown', 'NULL', None) for v in key):
            raise ValueError('GL call lacks an observed current display/context.')
        state = contexts.setdefault(key, dict(read_fbo='unknown', draw_fbo='unknown',
                                             pack_buffer='unknown', read_buffers={}, attachments={}))
        if name == 'glBindFramebuffer':
            target = args.get('target')
            if target in ('GL_FRAMEBUFFER', 'GL_DRAW_FRAMEBUFFER'):
                state['draw_fbo'] = args.get('framebuffer', 'unknown')
            if target in ('GL_FRAMEBUFFER', 'GL_READ_FRAMEBUFFER'):
                state['read_fbo'] = args.get('framebuffer', 'unknown')
        elif name == 'glBindBuffer' and args.get('target') == 'GL_PIXEL_PACK_BUFFER':
            state['pack_buffer'] = args.get('buffer', 'unknown')
        elif name == 'glReadBuffer':
            state['read_buffers'][state['read_fbo']] = args.get('mode', 'unknown')
        elif name in ('glFramebufferTexture2D', 'glFramebufferRenderbuffer'):
            target = args.get('target')
            fbo = state['read_fbo'] if target == 'GL_READ_FRAMEBUFFER' else state['draw_fbo']
            state['attachments'].setdefault(fbo, {})[args.get('attachment', 'unknown')] = deepcopy(args)
        interesting = (name.startswith(('glDraw', 'glClear', 'glBlit', 'glReadPixels', 'glMapBuffer'))
                       or name in ('glGetError', 'glUnmapBuffer', 'glCheckFramebufferStatus'))
        if interesting:
            events.append(dict(call=number, thread_index=thread, name=name, result=result,
                               raw_args=args_raw, egl=deepcopy(binding), gl=deepcopy(state)))
    if not any(name.startswith('gl') for name in counts):
        raise ValueError('No actual GL caller records in metadata stream.')
    return dict(scope='Passive last-observed GL/EGL state only; no rendering certification',
                input_sha256=hashlib.sha256(raw).hexdigest(), function_counts=dict(counts),
                events=events, generated_fake_calls_excluded=fake,
                whole_metadata_stream_accepted=boundary is None,
                completed_prefix_only=boundary is not None,
                first_excluded_line=None if boundary is None else boundary+1,
                accepted_prefix_sha256=hashlib.sha256(''.join(prefix).encode()).hexdigest(),
                excluded_tail_bytes=len(excluded.encode()),
                excluded_tail_sha256=hashlib.sha256(excluded.encode()).hexdigest(),
                actual_gl_errors=[e for e in events if e['name']=='glGetError'],
                mapped_pixel_bytes_observed=False,
                limitations=['No actual pixels decoded or injected API calls.',
                             'Draw/blit/map/swap metadata does not prove visible content.',
                             'State is last-observed, not framebuffer/object validity.',
                             'Deletion/reuse/share-group and native lifetime completeness unestablished.',
                             'Apitrace thread indices are not OS PIDs/TIDs.',
                             'Missing glGetError records never imply GL_NO_ERROR.'],
                native_window_lifetime_complete=False, candidate_runtime_pass=False,
                final_desktop_complete=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dump', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--completed-prefix', action='store_true')
    args = parser.parse_args()
    if args.dump.stat().st_size > MAX_BYTES:
        raise ValueError('Oversized GL metadata stream.')
    with args.dump.open(encoding='utf-8', newline='') as stream:
        result = review(stream.read(), completed_prefix=args.completed_prefix)
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(json.dumps({key: result[key] for key in ('function_counts', 'whole_metadata_stream_accepted',
                      'completed_prefix_only', 'mapped_pixel_bytes_observed', 'candidate_runtime_pass')}))


if __name__ == '__main__':
    main()
