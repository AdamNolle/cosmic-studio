# Native lock and login appearance candidate

The isolated candidate uses the exact installed greeter source
`bfb2745176e3fd0824e008d3efb2b37bce5ae0db`, pinned libcosmic
`87ab8179e1bd9880239c340855ae8862034bd0e8`, and that library's pinned iced
submodule `5fc4372d877ad2ca6eaab1c0ca5e424f238b9258`. The upstream Cargo lock
is retained: registry and Git dependency versions are unchanged. All packages
from the native library point at the same isolated fork, avoiding duplicate iced
types. Native client code, shaping, glyph fallback, line heights, layout,
locale/date formatting, display scaling and authentication remain upstream.

The candidate embeds the ten original licensed Archivo and Instrument Serif
faces. `studio::load_fonts` adds them once to COSMIC's existing native font
system before a surface or authentication flow starts. The private greeter
library chooses Archivo for ordinary UI and Instrument Serif regular for native
title helpers; the actual shared clock widget selects the same display helper.
This also works for the separate login account, which cannot read a desktop
user's local font directory. OFL license files accompany the embedded assets.

`studio::dark_theme`, `theme_for` and `select_theme` choose process-local dark
shell material and preserve explicit high-contrast themes. Greeter user-selection
and theme-reload paths use these helpers; the real locker initializes and applies
the same selection. These helpers do not change the user's application theme or
environment. The actual date/time widget is shared by the greeter, locker and
safe appearance preview.

`build-record.json` records the source revisions, original lock and compiled
artifact hashes, release profile and completed checks. Three native release tests
pass: embedded family availability/idempotence, process-local dark selection,
and preservation of explicit light high contrast. `--help` and `--version` pass;
PAM and dav1d resolve to existing distro runtime libraries. The source checker
matches every appearance edit against its exact upstream file and checks the
untouched common/authentication and Wayland modules.

The candidate has **not** been installed or substituted for the running greeter.
The main locked session stays intact. Real password, PAM failure, fingerprint,
Caps Lock, suspend/resume, multi-output lock and login persistence are not
verified by the fixture or these tests.

## Rebuild in isolated source trees

Clone the source and library into working directories, check out the revisions
above, and initialize the library submodules. Do not edit shared Cargo checkouts
or distribution source/binaries. From the COSMIC Studio repository:

```sh
python3 native/typography/patch_libcosmic.py /path/to/libcosmic-greeter --output /path/to/work/display-font.patch
git -C /path/to/libcosmic-greeter apply --check /path/to/work/display-font.patch
git -C /path/to/libcosmic-greeter apply /path/to/work/display-font.patch
python3 native/greeter/prepare.py /path/to/cosmic-greeter --library /path/to/libcosmic-greeter --patch-output /path/to/work/greeter-appearance.patch
python3 native/greeter/verify_source.py /path/to/cosmic-greeter
```

The preparation script requires both exact revisions, validates source shapes
and authentic font checksums, copies the licensed assets, and generates portable
source patches. It adds the private Archivo UI choice to this greeter library;
other clients use the ordinary configurable UI font. The packaged
`greeter-studio.patch` and `libcosmic-ui-font.patch` contain the same appearance
edits without machine-specific Cargo paths. A fresh preparation from the pinned
sources was checked against these patches; duplicate preparation and attempts to
edit installed/Cargo-cache source paths are rejected before source writes.
Compile in the prepared greeter directory:

```sh
cargo +stable build --release --offline --bin cosmic-greeter -j 6
cargo +stable test --release --offline --lib studio_tests -j 6
target/release/cosmic-greeter --help
target/release/cosmic-greeter --version
```

This machine lacked dav1d/PAM development headers and libclang's C API. Distro
development packages were downloaded and extracted into a private work directory;
no system packages were installed. Their local pkg-config paths and bindgen
include/libclang paths were supplied **only to the build commands**. libclang is
a build dependency, not a greeter runtime dependency. Build environments that
already provide these headers need no additional variables. Preserve the native
AVIF/image features; disabling codecs merely to avoid build prerequisites would
change wallpaper behavior.

## Safe regular-window preview

The command below takes the preview branch before account selection, PAM,
greetd IPC, logind lock, or Wayland session-lock code. It creates an ordinary
Wayland window with the real native clock/date widget, title helpers, embedded
fonts, and dark selection. The password field is a disabled specimen; it cannot
authenticate. Its visible caption identifies it as a preview.

```sh
XDG_RUNTIME_DIR=/path/to/private/runtime WAYLAND_DISPLAY=studio-headless XDG_CONFIG_HOME=/path/to/private/config XDG_DATA_HOME=/path/to/private/data dbus-run-session -- /path/to/cosmic-greeter/target/release/cosmic-greeter --studio-preview
```

Use the socket of an already-running private compositor. For Weston, a normal
desktop shell respects the requested 960 × 440 initial size. Its kiosk shell
maximizes the specimen, which is useful for a large font capture but does not
represent the actual lock-card geometry. Copy native theme configurations into
the private config directory to inspect the selected palette; an empty private
config uses COSMIC's default dark accent. Keep the real user environment and
active greeter untouched.

The fixture was rendered in private headless Weston at 1600 × 1000. That proves
native font loading/rendering in this representative window. Weston does not
provide COSMIC's backdrop frosting/refraction protocol, and this ordinary app
window does not use the real greeter's session-lock surface, authentication state
or output lifecycle. It cannot establish lock-screen glass, password behavior,
login safety or display persistence.

Upstream native source remains under its original licenses:
[cosmic-greeter](https://github.com/pop-os/cosmic-greeter) and
[libcosmic](https://github.com/pop-os/libcosmic). Redistributing a built greeter
also requires the upstream GPL source/license obligations.
