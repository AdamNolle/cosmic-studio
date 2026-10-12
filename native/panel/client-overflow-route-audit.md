# Actual synchronous inert overflow delivery — iteration38

This connects the **actual original SCTK callbacks** to the original-frame
converter and Iced wrapper. It does not enable keyboard activation, traversal,
recovery, hiding or deployment. The overflow view still refuses every keyboard
event before SDK/content processing. Essential recovery/auth controls stay visible.

## Native call and lock boundaries

Press/release call `route_overflow_keyboard` only after original Smithay input
returns; repeat calls it after original callback capture, without forwarding a
new server down. The original input/filter/keycode/server-serial expressions
remain exact. This caller is not in Smithay's filter/target callbacks.

The new caller refuses dead/unknown/ambiguous client keyboards/seats, mismatched
origin or stale frame, absent/grabbed server keyboard and non-overflow focus.
It requires unique same-seat active client focus, live matching outer layer,
no child/overflow popup, exactly one same-seat native focus and exactly one
mapped positive-size actual overflow element. It does not select a target by
pointer history, PID/config index/widget ID, call a fresh enter, or retarget
ordinary proxied-client keyboard events.

Smithay `is_grabbed/current_focus` and element `geometry` run **before** the
wrapper mutex. The validator does not query Smithay, geometry, another widget,
or perform synchronous native focus callbacks. Native state is immutably
borrowed, with no event-loop yield between snapshot and inert UI processing.
Conversion uses only the immutable original callback frame/masks/group/text,
explicitly for the validated internal target; ordinary proxied keys do not parse
XKB or invoke the converter.

The mandatory validator checks original origin/frame freshness, not a keyboard
popup grant. The exact OverflowButton type's dispatcher discards all outputs,
returns no task and never invokes ordinary pointer-authorized Program update.
Busy queued pointer/task/None outputs are refused without flushing or attributing
them. Wrapper housekeeping may request an ordinary redraw; it is not activation.
No authority is retained for idle/deferred work.

## Limits

This snapshot is sufficient only for synchronous **inert delivery**, not live
activation admission, consume-once press/grab/order, identical delayed surface
re-entry handling, exact server raw-mask synchronization, accessible recovery
or hardware. A future effectful path must separately establish those gates.
Message refusal after a side-effecting widget would not undo effects; unchanged
all-keyboard isolation is therefore mandatory. SDK features[] only; a11y-enabled
builds are not accepted.

Exact full prior preflight/delivery/isolation postimages, original panel HEAD/Git
blobs, contained nonsymlink sources, exclusive new module/patch, Git apply and
postimage guards remain. New generator/module fingerprints invalidate panel
only, not shared SDK. GPL authored source; original GPL/MPL/MIT licenses and
borrowed-Winit provenance, pins, locks, features and foreign graph unchanged.

Five Python source/Git cases establish exact callback positioning, guard/mutex
order, unchanged isolation, drift/refusal and fingerprints. Five authored native
cases exercise the same inert-delivery entry with the actual OverflowButton
wrapper/software UI and original converter; they do **not** instantiate live
Wayland keyboard/seat callbacks or certify desktop keyboard recovery. Native
compilation/result/provenance evidence is recorded separately in CHECKPOINT.md.
