# Pinned third-party COSMIC applets

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
No full Cargo app/backend compilation or release build has been run for these
four candidates. Their unchanged-runtime `ldd -r` gates and private Wayland
visual/input checks are still pending. No candidate was staged, launched or
installed; no Flatpak permissions, SDK, version or live app process was changed.
The independent lifecycle tests are source-level evidence and do not substitute
for those unfinished checks.
