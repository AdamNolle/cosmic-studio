# Bounded EGL/native-window diagnosis

This is bounded instrumentation/negative diagnosis, **not a rendering or desktop completion gate**.
The owned VM's pristine and Studio EGL probes still fail their strict capture gates.
Do not repeat them without call/lifetime evidence; retain every earlier failure.

## Verified loader and instrumentation

Original locked Smithay `e3d461a057ba244d213a8498ec372b0799cca103`
`src/backend/egl/ffi.rs` loads `libEGL.so.1` with libloading, resolves direct
symbols, then calls `eglGetProcAddress`. Ordinary LD_PRELOAD wrappers alone
need not observe handle-specific dlsym. Original loader SHA256:
`2a13f8e29d8c30a154af5cd23d5f072632391377a5914ec110ce647c1babe873`.

The API-only `egl-loader-canary.c` uses that same loader pattern. It never
initializes a display, native window, context or renderer. On the owned VM,
apitrace11.1 captures both QuerySurface paths; the real libEGL BAD_DISPLAY
returns and empty current context/display/draw/read remain unchanged. A separate
explicit native-window mock proves ltrace0.7.3 `-x` sees indirect symbol-entry
create/resize/destroy calls. These mock lifetime calls are **not Wayland evidence**.
The first wrapper's literal `function(` assertion failed because ltrace emits
`function@library(`; preserved raw records pass the corrected qualified-symbol
review. No renderer trial was performed for this canary.

Diagnostic tools were installed only after constrained simulation selected seven
new reviewed tools/dependencies, zero upgrades/removals. Installed versions of
all existing packages remained identical; no COSMIC, EGL driver or Xorg upgrade.
Tools are guest-development dependencies, not candidate sandbox permissions.
Full controls/simulation/install/old-new inventory/canary sources/native ELFs,
trace/dump/library-call logs and reviews remain private.

## Owned diagnostic (iteration18)

One unchanged pristine package ELF was traced inside the owned pixman-parent
private harness. Before launch, package/ELF hashes and the parent executable,
UID/PID/argv/socket ownership were verified. The tracing group alone received
30-second/64MiB/core-zero bounds; fixture, bus and parent were not traced.
An initial inherited SSH user-bus guard refusal occurred before any renderer
launch; the subsequent command explicitly unset that bus before creating the
private one. Nothing was attached to the stock desktop.

The strict image gate still fails (blank capture and fatal compositor log).
Termination interrupted a swap and a native proxy call. The original whole-stream
review correctly refuses these incomplete records; it has **not** been relaxed.
A separately labeled completed-prefix review retains the exact cut boundaries,
excluded tails and original trace/dump hashes: 309 complete EGL records and
147 complete native lifetime records. It is not complete lifetime coverage.

Observed EGL thread0 sequence: window surface creation succeeds; a damaged swap
succeeds with that surface current. Later, the last successful MakeCurrent leaves
both draw/read NULL with the same context. Plain swap then returns EGL_FALSE,
with actual caller GetError BAD_SURFACE. Recreating the same native window returns
NULL/GetError BAD_ALLOC. Later making the original surface current and swapping
succeeds again, without an observed completed-prefix destroy/terminate. This
narrows investigation to binding/age/no-damage submission; it does not prove
causation, permanent invalidation, a driver reset or EGL_CONTEXT_LOST. The initial
QuerySurface failure has no adjacent caller-observed error result and must not
be assigned an invented error from a log label. Native-window token matches the
EGL creation argument, but apitrace-index/OS-TID mapping remains unestablished.

All original trace/dumps, native probes/XML, wrapper/configuration/commands,
parent guards and cleanup evidence remain private. An external read-only review
hash-verifies them and independently rejects the capture. No trace replay or
second renderer trial followed. Next inspect original binding/no-damage logic
and buffer-age requirements before considering any narrowly scoped repair;
do not repeat an unchanged trial or certify runtime from successful later swaps.

## Source requirements and separate candidate repair (iteration19)

Original-code review plus the normative `EGL_EXT_buffer_age` specification requires
current draw-surface binding before QuerySurface. Mesa26.1.6 version-tag sources
also check that binding for plain/damaged swaps; their identity with the installed
Pop Mesa build is not established. Public references and exact hashes are retained
privately in `iteration-19-egl-reference/`. This supplies a real API requirement,
not a cross-stream PID/TID mapping or proof of a permanent invalid surface.

The candidate-only exact-source generator now restores its own window binding
before age and submission, preserving resize, damage and original Smithay. Its
first native check failed E0499 from a whole-State helper borrow. That failure is
retained; a backend-only borrow correction is replaying in an entirely fresh tree.
Three source guards pass on both platforms; the fresh corrected whole-compositor
locked check and all 12 original native tests also pass. The optimized release
completes87s/exit0; frozen ELF SHA3c3f923dce8060e4748567627af207c0e6697144aa9925e5b5ab335a61632370
and the original683 foreign dependency entries are independently verified.

Iteration20 performs one new bounded untraced repaired-candidate glass1 capture
under the same verified owned private pixman parent, new bus/HOME/XDG and child-only
30s/64MiB/core0 limits. Fixture/capture0 do not rescue the uniform1280x800 image:
unchanged strict harness1, independent rejection. The log lacks earlier
submission/BAD_SURFACE markers but still records startup driver/fallback warnings;
this is not actual caller-error/current-target/lifetime coverage or rendering.
Owned child reaped, parent stopped, private runtimes removed and independent
process scan empty. No second trial/replay follows. Next use justified call,
framebuffer/readback/damage evidence to distinguish no submission, wrong target
or capture from output failure; do not attribute a new cause from blankness alone. Any later
candidate trial needs a distinct changed-artifact manifest and unchanged strict
capture/parent/auth/cleanup gates; it must not be labeled pristine evidence.

## Separate passive GL review and fixture readiness (iteration21)

`gl_trace_review.py` is a separate bounded metadata reviewer; the EGL/native
reviewer's incomplete-tail refusal and the image gate are unchanged. It tracks
last-observed per-context read/draw FBOs, attachment arguments, read-buffer and
pack-buffer bindings. Generated apitrace `// fake` rows are not caller evidence.
`--completed-prefix` explicitly hashes the excluded tail; unknown/unthreaded or
unterminated input remains refused. Draw/blit/map/swap counts and a non-NULL PBO
mapping do not expose actual pixels, object validity or complete native lifetimes.
Missing `glGetError` records never imply GL_NO_ERROR.

One bounded passive trace of the frozen repaired candidate under the owned
private parent retained 36 draw calls, 3 blits, one ReadPixels/PBO map/unmap,
3 damaged and 52 plain swaps. The first read used FBO1/color-attachment0/PBO3,
following a window-current read-FBO0 to draw-FBO1 blit. The resulting1280x800
capture is still one RGB color and strict harness1; this is not a rendering pass.
All source/trace/protocol/capture/parent/termination evidence remains private.

The retained synthetic clients' protocol timestamps show capture.ready at
3118880.555, before the background's first buffer attach/commit at
3118890.883/3118890.938 and the later Panel/Dock commits. The harness used only
a fixed one-second sleep, not fixture readiness. This supplies a concrete
readiness deficiency for this instrumented case; it does not establish the
cause of every previous uninstrumented failure or an API-to-OS thread mapping.
The fixture now requests a frame callback before each initial buffer commit,
and emits an exact readiness marker only after all requested surfaces are
configured and their initial callbacks arrive. The harness waits boundedly for
that marker from the live fixture and refuses old/partial/missing markers,
exited fixtures and oversized logs **before attempting capture**. Callback
delivery is only a prerequisite, not presentation/pixel proof; image/fatal-log
validation stays unchanged. This source change has not yet received a new
renderer trial. Any later trial must preserve the new exact probe hashes and
all original candidate/parent/private-bus/limits/cleanup guards.

## Readiness-aware untraced synthetic frame (iteration22)

One changed-harness trial, not an unchanged renderer retry, uses the same frozen
repaired compositor SHA3c3f923d… and new exact callback-ready C probes. Independent
artifact/provenance/image review passes the unchanged strict gate:1280x800,
26,514 distinct RGB colors, three configured surfaces/initial callbacks, no fatal
frame markers. Fresh process/runtime scan verifies owned cleanup. Native PPM stays
authoritative; the separately hash-checked PNG is a lossless display derivative.
No tracer, API injection, replay, stock attachment or compositor source mutation.

This establishes one native synthetic layer/image-copy frame only—not combined
panel/apps/session compatibility, approved optical quality, scales/input/auth,
stability/performance, physical GPU/KMS/multi-monitor/DDC or complete API/lifetime
coverage. All earlier negative/interrupted evidence remains retained/refused;
readiness does not establish the cause of every earlier failure. Completion and
candidate runtime flags remain false. The preceding iteration21 section records
its historical pre-trial state, not the current result.

## Reproduction constraints

Use **one** unchanged, hash-verified pristine comp ELF initially. Do not modify
pinned compositor/Smithay sources or infer its revision from an invented version.
Run inside the existing disposable-bus/fresh-HOME/XDG private compositor harness,
with an owned verified private Weston parent (not an ordinary desktop socket).
Before launch verify parent executable/UID/PID/socket and child artifact hashes.
Do not run this command against stock DISPLAY/Wayland/bus, another VM, root or
an installed sandbox; do not disable authentication or change ptrace policy.

Only the owned compositor child—not Weston, dbus, fixtures or the stock desktop—
gets the tracing wrapper, along these lines:

```
ltrace -L -f -ttt -s 64 -F <fresh-owned-root>/ltrace.conf \
  -x 'wl_egl_window_*+wl_proxy_destroy+wl_display_disconnect' \
  -o <fresh-owned-root>/native-window.log \
  apitrace trace --api=egl --output=<fresh-owned-root>/egl.trace \
  <hash-verified-pristine-ELF> --no-xwayland
```

The config must specify correct pointer/int/void prototypes for those native
Wayland functions. Do not attach to existing processes or set persistent/global
LD_PRELOAD. Bound the owned process group to 30 seconds and every file to64MiB
(RLIMIT_FSIZE); core dumps disabled. On timeout/size limit terminate/reap only
that group, record incomplete evidence and preserve it. Preserve the trace,
not just a converted dump. Do **not** replay the trace as a rendering test.

Dump only EGL calls, with explicit thread indices, no colors or blobs:

```
apitrace dump --thread-ids=true --color=never --grep='^egl' <egl.trace> > <egl-dump.txt>
python3 native/compositor/probes/egl_trace_review.py \
  --egl-dump <egl-dump.txt> --native-dump <native-window.log> \
  --output <new-review.json>
```

Record EGL display/context/surface/native-window creation, destroy/terminate,
query/swap/recreation results and actual caller-observed GetError values.
Track current draw/read/context/display only from successful MakeCurrent and
explicit GetCurrent calls; this is last-observed binding, not object validity.
The generic Smithay ContextLost conversion is **not** actual EGL_CONTEXT_LOST.
Native Wayland proxy/window/disconnect identities belong in their separate
ltrace timeline. Apitrace thread indices are not ltrace OS PIDs/TIDs; establish
mapping/order explicitly before attributing a destruction to a fault. Do not
invent that mapping or declare complete native lifetime coverage from a few rows.

The bounded reviewer refuses unthreaded/malformed/nonmonotonic/truncated/oversized
records and never returns candidate_runtime_pass or final_desktop_complete true.
Keep the existing independent strict image/fatal-log gate unchanged. Tracing
perturbs timing; an instrumented success alone would not certify uninstrumented
rendering, combined session behavior, authentication or hardware performance.
