# Native callback/press pairing — iteration35

This is native **bookkeeping**, not keyboard activation or recovery. Existing
OverflowButton keyboard isolation remains inert before SDK pointer processing.
Manual hiding, config migration and deployment remain disabled/fail-visible.

## Concrete gap closed

The previous actual press callback discarded `InputLedger::press`'s original
per-press witness. The release callback retired that witness before capturing its
original event. Latest-only event context alone cannot correlate repeat/release
with the original press, and serial/time equality cannot replace allocation
identity.

`ClientSeat::key_delivery` now retains a private immutable `Delivery<WlSeat>`
pairing original `Frame` and optional `ClientPress`. Exact callbacks invoke one
coordinator before original ordinary server forwarding:

- Press: retain only the ledger's fresh press result. Duplicate down and entry-held
  keys get no fresh witness, while their original callback frame remains intact.
- Repeat: observe the held original witness without minting a press or forwarding
  another key-down. Preserve repeat callback serial/time/text separately.
- Release: clone the original witness **before** ledger retirement. Preserve the
  release frame serial/time/text; the press witness is retired, not a grant.
- Enter, matched leave, keymap/capability changes and modifiers clear the stored
  delivery. Original context/press invalidations remain. Latest-only is not FIFO.

`current_fresh_press` requires Press-kind, current original frame and current
per-press ledger token. It is a necessary freshness check only. **It is not a
consume-once activation latch, live WlKeyboard identity, admitted target, modifier
policy, event ordering or popup-grab authorization.** Invoking it twice does not
consume the token. Unknown release/repeat, mismatched origin/raw and invalid
context do not borrow another press. No client serial is normalized or replaced
with a generated server/pointer serial. Shared-reference accessors and redacted
Debug retain original text/masks/identity privacy.

## Exact source and native scope

Original panel b5cc19e3 / SDK23f5d63 / Iced87e1787 / panel Smithay0ff00983,
539 foreign dependencies, SDK features[] and existing GPL/MPL/MIT distinctions
remain. The original ordinary keycode/filter/server serial/input expressions,
keymap/modifier propagation and pointer-authorized Program path are not changed.
The latter path must never be used for keyboard activation.

`prepare_client_keyboard_delivery.py` applies after isolation using exact complete
prior postimages, original HEAD/blobs, nonsymlink contained fresh module, exclusive
patch, Git apply and postimage guards. Generator/module fingerprints are panel
only, excluded from shared SDK markers. Constructors and invalidation are patched
at actual ClientSeat seams, not an invented parallel seat or callback queue.

Fresh same-archive resumed tree: locked check/release/full-bin77 pass (69 prior
cases + eight new pairing cases). Standalone context8 repeats included cases,
not85 distinct tests. Full Linux source259 discovered/256 passed/3 explicit
missing-Blender-export skips, nine suites + compileall0. Host panel55/prepared19
pass. Exact postimages/archive/source inventories/compiler artifact/ELF/features/
foreign graph independently frozen and reviewed. These synthetic tests invoke the
production coordinator with actual SCTK KeyEvent types, not real Wayland seat
callbacks or UI/grab/recovery delivery.

Initial host SSH returned1073807364; shell tools temporarily failed, then strict
SSH refused connection. Read-only VBox inspection showed the owned VM **saved**.
Ordinary start resumed that state, without reset/discard/restore/config change.
Original report had only source55/exit0 and no native phase or end marker. No
active builder remained. Its entire source archive/guest tree and scoped external
driver/report/log/transport receipts are preserved. A NEW tree used the exact
same2992-input archive, not changed implementation or a false native-failure repair.

Fresh read-only reviewer found no issues: OK with notes for pairing/bookkeeping
only, native recovery BLOCK. Reviewer did not run native tests or attest generated
postimages/graph/ELFs; those checks are separate parent evidence.

## Still blocking actual activation

No native callback calls `ClientSeat::iced_key_event` or
`IcedElement::update_keyboard`. No Enter/Space/release/Escape/Tab lifecycle,
consume-once activation, traversal/restoration or accessibility has been delivered.
All keyboard events still stop before the original SDK overflow button.

A dedicated native caller must validate the actual originating WlKeyboard/WlSeat,
current admitted target/focus/geometry/modifiers/order and immutable per-press
lifetime **outside Smithay keyboard locks**. Apply effects only after the element
mutex releases, without synchronous element re-entry; retain and independently
revalidate deferred original envelopes. Tasks remain contextless/untrusted, and
TaskInbox readiness is not an executor/FIFO barrier.

Source inspection also confirms `space/overflow.rs::toggle_overflow_popup` closes
popups and may hide workspaces/create a surface before validating the requested
overflow element. A keyboard caller must perform full admission/target/parent/
popup checks **before invoking this effectful routine**, not rely on its eventual
missing-element error as rollback. Preserve original popup-root/leaf/grab and
compositor session-lock/exclusive-layer rules; do not retrofit authority from
first-seat pointer history or latest-event cache. Real desktop keyboard-only
entry/recovery and accessible hiding remain acceptance gates.

## Bounded externally rerunnable verification

Fresh Windows shell, cwd `C:/Users/adamm/Desktop/Code/cosmic-studio`, no
compiler/library/profile overrides:

```powershell
python 'C:/Users/adamm/VirtualBox VMs/COSMIC-Studio/iteration-35-review-evidence.py'
```

Preserve exact2992-input archive, interrupted/resumed35 guest roots, frozen native
artifacts/source/locks/features/metadata/driver logs, prior evidence/targets/caches,
strict private SSH, existing mounted build volume and original primary/auth/recovery.
This command is compilation/synthetic unit/source evidence **only**, not final
combined desktop verification. Both runtime/final flags remain false.
