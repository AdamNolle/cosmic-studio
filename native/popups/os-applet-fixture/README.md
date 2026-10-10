# Native OS applet popup fixtures

These are **private test copies, never deployment candidates**. They exercise
the exact installed 82e OS applets and03c native SDK with the latest font and
material patches already applied. `prepare.py` refuses different original
calendar/tooltip source fingerprints and records complete before/after input
inventories. It modifies only two files in a new copy:

- Time's initial task schedules its existing `Message::TogglePopup` once after
  1200ms. That normal handler creates the real calendar through managed
  `app_popup`, with its native anchor rectangle, calendar contents and popup
  container. The source's ordinary time subscription stays unchanged.
- The SDK tooltip widget injects one `CursorMoved` at the first native tooltip's
  laid out center. Its actual hover handler, existing delay, shared popup ID,
  autosize, placement, no grab, empty input zone and blur request remain native.
  AppList uses this widget for pinned/running icon labels; it is a separate
  Wayland popup surface, not an in-buffer tooltip overlay.

Preparation:

```sh
python3 native/popups/os-applet-fixture/prepare.py \
  --applets /path/to/native-fonts-os/cosmic-applets \
  --library /path/to/native-fonts-os/libcosmic-applets \
  --output /path/to/native-os-applet-fixture
```

Build the copied workspace against its copied SDK after the shared Cargo queue
is released. Prefer a separate target directory. If reusing the shared cache,
first preserve the deployable production ELF in its immutable artifact path,
then immediately copy the fixture ELF into a distinct fixture-only `bin`.
Never deploy the last `target/release/cosmic-applets` after a fixture build.
Invoke the fixture dispatcher through aliases named `cosmic-applet-time` and
`cosmic-app-list` to preserve the native multicall selection.

The test compositor runner must supply a private DBus session, its own nested
Wayland socket and these environment values:

```text
STUDIO_PRIVATE_TEST=1
STUDIO_TEST_ROOT=/absolute/disposable/test-root
XDG_CONFIG_HOME=/absolute/disposable/test-root/config
XDG_DATA_HOME=/absolute/disposable/test-root/data
XDG_CACHE_HOME=/absolute/disposable/test-root/cache
XDG_RUNTIME_DIR=/tmp/short-private-runtime
DBUS_SYSTEM_BUS_ADDRESS=unix:path=/dev/null
COSMIC_STUDIO_POPUP_GLASS=1
```

Set `STUDIO_PRIVATE_AUTO_CALENDAR=1` for Time and
`STUDIO_PRIVATE_AUTO_TOOLTIP=1` for AppList. The latter also logs its one injected
cursor event. Configure AppList's private favorites and private `.desktop`
files so it has a visible icon; do not copy personal application/window state.
Both triggers fail closed without the explicit private flags, scoped XDG
directories and disabled system bus. Main `/run/user` runtimes and path escapes
are rejected. The guard's independent Rust test covers these boundaries.

Capture at least2seconds after the applets have configured. Inspect the real
XDG popup surface and its native mask in the private protocol/render evidence,
then compare the capture against the opaque no-opt-in control. A compiled
fixture and a completed visual capture are separate checks; preparing these
copies confirms neither one.
