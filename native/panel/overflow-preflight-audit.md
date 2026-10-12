# Native overflow opening preflight — iteration36

This changes the **actual** `PanelSpace::toggle_overflow_popup` opening path,
not a parallel helper or keyboard dispatcher. Manual hiding/deployment remain
disabled and all overflow keyboard input remains isolated before the SDK button.

## Original defect and narrow correction

At original panel b5cc19e3, the routine closed existing popups, hid Workspaces and
created a Wayland surface **before** discovering a missing overflow ID/section
popup. Missing anchor location defaulted to zero; the parent layer was unwrapped
later. An eventual error could not undo those effects.

Opening now takes a synchronous read-only snapshot before those effects:

1. Resolve the existing overflow button and section popup by requested ID.
2. Require the anchor's actual mapped location (no zero-location fallback).
3. Require a parent layer surface whose client proxy is alive.
4. Capture existing anchor/popup geometry, retaining original `.max(1)` protocol
   clamps and all orientation/scale/gravity behavior.

Missing membership/location/parent refuses before `close_popups`, Workspaces
hiding, surface or positioner creation. Existing **force-hide or already-open**
dismissal deliberately runs first without requiring a surviving opening anchor
or parent, so recovery is not blocked by these new opening checks.

`close_popups` does not replace the layer or unmap the anchor; no callback/yield
occurs between this local snapshot and existing effects. The original seat/client
serial `grab(&seat.1, seat.0)`, protocol roles/tail, pointer path and compositor
admission rules are unchanged. Later allocation/protocol errors are **not**
transactional rollback. A live proxy is not compositor admission or protocol
success. Geometry clamps are preserved, not certified physical bounds.

## Guards and validation scope

`prepare_overflow_preflight.py` requires original HEAD, byte-exact GPL overflow
Git blob/fixture and all preceding delivery postimages, contained nonsymlink
source, exclusive patch output, real Git apply and exact final postimages.
It changes only `space/overflow.rs`. Builder fingerprints generator/fixture for
panel only, never shared SDK. Original GPL/MPL/MIT distinctions remain; full
GPL text is `pinned-keyboard-focus.LICENSE`.

Six new **Python source/Git** regressions check original failure ordering, new
ordering, recovery before opening validation, unchanged serial/geometry/protocol
tail and isolation, drift/reapply/raw-byte refusal, exclusive patch/lock retention
and panel-only fingerprints. They are not native Wayland failure-injection tests.

Fresh2997-input source archive SHA256
`98ec5ce67a615e0ce6baa09fc55056c55a4c653eb14615abba266c72464a58c4`
was verified before extraction into NEW
`/mnt/cosmic-studio-builds/studio/cosmic-studio-panel-preflight-iteration36`.
Existing locked whole-caller builder ran check/release, followed by full-bin
**77 existing native tests** (no new native popup cases), standalone context8
included, not85 distinct. All eight driver phases pass in330.30s.
Full Linux265 discovered/262 passed/3 explicit missing-Blender-export skips,
nine suites+compileall0; host panel61/prepared19 pass.
Original539 foreign graph/pins/features[]/GPL/MPL/MIT, postimages, actual
package-bin-main compiler artifact, ELF and unchanged app/SDK inventories reviewed.
These checks are compilation/source/synthetic-unit evidence, not desktop runtime.
One fresh read-only reviewer found no issues, OK with notes for ordering only;
native keyboard recovery BLOCK. Parent read complete saved report/status.
Child did not run tests or attest inventories/graph/ELFs.

Release SHA256 `7590c0b80f3f0807986bbb8d0fbe6c2a91657b5c5390e8dc0045478936a4af1b`;
app-test `a42039936adf747533a0b07dd960873f677ea6bdf1ccd3e0189f8cc70debd741`;
frozen evidence `465339e392bb562265cf98ff8c141920e1d7f8bc5c64b5e2d15ea1c876a3afb0`.

## Still open

No callback invokes the converter/UI, no consume-once keyboard lifecycle or live
originating keyboard/seat/admitted target/modifier/order/client press/grab validator
or dedicated keyboard-only dispatcher. The preflight does **not** authorize the
ordinary pointer Program path for keyboard. Deferred work still needs original
envelope/live revalidation outside Smithay locks and after element mutex release.
Real keyboard-only entry/traversal/restoration/recovery/accessibility remains
blocking before manual hiding/config migration or combined desktop acceptance.

After freeze/read-only verification, build volume has approximately20.0GB
(18.6GiB) free: **further full builds refuse the unchanged >20GiB guard**.
Root >10GiB, primary/build UUID/UID/nodev,nosuid provenance preserved. No cache,
source, failure or artifact deletion and no storage change. Read-only native-test/
hash reruns do not launch compilers and remain supported; this is not a lowered
full-build preflight. Additional storage requires an explicit operator decision.

## Bounded externally rerunnable command

Fresh Windows shell, cwd `C:/Users/adamm/Desktop/Code/cosmic-studio`, no
compiler/library/profile overrides:

```powershell
python 'C:/Users/adamm/VirtualBox VMs/COSMIC-Studio/iteration-36-review-evidence.py'
```

Seven commands: frozen archive/postimage/graph/ELF/source review; strict SSH same
native77/source61/complete inventories/volume provenance; host61/prepared19;
compileall/diffcheck (plus saved guest-checker transfer). Preserve new36 and all
prior guest roots/targets/caches/sources/frozen artifacts/logs/scripts/archives,
strict private SSH identity, original primary/build VDI and auth/config/cold recovery.
Historical current-source hash reviewers may now refuse drift; original results
remain intact. Both runtime/final flags false; this is not final desktop verification.
