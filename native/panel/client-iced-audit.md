# Explicit original-client Iced conversion (iteration29)

**Metadata candidate, not routing/activation or keyboard recovery. Hiding disabled.**

- Exact panel b5cc19e / SDK23f5d63 / Iced87e1787f / panel Smithay0ff00983.
  Unchanged graph: use `cosmic::iced::keyboard` and existing public Smithay xkb0.9.
  No Winit or xkbcommon-dl dependency added.
- Original Iced Wayland keymap SHA `b9cd75a04eac85d73d4104239c2884f2dce85c302156af823f45e83748816062`:
  complete forward Linux-scancode, named-symbol and keysym-location tables,
  with original omissions/unknown handling. Adapt directly to Iced Physical/Code;
  Winit MetaLeft/Right correspond to Iced SuperLeft/Right, not legacy Meta.
  Original MIT fixture/license and "Borrowed from winit" notice retained.
- SCTK raw is already Linux scancode. Physical mapping never subtracts8;
  XKB lookup independently uses checked raw+8. Unknown scancodes preserve the
  upstream Xkb-tagged native value; special0/240 cases unchanged. This is the
  existing native identifier convention, not a new physical hardware claim.
- Logical `key` uses active-layout level0 symbol; `modified_key` uses original
  depressed/latched/locked/group state with actual Control bit cleared and
  residual-Control refusal. Current all-modifier symbol must match SCTK.
  Location uses current keysym table, never logical character as physical identity.
  No universal virtual-modifier/layout or Winit behavioral equivalence claimed.
- Symbol-to-character uses **existing safe** xkb0.9 `keysym_to_utf8`, which
  already excludes NUL. Original Iced Wayland `sctk_event.rs` blindly pops its
  last character and sets modified_key to key with a Ctrl TODO; those defects
  are not copied. Preserve Unicode exactly; unknown/dead symbol remains
  Unidentified where no character/name exists. Character is not composed text.
- Named original callback maps SHIFT/CTRL/ALT/LOGO/CAPS_LOCK. Iced has no NumLock
  flag: retain it and raw masks/group in original frame, do not alias it.
  Missing callback remains an error, measured all-zero remains all-zero.
- Original SCTK UTF8 supplies pressed/repeat text, including None versus empty.
  Release has no Iced text/repeat fields; its original payload stays immutable
  in envelope. Only original `Kind::Repeat` sets repeat. No timers or new press.
- `ClientSeat::iced_key_event` is explicit and read-only. Result privately owns
  original immutable frame plus Iced event; Debug logs neither. Currentness
  required at conversion only, not later queue validity. No native callback
  invokes conversion, no per-ordinary-key map parsing or changed forwarding.

## Remaining gates

The explicit converter retains latest-only provenance, **not** FIFO dispatch,
keyboard/target/grab authority, live admission or held-key activation. Routing
must separately preserve actual keyboard/origin/client serial/time and validate
live focus/seat/keyboard/target/modifier/event order/client press/grab. Original
session-lock/exclusive-layer/popup-root/leaf/grab and pointer serial paths remain.
Actual keyboard-only entry, cached-widget focus, Enter/Space/Tab/Escape,
traversal/restoration/accessibility/runtime and persistent config identity remain
open. Build/unit/source evidence does not justify enabling manual hiding.
