# Populated panel diagnostic prerequisites

Iteration42 inspected authenticated original and compiled39 input contracts.
**No new renderer, populated panel, native build, input or popup trial ran.**
Opening/manual hiding/deployment and final desktop acceptance remain open.

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
**the actual applet backend-to-connection call chain is not yet accepted**.
The library API alone cannot fill that gap.

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

## Retention and scoped rerun

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
