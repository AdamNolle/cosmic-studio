# Owned client XKB lookup boundary (iteration28)

Panel b5cc19e / Smithay0ff00983 (not compositor e3d461a) already publicly exports
`smithay::input::keyboard::xkb`. Its original locked xkbcommon0.9.0 archive/API
was authenticated in iteration26. No direct/absent dependency is added.

SCTK0.20 Keymap::as_string returns original compiled text-v1. Its callback docs
explicitly require independent keymap construction because its borrowed keymap
uses non-thread-safe refcounts. Safe new_from_string consumes owned String and
returns Option<Keymap>. Store only owned text in ClientSeat, not a borrowed XKB
reference, FFI pointer, non-Send keymap or unsafe Send implementation. Create
independent local keymap/state only for explicit lookups; no query per native
keypress or master-state mutation. Default includes/environment RMLVO are disabled.

SCTK applies update_mask(depressed, latched, locked, 0, 0, group) before the
modifier callback. Slave-state update_mask is supported; do not update_key or
serialize_back a master/named-only Smithay state. Preserve all three original
mask domains/layout group. Missing keymap/modifier callback is unavailable.
Raw+8 is checked, never saturated; invalid key/layout/symbol cardinality is refused.
Layout-level0 is logical/base, NOT physical identity. Multiple symbols and missing
Control indices are not invented as a single key. Full current symbols must match
the original SCTK event keysym before later consumers accept a lookup.

Control-cleared lookup removes the keymap's named Control bit independently from
all three masks, preserving every other bit and layout group. Reject if Control
remains effective (e.g. virtual dependency); do not silently label that as Iced
modified_key. This is a keysym lookup boundary, NOT full Iced conversion or a
universal virtual-modifier guarantee. Physical Code/location/named mapping,
composed text/release/repeat envelopes, live originating keyboard/focus/target,
queued-event rules and popup-grab/client press authorization remain mandatory.
SCTK UTF8 remains original; symbols are not converted back into composed text.

Keymap callback records exact source text before original server forwarding;
capability replacement/removal clears it. Leave clears event/press context but
retains the still-same keyboard's keymap; keymap change still requires fresh enter
and modifiers through the earlier fail-closed ledgers. No timer, server modifier
behavior, global entry, popup activation, hiding/config or permissions changed.
