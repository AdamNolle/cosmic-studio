# Native decoration helpers and private bus boundary

Iteration46 is a **source/provenance audit**, not another native trial. The
iteration45 raw startup refusal, wrapper exit0 and cleanup remain unchanged.
No rendering, input, package, feature, permission or global-service change.

## Authenticated locked caller

Original Caffeine `41edb7bc1dabfa7d0033484ca81db0ac64e32a5c` and its preserved
resolved lock select `sctk-adwaita 0.10.1`, checksum:

`b6277f0217056f77f1d8f49f2950ac6c278c0d607c45f5ee99328d792ede24ec`.

The complete cached crate was checked against that checksum; eighteen actual
registry Rust/manifest/license files match its archive bytes. Original locked
Winit `8dfaba290f9a00d3e13be71f1e6f438889cf5546` caller/manifests/licenses also
match Git HEAD. Original features retain `wayland-csd-adwaita`/`ab_glyph`.
No crate, compiler feature, SDK, dependency graph or native ELF was changed.

Winit `WindowState::configure` constructs its frame when client decorations are
selected, a subcompositor exists, no frame exists and prior CSD failure is absent.
It calls the constructor **before** hiding the frame for undecorated windows.
The constructor calls `Buttons::new(get_button_layout_config())` in the locked
crate. That function synchronously launches, without a shell:

```text
dbus-send --reply-timeout=100 --print-reply=literal
  --dest=org.freedesktop.portal.Desktop
  /org/freedesktop/portal/desktop org.freedesktop.portal.Settings.Read
  string:org.gnome.desktop.wm.preferences string:button-layout
```

`src/config.rs` SHA256:
`3c1258249f4f3ec8c524a34ea086267fff3be04b58c0b9175a7b34cdf20964f9`.
This establishes the source-level caller matching the observed query, not an
instrumented call stack or proof that every decoration constructor ran.

The method uses `Command::output().ok()`, collects stdout, and parses the last
space-delimited token into left/right layout. It does **not** check successful
exit status. Missing/unparseable layout falls back through `Buttons` defaults;
that fallback is not runtime compatibility or presentation acceptance.

Other commands in this original decoration path must not be overlooked:

- Automatic theme: another `dbus-send` Settings.Read for
  `org.freedesktop.appearance` / `color-scheme`; explicit light/dark bypasses
  only that automatic query, not button layout.
- Title font: `gsettings get org.gnome.desktop.wm.preferences titlebar-font`.
- Original ab_glyph font lookup: `fc-match -f %{file} <font-pattern>`, where the
  pattern derives from the font preference. This is not a fixed arbitrary argv.

These use synchronous output collection too. The 100ms option is a **DBus reply
wait**, not a whole-process, connection, output-size or descendant deadline.
There is no total child cancellation/cleanup policy in these crate routines.
They inherit the native environment; the native PATH was `/usr/bin:/bin`.
The existing 8s native/30s diagnostic and64MiB/core0 ownership constraints must
remain independent of the query's timeout. Helper environment, FD closure and
short-lived exec coverage were **not** authenticated in45.

## Spawn arguments versus observed command-line bytes

The45 `/proc/<pid>/cmdline` record has separate entries for
`org.freedesktop.portal.Settings`, `Read`, `string`, and each value. Those are
**not byte-identical** to the original source spawn arguments above. Preserve
both representations; do not silently normalize them into exact argv proof.

A retained [Debian DBus1.14.10 reference](https://sources.debian.org/data/main/d/dbus/1.14.10-1~deb12u1/tools/dbus-send.c)
mutates the last interface/method dot and typed-value colons to NUL in-place.
It also sets method-call auto-start true. That explains a source-consistent
post-exec representation, but the Debian source is **not authenticated as the
installed Ubuntu1.14.10-4ubuntu4.1 build**. Installed executable/package/hash
provenance is retained separately. A future identity policy needs a justified
pre/post-parse model and adversarial tests, not broad punctuation normalization.
The raw45 helper remains refused, not retrospectively accepted.

The portal log's first requesting helper PID differs from the later helper in
raw refusal. Do not attribute every portal activation to that single later PID,
or claim the polling supervisor recorded every earlier short-lived helper.

## Why fresh XDG/private DBus did not prevent portal activation

The45 runner invoked `dbus-run-session` without `--config-file`. Installed
`/usr/share/dbus-1/session.conf` includes `standard_session_servicedirs` and
permissive session send/receive/name ownership. Its installed manual documents
both XDG service paths **and the compiled-in datadir**, typically `/usr/share`.
Fresh HOME/XDG_DATA_DIRS therefore does not exclude the latter service directory.
Optional local config/includes were absent or empty at46 collection; no global
configuration was edited. This is installed configuration/manual evidence, not
instrumented service-search execution.

Installed definitions explicitly map names to:

| Name | Exec |
| --- | --- |
| org.freedesktop.portal.Desktop | /usr/libexec/xdg-desktop-portal |
| org.freedesktop.portal.Documents | /usr/libexec/xdg-document-portal |
| org.freedesktop.impl.portal.PermissionStore | /usr/libexec/xdg-permission-store |
| org.freedesktop.impl.portal.desktop.gtk | /usr/libexec/xdg-desktop-portal-gtk |

The45 raw log records desktop/document/permission-store activation, GTK display
failure and missing-GSettings-schema signal5. Those failures are not a native
Caffeine crash diagnosis. Package ownership places the document/permission-store
service definitions in the portal package; guessed standalone package lookups
returned1 in the first inventory and remain retained. Corrected named-package
inventory is a separate supplement, not an overwritten success report.

## Narrow revised diagnostic boundary — proposed, NOT tested or enabled

A future private **no-activation** bus can use an explicit owned0600 config via
`dbus-run-session --config-file=<private-config>`. It must have only the owned
UNIX socket, EXTERNAL authentication, session messaging/name ownership needed
for owned clients, bounded resources, and **no** standard service directories,
service directories/includes, service helper or systemd activation. Never include
the installed session config, edit global services, expose the system bus or
broaden permissions. No mock portal/setting response or suppressed feature.

Before using it with native apps:

1. Run a bounded bus-only negative probe: original query fails honestly with
   service-unavailable evidence, no service executable/descendant activation,
   exact bus/helper PID/start/exe/argv/environment/socket/limits and owned cleanup.
2. Test narrow helper identity/refusal profiles, including mutable cmdline,
   unexpected executable/parent/environment/FD/argv, count/deadline and escaped
   descendants. Source constructor calls are not a lifetime exec-count bound.
   Do not set generic `allow_descendants=true` or infer cleanup from child exit.
3. Preserve dual independent wrapper/native admission, surviving guardian,
   original panel peer/desktop metadata/FD, frozen ELFs and no-input policy.
   Permit only individually justified helper profiles; refuse all other children.
4. Only then consider ONE NEW populated observation. Missing settings/font
   services are diagnostic limitations, not accepted full-session behavior.
   Require object-correlated buffer attachments/completed requested surface
   frames before capture; popup/input/recovery/restoration remain separate gates.

No revised config, bus probe, helper fixture or native retry ran in46. Historical
state drift, native abrupt interruption/total-supervision loss, keyboard-only
accessibility/hiding, devices/optics/Flatpak/package/session and combined desktop
acceptance remain open. App93/Linux277/274/3 counts are unchanged.

## Preserved scope and read-only monitor command

Two archives authenticate69 regular member payloads (63 original contract,
6 supplement), including full MIT crate/license, original caller/license provenance,
installed definitions/manuals, executed collectors and prior raw45 evidence.
The public DBus reference remains separate and GPL-licensed; no implementation
source from these private archives is republished or relicensed as repository MIT.

```powershell
python 'C:/Users/adamm/VirtualBox VMs/COSMIC-Studio/iteration-46-review-evidence.py'
```

Fresh Windows shell, cwd `C:/Users/adamm/Desktop/Code/cosmic-studio`, no compiler/
library/profile overrides. Retained bytes/contracts/raw refusal, fresh read-only
strictSSH registry/installed-config/executable/native/storage/cleanup provenance,
and diff only. NO network refetch, native/renderer/compiler/input/fixture replay.
Preserve every original source/target/cache/native ELF/private script/archive/
receipt/strictSSH/exact existing mount/VDI/snapshot/auth/config recovery. Never
repeat a formatter. Both runtime/final flags remain false; not the final desktop
verification command.
