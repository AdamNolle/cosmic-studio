# Native callback routing audit (iteration30)

This is a source audit, not desktop/input acceptance. Exact original panel
b5cc19e3, Iced87e1787f and panel-Smithay0ff00983 collections and the frozen
iteration29 postimages remain external. Compositor Smithay is different.

## Do not wire metadata directly to Enter

- `iced/state.rs::update` feeds queued events to widgets, collects plain Program
  messages and clears events before Program update. A message carries neither the
  original WlKeyboard/WlSeat nor client callback serial/press lifetime.
- `iced/elements/overflow_button.rs::Program::update` inserts an idle closure.
  That closure selects `state.server_state.seats.first()` and
  `seat.client.last_pointer_press.0`, not the originating keyboard press.
  Sending complete Iced Enter/Space metadata through this path would not fix
  authorization, and must not be accepted as keyboard activation.
- Smithay `input_intercept` locks keyboard internals across the filter;
  `input_forward` locks internals across `with_grab` and target dispatch.
  `current_focus`/`is_grabbed` also lock those internals. Do not call them
  recursively from a filter/target callback. This is source-established locking,
  not an observed runtime deadlock or permission to change the dependency.
- Original queued pointer/task messages can already exist; synchronously forcing
  Iced update does not retroactively attribute every resulting message to the
  latest keyboard context. Serial arithmetic/latest-frame identity is not FIFO,
  an originating-client grab grant, or a complete immutable event bridge.

A future route needs pre-callback live seat/keyboard/target/admission checks,
original release/repeat/text/press provenance, per-message originating keyboard
context and live deferred revalidation. Preserve original popup root/leaf/grab,
exclusive layer and session-lock admission. No new key-down as a repeat, pointer
serial substitute, global shortcut, host, config identity or hiding.

## Concrete lifecycle repair

Original leave selected the first matching surface regardless of seat/status,
invalidated the actual ClientSeat ledgers before validating the leave, and always
cleared the server keyboard focus. Two seats may share a surface; an old
LastFocused surface must not retire a newer active surface. Original press
history also selected same-seat LastFocused rows.

`prepare_client_focus_match.py` requires exact complete iteration29 postimages,
original Git HEAD/blobs/licenses, contained fresh nonsymlink module and exclusive
patch/postimage guards. `client_focus_match.rs` selects exactly one active row for
an exact seat name; leave additionally requires the original surface. Ambiguous,
absent, stale and repeated leaves return before ledger invalidation/space leave/
server set_focus. Accepted leave keeps original popup/proxy/space/set_focus paths.
Press history selects only unique active focus. Ordinary press/release input,
modifiers, repeat observation, keymap/capability invalidation, composed text and
client/server serial domains are unchanged. No callback invokes iced_key_event.

Six production helper tests and five source/Git guards cover selection, not
real Wayland multi-seat callback delivery, global reachability, popup authority,
cached widget behavior or restoration. Full application validation is separate.
Hiding and deployment remain disabled; essential recovery controls stay visible.
