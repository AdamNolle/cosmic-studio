# Isolated combined startup — layer observations only

Iteration41 ran the frozen repaired compositor (`3c3f923d…`) and compiled39
panel (`f9befde5…`) together once. Neither ELF/source was changed or installed.
This is **not** a combined-desktop, rendering, keyboard-recovery or session-
compatibility acceptance result. Opening/manual hiding remain disabled.

## Isolation and exact inputs

Original panel main/config/spawn and SDK config/derive contracts were exported
from authenticated Git HEADs. Native version1 config uses the existing `Panel`
entry, OnDemand keyboard interactivity, Never autohide and empty wing/center
plugin lists. Fresh private HOME/config/data/cache/state and private data/config
search roots exclude installed applet launchers and user settings. This is an
**empty native panel**, not the configured desktop or an overflow fixture.

Exact original panel/SDK inventories, frozen ELF receipts and both existing
build-volume/root/fstab/package identities were checked before execution.
Private Weston headless/pixman/kiosk1280×800, the candidate compositor and panel
were authenticated by executable hash, UID1000, PID and exact argv. Socket
ownership plus actual SO_PEERCRED identified the Weston and candidate peers;
those validation connections sent no protocol messages. New private DBus,
deliberately absent system bus, no Xwayland, compiler/library override or stock
attachment. Renderer observation lasted8.14s within30s/64MiB-per-file/core0 limits.

## Actual preserved observations

The panel client stream records:

- A native `Panel` layer surface and OnDemand request.
- Actual `seat-0` keyboard keymap/repeat-info, then **layer-surface** enter with
  an empty held-key array and subsequent zero depressed/latched/locked/group
  masks. This is not popup enter or internal overflow-anchor focus acceptance.
- Layer configure1280×8/serial2 and acknowledgement; later configure1280×1/
  serial3 and acknowledgement. These are original protocol IDs/serials, not
  process IDs or fabricated keyboard authorization.
- A requested native frame callback, but **no observed callback completion or
  panel buffer attach** before owned termination. Buffer allocation and commit
  requests do not establish presentation.

There was no key press/release/repeat, popup creation/grab/admission, internal
validator/consume/effect attribution, protocol popup teardown or restoration.
No capture was attempted because buffer attachment was unobserved; no pixels or
optical result exist. Empty-panel behavior is not evidence that a populated
panel would behave identically or a diagnosis of the missing attach.

Private empty-system-config/locale diagnostics, EGL/driver fallback BAD_ALLOC
and the deliberately absent system-bus error remain in the original logs.
Process survival/protocol acknowledgements do not turn them into compatibility
or rendering acceptance. No unchanged renderer retry or speculative repair ran.

## Cleanup, retention and later state difference

Owned panel/compositor leaders were reaped after SIGTERM; Weston exited0. Private
runtime was removed and an independent fresh read-only scan found no owned
candidate processes. ELFs/full panel-SDK inputs remained unchanged. Stock user
configuration and state fingerprints matched **immediately after** the diagnostic.

A later strict read-only verifier refused because the current stock state
fingerprint no longer equalled its pre-diagnostic value. Complete first script,
transport, stdout/traceback and exit1 remain preserved. Cause of the subsequent
state change is **unknown**; no state was repaired or reset. A NEW evidence
checker reports immediate authenticated equality separately from the later
mismatch; it does not certify stock-state stability or accept recovery. Current
configuration still matched at that observation.

All100 regular startup archive payloads were checked against SHA256, size,
mode and original UID/GID1000. Archive SHA256:
`5ecf948809ea33a241b7dce686bb7f3bfde547803f0a0f8b4ae26c3e94ea1bb9`.
Full guest runtime evidence, private transport/contract exports, archive/external
copies, first refusal/corrected checker and all prior sources/targets/caches/
VDIs/snapshots/authentication/recovery remain retained. No native build or new
unit cases; prior app93/Linux277/274/3 coverage is unchanged.

## Scoped monitor rerun, not the final desktop command

Fresh Windows shell, cwd `C:/Users/adamm/Desktop/Code/cosmic-studio`, no
compiler/library/profile overrides:

```powershell
python 'C:/Users/adamm/VirtualBox VMs/COSMIC-Studio/iteration-41-review-evidence.py'
```

This reviews original preserved startup/ownership/raw layer observations and
runs a fresh **read-only** guest hash/inventory/storage/cleanup check. It launches
no renderer/compiler/tests and reports later state equality independently.
Retain strict installed SSH, the owned running VM/exact existing mounts and
all private receipts/scripts/evidence/native originals. Both
`candidate_runtime_pass` and `final_desktop_complete` remain false.

Next: authenticate a bounded real native applet's launch/input requirements and
observe populated native rendering/overflow in a NEW private diagnostic. No
installed-default applet queue or system-bus permission expansion. Real popup
focus/modifiers/fresh Escape/internal consumption/teardown/restoration and
keyboard-only entry/accessibility remain separate required gates.
