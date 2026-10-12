# Publication checkpoint — 2026-10-10

Work stopped at the user's request to publish the source repository. This preserves approved design and recovery tools while retaining the remaining rollout tasks.

## Iteration39 recovery-only callback and native popup teardown

The actual outside-Smithay-input route now tries a dedicated fresh Escape
dismissal before inert wrapper delivery. It requires the exact live originating
keyboard/client seat, unique active focus on its exact owned native leaf popup,
no ordinary/descendant popup or server grab/proxied focus, current original
press/frame and explicit known-zero modifier policy. Original press serial/seat
are retained; consume once after all refusals, then synchronous original force-
hide outside UI locks. Physical held/release bookkeeping is unchanged.
**No Enter/Space opening, SDK keyboard forwarding, task/pointer fallback,
synthetic focus/grab/restoration, hiding/config migration or deployment.**

Actual PopupDone routing now includes native overflow. The exclusion predicate
closes the requested recorded client-surface subtree, not unrelated roots.
Child-first teardown MOVES whole native PanelPopup resources and original
embedded PopupSurface into an owned batch: focus cleanup/embedded Done before
original RAII release. Raw proxies alone do not retain SCTK PopupInner; no
manual duplicate role/surface destruction. Callback Arc ownership can defer
final destruction; this is not observed protocol/restoration acceptance.

Fresh guarded whole-caller locked check/release/test compilation and **app93**
pass (prior82 + eight synthetic consume/converter + three actual generic
subtree/order/owned-drop cases; context8 included, not101). Linux277 discovered/
274 pass/3 explicit missing-Blender-export skips, nine suites+compileall0;
host panel71/prepared19 pass. Original539 foreign entries/pins/features[]/
licenses, all postimages, actual compiler artifacts/ELFs and complete app/SDK
inventories retained. First native39 build's eight phases all0/1122.07s.

Unbuilt leaf-only, intermediate subtree and raw-order source candidates stay
separate. Read-only reviewers found descendant retention, then premature SCTK
owner destruction; both P1s corrected before native compilation. Initial source
transform refused a guessed seam before output; exact original seam correction
and zero-postimage partial root preserved. Original SCTK0.20.0 read files match
locked-checksum crate bytes; panel Smithay0ff00983 source matches Git HEAD/blobs,
not Compositor e3d461a. Final focused source review: no issues/OK with notes;
live activation/recovery BLOCK, no reviewer build attestation.

New3009-input archive/tree/target/frozen evidence retained on the explicit approved
256GiB build volume. Unchanged >20GiB-volume/>10GiB-root/no-compiler/override
guards; old128GiB still refuses full-build budget. No formatting/deletion/resize/
package or stock-session change. **No live keyboard-only entry/dismissal/
traversal/restoration/accessibility or final combined-desktop pass.**

Bounded rerun, **not final desktop verification** (fresh Windows shell, cwd
`C:/Users/adamm/Desktop/Code/cosmic-studio`, no compiler/library/profile overrides):
`python 'C:/Users/adamm/VirtualBox VMs/COSMIC-Studio/iteration-39-review-evidence.py'`.
Keep both volumes, all old/new source/target/cache/failed previews/archives/
ELFs/logs/strict SSH/auth/config/cold recovery. Both runtime/final flags false.

See [recovery audit](native/panel/overflow-keyboard-recovery-audit.md).

## Historical iteration38 actual synchronous inert callback delivery

Original client Press/Release callbacks now invoke the converter/wrapper path
**after** Smithay input returns; Repeat after capture, without a server repeat
down. Actual keyboard/seat/original-frame, unique same-seat active live outer
layer, ungrabbed overflow focus and mapped positive-size target checks precede
the wrapper mutex. Its validator performs no Smithay/geometry/widget queries.
Every output is discarded/no task/ordinary Program/pointer popup fallback.
The original SDK keyboard isolation remains mandatory and inert.

Fresh corrected locked check/release/app82 pass (prior77 + five synthetic actual
OverflowButton wrapper/converter cases; standalone context8 included, not90).
Linux272 discovered/269 passed/3 explicit missing-Blender-export skips, nine
suites+compileall0; host panel66/prepared19 pass. Original539 foreign entries,
pins, SDK features[], licenses, postimages, actual compiler artifacts/ELFs and
complete app/SDK inventories retained. **No live Wayland callback/recovery or
desktop acceptance.** Source wiring is no longer absent; activation, consume-once
client press/grab/order, traversal/restoration/accessibility/hiding remain open.

First fresh check/release0 and testcompile101/E0283 are preserved: only a test
constructor's unnecessary `.into()` was removed in a NEW tree. Both3003-input
archives, full guest trees/targets and45 scoped first artifacts remain. First
bounded verifier also refused an old log filename; separate corrected verifier,
first scripts/logs and original results retained. Read-only reviewer found no
issues: OK with notes for inert routing only, recovery BLOCK; no build attestation.

Both38 drivers explicitly use the approved new256GiB mount and exact provenance,
unchanged >20GiB-volume/>10GiB-root/no-compiler/override guards. Read-only reruns
record budgets without compiler launch; old128GiB still refuses full-build
headroom. New volume ~238GiB free; no deletion/resize/format/deployment.

Bounded rerun, **not final desktop verification** (fresh Windows shell, cwd
`C:/Users/adamm/Desktop/Code/cosmic-studio`, no compiler/library/profile overrides):
`python 'C:/Users/adamm/VirtualBox VMs/COSMIC-Studio/iteration-38-review-evidence-corrected.py'`.
Keep both volumes, first/fixed38 and prior sources/targets/caches/frozen artifacts/
archives/logs/strict SSH/auth/config/cold recovery. Both runtime/final flags false.

See [caller audit](native/panel/client-overflow-route-audit.md).

## Historical iteration37 explicitly approved additional build storage

The operator chose a NEW dynamic256GiB build-only disk, preserving both existing
disks/caches/evidence. Authenticated ordinary shutdown and cold recovery snapshot
preceded SATA port3 attachment. Exact new-empty-disk/primary/old-volume guards,
repeated read-only wipefs checks and private authenticated formatting succeeded.
New ext4 UUID `aba53340-ed2a-48ff-b532-8b6371f81d9c` at
`/mnt/cosmic-studio-builds-37` nodev,nosuid, studio1000:1000/mode0700;
initial ~251GiB free. Old volume remounted without formatting; fstab unchanged.

Default read-only empty-disk guard still requires128GiB; explicit approved256GiB
selection retains all identity/signature/refusal checks. Host VM source48 and
five targeted Linux guard cases pass. First directory-only preflight assumption
failed before shutdown/mutation and is retained separately. Existing native77/
source61/539graph/full app-SDK inventories/ELFs rerun successfully; no new native
compilation or full Linux aggregate. Prior full Linux265/262/3 remains iteration36.
Storage recovery does not deliver keyboard activation/admission/traversal/recovery,
hiding, deployment or final desktop acceptance. See [VM details](native/vm/README.md).

Bounded rerun (fresh Windows shell/checkout cwd/no overrides):
`python 'C:/Users/adamm/VirtualBox VMs/COSMIC-Studio/iteration-37-review-evidence.py'`.
Keep both build volumes, all prior/new artifacts/trees/targets/caches, cold snapshots,
strict SSH and auth/config recovery. After reboot remount existing filesystems only,
NEVER repeat formatting. No completion claim from source/storage/unit verification.

## Historical iteration36 actual native overflow opening preflight

The existing popup routine now resolves overflow membership, mapped anchor
location and a live parent proxy **before** dismissing popups, hiding Workspaces
or creating protocol surfaces. Force-hide/already-open recovery remains independent
of a surviving opening anchor. Original serial/grab/geometry clamps/protocol tail,
pointer path and all-keyboard isolation remain. This is not keyboard admission or
transactional rollback of later protocol errors.

Fresh locked check/release/existing app77, Linux265/262/3 and host panel61/prepared19
pass; six new source/Git regressions, **no new native popup runtime tests**.
Original539 graph/features[]/licenses/postimages/compiler artifacts/ELFs retained.
At iteration36 the128GiB build volume fell to ~20.0GB/18.6GiB, blocking its
unchanged >20GiB full-build guard. Iteration37 adds separate explicitly approved
storage without deleting/resizing that volume. Read-only verification remains supported.
No keyboard routing/activation/recovery/hiding/deployment or final desktop pass.

See [native preflight audit](native/panel/overflow-preflight-audit.md).
Current bounded rerun (fresh Windows shell/checkout cwd/no overrides):
`python 'C:/Users/adamm/VirtualBox VMs/COSMIC-Studio/iteration-36-review-evidence.py'`.
Compilation/unit/source evidence only; preserve36/prior roots/targets/caches/SSH/
volume/auth/recovery. Historical reviewers may correctly refuse current source drift.

## Historical iteration35 native callback/press pairing

Actual ClientSeat callbacks now retain immutable original event/per-press pairing:
fresh press only, repeat observation without fresh activation, release witness
captured before retirement. Duplicate/entry-held/unknown events do not mint a
grant; enter/leave/keymap/capability/modifiers invalidate stored delivery. Ordinary
server forwarding and inert overflow keyboard isolation remain unchanged.
Fresh original-feature locked check/release/app77 (prior69 + eight pairing cases),
Linux259/256/3/nine suites+compileall0 and host panel55/prepared19 pass. Original539
foreign graph/pins/features[]/licenses/postimages/compiler artifacts/ELFs preserved.

Initial host interruption1073807364/source55-only report retained; owned VM was
saved, resumed normally without reset/discard, then a NEW same-archive tree passed.
No native compilation failure or changed-source repair is inferred. Read-only
reviewer: no issues, OK with notes for pairing only; native recovery BLOCK.
No callback invokes conversion/UI dispatch, no consume-once activation/lifecycle,
live admitted target/grab/deferred authority/traversal/restoration/recovery/hiding.
Both runtime/final flags false. See [pairing audit](native/panel/client-keyboard-delivery-audit.md).
Bounded rerun (fresh Windows shell/checkout cwd/no compiler-library-profile overrides):
`python 'C:/Users/adamm/VirtualBox VMs/COSMIC-Studio/iteration-35-review-evidence.py'`.
Preserve interrupted/resumed35/prior roots/targets/caches/artifacts and SSH/volume/
auth/recovery. Compilation/synthetic unit/source evidence, not final desktop gate.

## Historical iteration34 overflow-local fail-closed isolation

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

Release ELF SHA256 `47a95598c4d83f19b1233f75e6c6d6708dabd87738342192db7941cc15e7bb01`;
app-test ELF `af354a62fa3c9115beeb5bfaa2d4a1f1ac68454e2421921149cbe72f98842b9b`;
frozen evidence archive `32cdef3adc950c9998672205d6a85debbe0317bf00cd7abf59d5132747c1e56f`.

## Historical owned-VM evidence — iteration33 diagnostic

Native callback activation remains blocked by a newly reproduced production
button input-isolation defect, not merely missing provenance. Actual compiled
SDK custom-button/Tree/layout/focus operation diagnostics show focused Enter
accepts repeat and leaves pressed state after keyboard release or unfocus;
a later inside pointer release can publish without pointer down. Fresh Space
character does not activate. CursorLeft clears it, but synthetic leave is not
a valid repair because it would discard genuine pointer state.

Six native diagnostics pass as **observations of existing unsafe behavior**,
not keyboard recovery or acceptance. Initial compile1/E0599 (`Named::Space`)
inputs/report/logs retained; corrected Character-space harness then reviewed
source-preservation driver pass in separate fresh directories. No panel/SDK
input mutation, new whole-panel build, renderer trial, deployment or hiding.
Latest whole-panel app61/Linux244/241/3 remain iteration32 results, not67 app tests.
Host panel source45 and targeted Linux probe guards5 pass; no full Linux rerun.
All1312 dependency files and original app/SDK source inputs remain unchanged
through the reviewed diagnostic. Existing licenses/locks/features preserved.

Reviewed probe ELF `2c2b79f787e3d3234a0669a6f14b03c6bc071b36cc57455a6b4847c86bc4009d`;
evidence archive `bca7bcfbd8ef7740dd71490962795f13651f7d494b1dac6a72c2fd6551b2e842`.
Fresh read-only reviewer confirms diagnosis/scope, identifies missing after-run
source check; parent fixes it in a NEW reviewed driver/run without altering
first/corrected evidence. Native overflow-local keyboard/pointer isolation,
callback/live seat/press/grab authority and actual recovery remain open.
See [audit](native/panel/overflow-keyboard-audit.md). Four-command bounded rerun:
`python 'C:/Users/adamm/VirtualBox VMs/COSMIC-Studio/iteration-33-review-evidence.py'`
in fresh Windows shell, checkout cwd/no compiler/library/profile overrides.
Keep first/corrected/reviewed33 diagnostics, reviewed32 original source/target/
compiled SDK/dependency inventories, artifacts/logs/archives/strict SSH/approved
volume/auth/recovery. Both runtime/final flags remain false.

## Last whole-panel owned-VM evidence — iteration32

The actual IcedElement wrapper now has an explicit call into the single-event
State boundary. Its task receiver stages one complete Option output losslessly
(including None), refuses pending work without flushing/relabeling, and leaves
later task output ordinary/untrusted. Validator/dispatcher remain mandatory and
run under the element mutex: no re-entry or synchronous focus callback that
locks the same element. This is not a scheduler/FIFO barrier or client grab grant.
No native callback invokes the route; hiding/deployment stay disabled.

First native32 whole-panel check/release0, test-compile101/E0053 retained with
complete consumed archive/driver/phase logs/four inputs; full original guest tree
and target remain. Mutable test draw renderer is evidenced by authentic Widget
API. NEW reviewed archive `eb1898ad6d442735f325c3877de13eaed608b01cc95a9999c44c95fe94ee5679`
adds that correction, pending-only Debug redaction and mutex contract in NEW
`/mnt/cosmic-studio-builds/studio/cosmic-studio-panel-wrapper-reviewed-iteration32`.
All eight phases0, locked whole-panel check/release/app61 (six new actual-wrapper
synthetic cases; context8 repeats included, not69 distinct), driver245.27s/full
supervised host session10m26s. Source40/prepared19, Linux244/241/3/nine suites+
compileall0. Original539foreign graph/pins/features/postimages/licenses/native
ELFs/actual compiler artifact and unchanged app/SDK inventories independently
frozen/reviewed. Preflight volume56205361152bytes; post-driver50432790528/root
15479844864bytes. Original UUID/primary/UID/mount/headroom guards unchanged;
no formatting or deletion. Debug redaction is not a test-only correction.

Frozen release `03f646ebc7564965e3975eee63bf71bf335367719fbdfa24e902d42c600d641c`;
app-test `ada5d2f83a1cd6d10dd2f4d9a73f38f63d4953c6977020fa59a3c033277b3150`;
evidence archive `dfa0e89c47651d8143b1e9adcca1f3587765b3d56e6895d8000d38b566f2bd97`.
External `iteration-32-native-reviewed-panel`; guest frozen directory is
`work/native-artifacts/iteration-32-panel` (initial guessed reviewer template
retained/corrected before execution, not a failed native run). External19
commands0: `iteration-32-review-reviewed-runs/20261012T020005.331112Z/report.json`.
Bounded fresh-shell/no-overrides/checkout-cwd rerun:
`python 'C:/Users/adamm/VirtualBox VMs/COSMIC-Studio/iteration-32-review-reviewed-evidence.py'`.
Keep first/reviewed32/prior roots/artifacts/caches/SSH/approved volume/auth/recovery.

Unused intermediate export is retained but NEVER transferred/built. Fresh
read-only reviewer found no concrete blocker (OK with optional test note);
parent read full report, no pending supervisor requests. It did not verify
native build/counts. First source KeyErrors/six inputs/repeated log and first
native signature101/complete consumed archive/driver/logs remain separate;
original full guest tree/target retained, not a full external checkout-copy claim.
Post-documentation repeat19 commands0:
`iteration-32-review-reviewed-runs/20261012T020331.442639Z/report.json`.
`iteration-32-verifier-receipt.json` preserves272 SHA256 dependencies and required
first/reviewed/prior roots, scoped failures, unused intermediate, reviewer and
exact module correction diff. Source manifests differ only module/test/README.
This is compilation/synthetic wrapper/unit/source evidence, not keyboard
activation/recovery or final desktop acceptance. Both final flags remain false.

## Last completed owned-VM evidence — iteration31

Added an explicit single-converted-keyboard-event method at the real Iced State
boundary: nonempty event/message queues refuse without flushing/relabeling;
mandatory explicit validation precedes UI and each resulting widget message;
each dispatcher receives the original immutable envelope. No ordinary Program
update/pointer-serial fallback or recursive Smithay query. Ordinary State/wrapper/
receiver/overflow/native callbacks remain unchanged; no callback uses the new path.
Returned tasks and the separate wrapper receiver do not inherit keyboard authority.

First production check/release passes but app-test compile101/E0063 refuses the
test's missing original Style fields. Complete first source archive/driver/phase
logs and five inputs retained, full original guest tree/target preserved. Narrow
test-only correction is evidenced by original mod.rs; NEW2976 snapshot
`2a9cfc569c7c9347891624afefab8231c391a2ddab0a3a6f1e01e3e94a49c5f4`,
root `/mnt/cosmic-studio-builds/studio/cosmic-studio-panel-message-fixed-iteration31`,
all eight phases0. Driver202.43s, full host supervised session9m52s. Locked whole
panel check/release/app55 (six new actual-UI synthetic cases; context8 included
repeats, not63 distinct), source35/prepared18/Linux238/235/3/nine suites+compileall0.
Original539foreign graph/pins/features/postimages/licenses/native ELFs/actual
package compiler artifact and unchanged input inventories independently reviewed.
Release `9d0bb2d2fab595bf307c929b3a5816945870427442d5b488e43be98552340f77`;
app-test `30d4a966265f5b501b69c6660d61170a04e76eb1a30e36b8b6de76d9a6ca9f1d`;
evidence archive `a3fdf857d5451387b7f62581bdcb40173d97727b5eb34b727ebb8f5f7e9937a5`.

External18 commands0: `iteration-31-review-fixed-runs/20261012T011024.725779Z/report.json`.
Fresh Windows shell/no compiler/library/profile overrides, checkout cwd:
`python 'C:/Users/adamm/VirtualBox VMs/COSMIC-Studio/iteration-31-review-fixed-evidence.py'`.
All first/corrected31/prior native/source/cache/API/failure/SSH/auth/recovery roots
retained; approved UUID/primary/mount unchanged. No renderer retry/deployment.
This is compilation/synthetic real-UI unit/source verification, not native input
admission, keyboard press/grab/deferred authority, recovery/accessibility or final
desktop acceptance. Live validator/wrapper/client integration is still required;
manual hiding remains disabled and both runtime/final flags false.
Post-documentation repeat18 commands0:
`iteration-31-review-fixed-runs/20261012T011318.474752Z/report.json`;
`iteration-31-verifier-receipt.json` preserves205 SHA256 dependencies/required roots
and independently verifies the exact test-only Style correction.

## Prior owned-VM evidence — iteration30

Native routing audit refuses direct Enter forwarding: plain widget messages lose
origin, overflow idle closures use first-seat pointer serial, and recursive
Smithay locking from filter/target callbacks is unsafe. Same-seat active callback
lifecycle repaired first with exact prior-postimage/Git/license/fingerprint guards:
leave matches a unique active seat/surface before retiring ledgers/space/server
focus; press history excludes LastFocused. No callback metadata dispatch or new
keyboard popup authority. Different-surface stale/wrong-seat/repeated/ambiguous
selection is covered, not delayed same-seat/surface re-entry lifetime or runtime.

NEW2971 archive `6971feb5ed3b163975fc0850c1f1e8ababc2227908de569d93ec60cf0ac724dd`;
root `/mnt/cosmic-studio-builds/studio/cosmic-studio-panel-active-focus-iteration30`.
All eight phases0 in10m06s: locked whole-panel check/release/full-bin49 (six new
production selection cases); context8 repeats included cases, not57 distinct.
Source30/prepared17/Linux232/229/3, nine suites+compileall0. Original539graph/
pins/features/postimages/licenses/native ELF/actual package compiler artifact and
unchanged metadata/test inventories frozen/reviewed. First exact transform
refusal (ambiguous iter_mut seam, four source errors) and five source input copies/
separate captured repeat log retained; corrected seam targets actual seats only.
No failed prepared-source mutation or guard weakening.
Release `894f06d43331425e9f1f5b3ab5313cc56847f5b93ed77f2c827771f7ee25d6be`;
app-test `f7293b98fe7c6b6a563e3a453187a026b8443863776b2b7a3a9730eb1b9e4f39`;
evidence archive `9cb0f42faff2016edbf861703eb207a305c2281ff1c751e3f1a4fb23753547d9`.
External17 commands0: `iteration-30-review-runs/20261012T002934.204531Z/report.json`.
Fresh Windows shell/no compiler/library/profile overrides, checkout cwd:
`python 'C:/Users/adamm/VirtualBox VMs/COSMIC-Studio/iteration-30-review-evidence.py'`.
All prior/current roots/cache/artifacts/negative cases/approved volume/SSH/auth/
recovery retained. Nothing deployed, hiding disabled; actual event routing/
activation/recovery/accessibility/combined desktop still OPEN. Both runtime/final
flags false; this is compilation/unit/source evidence, not final acceptance.
Post-documentation repeat17 commands0:
`iteration-30-review-runs/20261012T003132.428955Z/report.json`;
`iteration-30-verifier-receipt.json` retains152 SHA256 dependencies/required roots.

## Prior owned-VM evidence — iteration29

Explicit actual-ClientSeat Iced metadata conversion now compiles using existing
Iced core/locked Smithay xkb0.9, without Winit/xkbcommon-dl dependencies. Exact
prior-keymap-postimage/Git/license/fingerprint guards, original MIT forward table
fixture/notice and GPL converter retain complete logical/Control-cleared modified/
physical/location/named-modifier/text/repeat fields plus immutable original
client envelope. Original Wayland Ctrl TODO and Unicode-pop defect are not copied.
No native callback dispatch/per-ordinary-key parsing, server-state synchronization,
repeat timer, popup authorization/hiding/config migration or deployment.

NEW2966 snapshot `4ee774cb60d61d20921808f76847e189125d565978f03eb98e1d4fdfe144cd50`;
root `/mnt/cosmic-studio-builds/studio/cosmic-studio-panel-iced-iteration29` under
unchanged volume/primary/UID/headroom/no-builder/override guards. All eight
phases0: locked whole-panel check/release/full-bin43 (nine new converter cases),
context8 repeats included cases, not51 distinct; Linux226/223/3, nine suites and
compileall0. Original539graph/pins/features/postimages/native ELF/license/compiler
artifact and unchanged metadata/test source inventories frozen/reviewed.
Release `0cd9a8e4b20b0525cd04abeef271a07b3722581675f5a6ec65e62539160bf4e2`;
app-test `f183af69476b33500e297295f314130928dcccc2aab39444bdd38c7cea610679`;
frozen archive `b0e3f10c61a0d067d4529d69ebc7a3423819260eb1cc77281bd4b62ee0b567e6`.
Source25/prepared16 pass. First commented-code creator assertion/separate
correction and initial EOF warning are recorded; initial API collector template
retention gap is explicit, not mislabeled a full first input/log receipt.

External16 commands0: `iteration-29-review-runs/20261012T000215.753937Z/report.json`.
Rerun fresh shell/no compiler/library/profile overrides, checkout cwd:
`python 'C:/Users/adamm/VirtualBox VMs/COSMIC-Studio/iteration-29-review-evidence.py'`.
Preserve new/old prepared roots, native artifacts/source/cache/API/negative
cases/verifiers/approved disk/SSH/auth/recovery. Conversion is explicit/latest-only,
not queued dispatch/grab authority or actual keyboard-only entry, traversal,
restoration/accessibility. Manual hiding disabled; runtime/final flags false.
Post-documentation repeat16 commands0:
`iteration-29-review-runs/20261012T000402.713563Z/report.json`;
`iteration-29-verifier-receipt.json` preserves124 SHA256 dependencies/required roots.

## Prior owned-VM evidence — iteration28

Original SCTK/locked panel-Smithay xkb0.9 API bytes establish an existing public
safe client keymap path. Exact previous-postimage/Git/license/fingerprint guards
now capture original callback keymap text in actual ClientSeat and clear it on
capability/replacement. Explicit independent local slave map/state lookup uses
original raw depressed/latched/locked/group, checked+8, single base/current/
Control-cleared symbols and original event correspondence. Residual Control,
missing/invalid/stale/ambiguous/overflow inputs refuse; no default keyboard/text,
borrowed XKB/unsafe Send/new dependency/per-key parsing or ordinary forwarding
change. This is not physical identity, full Iced conversion or input authorization.

NEW2958 archive `4c51a46a43bef1458a800cefaf5591ea5ceb92af912a840e4ffd61daab777f43`;
root `/mnt/cosmic-studio-builds/studio/cosmic-studio-panel-keymap-iteration28`;
all eight phases0: locked check/release/full-bin34 including7 new client-XKB cases,
standalone context8 (included cases, not42 distinct), Linux220/217/3 and nine
suites+compileall0. Original539graph/pins/features/postimages/license/ELFs/actual
compiler artifact and unchanged metadata/test inventories frozen/reviewed.
Release `5ce0a01d02941a3394745511b8bb10c5aed2352e9c6525aa057879ea3e0a7768`;
app-test `8167bbc6519419d3718749097a4bac4aee5fc2f0f2e5f3863e932b507690048f`;
frozen archive `bded944d48e534838679b03cddbd0c69e02c00288af0be76e5356eba953309ed`.
Initial aggregate creator exact-root assertion refused before verifier creation/
execution; original/observation/separate corrected creator retained. Not a native
compiler failure. External15 commands0, rerun fresh shell/no overrides/checkout:
`python 'C:/Users/adamm/VirtualBox VMs/COSMIC-Studio/iteration-28-review-evidence.py'`.
All old/current prepared roots/failures/caches/stock/auth/recovery untouched; no
candidate deployed or keyboard-only recovery/accessibility/final desktop accepted.
Post-documentation repeat15 commands0:
`iteration-28-review-runs/20261011T232802.478135Z/report.json`;
`iteration-28-verifier-receipt.json` preserves93 SHA256 dependencies/required roots.

## Prior owned-VM evidence — iteration27

Verified original panel-Smithay/SCTK API bytes and timing: cached serialized
modifier assignment is explicitly ignored by lossy serialize_back, not an exact
client raw-mask/layout synchronization path. Added exact prior-postimage-guarded
per-ClientSeat immutable original KeyEvent/serial/origin plus optional named/raw
masks/layout-group/serial frames; private accessors, focus/event identity, debug
redaction, invalidation and latest-only semantics. Repeat observer creates no
arming, key-down, timer or Iced event. Original ordinary forwarding/modifier
behavior remains unchanged. No authorization, hiding or keyboard recovery added.
Two initial source-test prefix assumptions are preserved as parent observations,
not mislabeled full first trees/logs. Source15/prepared14 pass. NEW2953 snapshot
`478de31ed7a459962a264ab586673932748143410bcae6a288b644bc7c99f654`;
whole native locked check/release/full-bin27 and standalone context8 pass, with
8 already included cases (not35 distinct). Original539 graph/pins/features,
postimages/ELFs/licenses/actual compiler artifact and unchanged metadata/test
inventories independently frozen/reviewed. Linux214/211/3, nine suites+compileall0.
Release `558e7a2c9a225a2727de683c875282cbacae92561e6451450dd4f567c95a8f9b`;
app tests `6a9cc14d7149356d300f908cba54ec5dacd037b9dcbd1e42b5dd9e449e2d436b`;
frozen archive `4c4288bc00f17c4dc1fb9f7c3903fad814c995a175240c9cf2b72efec0cedac8`.
Bounded external14 commands0:
`python 'C:/Users/adamm/VirtualBox VMs/COSMIC-Studio/iteration-27-review-evidence.py'`,
fresh host shell/no overrides/checkout cwd. All prior failures/artifacts/roots,
approved volume/caches/auth/recovery remain untouched. No candidate deployment,
raw XKB/Iced conversion, traversal/recovery/accessibility or final desktop pass.
Post-documentation repeat14 commands0:
`iteration-27-review-runs/20261011T230159.999228Z/report.json`;
`iteration-27-verifier-receipt.json` preserves72 SHA256 dependencies/required roots.

## Prior owned-VM evidence — iteration26

Authenticated54 original key/API files plus four original lock-checksummed
registry archives. Existing Winit keymap source is not directly callable with the
panel's unchanged graph. Added guarded per-ClientSeat held/raw/client serial/time
ledger, fresh focus/press lifetimes and debug redaction. No key conversion/repeat
forwarding/popup activation/global entry/traversal/hiding/config migration added.
Original MPL source notice/full MPL text and GPL fixture/module preserved.

First source-license expectation and pre-compilation UUID typo refusals retained.
Initial whole-panel18/ledger8 pass is preserved separately; an additional actual
native regression fails on stale press resurrection after identical serial/time
reuse. Per-press token correction in a NEW source root now passes locked whole
panel check/release/full-bin19, including nine ledger cases also run standalone
(not28 distinct cases). Original539 foreign entries/pins/features/postimages/native
ELFs/actual package compiler artifact and unchanged metadata/test source inputs
are independently frozen/reviewed. No prior artifacts overwritten or deployed.

Prior2949 snapshot; Linux208 discovered/205 pass/3 explicit missing-Blender
skips, nine suites+compileall0. Release SHA256
`62a06cda3b591184a21dc1a7705690f6db8067820676913a6dd0f9a9c6c200db`;
app-test `d3cba82a3eda7f25f59e1126423acb95f1256562ba45991d1182ec5858ace34c`.
Bounded external13 commands0:
`python 'C:/Users/adamm/VirtualBox VMs/COSMIC-Studio/iteration-26-review-fixed-evidence.py'`,
fresh Windows shell/no overrides/repository cwd. All original/corrected source
roots, negative case, artifacts, approved volume, SSH/cache/recovery retained.
Post-documentation repeat13 commands0:
`iteration-26-review-runs/20261011T223116.642182Z/report.json`;
`iteration-26-verifier-receipt.json` preserves53 dependencies/required roots.
Compilation/unit/source scope only; keyboard admission/recovery, accessibility,
physical-device/optical/package/combined desktop gates remain open. Hiding disabled.

## Prior owned-VM evidence — iteration25

Exact-source native panel focus prerequisite now compiles in the owned VM:
locked check/release, full binary10 native unit tests (five existing material/
edge/forwarding and five seat-ownership), plus the same ownership5 in a standalone
harness. Typed existing SpaceTarget routing and explicit cached widget focus ID/
State::operate added; original popup/leave/grab/proxy paths retained. Full keyboard
metadata/activation serial/traversal/restoration and actual keyboard-only entry
remain open; no key forwarding, hiding, config migration or deployment accepted.

Fresh2942 source snapshot; Linux202 discovered/199 pass/3 explicit missing-Blender
skips, nine suites+compileall0. Frozen native release
`57e25f87e132e6b3965668ac7fe89fb0af6820abbbc8d8162c8907fd385ed069`;
app-test ELF `0b1e06eeb32bf3ed1dc2b88e4f8aeb99ffa1dcc2a000696fe0dcc85d16b15a71`.
Independent review passes exact panel/SDK/Iced/panel-Smithay pins, original539
foreign entries/features/postimages/native ELFs and unchanged continuation inputs.
First Cargo warning/JSON parser refusal and cache-directory reviewer refusal stay
preserved separately; narrow corrected continuation/reviewer pass without source/
lock/feature/guard change. Bounded rerun12 commands0:
`python 'C:/Users/adamm/VirtualBox VMs/COSMIC-Studio/iteration-25-review-evidence-corrected.py'`,
fresh Windows shell/no overrides/repository cwd. Required approved volume/new
native source root/external frozen artifacts/private SSH/recovery retained.
Compilation/unit/source evidence only, not final combined desktop acceptance.

## Prior owned-VM evidence — iteration24

Operator-approved separate128GiB build-only VDI now provides guarded headroom;
original160GiB OS disk/install guards/caches remain unchanged. Cold pre-volume
snapshot/root formatter receipts retained. Volume nodev,nosuid, root-owned
provenance, studio UID/GID1000/mode0700; `/etc/fstab` unchanged. Reboot requires
verified existing-volume remount, never repeat formatting or delete evidence.

Changed Sysinfo now passes genuine locked check/app11/release537.73s using
original664-entry graph/features, source/metadata/native ELF guards. Five rate
tests and six original app tests repeat. Frozen release
`8e626a5c41433eab2fca7557cae09abd92492537e868e3195cbd09bb9dca7883`;
app-test ELF `2e5e14617163b1c10c6af302333a6f4240b3eaadafdec8d819fa6e0dccf8761a`.
GPU host subprocess remains unbounded; sensors/detail/physical accuracy/runtime
not certified. Changed Brightness app5 evidence remains distinct.

Original focus/API collection confirms the existing overflow SpaceTarget but
surface-only wrapper focus entry. Operator approves coordinated native focus/
input extension; full key schema and lock/exclusive focus protections recorded.
No partial key forwarding, global hotkey, manual hiding or config migration.

Latest source snapshot2936 files; Linux195 discovered/192 pass/3 explicit
missing-Blender-export skips, eight suites and compileall0. Historical bounded
rerun from fresh Windows shell/no special environment/repository cwd:
`python 'C:/Users/adamm/VirtualBox VMs/COSMIC-Studio/iteration-24-review-evidence-corrected.py'`.
Not combined desktop acceptance; candidates remain undeployed. Historical
iteration23 implementation-hash review must refuse present source drift.

## Installed layers

- Archivo system/toolkit settings and pinned Archivo/Instrument Serif font files.
- Earlier shell glass settings and GTK outer-frame removal, with backups.
- Approved Studio Dock, 71 application designs covering 75 launchers, compact spacing, blue Files and frosted empty/full Trash.
- Approved window-button GTK styles, selected app-private styles, Zed server-decoration preference and Obsidian titlebar snippet. See the [window-controls checkpoint](native/window-controls/CHECKPOINT.md) for recovery and exact scope.

Final denser glass, rounded geometry and semantic font roles are saved in source. They have not all been applied together to the running desktop. Existing applications and the compositor were kept open.

## Validation and candidates

- Portable checks: 24 setup/font tests, 18 native installer/builder tests, 15 popup tests and 10 icon tests passed.
- Actual compositor policy/font/material tests: 12 passed. An optimized candidate predates the last optical corner change and approved control composition.
- Actual panel tests: five passed, including fullscreen/maximized/minimized policy. The rounded/adaptive release built successfully.
- The newest popup specimen built successfully. Native palette checks passed: minimum checked contrast 6.3254 for dark popups, 7.2507 for dark windows and 11.7030 in light mode. Headerbar checks passed with popup opt-in both enabled and disabled, including high contrast.
- Font/menu source preparation and byte-level replay passed for supported revisions. Some final combinations still need complete rebuilds.
- Coordinated window-control work built compositor, Files, Settings, Edit, Term, Store and Monitor against refreshed sources. Button candidates were not installed. Player lacked development dependencies; Viewer stopped during compilation. Exact hashes and isolated screenshots are in its checkpoint.
- GPU probes passed; timings cover the final shader only, excluding backdrop blur, client rendering and whole-frame cost.
- Four third-party preparations preserve original Flatpak runtimes and permissions. Final compilation and runtime dependency gates remain pending.

Private products and recovery data remain outside Git. Patches, generators, assets, tests, source pins and sanitized evidence are retained here.

## Isolated Windows-hosted VM continuation

Iteration23 adds a fresh genuine locked changed-Brightness check/full-app5/release
with original676-entry graph/features and externally frozen native ELFs; five
tests repeat. Separate Sysinfo elapsed delta-rate source/module5 and source5
guards pass, including actual original Git application/unchanged lock; whole
changed Sysinfo/GPU host cancellation/runtime remain open. Native panel contract
inspection finds internal key/focus/seat-serial and persistent-identity gaps;
no pointer-only hiding is shipped. No approved icon render, candidate deployment
or combined desktop acceptance. Ten-command corrected bounded review0:
`python 'C:/Users/adamm/VirtualBox VMs/COSMIC-Studio/iteration-23-review-evidence-corrected.py'`,
fresh Windows shell/no special environment, cwd
`C:/Users/adamm/Desktop/Code/cosmic-studio`. Source192/189/3/native app5/rate5
are distinct from the prior single synthetic frame and final desktop gate.
All immutable failures/source/locks/ELFs/traces/recovery dependencies retained;
fresh disk headroom preflight required for further full builds.


A separate Pop!_OS 24.04 generic-28 VirtualBox guest now has real final-combination compositor and panel release candidates built from the existing exact pins. The compositor's locked check and 12 native Rust tests passed; both locked optimized builds exited 0 with original foreign registry/checksum/Git dependencies preserved. Verified native x86-64 ELF artifacts and all dynamic libraries are retained privately. Builds used Rust/Cargo 1.99.0, Linux 7.0.11, normal uid1000, 8 guest CPUs, and 4/2 build jobs respectively.

These candidates are **not installed or runtime-validated**. Combined core/app/client/media and third-party gates remain pending. The ISO-installed packages and current APT candidates differ from the approved source revisions; existing installer guards remain intact. The operator approved preparing genuine source-matched stock packages for reversible VM-only alignment after compatibility checks. Current VM source/recovery verification: 195 discovered, 192 passed, three explicit missing-Blender-export skips (iteration23 fresh full aggregate). Core and Player/Viewer locked release compilation is complete; remaining pipelines use bounded jobs. The full core pipeline completed exit0; Files, its applet, Edit, Term, Settings and Player have privately frozen optimized ELF hashes/resolved libraries. Viewer’s original failed `-lnuma` link report is preserved; after installing the evidenced `libnuma-dev`, a separately retained locked resume completed exit0 with unchanged prepared sources/dependency graph and a frozen native ELF. Player/Viewer compilation is complete; media behavior/codec runtime coverage remains pending. The six-component non-media client pipeline completed exit0 in its original isolated snapshot. Its applet and panel-button releases are built, frozen/hash-verified with resolved libraries and both compact/popup ELF gates recorded; alias deployment/runtime remain pending. A separate pristine stock compositor Debian package build completed exit0 with original Rust 1.93.1, byte-exact original lock and unmodified tracked source/default features. Its native amd64 `.deb` and recovery/build metadata are privately hash-verified and retained; no COSMIC package is installed or compatibility-certified. The pristine stock panel package also completed exit0. Both packages have resolved dynamic libraries and a simulation selecting only the two intended package upgrades, not actual protocol/runtime compatibility. Launcher’s guard correctly stopped its first attempt; diagnosis found a trailing-slash spelling of the exact same native repository, not real foreign changes. Exact-identity normalization is corrected and the fresh launcher locked check/release completed exit0; its native ELF is frozen/hash-verified with resolved libraries. Fresh app-library/workspaces pipelines completed exit0 with strict original graphs and locked releases; both native ELFs are frozen/hash-verified with resolved libraries. All four third-party exact-source preparations passed; Caffeine's locked check failed on E0502 (a mutable blur reconciliation while its parent-toplevel borrow remained live), despite seven independently passing production lifecycle tests. The failed source/lock/cache/phase logs are retained. A narrowly fingerprinted owned-parent lifetime correction now applies byte-exactly to the original Iced state; all four fresh preparations pass. The genuine locked replay no longer reports E0502 or the lifecycle unused-result errors after explicit discard acknowledgments. Seven actual prepared production module tests pass with the inherited denial enforced. The exact pinned Size::INFINITY API is now corrected and byte-exactly guarded; fresh whole-Caffeine locked check passes53.71s. The original backend-test routing failure remains retained. Corrected locked dependency-package selection now preserves the complete original application feature graph, verifies exact compiler artifact source/features before execution, and passes seven full-crate native backend tests. Caffeine's guarded locked check/release also completes exit0; its native release/test ELFs are externally hash-verified with resolved libraries, not runtime-certified. The three historical applet metadata refusals remain retained with original locks restored. The native `build_helpers` classification now requires exact reviewed path/manifest/library/submodule identities and rejects lookalikes or foreign checksum/version drift. Fresh independent graphs preserve the complete original foreign locks; Brightness, Sysinfo and Status Hub locked check/releases all pass (optimized releases5m45s/4m26s/2m23s). All three native ELFs/markers/locks are externally frozen/hash-verified with resolved libraries; those profiles do not run native app unit tests. With Caffeine, all four native applet releases now exist. No sandbox runtime, permission change or foreign exception is credited. Final logs/locks/cache and the first malformed-hunk replay are separately preserved. The VM has no installed Flatpak apps/runtimes or historical private baseline trees; unchanged-sandbox runtime compatibility is blocked until genuine baselines are established, not inferred from host compilation. Notifications and OSD also completed locked releases; both ELFs are frozen/hash-verified with resolved libraries. Store and Monitor locked releases also completed and are frozen/hash-verified with resolved libraries. OSK locked release8m58s completed and its genuine native ELF is frozen/hash-verified with resolved libraries; all six client releases are complete, alias deployment/runtime remain pending. Additional original recipe prerequisites passed after a guarded development-only install. Installed COSMIC recovery versions are unavailable in current APT/cache; explicitly tagged comp/panel recovery repacks now preserve exact installed payloads/permissions/ownership with verified external copies. Current private configuration recovery is inventory/tar-payload/mode/ownership verified with a protected external copy. Cold snapshot `PopOS-pre-alignment-built-evidence-iteration16` (`e61ceb91-d2c6-48f6-a025-43fc42f34f80`) preserves the unaligned stock guest and then-current build/source/cache evidence; another cold boot reached stock greeter/strict SSH with eight CPUs and only the existing clock flags. Later Caffeine test/release artifacts are externally preserved separately. Protocol/configuration/runtime compatibility remains required before alignment. A first owned private headless-Weston attempt launched the frozen candidate and completed native layer/image-copy protocol roundtrips. Glass-off captured the synthetic fixture but logged EGL context/frame loss; glass-on captured a blank frame with the same failures. Neither is a valid combined visual/runtime pass. Original raw exit0 reports/images/logs are retained with a separate rejecting review; the capture harness now fails on blank fixtures or frame-render loss. A bounded follow-up with a pixman Weston parent compared the genuine pristine exact-source package ELF and both Studio variants: all three failed the strict gate with blankness or EGL frame/context loss. Failure also occurs without Studio patches, but neither variant is certified; all negative artifacts and an externally rerunnable rejection review are retained. A different authenticated private rootful-Xwayland SHM/X11 route also failed every pristine/candidate strict frame gate; no Xorg upgrades or access-control disabling occurred. Complete failure artifacts are retained. Weston used Mesa llvmpipe/pixman, not certified physical GPU acceleration. Boot/auth and these limited protocol observations do not certify physical KMS/multi-monitor/performance. [Bounded EGL/native-window tracing](native/compositor/probes/tracing.md) is now prepared: original dynamic loader verified, constrained diagnostic tooling installed without any existing-package upgrades, and API-only dlopen/dlsym/GetProcAddress plus explicit native-window mock interception demonstrated. Three bounded-review source tests pass; no new renderer trial or attribution from generic ContextLost text occurred.

Iteration18 ran one bounded unchanged-pristine child trace under the verified owned private parent; strict capture still fails. The whole-stream reviewer correctly refuses termination-incomplete records. A separately labeled completed-prefix review (309 EGL/147 native entries) observes a plain swap BAD_SURFACE with last-observed surfaceless draw/read, recreation BAD_ALLOC, and later successful swaps on the original surface token. No actual EGL_CONTEXT_LOST is recorded in that prefix; causation and native lifetime/thread mapping remain unresolved. Raw trace/dumps/hashes/commands/cleanup and independently rerunnable negative reviews are retained privately; no repeat renderer trial or deployment followed. Original four-app Flatpak recipes and explicit remote metadata/history are now preserved: Caffeine24.08, others25.08. Sysinfo's current remote omits an original wildcard bus rule, and generic Export histories do not authenticate app-SHA/OSTree correspondence. No baseline app/runtime is installed or permission changed. Four trace source guards pass on Linux; host VM29 guards pass. Latest full Linux aggregate remains131/128/3, not rerun or inflated by these targeted checks.

Iteration19 reviews the normative buffer-age/current-draw requirement and version-tag Mesa swap checks; the public Mesa source is not authenticated as byte-identical to the installed driver. A candidate-only exact-Winit generator resizes through original bind and restores its own window before age/submission; Smithay/pristine packages/foreign graphs stay unchanged. Its first real check failed E0499 from a whole-State borrow and is preserved. A fresh backend-only correction passes locked check49.69s and 12 original native compositor tests; optimized release was pending at that observation. Three source guards pass on Windows/Linux, not runtime. No renderer retry or deployment occurred. Independent owned OSTree acquisition enforces the existing public trust and exact recorded commit IDs. Sysinfo payload passes; three others refuse a common content checksum mismatch. Separately verified signed cached manifests authenticate Brightness/Sysinfo app/library declarations, reveal Caffeine's current app SHA is not the reviewed pin, and confirm Sysinfo's missing wildcard permission. No missing permission is added or incomplete payload accepted; all four unchanged installed baselines/runtimes/rollback remain open. The signed object/refused-partial and failed Winit archive has 110 byte/mode/UID/GID-verified files and public trust, preserved externally. Fresh full Linux source/recovery135/132/3 and eight suites+compileall0 are separate from native, runtime and physical gates.

Iteration20 freezes the completed repaired compositor87s locked release and native test ELF (12 tests also pass in a fresh SSH shell), independently verifies exact source/patch/manifest hashes and683 unchanged foreign entries. Release SHA3c3f923dce8060e4748567627af207c0e6697144aa9925e5b5ab335a61632370. One new bounded glass-enabled private candidate capture still fails: uniform1280x800, fixture/capture0 versus strict harness1. Older submission/BAD_SURFACE log markers are absent, not rendering proof; startup warnings persist. Raw evidence/independent rejection/owned cleanup are retained, with no second trial or deployment. Read-only Flatpak diagnosis retrieves the refused36-byte object: declared empty-file mode0664 canonically hashes to194420d4… (refusal), while mode0644 would hash to advertisedcc700d46…. Served metadata and advertised identity conflict; original publisher/transport history is unknown. No header/object alteration, checksum waiver or baseline acceptance. Source aggregate remains135/132/3 from iteration19, not a new runtime/full-source pass.

Iteration21 completes six bounded read-only advisory lanes, including explicitly
requested GPT-Astra icon routes (requested routing, not independently attested
provider identity). The operator added native stats, multi-monitor brightness
and hidden-bar scope. Exact original utility/panel source contracts are retained;
Sysinfo already exposes CPU/RAM/GPU/disk fields, Brightness already keys controls
by monitor, and panel already has automatic overflow. Detail/queue/hotplug
refinements, reversible manual hiding and original utility geometry remain open.
No new utility/icon family or candidate desktop is installed.

The active icon inventory now audits actual Studio Dock files, exact names,
XDG desktop priority and declared inheritance—not the inactive study's manifest.
The owned guest census finds38 launchers,34 matching custom source assets,
3 inherited and1 unresolved; source-file coverage is not theme installation,
startup, embedded-resource coverage or optical proof. A Linux test assumption
about case-colliding aliases failed and is preserved; corrected actual-file
assertions pass in a fresh snapshot without changing approved artwork.

A separate passive GL reviewer plus one bounded repaired-child trace retains
actual draw/blit/FBO/PBO/readback metadata. Capture still fails the unchanged
strict gate. Synthetic protocol logs expose capture readiness before initial
fixture buffer commits; the old fixed sleep did not establish readiness. Only
the probe fixture/harness now use a bounded initial-frame-callback handshake,
with four source fixtures and actual native C compilation (existing warnings
retained). Callback delivery is not pixel/presentation proof. No readiness-aware
renderer trial yet; the earlier interrupted trace remains refused. Latest full
Linux source/recovery153/150/3 and externally rerunnable passive/negative checks
are not desktop completion. See [tracing scope](native/compositor/probes/tracing.md)
and the concrete [implementation backlog](to-do.md).

## Iteration22 bounded visibility and utility sources

One readiness-aware, untraced capture of the unchanged frozen repaired compositor
now independently passes the strict image/fatal-log gate:1280x800,26,514 distinct
RGB colors, all three initial callbacks. The authoritative PPM, lossless PNG,
source/ELF/probe hashes and fresh owned cleanup remain private. This proves one
synthetic layer/image-copy frame, **not combined desktop compatibility**, optical
approval, input/scales/authentication, stability/performance or physical GPU/KMS.
Earlier failures and interrupted-trace refusals remain authoritative.

Two explicitly GPT-Astra-requested isolated writers and a fresh read-only reviewer
completed. Parent verifies all four handoff hashes and integrates original utility
geometry/owned inactive scene specifications and 32 recolorable state/size SVG
candidates.27 source/fake-adapter/XML tests pass; no real Blender, render, export,
active alias/theme or installation. Opaque relief materials are starting intent,
not approved family/glass optics. Requested routing is not provider attestation.

The exact-source Brightness transform sends a grouped action as one watch value,
then applies every included original per-monitor write. Empty groups preserve
original no-send behavior, avoiding refresh displacement; the initial snapshot
and its passing reports are retained separately from the corrected fresh snapshot.
Original DDC/gamma/clamps,
refresh, delay, dependencies and permissions stay unchanged. Four source/real-patch
guards and five genuine native production command-module tests pass under Rust1.99
with unused-results denied. **Distinct actions still coalesce**; full changed-app
compilation/receiver/DDC/hotplug/runtime remain open. Old prepared artifacts are
not relabeled as this new implementation. Fresh2927-file Linux snapshot passes
184 source checks181 pass/3 explicit missing-Blender-export skips; all eight suites
and compileall0, native C warnings retained. Native module and synthetic evidence
remain separate. Bounded monitor-rerunnable command is recorded in [to-do.md](to-do.md);
candidate_runtime_pass/final_desktop_complete remain false.

## Resume

Start with [to-do.md](to-do.md). Rebuild and validate final combined sources in owned isolated scenes, then activate through reversible installers. A new compositor requires a deliberate later login. Authentication, mixed-scale interaction and main-session rendering need separate validation.
