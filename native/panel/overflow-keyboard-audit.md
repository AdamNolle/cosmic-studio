# Overflow keyboard isolation blocker (iteration33)

This is a **diagnostic**, not delivered callback routing or keyboard recovery.
Manual hiding, configuration migration and deployment remain disabled.

## Concrete behavior at the actual widget boundary

Exact SDK `23f5d63fed2a370f3c2f54b90ec8f0896fe82105`, original
`src/widget/button/widget.rs` SHA256
`e1542a78f5739904dd5f3656c8cf46c94a2455f6985f101622ff6e6a77b0f2c0`:

- Lines862–870 accept focused logical Enter, set `is_pressed=true`, publish
  `on_press`, and do not inspect `repeat`.
- There is no keyboard-release branch. A later mouse-left release can publish
  another message without a preceding pointer down when released inside the
  button (lines818–837). The probe deliberately uses an inside cursor.
- The focusable unfocus operation clears focus, not the pressed state.
- Space is logical `Key::Character(" ")`, not a nonexistent `Named::Space`.
  This original button does not activate for it.
- A real CursorLeft clears pressed state. **Do not synthesize one as a fix**:
  that would also discard genuine pointer state and fabricate input ordering.

Original panel `OverflowButton::view` directly uses this custom button with
`on_press(Message::TogglePopup)`. Its ordinary Program update still schedules
first-seat **pointer** authority. Envelope-preserving single-event dispatch alone
cannot prevent a keyboard event leaving widget state that emits a later ordinary
pointer message. A rejected repeat/message can still have processed the widget;
message refusal is not transactional rollback.

## Native diagnostic, not a copied widget implementation

`probes/overflow_button_keyboard.rs` constructs the actual SDK custom button,
real Element/Tree/layout/software renderer, applies the actual focusable
operation and invokes actual widget update. It defines no substitute Widget.
Six cases reproduce focus admission, repeat Enter output, missing Space output,
Enter-release/later-pointer output, unfocus/later-pointer output and CursorLeft
cleanup. They use synthetic Iced events, not live WlKeyboard delivery, the actual
panel OverflowButton wrapper/view, popup authorization or desktop presentation.
The custom button family is the one used by the original overflow view; the
probe does not instantiate that entire view. Space nonactivation is tested
from fresh state, not as cancellation of previously armed Enter/pointer state.

`probes/run_button_keyboard.py` links the preserved original-feature **compiled
SDK** from reviewed iteration32 using rustc `--extern cosmic=<exact rlib>` and
`-L dependency=<exact deps>`. It checks the actual original SDK widget Git blob,
app/SDK input inventory, local SDK package/compiler artifact and resolved feature
set. All1312 compiled `.rlib`/`.rmeta`/`.so` dependency files are hashed
before/after unchanged (not1312 distinct crates).
The existing app61 and original539 foreign graph are prior reviewed evidence,
not a new whole-panel build or67 distinct application tests. No Cargo/source
preparation, SDK/panel mutation, stock attachment, activation or rendering trial.

Initial native probe compilation failed because `Named::Space` does not exist.
First complete probe/driver/report/compiler log/dependency inventories remain
separate; no diagnostic cases passed in that first attempt. A fresh corrected
probe uses the actual logical character representation; six cases pass. The
fresh read-only reviewer confirmed the diagnosis and noted that the first
corrected driver checked source inputs only before execution. A separate reviewed
run rechecks original app/SDK sources afterward too; same six cases pass, with
all source inputs and1312 dependency files unchanged. First/corrected/reviewed
drivers, reports and native artifacts remain separate. These
passes establish the unsafe **existing behavior**, not acceptance of keyboard
activation. Original MPL SDK code and existing GPL/MPL/MIT licenses are unchanged;
this authored GPL diagnostic does not relicense the SDK.

## Iteration34 overflow-local fail-closed isolation

The actual OverflowButton view now wraps its original SDK button with a
panel-local delegating widget. **All keyboard events are inert before SDK
processing**; Enter/Space/repeat/release/Escape/Tab cannot contaminate pointer
pressed state. No synthetic CursorLeft, shared SDK repair, pointer-serial
keyboard activation or keyboard lifecycle/dispatcher is supplied. Real pointer
down/release, real leave cancellation, cached tree, focus operations, layout,
style/draw and original-feature widget methods remain delegated.

Eight synthetic native cases instantiate **actual OverflowButton::view**,
including pointer-down → Enter/repeat/release and pointer-down → Space/unfocus/
release. Fresh full-panel locked check/release/app69 pass (prior61 + these8;
context8 repeats included, not77 distinct). Full Linux source254/251/3, nine
suites+compileall0; host panel50/prepared19 pass. SDK features[] and original539
foreign entries/pins/licenses/postimages/compiler artifacts/inventories preserved.
The first build's check/release0 and testcompile101/E0277 remain separate:
Tree::diff required mutable widget access. Only the test's as_widget_mut call
and matching source assertion changed in a NEW fresh build.

Fresh read-only review: OK with notes for isolation only; no independent native
build attestation, unsupported a11y features not covered. **No native callback,
live originating keyboard/seat/target/press/grab authorization, keyboard-only
activation/traversal/restoration/accessibility/recovery, hiding or deployment.**
Both runtime/final flags remain false. Later work must use a dedicated keyboard
dispatcher outside Smithay locks and apply independently revalidated effects
after the element mutex releases; ordinary Program pointer authority is forbidden.

Bounded rerun, not final desktop verification:
`python 'C:/Users/adamm/VirtualBox VMs/COSMIC-Studio/iteration-34-review-evidence.py'`
in a fresh Windows shell, checkout cwd, no compiler/library/profile overrides.
Preserve first/fixed34 archives/guest roots/targets/frozen artifacts/logs and prior
sources/caches/diagnostics, strict SSH, approved mounted volume and auth/recovery.

## Next coordinated native authority seam

1. Keep the iteration34 fail-closed isolation; implement separate keyboard
   activation/lifecycle only through a dedicated authorized dispatcher. Never let
   keyboard input arm SDK pointer state or clear genuine pointer state.
2. Validate real focused widget/target membership and the originating live
   WlKeyboard/WlSeat, admitted outer layer, immutable event/order/modifier frame
   and original per-press lifetime. Reject duplicate/repeat activation **before
   widget side effects**, not only after a plain TogglePopup message appears.
3. Define Enter/Space/release/Escape/traversal semantics explicitly. Route output
   through a dedicated keyboard dispatcher, never ordinary overflow Program
   update. Keep original client serial/seat and popup-root/leaf/grab rules.
4. Collect effects without re-entering the element mutex; validate/apply native
   popup work after the wrapper releases it, outside Smithay keyboard callbacks.
   Deferred work must retain and independently revalidate the original envelope;
   task-output readiness is still not an executor or FIFO barrier.
5. Verify actual keyboard-only admission/traversal/restoration/recovery and
   accessibility before any opt-in hiding. Compilation or these six diagnostics
   cannot close those gates.

## Preserved bounded rerun

Fresh Windows shell, checkout cwd, no compiler/library/profile overrides:

```powershell
python 'C:/Users/adamm/VirtualBox VMs/COSMIC-Studio/iteration-33-review-evidence.py'
```

Requires private strict SSH config, the original mounted build volume, reviewed32
source/target/driver/frozen artifacts and first/corrected/reviewed33 diagnostic inputs,
ELF/logs/dependency inventories/archives. The command independently reviews
existing evidence and reruns the same six SDK diagnostics. It does not compile or
launch a candidate desktop. Both runtime/final flags remain false.
