# Recovery reachability: source feasibility, not live acceptance

Iteration40 leaves the compiled iteration39 candidate unchanged. Opening,
manual hiding, configuration migration and deployment remain disabled.

## Two keyboard domains

The compositor uses Smithay `e3d461a057ba244d213a8498ec372b0799cca103`;
the panel embeds `0ff00983b6007257a7a161a4fe8b14a778e2ac8f`.
An upstream popup grab is not an embedded-panel keyboard grab. Recovery requires
an upstream focused popup while the embedded keyboard has **no** target/grab.
These predicates are not contradictory.

Original compositor `src/wayland/handlers/xdg_shell/mod.rs:90–163` resolves a
layer root, then focuses `grab.current_grab()`. Original Smithay
`src/desktop/wayland/popup/grab.rs:357–362` selects the active popup, falling back
to the root only when appropriate. Original compositor
`src/shell/focus/target.rs:961–964` converts `PopupKind` to `Popup`, not LayerSurface;
its keyboard target and WaylandFocus implementations use the popup surface
(`:328–340,795–867`). `src/shell/focus/mod.rs:448` passes that focus to the keyboard.
This is a possible source path, **not proof a request was admitted or executed**.

## Actual candidate callback chain

1. Outer-layer leave while overflow exists returns before panel teardown
   (`space/wrapper_space.rs:1398–1425`). Client focus/press/context retirement
   still occurs for the matched leave.
2. Popup enter records the real same-seat client surface and starts new ledgers
   (`xdg_shell_wrapper/client/handlers/keyboard.rs:16–75`). Panel keyboard-enter
   returns None for the popup (`space/wrapper_space.rs:1428–1467`); the actual
   callback sets the embedded keyboard focus to None. This is deliberate for
   the dedicated recovery branch, not an internal widget-entry implementation.
3. A real modifiers callback must arrive after enter; enter clears prior masks.
   Missing masks cannot become zero. The original compositor Smithay Wayland
   keyboard code sends enter and modifiers to the focused client's keyboard
   (`src/wayland/seat/keyboard.rs:207–218,263–324`; focus code also dispatches
   modifiers). Nonzero lock masks, including NumLock, are conservatively refused.
4. A fresh actual Escape press captures original frame/press before the panel's
   ordinary server input and calls recovery only after that input returns
   (`keyboard.rs:137–188`). Panel Smithay's default grab delegates input;
   `KeyboardInnerHandle::input` returns for None focus and does not manufacture
   another focus (`src/input/keyboard/mod.rs:1540–1570,1645–1670`).
5. Dedicated recovery independently checks live keyboard/seat, exact active
   popup/owner, no embedded grab/focus, no ordinary popup, current fresh frame,
   conversion and known-zero masks. Only then consume and synchronously force-hide
   (`iced/overflow_keyboard_recovery.rs:77–130`). No UI mutex/ordinary Program,
   pointer serial, idle task or synthetic focus is involved.

Original compositor input filtering only uses its special Escape cancellation
for Swap/Move/Resize/Menu grabs, not PopupKeyboardGrab
(`src/input/mod.rs:2309–2317,2479–2496`). That does **not** guarantee delivery:
configured shortcuts, accessibility interception, suppressed keys, other focus
or an unadmitted grab can still prevent the callback. Preserve those controls.

Parent source inspection finds a conditional feasible path, not a proven live
path or a reason to change keyboard admission. A new read-only review timed out
before a final verdict; its partial supervisor observations are not approval.

## Required owned live evidence — still absent

Use a NEW isolated candidate runtime, never attach to stock/greeter/session
sockets. Authenticate both executable hashes, UID/PID/argv, private sockets,
original pins/graphs and fresh HOME/XDG/private bus; keep absent system bus,
30s/64MiB/core0 limits and owned-only cleanup. No global instrumentation,
protocol replay, synthesized focus/serials or permission changes.

Capture separately:

- Actual popup creation/configure/commit and original seat/grab request; local
  `grab:true` is not admission. A pointer-opened popup is at most a **recovery
  diagnostic**, never proof of keyboard-only entry.
- Real popup-specific keyboard enter, ordered subsequent original modifier masks
  and fresh Escape raw code/serial/time on that exact seat. Record held keys;
  repeat, release, duplicate down and entry-held input must not dismiss.
- Candidate route refusal/admission/consume/effect observations tied to that
  delivery. Protocol traffic alone cannot prove internal validation or consume;
  any missing internal observation stays unknown, not inferred from no errors.
- Actual native teardown and protocol role/surface destruction. PopupDone is an
  alternative path, not evidence the Escape branch ran. Final SCTK Arc release
  may be deferred; helper drop order is not observed protocol order.
- Real root enter/modifiers and recovery to the surviving same-seat mapped anchor;
  key release must not leak activation. Root restoration is not automatically
  restoration to an internal anchor. Repeat with identical re-entry, separate
  seat, changed modifiers and mixed pointer input before acceptance.
- Keyboard-only entry/traversal, accessibility and essential-control reachability
  remain separate prerequisites before any manual hiding.

A private diagnostic that cannot observe these facts must report blocked or
partial. Synthetic fixture callbacks, pixel captures, ldd, compilation and
source feasibility do not close this gate. No new runtime trial is claimed here.
