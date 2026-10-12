# Windows-hosted Pop!_OS development VM

The Windows host edits and packages source. Native COSMIC builds and POSIX recovery tests run inside a separate Pop!_OS 24.04 guest. This tooling does not replace Windows, modify other VMs or install Studio candidates automatically. Source/build phases do not stop a desktop session; the explicitly selected `poweroff` phase performs an authenticated normal shutdown of the owned VM for boot/resource diagnostics.

## Approved build-only volume (iteration24)

The original160GiB OS disk/install guard remains unchanged. The operator
explicitly approved a separate dynamic128GiB VDI at SATA port2 on this VM only,
after normal shutdown and `PopOS-before-build-volume-iteration24` cold snapshot.
`build_volume.py` is a read-only identity/empty-disk guard, **not a formatter**.
It requires the exact original OS disk/root plus a distinct explicitly identified
empty whole128GiB VirtualBox disk. Private authenticated formatting repeated
identity and wipefs checks; original caches/artifacts, other VMs/security and
`/etc/fstab` were not changed.

Current build volume: `/mnt/cosmic-studio-builds`, nodev,nosuid; owned studio
subdirectory UID/GID1000/mode0700. ext4 UUID
`8cc60e47-3725-44b2-a9a1-42294265f707`, VBox medium
`b58f2faf-94a5-4ca5-8108-5f01407eedd1`, guest serial `VBb58f2faf-d1ed7e40`.
Root formatter/provenance receipts and all failures are preserved privately.
Native test execution is permitted; this is not a filesystem sandbox claim.

After reboot the volume needs **explicit provenance-checked remount**, never
reformatting. Check original OS identity, exact medium/serial/size and ext4 UUID,
root-owned mountpoint/provenance, then mount the existing filesystem nodev,nosuid.
Rollback: stop owned builders, unmount, ordinary shutdown, detach only SATA port2;
retain the VDI and required artifacts. Do not delete evidence or relax headroom
checks. New builds check both build-volume and OS-root headroom.

## Provision

VirtualBox must already be installed. From the repository in PowerShell:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File native/vm/provision.ps1 -Start
```

Defaults: `COSMIC Studio PopOS`, 8 vCPUs, 16 GiB RAM, dynamically allocated 160 GiB VDI under `%USERPROFILE%\VirtualBox VMs\COSMIC-Studio`. Networking uses NAT; SSH forwards **127.0.0.1:2224** to guest port 22. Clipboard and drag-and-drop are disabled. The script downloads from the same `24.04/generic?arch=amd64` API used by System76's current Intel/AMD download page, validates the URL host, byte size and SHA-256 before attaching it. The legacy `intel` API channel is not the current standard image.

Existing VM names/directories and occupied ports are refused. An interrupted download can resume. A partially created VM is left intact on error: inspect it with `VBoxManage showvminfo` and finish the failed step, rather than delete data or automatically overwrite it. `-DownloadOnly` verifies an ISO without creating/modifying a VM. ISO metadata is retained beside the disk, outside this repository. Neither a downloaded image nor a running live session is an installed OS.

Install only onto the new virtual disk using the Pop!_OS installer. Do not attach physical disks. Create a dedicated development user and retain its credentials locally, not in this repository. After installation, eject the ISO, boot from the virtual disk and take a clean snapshot before changing guest packages or desktop settings.

### Guarded headless installation

Alternatively, `install_guest.py` drives the **official installed distinst CLI**, not a replacement distribution installer. It is read-only by default and refuses non-VirtualBox/non-live/non-Pop!_OS environments, non-EFI boots, mismatched disk serial/size/model, partitions, read-only devices, filesystem signatures and non-ISO source images. It requires the caller to supply the identity of the newly created disk; it never guesses the first usable disk.

With verified live-user SSH configured in a private `ssh-live.conf`, copy `install_guest.py` into that guest's home. Run the Windows driver in PowerShell, supplying the disk serial from the new VM and its actual casper ISO directory:

```powershell
python native/vm/run_install.py --root <private-vm-directory> --expected-serial <new-vm-disk-serial> --expected-bytes 171798691840 --iso-root /cdrom/<actual-casper-directory>
# Add --install only after the read-only preflight passes and the new blank disk is confirmed.
```

The proposed layout uses a 1024 MB EFI boundary, root, and 8192 MB disk swap (`distinst` uses decimal MB for `M`, not MiB). The attached verified ISO and VM snapshots provide recovery. The driver repeats preflight before installation. It creates a high-entropy `studio` development password in an owner/SYSTEM-only Windows credential file outside this repo, transmits it through **binary LF-only private stdin**, never uses a password argument, and redacts credentials from installer logs. Successful distinst execution still leaves first-boot and desktop validation pending. Any failure leaves the disk intact for inspection; it does not delete a VM or automatically wipe/retry a partially installed disk.

Git Bash/MSYS rewrites Linux-looking arguments when launching Windows executables. When launching this driver from Git Bash (including a Git-Bash-backed terminal overlay), prefix **that one command** with `MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*'`. Do not disable path conversion globally.

## Guest access and dependencies

Use SSH public-key authentication for the development user. Disable SSH password authentication once key access is verified; leave root SSH login disabled. Use a dedicated SSH config with quoted file paths, `IdentitiesOnly yes`, `StrictHostKeyChecking yes`, no agent/X11 forwarding, and a console-verified host key. Windows OpenSSH 9.5's key scanner can choose an unsupported `sntrup761x25519` KEX; an installed compatible Git OpenSSH scanner can fetch the public key without weakening the guest's crypto policy. Compare its fingerprint with the guest console before saving it as trusted. Keep the private key on Windows, never inside a source snapshot. Verify the guest's host-key fingerprint from its console before trusting it. The NAT rule restricts the forwarded port to the Windows host; it does not configure or authenticate the guest SSH server.

Run inside the installed guest as the desktop user:

```sh
bash native/vm/bootstrap.sh
python3 native/vm/verify_guest.py
```

The bootstrap uses `sudo` only for development packages. It verifies Pop!_OS 24.04, fetches rustup from its official site, and does not apply appearance settings or replace binaries. Dependency installation has been exercised in the installed guest; actual native builds remain a separate gate. Never remove default upstream features or bypass source guards to hide failures.

For owned non-TTY SSH setup, `bootstrap.sh --sudo-password-stdin` authenticates normal sudo calls using private stdin (no NOPASSWD or login-policy changes). It unsets the in-memory password before rustup; the official installer is retained under the guest's `.cache/studio-vm-bootstrap/`. After source extraction into `~/cosmic-studio` and installed-user host-key verification, the Windows adapter retains private logs:

```powershell
python native/vm/run_guest.py --root <private-vm-directory> --phase bootstrap
python native/vm/run_guest.py --root <private-vm-directory> --phase verify
```

`console_password.ps1` submits the private credential through the owned VM's **COM keyboard API**, never password/key-code process arguments. It requires `-PasswordPromptConfirmed`: visually verify a protected prompt first, never send it blindly to a shell. Credentials must be outside the repo; the helper is restricted to `COSMIC Studio PopOS` and the specified dedicated account.

Use a temporary **sleep-only** systemd inhibitor during long owned-guest jobs, leaving screen locking/authentication intact. Generic 28 entered s2idle during unattended live setup; keyboard wake failed, and the ACPI event eventually powered it off. A cold pre-first-boot snapshot protects the installed disk. On this Windows NEM backend, default disk boot stalled; a one-boot systemd-boot edit with `clocksource=acpi_pm tsc=unstable` reached greeter/TTY/SSH and successful local authentication. This is a diagnostic VM workaround, not hardware/performance certification. Preserve stock boot configuration, document any persistence, and verify repeat boot before calling it reliable.

`configure_clock.sh` guards the exact validated guest/kernel/clocksource, backs up original kernelstub and EFI loader configuration under root-only `/var/lib/cosmic-studio-vm/boot-original`, then adds only `clocksource=acpi_pm tsc=unstable`. Transfer and syntax-check the script before selecting `run_guest.py --phase clock`; it authenticates normal sudo through private stdin. Rollback: `sudo kernelstub -d "clocksource=acpi_pm tsc=unstable"`. On the owned build-28 guest, an authenticated normal shutdown followed by a cold boot with the approved **8 CPUs** reached SSH with `acpi_pm` and preserved stock boot options. This is one cold-repeat result, not loaded stability or hardware certification. Cold snapshot `PopOS-development-ready-clock-candidate` also preserves the development-ready stock baseline.

`--phase inhibit` creates a reboot-scoped transient `cosmic-studio-build-inhibit` unit that blocks **sleep only** during owned builds. Stop with `sudo systemctl stop cosmic-studio-build-inhibit`; it does not inhibit screen locking or change authentication. `--phase poweroff` requires the retained credential and performs normal systemd shutdown, ignoring the owned setup inhibitor; SSH may disconnect before returning a success code. Confirm actual VirtualBox power state independently—transport disconnect is not shutdown proof.

## Transfer an auditable source snapshot

Export only tracked files plus explicitly listed new source files. Ignored build products, backups, VM images and arbitrary untracked files are not swept into the archive. Symlinks and escaping/private paths are refused; executable modes come from the Git index. The snapshot has deterministic bytes and a per-file SHA-256 manifest, including current working-tree edits.

```powershell
$newSources = @('.gitattributes', 'native/typography/build_os_clients.py', 'native/tests/test_os_clients.py',
    'native/vm/provision.ps1', 'native/vm/bootstrap.sh', 'native/vm/snapshot.py', 'native/vm/test_host.py',
    'native/vm/verify_guest.py', 'native/vm/README.md', 'native/vm/install_guest.py',
    'native/vm/run_install.py', 'native/vm/test_install_guard.py',
    'native/vm/console_password.ps1', 'native/vm/run_guest.py', 'native/vm/configure_clock.sh',
    'native/vm/build_native.py', 'native/typography/lock_guard.py', 'native/tests/test_lock_guard.py')
$includeArgs = foreach ($source in $newSources) { '--include'; $source }
python native/vm/snapshot.py --output "$env:USERPROFILE\VirtualBox VMs\COSMIC-Studio\source.tar.gz" @includeArgs
# Once SSH and the guest host key are verified:
scp -P 2224 -i <private-key-path> <source.tar.gz> <development-user>@127.0.0.1:~/
```

Extract into a **new empty** guest source directory, not over a prepared tree. Export refuses to overwrite an existing archive. `.gitattributes` keeps fingerprinted source and licensed metadata at LF on Windows; it does not weaken byte-level checksum checks.

Portable host checks:

```powershell
python -m unittest discover -s native/vm -p 'test*.py' -v
python -m compileall -q setup.py native icons
```

The full guest verifier runs each suite separately and records commands, return codes, test totals and explicit skips in timestamped `work/vm-validation/` reports. Zero discovered tests fail the gate. A passing source/recovery summary **does not** establish successful native builds or feature completeness.

## Native build and runtime gates

Consult the component READMEs and existing source pins. Compile into fresh work directories, preserve original lockfile registry versions/checksums and foreign Git pins, and use the reversible installer only when installed package revisions are compatible. Builders explicitly fetch the exact pinned SHA before detached checkout: authentic older commits may be obtainable by exact fetch but absent from advertised branch ancestry. Do not substitute a new revision.

As the non-root guest user with `source ~/.cargo/env`, run `python3 native/vm/build_native.py --component compositor --jobs 4` (also `panel`, `core`, `os-clients`, or `media` for only Player/Viewer). It retains the exact builder command, toolchain/kernel/CPU/environment, an immutable per-run source-manifest copy/digest, stdout/stderr and final return code in a fresh `work/native-builds/<component>-<UTC>/`. From Windows, `run_guest.py --phase compositor` starts that same non-root compositor build detached over verified SSH (4 jobs). `--phase panel` selects the existing panel builder with 2 jobs. `--phase core` selects all four existing core apps with 4 jobs; `--phase media` selects only Player/Viewer with 2 jobs. Allow only bounded overlap and inspect RAM/disk; each uses a separate fresh work directory. A successful launch is **not** successful compilation. Inspect guest `report.json` and `build.log`. Keep all source trees, caches, manifests, logs and candidates needed to rerun verification. The common lock guard recognizes the same exact libcosmic repository with an optional `.git` suffix or single trailing slash, including the launcher's original `libcosmic/#SHA` spelling; lookalike hosts/repositories remain foreign. It resolves only equal-version original libcosmic Git packages to local paths and refuses/restores original locks on foreign registry/checksum/Git drift before locked compilation.

`--component os-clients` selects the six remaining non-media clients (applets, notifications, OSD, Store, Monitor and OSK), avoiding a duplicate media build. Windows `--phase os-clients` launches at 1 job in a separately hash-verified fresh `~/cosmic-studio-clients` source snapshot, leaving active core/media/stock builders untouched. The applet preparation includes the existing exact compact-dock patch and calendar heading; after release it records the multicall ELF only if both reviewed compact/popup feature gates are linked. Keep `artifacts/compact-dock-build.json` and both dispatcher/panel-button outputs. This is not alias deployment or runtime certification.

Windows `--phase launcher`, `--phase app-library` and `--phase workspaces` use the existing exact-pinned `native/build_shell.py` via retained native-build reports, at 2 jobs in a separately hash-verified `~/cosmic-studio-shell` source snapshot. Guest adapter components have the same short names. Each invocation gets a fresh work tree; run sequentially or inspect resources before overlap. No new shell architecture or source revisions are introduced.

`build_thirdparty.py --jobs 1` prepares the four existing reviewed applet pins in fresh `work/thirdparty-builds/<UTC>/sources`, applying the authentic fonts/menu roles, popup routes and exact legacy Caffeine backport before invoking the existing locked third-party builder. `--prepare-only` stops before Cargo. It refuses root/caller compiler/library overrides, preserves original locks/submodules, copies the immutable source manifest and executed builder, and records every command/result even on failure. Run from an independent source snapshot; it never installs Flatpaks, changes sandbox permissions, stages or launches apps. Its three portable guards are not compilation evidence. The owned generic-28 VM currently has no installed Flatpak apps/runtimes and no historical Linux private prepared trees; genuine source checkout/preparation/build and an unchanged-runtime baseline are separate gates. Do not invent an installed baseline or treat host `ldd` as sandbox compatibility.

The iteration13 Caffeine backport replay owns the original returned parent handle before mutable reconciliation; its same pinned original state applies to a byte-exact corrected postimage. An initial malformed-hunk replay remains preserved separately. The corrected all-four preparations and Caffeine metadata graph checks pass; preparation alone did not establish the remaining profiles' Cargo metadata graphs. Its genuine full check no longer reports E0502 or lifecycle lint errors after four production/one test explicit discard acknowledgments; seven actual prepared module tests pass with `-D unused-results`. The exact old Iced `Size::INFINITY` spelling is corrected with its original API file hash guarded. Fresh whole-Caffeine locked check passes53.71s; its historical backend invocation then refuses features for a dependency outside the application workspace. Iteration16 uses locked `-p iced_winit --lib --no-run --message-format=json` from that same application manifest without changing features. The actual test artifact must match the original resolved application's complete backend features and exact reviewed local source before the owned ELF executes. Seven full-crate native tests pass with Wayland/X11/default/multi-window/program coverage intact; the production guarded Caffeine check/tests/release continuation exits0. Native release/test ELFs are frozen externally and hash-verified with resolved libraries; protocol/rendering/sandbox runtime remain unvalidated. Each other profile independently refuses before compilation: saved metadata differs only by same-version pinned-native `build_helpers` Git-to-local identity. Its original Iced manifests/submodule commits are verified. The native classification is now guarded by exact path/original manifest hash/library/submodule identities, not a foreign exception. Fresh independent metadata graphs pass with original foreign versions/checksums; Brightness, Sysinfo and Status Hub check/releases all succeed and native ELFs/markers/locks are externally frozen/hash-verified with resolved libraries. Together with Caffeine all four native releases exist; unchanged-sandbox compatibility/permission/OSTree/runtime remains unvalidated. Historical refused locks restore byte-exactly and all failure logs/metadata/locks/cache remain retained. Host and Linux guards include real Git application on the licensed compressed original state, with command-local LF preservation, not alternate-checksum acceptance. Latest complete Linux source/recovery aggregate: 131 discovered, 128 passed, three explicit Blender-export skips, all eight suites/compileall exit0. OSD's locked optimized release is now frozen/hash-verified; Store and Monitor locked optimized releases are frozen/hash-verified; OSK release8m58s completed; the six-client pipeline exited0 at02:09:45Z. Its OSK ELF and graph marker are frozen/hash-verified with resolved libraries; aliases/deployment/runtime remain pending. A bounded pristine/candidate pixman-parent runtime comparison failed every strict capture case; no runtime pass or installed alignment is claimed.

The pinned Viewer is the `cosmic-viewer` package/repository, source `d820ab36b84d0fe97b9e1fb96683b9597f03ac83` (workspace 1.9.0). It is absent from the generic-28 installed package set but present in current APT catalogs. Its original `debian/control` explicitly requires NASM; bootstrap now includes it. `run_guest.py --phase media-deps` authenticates normal sudo to install only `nasm`, `zlib1g-dev` and the evidenced Viewer link prerequisite `libnuma-dev`, with no upgrades/removals. Preserve its original `libheif-rs` embedded-libheif/v1_17 features; do not disable codecs/default features to hide failures. Observed GStreamer development modules are 1.24.2 and system libheif is 1.17.6; dependency inventory is not media compilation/runtime evidence. The original embedded HEIF build reached linking and required `-lnuma`; installing `libnuma-dev` repaired the genuine linker failure without disabling codecs.

`resume_viewer.py --project PROJECT --build-dir PROJECT/work/native-builds/FAILED_MEDIA_RUN --jobs 2` retains a separate locked resume report/log, immutable original manifest and before/after complete app/library input hashes. It verifies exact original commits/foreign graph, rejects root or caller compiler/profile overrides, reuses the unchanged original target cache, and freezes/hash-checks the native ELF with `file`/`ldd`. Original failure reports/sources remain untouched. Success is compilation only; no installation/runtime claim.

Generic-28 installed versions and current APT candidates differ from the approved source pins. Do **not** waive `native/install.py` revision guards or fabricate matching package versions. The operator approved preparing genuine, unmodified source-matched stock packages and reversible VM-only package alignment after compatibility checks. This preparation/deployment gate remains pending; retain original distro packages and the cold snapshot. `--phase packaging-deps` installs only the inspected original build prerequisites (`debhelper`, `just`, packaged `cargo`/`rustc`) through authenticated sudo. The first owned-guest simulation and installation added 20 development packages, with no upgrades/removals. Original core/media/General Applet controls additionally require `rust-all`/`libclang-dev`; the phase now includes these plus original Settings recipe's `ripgrep` and recovery tool `dpkg-repack`, with explicit `--no-upgrade --no-remove`. The second simulation/installation added 11 development/recovery packages and no COSMIC upgrades/removals. Rustup remains the recorded candidate toolchain; a packaged compiler also satisfies Debian's real build-dependency checks. Do not skip these with `dpkg-buildpackage -d`.

Read original recipes from `git show HEAD:<path>`, not patched candidate contents. Compositor uses `Makefile`, not `justfile`; panel uses `justfile`. Upstream Debian clean/vendor hooks can resolve dependencies without an explicit lock flag. Plan locked vendoring and byte-exact original-lock verification before no-pre-clean Debian builds, preserving recipe/default features rather than silently running unlocked resolution. Publication metadata must accurately identify actual pristine source commits, not label unrelated binaries with matching versions.

`build_stock.py --component cosmic-comp --jobs 1` (also `cosmic-panel`) builds in a new stock work tree as a normal Linux user. It fetches the full reviewed SHA, verifies pristine tracked code/submodules, preserves original locks/changelog, checks real Debian prerequisites, vendors with `cargo vendor --locked`, and runs the unchanged upstream Debian recipes with `dpkg-buildpackage -b -nc -us -uc` and bounded jobs. No dependency/feature checks are skipped. The sole tracked alteration is a truthful local publication stanza/version containing the actual full source SHA. Caller profile/flag overrides are refused; original rust-toolchain selection is respected and recorded. Locks and pristine code are rechecked before publishing .deb hashes/control reports. The tool does not install anything.

Windows `--phase stock-comp`/`stock-panel` launch the tool at 1 job in a separate source snapshot `~/cosmic-studio-stock`, preventing mutation of active Studio candidate inputs. Extract a hash-verified complete source snapshot into that fresh directory first. Keep source/codecs/default features, vendor.tar/config, toolchains, package logs, original locks, .buildinfo/.changes and .deb outputs. Local package compilation is not compatibility, installation or authentication evidence. Unsatisfied dependencies or protocol incompatibilities are blockers, not reasons to weaken pins or package checks. Never bypass its revision checks to install an incompatible candidate.

The ISO-installed COSMIC versions are absent from current APT indexes and local `.deb` cache. `apt-get --print-uris download PACKAGE=INSTALLED_VERSION` failed for the inspected installed COSMIC packages; current candidates are not rollback substitutes. Before alignment, preserve accurate repacked installed-package recovery (explicitly tagged as repacked), original hashes/control/configuration, and a new cold pre-alignment VM snapshot after all builds finish. Earlier cold snapshots remain recovery checkpoints but would omit later build evidence; export necessary artifacts before relying on restoration. A passing `dpkg --audit`/APT dependency simulation is not source/protocol or runtime compatibility.

[EGL/native-window tracing preparation](../compositor/probes/tracing.md) verifies original Smithay dynamic symbol loading and bounded API-only instrumentation without launching another compositor trial. Seven reviewed diagnostic packages were added after zero-upgrade/removal simulation; all existing installed versions remained unchanged. Native EGL invalid-display canary results preserve error semantics, while native-window lifetime calls are explicitly mock-only. Retained qualified-symbol review/source guards reject malformed evidence and never certify rendering or invent PID/thread ordering. Iteration18 subsequently ran one bounded unchanged-pristine child trace with verified owned parent/socket and child-only limits. Strict image gate still fails; interrupted raw streams remain refused. An explicitly labeled completed-prefix review retains all raw hashes/boundaries and observes surfaceless plain-swap BAD_SURFACE, recreation BAD_ALLOC and later same-surface-token successful swaps. No actual EGL_CONTEXT_LOST or complete native lifetime/thread mapping is established. Original four-app Flatpak recipes and current remote metadata/history are preserved, not installed baselines: Sysinfo's current remote omits an original wildcard bus rule and exact app-source/OSTree mapping remains open. Targeted Linux trace4/host VM29 source guards pass; full Linux aggregate remains131/128/3 from iteration17.

Iteration19 adds an exact-fingerprint candidate-only Winit correction after normative buffer-age/original-code review. It restores the same backend's owned window binding before age and submission, without editing Smithay, locks or pristine packages. The initial whole-State helper borrow failed native checking with E0499 and remains preserved; the disjoint backend-only correction in fresh `~/cosmic-studio-winit-binding-corrected` passes locked check49.69s and 12 native compositor tests. That release subsequently completes87s/exit0 and is frozen with its native test ELF in iteration20; original683 foreign graph entries remain unchanged. One bounded glass1 repaired-candidate capture still fails the strict gate on a uniform1280x800 image despite protocol exits0 and absence of earlier submission/BAD_SURFACE log markers. Parent/child/runtime cleanup and independent rejection are preserved; no second renderer trial/deployment follows. New three source guards pass on Windows/Linux. A fresh full Linux `verify_guest.py` from that root passes135 discovered/132 passed/3 explicit missing-Blender-export skips, eight suites+compileall0; external `iteration-19-linux-command.json` records exact command/environment/source archive.

Separate owned OSTree acquisition uses original cosmic public trust plus explicit recorded commit IDs and mandatory GPG verification, never Flatpak installation or permissions. Sysinfo payload acquisition passes; three others retain a common object checksum refusal. Read-only signed cached manifests authenticate Brightness/Sysinfo app/library declarations and reveal Caffeine's current app SHA differs from the reviewed pin. Sysinfo's signed recipe confirms the original wildcard permission is absent. Those limited proofs do not establish four unchanged installed baselines, runtimes or rollback. Complete signed objects/refused partials, public trust and initial Winit failure are externally byte/mode/UID/GID verified in a 110-file archive. No actual renderer, sandbox deployment or final-desktop pass is inferred. Iteration20's read-only raw36-byte published object diagnosis finds empty-file mode0664 whose native canonical checksum is the refused194420d4…; hypothetical mode0644 computes the advertisedcc700d46…. Raw bytes/HTTP metadata/GVariant decode/pure checksum verifier remain external. No header rewriting/object import, acceptance or signature/checksum waiver occurred; publication history remains unestablished.

Current private configuration recovery and cold snapshot are preserved: `PopOS-pre-alignment-built-evidence-iteration16`, UUID `e61ceb91-d2c6-48f6-a025-43fc42f34f80`, taken only after independent poweroff confirmation with builders idle. Configuration inventory/tar payload/symlinks/modes/UID/GID and the protected external copy are verified. Another cold boot reached stock greeter/strict SSH with eight CPUs and only the previously approved clock flags. This is stock recovery/boot evidence, not candidate authentication or protocol compatibility; later Caffeine artifacts are externally retained separately.

Validate combined compositor, panel, shell clients and application candidates in owned isolated sessions before staging a later guest login. Preserve the stock session as recovery. Keep source/build/runtime evidence distinct: source preparation, Cargo success, shader timing and actual desktop behavior are different gates.

VMSVGA graphics, Windows Hyper-V coexistence and the guest graphics driver may limit accelerated Wayland rendering. Record the actual backend and fallback. VM tests cannot certify real multi-monitor/KMS behavior or hardware performance. Unsupported checks remain blocked, not marked complete. Authentication requires its own greeter/locker checks, not screenshots alone. Private screenshots, logs, SSH keys, disks and recovery manifests stay outside tracked source.
