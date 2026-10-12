# Pinned third-party COSMIC applets

## Latest bounded native evidence (iteration24)

Repeatable `native/vm/build_thirdparty.py --profile brightness --jobs 2`
selects only that profile; omitting --profile retains all four. Duplicate,
empty and unknown selections refuse. Fresh source only; preserve old trees.

Changed Brightness now passes genuine locked check, full-app native test
compilation/execution and release. The binary test route selects the original
application manifest/package/default features, validates compiler package,
src/main.rs, complete resolved features and owned native target ELF before
freezing/running. Five production command tests pass and repeat; they do not
exercise receiver scheduling/DDC/hotplug. Original676-entry lock graph preserved.
Release `cc2c073536834cfb0d33db32e443f8b6a3a2d02e30318ad81817ffeec41f4868`;
test ELF `c9233a03c0569e7353b4d8bfbb09a64b031c6e9164d84fc76590a36dce1f5627`.
Full source/locks/markers/logs/native artifacts are independently preserved.
No sandbox/desktop installation or runtime acceptance.

`prepare_sysinfo_rates.py` runs after managed popup routing and before
prepare_build, with exact original Git/SHA/raw-byte/ancestry/new-module guards.
Production `sysinfo_sample_rates.rs` converts existing sysinfo0.39.6 byte
deltas to decimal MB/s using measured aggregate refresh-completion intervals,
not an assumed one second or a second cumulative-counter subtraction.
First/empty/identity-changed/paused/zero-time/overflow samples remain unknown;
a genuinely sampled zero remains zero. Original filters/dedup/providers and
schema/user preferences stay intact; only default M/s labels become MB/s.
Exact original source fixture and full GPL license/notice are retained.
Five source/Git guards and five real native module tests pass. Actual original
upstream Git clone applies byte-exactly with its lock unchanged.

**Changed whole Sysinfo now passes locked check/app-test-build/app11/release.**
The same guarded original-package/target/default-feature/compiler-artifact route
used by Brightness also applies to Sysinfo; it freezes `<profile>-app-tests`.
Original664-entry graph/features and exact app/library pins preserved. Five
production rate tests plus six original application tests pass and repeat;
release537.73s. Release SHA
`8e626a5c41433eab2fca7557cae09abd92492537e868e3195cbd09bb9dca7883`;
app-test ELF `2e5e14617163b1c10c6af302333a6f4240b3eaadafdec8d819fa6e0dccf8761a`.
Fresh guarded source lives on the separately operator-approved build-only disk,
not in an overwritten earlier preparation. These tests validate compilation,
rate semantics, temperature-name matching and template parsing, not actual
provider reset/errors, simultaneous device timestamps, physical precision or
desktop/accessibility behavior. Source/source-lock/ELF receipts remain private.
Original GPU command .output() is intentionally unchanged/unbounded. Bounding
a local flatpak-spawn proxy is not proof of remote host child cancellation;
a genuine unchanged-permission cancellation contract remains required.


The four installed applet versions are preserved. Build candidates use their
exact application commits, libcosmic commits, Iced submodules and Cargo lock
versions. Fonts and semantic heading helpers are embedded with the strict
typography generators. Popup materials use the separately reviewed native
popup generator; no main-window material is enabled for these applets.

Brightness and Sysinfo's lower-level popup constructors need the small
`prepare_routes.py` port to managed `app_popup` registration. Their original
positioner, IDs, input behavior, application identity and `view_window` remain
unchanged. Status Hub already uses this managed registration.

Caffeine's exact older Iced supports XDG popups but has no native background
effect command. `prepare_caffeine_blur.py` applies only the reviewed backport to
the exact Iced submodule. It refuses changed fingerprints, unexpected revisions,
installed paths and repeated application. The existing locked
wayland-protocols 0.32.9 contains the needed v1 extension; no dependency upgrade
is required. That version's generated capability enum has a historical bit
error, so the adapter recognizes the installed COSMIC target's corrected wire
bit 1 explicitly. Zero or a missing manager keeps popup materials opaque. It
does not enable blur against the older wire-zero implementation.

Desired popup regions survive request/creation/capability ordering. One effect
object is reused per popup, unchanged requests are quiet, copied temporary
regions are destroyed, and both explicit destruction and native popup_done
clear descendants. Regions remain in surface-local logical coordinates at any
output scale. Native effect changes commit once, with ordinary frame callbacks;
there is no capture overlay, timer, polling or animation loop. Only XDG popup
roots are eligible; layers, lock surfaces, input methods and main windows are
excluded by this backport.

A genuine full Caffeine check in the Windows-hosted VM exposed E0502: popup creation retained a borrowed parent-layer handle across mutable blur reconciliation. The backport now owns the same returned toplevel handle before reconciliation (without an extra clone or behavior/geometry change). Only the patch digest and that one verified postimage changed; original source/Iced pins and all preimage/foreign lock guards remain unchanged. The fresh exact preparation passes. Its genuine full check no longer reports E0502, but reaches four inherited `-D unused-results` denials at production `blur_lifecycle.rs`83/86/120/121 (HashMap insert/remove deliberately discard old values). The updated backport explicitly acknowledges those four deliberate discard results, plus the one deliberate test-fixture reconciliation discard found by compiling the actual production module with the same denial. No original lint is suppressed or state-machine operation changed. Fresh full backend verification remains required. Seven actual final prepared module tests pass with inherited `-D unused-results`. The exact pinned Iced API defines `Size::INFINITY`; the adapter typo is corrected and that original API file is now byte-exactly guarded. Fresh genuine locked whole-Caffeine check passes (53.71s). The historical backend-test invocation refused before compilation because it requested dependency features outside the application workspace. Iteration16 corrects only routing: locked application-manifest `-p iced_winit --lib --no-run --message-format=json`, without overriding original features. Before executing the owned native test ELF, the builder requires its compiler artifact's exact local source/package and full feature set to match original resolved application metadata (including Wayland, X11/default, multi-window and program); reduced or extra coverage is rejected. Seven full-crate native backend tests pass, and the guarded Caffeine locked check/release now completes exit0. The optimized release SHA256 is `0592bc364a68ec68fc5a4bfed3996dbe91003db865ed9c8b615ce4f075bca8a6`; test ELF `c7879f17af63ed8964377d97bc3059468b10c6c2e954c3f284d744a52ae239d9`. Both native x86-64 ELFs, resolved libraries, source/lock markers and full phase logs are retained privately. This is compilation/native unit-test evidence, not compositor protocol, rendering or sandbox-runtime certification. Independent Brightness/Sysinfo/Status Hub metadata attempts each refused before compilation and restored original locks byte-exactly. Saved metadata shows only same-version `build_helpers` Git-to-local identity changes; original manifests byte-match each exact pinned Iced submodule. Iteration17 classifies only the reviewed `iced/build_helpers/Cargo.toml`, requiring its byte-exact original manifest, exact library pin, parent submodule entry and matching Iced checkout. Lookalike repositories, wrong paths/bytes/pins and foreign checksum/version changes are refused. Fresh independent metadata graphs now pass with original foreign checksums intact; Brightness, Sysinfo and Status Hub locked checks/releases all complete exit0 (optimized releases5m45s/4m26s/2m23s). All three genuine native x86-64 ELFs/markers/locks are frozen externally with matching hashes and resolved dynamic libraries. These check/release-only profiles do not claim native app unit tests. All four reviewed native applet candidates now compile; unchanged-sandbox/permission/OSTree/runtime validation remains open. No foreign exception or sandbox permission change occurred. All failed trees/reports/caches remain retained, not repaired in place. Three portable source regressions protect clone ordering/fingerprints and run real `git apply --check`/application against the compressed exact original `state.rs` fixture (original SHA-256 remains in the profile; upstream Iced MIT notice is alongside it). The fixture test disables CRLF conversion only for that Git command, rather than changing host policy or accepting alternate hashes. These checks do not prove backend compilation.

The seven lifecycle tests live in the same production `blur_lifecycle.rs` module.
They can run with `rustc --test` independently of the shared Cargo build queue.
Full backend/app compilation and an actual private Wayland protocol fixture are
separate validation steps and must pass before deployment.

`prepare_build.py` records the complete app/library source and embedded resource
inventories, recursive submodule files, selected generator inputs and local crate
overrides. Reuse rejects any source or generator drift. Its original upstream
lock snapshot allows only the exact native crates' Git-to-local source
substitution; all package versions and other sources/checksums remain fixed.
This permits Cargo to record local paths without allowing dependency upgrades.
`build.py` first lets Cargo normalize the already reviewed local source aliases
without compiling. Preparation then compares the complete locked package graph
against the exact upstream lock before any build. A failed resolution or foreign
dependency change restores the previous lock and stops. Actual check, backend
tests and release commands use `--locked`, with source validation between phases.
The helper accepts an independent target and private development-header root;
it does not set `LD_LIBRARY_PATH`, stage candidates or change Flatpak settings.

## Owned-VM baseline provenance inventory

Iteration18 preserves original pinned Git-HEAD manifests/desktop metadata and
read-only metadata/history for the four explicit existing cosmic remote
`app/<id>/x86_64/master` refs. Caffeine specifies freedesktop24.08; the other
three specify25.08. Status Hub's original v1.5.13 tag resolves to its exact
reviewed app SHA. Brightness's original bundle workflow selects `testing`,
not proof of the publication's `master` baseline. No workflow was executed.

Current cosmic remote metadata matches the original manifest permissions for
Caffeine, Brightness and Status Hub. Sysinfo's current remote lacks the original
`com.system76.CosmicSettingsDaemon.*=talk` rule. Do not add that permission or
call this remote an unchanged original baseline. All four histories use generic
Export subjects, not an authenticated app-source-SHA/OSTree mapping. No Flatpak
app/runtime is installed in the VM; no candidate is staged. These preserved
recipes/remote histories narrow baseline acquisition but do not establish
installed rollback, sandbox symbol resolution or runtime provenance. Current
remote versions are not silently substituted for the historical baselines.

### Signed-object acquisition (iteration19)

An independent owned OSTree repository imports only the existing cosmic public
trust key and enforces commit/summary GPG verification. Explicit recorded commit
IDs override mutable refs; no Flatpak install/deploy, runtime pull, app execution
or permission command occurs. Existing installation/configuration/key hashes
remain unchanged. All acquired objects and refused partials are externally retained.

Whole payload acquisition passes for Sysinfo only. Caffeine, Brightness and
Status Hub refuse a common content object checksum mismatch (expected
`cc700d46f407c6c5ab2d5dde474366a928b7398277e61162e7f8ec06f469f07e`,
actual `194420d44c511b99b60c2dec54f7f9d14a5bfbeb343da0f7619982209cea443c`).
Iteration20 diagnoses the served archive metadata as below; no object guard is
waived or full pull retried unchanged. Read-only inspection separately verifies one valid signature
on cached Caffeine/Brightness/Sysinfo commits and reads their signed manifests.
That **partial metadata evidence does not accept incomplete app payloads**.

Signed manifests establish exact original app/library pins for Brightness and
Sysinfo; their 622/610 original registry sources/checksums also match. Original
foreign Git graphs and complete build/runtime identities still require their own
gates. Caffeine's current signed app source is `da9d91e75f3f21635160e8fa89cbde929941f429`,
not the reviewed `41edb7bc1dabfa7d0033484ca81db0ac64e32a5c`; it is refused as a
source-matched baseline despite matching SDK/603 registry declarations.
Sysinfo's signed recipe confirms the missing original wildcard bus rule. Do not
add it or call the package an unchanged original-permission baseline. Status Hub
has no acquired signed commit/manifest. All four unchanged baselines, runtimes,
installed rollback and sandbox tests remain open; nothing is staged or installed.

### Refused-object diagnosis (iteration20)

The exact advertised object endpoint serves36 bytes (HTTP200), raw transport SHA
`8692271d2a080bad6fba7ba5d05d84fdad3e6535ae60735dc8ecd8c4761a8b19`.
A bounded read-only GVariant/raw-deflate decode finds an empty regular file,
UID/GID0, no xattrs, mode0664. The installed native OSTree canonical checksum API
computes `194420d4…` from that declared metadata, exactly the refusal result.
Computing the same empty metadata with mode0644 instead gives the advertised
`cc700d46…`. Thus the served object's declared mode does not match its advertised
canonical identity. The publisher/transport history producing that inconsistency
is not established. Raw compressed SHA is not the canonical file-object checksum.

Original bytes/HTTP metadata and pure checksum computations are retained on host
and guest, with a no-write rerunnable verifier. No header is rewritten, object
reconstructed/imported, checksum/signature requirement waived or package accepted.
Seek a genuine validated representation (for example published delta/alternate
transport) and exact historical source correspondence, not an arbitrary latest ref
or a permission override. The earlier complete/partial acquisition distinctions
and all unchanged-runtime gates remain intact.

## Grouped Brightness commands (iteration22 source implementation)

`prepare_brightness_batch.py` follows `prepare_routes.py` only for Brightness in
NEW exact-source preparations. It checks the original HEAD/three Git blobs and
exact routed app postimage; exclusive patch output and existing-command refusal
prevent silently repairing prepared trees. Generator fingerprints include the
new production `brightness_commands.rs`. The original GPL source fixture/full
license/notice are retained; repository MIT does not relicense those sources.

One synchronous group action now submits one `SetBatch` watch value, and the
receiver iterates every included monitor through the original DDC path. Empty
groups retain the original no-send behavior so they cannot displace refresh.
Parent review caught this edge after the first passing snapshot; that archive
and its reports are preserved, and the corrected source is checked in a NEW tree.
Original
single-monitor/refresh behavior, gamma/clamps, delays, dependency graph and
permissions stay intact. **This is not a general FIFO**: distinct actions can
still replace an unconsumed watch value. Original hotplug/error limitations stay
open; no hardware support is asserted.

Four source/real-git-patch guards pass (revision in the tiny test repository is
explicitly mocked). Five genuine native tests compile/execute the actual new
production command module with edition2024/Rust1.99/unused-results denied. These
test the enum/helper, NOT the whole app/watch scheduling/DDC or native desktop.
The earlier full Brightness check/release applies to the older source, not this
new transform. That iteration22 gap is closed by the separate fresh iteration23 whole-app check/app5/release above; receiver/DDC/runtime gates remain open.
Do not mutate old trees/markers or call their artifacts the updated candidate.

## Same-sandbox candidate gate

Keep the existing Flatpak app ID, x86_64 architecture, master branch, runtime,
finish arguments, permissions, application arguments and panel Wayland socket
inheritance. The host's ordinary `~/.cache` is not mounted in these sandboxes.
The existing app-private cache is already mounted at the identical absolute
path on both sides:

`~/.var/app/<existing-app-id>/cache/cosmic-studio/<original-binary-name>`

After an authorized build, a candidate can be staged only at this app-private
path. Select it with `flatpak run --branch=master --arch=x86_64
--command=<absolute-app-private-path> <existing-app-id>` and preserve all original
arguments. Do not add filesystem, socket, device or bus permission overrides;
do not launch the candidate outside Flatpak. The absolute command is the only
intended launcher difference, plus the reviewed material opt-in environment.

Before any app is launched, compare its current `flatpak info --show-permissions`
and runtime/branch against the captured baseline. Run `ldd -r` on the candidate
*inside its unchanged runtime* and require no missing libraries, symbol-version
errors or unresolved symbols. Host compilation alone does not prove runtime
compatibility. Then validate the candidate in an isolated native compositor
with representative popup text, focus, dismissal, scale and high-contrast
fallbacks. The original installed ELF and launcher remain the rollback source.

`runtime_gate.py <captured-baseline.json> --app-id <existing-id>` runs only
read-only baseline checks. Add `--instance <existing-same-app-instance>` after
authorized staging to run the candidate's `ldd -r` inside that unchanged
runtime. The gate rejects a different installed OSTree commit, permissions,
runtime, branch, architecture, staging path or unintended launcher changes.

At the publication stopping point, the original exact inputs and unchanged
runtime baselines are under `work/thirdparty-font-build-inputs`. Fresh prepared
copies under `work/thirdparty-readable-build-inputs` include the final .95 popup
surround, .98 controls, neutral header styling and semantic Instrument Serif
MenuRoot roles. The earlier prepared trees are preserved rather than silently
reusing their stale markers. These task-local trees and runtime metadata are
private build inputs, not repository deployment artifacts.

All four source preparations passed their exact original dependency-lock
comparison. The portable build helper passed syntax and lock rollback checks.
That original publication preparation did not establish compilation. The later
owned-VM Caffeine check/full-backend unit tests/release pass as described above;
fresh Brightness/Sysinfo/Status Hub whole builds also pass. No unchanged-sandbox runtime, permission/OSTree provenance or visual/input pass is inferred from those host-native builds. Their unchanged-runtime `ldd -r` gates and private Wayland
visual/input checks are still pending. No candidate was staged, launched or
installed; no Flatpak permissions, SDK, version or live app process was changed.
The independent lifecycle tests are source-level evidence and do not substitute
for those unfinished checks.
