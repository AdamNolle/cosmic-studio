# Exact native keyboard API audit — iteration26

Scope: original panel b5cc19e351b82eed999097ced1ff267d27bf8e7a,
SDK23f5d63fed2a370f3c2f54b90ec8f0896fe82105, Iced87e1787fbb9b924576e6f6ea2ef2f45d0729e63d,
panel Smithay0ff00983b6007257a7a161a4fe8b14a778e2ac8f. Not compositor Smithay.
Original Git/locked registry archive bytes/licenses are externally retained in
`iteration-26-key-api` (54 files); no dependency or installed source changes.

## Findings

- Original Iced `winit/src/platform_specific/wayland/keymap.rs` exists. Functions
  `raw_keycode_to_physicalkey`, `scancode_to_physicalkey`, `keysym_to_key` and
  location logic are available as source, not proven importable panel APIs.
  Physical conversion returns Winit types and keysym conversion imports
  xkbcommon-dl. Original panel lock has neither Winit nor xkbcommon-dl. Do not add
  those dependencies/features to pretend the existing converters are callable.
- Raw keycode namespace is evidenced, not guessed: SCTK0.20.0 enter passes
  Linux/Wayland raw values; it adds8 only for XKB symbol lookup. KeyEvent raw_code
  uses that same raw domain. Panel press/release currently add8 before Smithay;
  Smithay KeysymHandle raw_code is XKB code, raw_syms is layout-level0 logical
  identity, not physical identity. Existing dead-surface cleanup does not add8;
  that discrepancy needs a separate checked repair, not trace inference.
- Iced KeyPressed requires logical key, modified_key excluding Ctrl, physical,
  location, modifiers, text, repeat. Smithay modified_sym applies all modifiers;
  it cannot fill both logical domains. Smithay Xkb exposes unsafe borrowed
  state/keymap accessors whose refcounts must not outlive Xkb. Any fresh
  Ctrl-stripped state must obey that lifetime and preserve layout/latched/locked
  modifiers. No conversion or unsafe access has been added by this audit.
- Original locked SCTK0.20.0 checksum
  `0512da38f5e2b31201a93524adb8d3136276fa4fe4aafab4e1f727a82b534cc0`
  supplies KeyEvent keysym/UTF8, with no text on release; key processing includes
  compose state. Exact XKB0.8.0/0.9.0 and xkeysym0.2.1 archives match original
  checksums. Forwarding only a server keysym would lose original composed text.
- Original panel binds get_keyboard, not get_keyboard_with_repeat. Its repeat
  callback is a TODO, and repeat source setup must be coordinated explicitly;
  ordinary presses are not repeat events. Do not send another Smithay key-down
  just to label repeat. Enter's held raw list is currently ignored by the panel.
- Existing client handler selects the exact keyboard SeatPair and receives
  original client press serial/time; then generates a separate server serial
  for Smithay input. The latter is not client popup-grab authority. Original
  overflow still selects first-seat pointer serial and emits messages without
  keyboard provenance; that remains unmodified and unaccepted for keyboard use.

## Safe next prerequisite

Capture held raw keys and immutable original-client press provenance per actual
ClientSeat, with fresh focus lifetime, duplicate/repeat non-arming, release/leave/
keymap/capability/seat-removal invalidation. Preserve original ordinary input
forwarding and last-press behavior. This ledger does not convert keys, forward
Iced events, activate/grab popups, claim global entry/traversal/restoration, or
provide persistent applet identity. It must be compiled/tested with actual callers
before later event/activation integration. Manual hiding remains disabled.
