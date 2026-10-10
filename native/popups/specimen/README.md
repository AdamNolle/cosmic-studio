# Native popup visual specimen

This owned native Rust/Iced application creates a managed
`cosmic::surface::action::app_popup` automatically when its real parent window is
available. It uses the reviewed `08a09e3` SDK, original native foreground widgets
and actual per-popup `LiveSettings.blur=Some(true)` requests. The specimen draws
Archivo body labels, an Instrument Serif heading, neutral ordinary/icon/disabled
controls, a native blue suggested state and a menu-like trailing-arrow row.
Main-window content uses the original opaque theme. The fixture-owned palette
sets the fixture-only subtle native radius map (0/2/4/6/8/10 logical pixels)
without writing any preferences. Native Window corners add four pixels to the
small radius, yielding eight; native managed Popup corners use six directly.
The popup opens adjacent to its smaller parent so actual wallpaper refraction
can be reviewed without overlapping opaque parent labels.

Prepare in a fresh isolated directory, then compile only when the shared native
target queue is free:

```sh
python3 native/popups/specimen/prepare.py /absolute/work/native-popup-specimen \
  --sdk /absolute/work/libcosmic-core-08a \
  --lockfile /absolute/work/cosmic-files-native/Cargo.lock
```

The copied lockfile seeds the existing application dependency versions; the
first offline Cargo invocation resolves this smaller owned application graph.
Subsequent checks/builds use the resulting lockfile. The preparer verifies the
exact generated native material source and all 24 native package paths. It does
not build, start clients, alter compositor code or access the live session.

Run only in the private combined compositor fixture with private XDG config,
data/runtime paths, private D-Bus and Wayland socket. Both
`STUDIO_PRIVATE_TEST=1` and `COSMIC_STUDIO_POPUP_GLASS=1` are required;
the window flag stays unset. Positional theme argument: `dark`, `light`,
`contrast-dark` or `contrast-light`. A compositor lacking the background-effect
capability must show opaque popup material; high contrast must also be opaque.
The popup does not request a grab because its automatic opening has no input
serial. Interactive grab/dismissal requires a separate native applet review.
The owned runtime must resolve to a `cs-panel-*` directory outside `/run/user`
with mode0700, and the real Wayland socket must be owned and directly inside it.
Config/data paths must differ from the real account's home XDG paths. These
checks happen before connecting or starting native rendering.

Native unit tests invoke the actual toolkit HeaderBar class for original opaque,
Popup and Window palettes, light/dark/high contrast and transparent/opaque modes.
Run them with the popup flag both unset and set to prove the scoped neutral rule
and exact accessibility fallback. They open no UI; the runtime guard remains a
separate three-test validation of owned paths/socket/mode.
