# Populated panel diagnostic prerequisites

Iteration42 inspected authenticated original and compiled39 input contracts.
**No new renderer, populated panel, native build, input or popup trial ran.**
Opening/manual hiding/deployment and final desktop acceptance remain open.

## Iteration43: authenticated backend chain and launcher fixtures

The missing connection link is the **locked Winit fork**, not a direct Iced
`connect_to_env` call. Actual prepared chain files match their original bytes:

- Caffeine `main` → SDK `applet::run` → `MultiWindow::run_with`.
- Iced `src/program.rs` → `iced_winit::program::run` → Winit `EventLoop::new`.
- Winit `8dfaba290f9a00d3e13be71f1e6f438889cf5546` builds the Linux event loop;
  nonempty WAYLAND_DISPLAY or WAYLAND_SOCKET selects Wayland unless explicitly
  forced otherwise. Its Wayland event loop calls `Connection::connect_to_env`.
- Actual metadata selects SCTK0.19.2 for Winit; its authenticated crate reexports
  wayland-client0.31.11. CCTK separately selects SCTK0.20.0, not the same toolkit.
  Both resolve the same locked wayland-client package. The inherited-FD behavior
  reviewed in iteration42 therefore belongs to the actual source call chain.

Iced's auxiliary Wayland event loop takes Winit's owned display handle and uses
`Backend::from_foreign_display`/`Connection::from_backend`; its reviewed
connection block is original, although the whole file has accepted blur changes.
This is source correspondence, **not observed execution or connection success**.
Complete prepared app22/SDK933 input inventories, marker/lock and frozen Caffeine
ELF still match the retained native build. No dependency, feature or native code
changed; no Caffeine, panel, compositor or compiler was launched in iteration43.

A **private diagnostic-only** Python launcher now has seven real Linux
process/socket fixture cases, repeated in a hash-checked run:

1. One child receives the same inherited socket FD/inode and sends fixture bytes.
2. Raw child exit7 is retained separately from wrapper exit0.
3. Concurrent/repeated wrapper invocations cannot regain an atomic attempt.
4. Invalid FD consumes the attempt without spawning.
5. Wrong executable hash consumes the attempt without spawning.
6. Deadline cleanup reaps an observed setsid/double-fork descendant.
7. SIGTERM cleanup separately reaps that descendant.

An exclusive-create marker consumes the attempt **before validation/spawn**.
`pass_fds` preserves the designated FD, with other unrelated FDs closed. The
owned wrapper is a Linux child subreaper; it observes descendant identities,
opens pidfds and cleans/reaps those descendants rather than assuming
`kill_on_drop` handles them. Its wrapper exit0 deliberately prevents the original
manager's failure restart; **exit0 never accepts the raw child result**. A NEW
supervisor must reject refused/failed/timed-out/unexpected-child results.

These are seven helper fixture cases, not fourteen native app tests, not an
execution of launch-pad's manager, and not native Caffeine cleanup acceptance.
The wrapper has not been used by the panel. Abrupt wrapper SIGKILL/interrupted
supervision is not covered by the graceful-signal fixtures. Before populated
execution, the outer owned supervisor must independently track and clean the
actual wrapper/native descendants (including interruption), authenticate
actual executable/argv/UID/environment/FD/socket and preserve first outcomes.
Keep the genuine desktop ID/metadata and production restart policy unchanged.
No input, logind permission expansion, installed queue or stock attachment.

Four private archives retain196 regular payloads, checked SHA/size/mode/UID/GID,
including original/actual sources, both fixture runs and full input marker.
The scoped command below checks those artifacts, fresh source/storage/cleanup,
and repeats only the seven process/FD fixtures:

```powershell
python 'C:/Users/adamm/VirtualBox VMs/COSMIC-Studio/iteration-43-review-evidence.py'
```

Fresh Windows shell, cwd `C:/Users/adamm/Desktop/Code/cosmic-studio`, no compiler/
library/profile overrides. Preserve strict SSH, exact existing mounts, original
source/targets/caches/ELFs, private scripts/archives/receipts and all recovery.
Later stock-state mismatch remains unknown. App93/Linux277/274/3 are unchanged;
no independent child final verdict or populated/runtime/final desktop pass.

## Empty startup: check native size refusal before changing frame handling

The compiled39 `space/render.rs` is byte-equal to original panel
`b5cc19e351b82eed999097ced1ff267d27bf8e7a`:
SHA256 `a9823be70b64204a8fc6f9898e1e69f23df3e4bf6ca4d3d0f8b910948a3592f0`.
Its `PanelSpace::render` returns before drawing when a space event is pending
**or either actual-size/dimensions axis is at most20**. Rendering then separately
requires dirty state and `has_frame`.

Actual compiled39 `PanelSpace` starts with `has_frame: true`. Its two configure
resize branches publish EGL/viewport sizes only when both dimensions exceed20.
The reviewed layout calculation remains original: sum the mapped applet/button
lengths plus panel padding/spacing; thickness is the maximum mapped thickness
(or0 when absent) plus twice panel padding, followed by configuration constraints.
The complete layout/PanelSpace files contain previously reviewed changes;
**only the relevant size-calculation block**, not whole files, is byte-equal.

Iteration41 deliberately had no applets and padding/spacing0. Its observed
1280×8 then1280×1 configure/ack chain and absent attach are **consistent with this
native size refusal**. Neither internal dimensions nor the executed return branch
were instrumented; this is not a proved dynamic cause. Initial `has_frame: true`
also means an uncompleted requested callback alone is not proof of an initial
callback deadlock. Do not patch rendering, fake a callback or repeat that empty
run unchanged. A real mapped applet is the next distinct observation.

## Genuine native Caffeine: no-input startup only

Original application `41edb7bc1dabfa7d0033484ca81db0ac64e32a5c` and SDK
`76c1897d4d9a637c8aa4016483bf05fec5f10ebd` were exported from Git HEAD. Reviewed
main/window/applet-context source bytes match the preserved native preparation.
The existing iteration16 release remains:
`0592bc364a68ec68fc5a4bfed3996dbe91003db865ed9c8b615ce4f075bca8a6`.
This iteration did not rebuild, run or accept it as a sandbox baseline.

Original init returns no task with popup/inhibitor/deadline absent. Its own timer
subscription is absent without a deadline. But **left activation** toggles an
idle+sleep logind inhibitor; right press opens the applet menu, whose choices can
also request an inhibitor. Therefore an initial diagnostic must send **no input**,
keep a fresh HOME/XDG/private session bus and deliberately absent system bus,
and never expand permissions to make an action succeed. No auth/sleep behavior,
keyboard accessibility or popup recovery is accepted from this source audit.
SDK/session theme/config subscriptions still need their own runtime observation.

The genuine desktop ID is `com.github.codevardhan.caffeine-applet`. A private
launcher override may select the exact frozen native ELF without installing or
renaming the applet. Preserve original metadata, especially that it does not
request `X-HostWaylandDisplay`. Do not launch installed default applet lists,
use Flatpak as an unverified substitute or invent a persistent instance identity.

## Native process supervision is not yet bounded enough

Original panel `main.rs:200–211` sets exponential backoff from2ms and
**999,999 maximum restarts**. A30s deadline alone does not establish one applet
execution or a bounded number of transient children.

The panel passes a private socketpair FD as `WAYLAND_SOCKET`. Locked launch-pad
`5b516ee6a012b5ad4a5acc0cf51b4472fc6733af` preserves designated FDs by clearing
CLOEXEC in pre-exec and extends the parent's environment via `.envs`, not a
fresh environment. Its `kill_on_drop` and cancellation target the managed child;
these source contracts are not an observed descendant cleanup guarantee.
Actual inherited environment/process-group/PID/executable/argv/FD identity must
be checked, not inferred from launcher metadata.

The library contract for locked wayland-client0.31.11 is authenticated against
its original crate SHA256
`c66a47e840dc20793f2264eb4b3e4ecb4b75d91c0dd4af04b456128e0bdd449d`.
`Connection::connect_to_env` prioritizes the inherited FD, consumes/removes
`WAYLAND_SOCKET`, and sets CLOEXEC; only otherwise does it use WAYLAND_DISPLAY.
Consequently absence of that variable after startup does not prove no inherited
connection. Original Iced tree searches found no direct matching call;
the library API alone could not fill that gap. Iteration43 authenticates the
actual source chain through the locked Winit fork above; execution is still
unobserved.

Before a NEW populated run:

1. Authenticate that actual backend connection call chain and preserved ELF/
   complete prepared app+SDK inputs. No source/dependency/feature substitutions.
2. Provide a tested private one-shot launch/restart bound, preserving native
   inherited FDs. A diagnostic-only wrapper must be explicitly distinguished
   from production, deny repeated native exec and preserve first failures.
   Do not change original process-manager policies or claim a timer is a count cap.
3. Authenticate every actual child and environment/socket; enforce30s/64MiB/core0,
   reject unexpected launch/restart, stop owned launcher and descendants, and
   verify they are gone independently. Never attach stock/global processes.
4. Observe real applet mapping, panel attach and completed frame callbacks before
   any observational capture. Then separately establish popup admission, original
   keyboard input, internal consumption/effect, teardown and restoration.

A single Caffeine applet need not trigger overflow. No-input startup cannot
certify keyboard-only entry or manual hiding. Source/native/layer startup,
physical devices, sandbox/session compatibility and combined desktop gates stay
separate. Existing app93/Linux277/274/3 counts are unchanged; no new independent
child verdict or native test coverage is claimed.

## Historical iteration42 retention and scoped rerun

First collector refused a guessed upstream `LICENSE` name before runtime work;
its script/stdout/partial original exports remain separate. A NEW collector used
actual tree-listed license names. Three archives retain62 regular payloads,
with every SHA256/size/mode/UID/GID1000 checked. Original Git blobs/pins,
locked crate/license bytes, actual reviewed source copies and first failure
remain outside Git. No source/cache/target/media/recovery cleanup.

Fresh Windows shell, cwd `C:/Users/adamm/Desktop/Code/cosmic-studio`, no
compiler/library/profile overrides:

```powershell
python 'C:/Users/adamm/VirtualBox VMs/COSMIC-Studio/iteration-42-review-evidence.py'
```

This checks retained contracts and runs a fresh **read-only** guest source/ELF/
storage/cleanup check, not a renderer/compiler/test. It retains iteration41's
immediate stock-state equality separately from its later unknown mismatch;
no state reset or stability waiver. Strict installed SSH, owned VM/exact existing
mounts, original source/targets/caches/ELFs, all private receipts, VDIs/snapshots
and auth/config recovery are required. Both `candidate_runtime_pass` and
`final_desktop_complete` remain false; this is not the final desktop command.
