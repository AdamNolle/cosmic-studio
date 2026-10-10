# Native dock separator

This small original Rust applet replaces the fake divider's ordinary 64px icon
button with a static rule. It uses libcosmic revision
`03c8f93b294ad239ea935f6dd3c14a15acde8d0d`, matching cosmic-applets revision
`82e7cd814addb0641959b634227fe550374e195b`.

The M dock uses a 20×56 logical pixel separator slot with a centered 1×28px rule.
Larger dock cells use a 24px slot; the rule remains bounded to 36px. Left and
right docks transpose the geometry. The neutral foreground color follows the
native light/dark theme at 28% opacity. There is no button, icon, tooltip,
click action, timer, custom render loop, or extra backdrop blur request.

The direct native Autosize widget negotiates the narrow slot through Wayland.
It does not inherit the ordinary applet icon button's minimum width. Tests
exercise the actual Iced widget layout in both orientations and verify that
the centered rule fits small and large configured bounds.

Build with an existing isolated native library and the pinned applets lockfile:

```sh
python3 native/dock-separator/build.py \
  --library /absolute/path/to/libcosmic-applets \
  --lock-source /absolute/path/to/cosmic-applets/Cargo.lock \
  --work /absolute/path/to/separator-build \
  --target /absolute/path/to/available-shared-cargo-target
```

Wait for other builds using the target directory to finish first. The helper
checks the exact library revision, reuses its workspace crates, and preserves
the upstream transitive lock versions. It builds a release candidate, runs the
layout tests, and checks runtime libraries; it does not install or launch it.
The checked-in `Cargo.lock` records the verified candidate's resolved
dependencies and may also be passed as `--lock-source`. Changed prepared
inputs require a fresh work directory. The helper includes generated untracked
native modules and embedded fonts in the library source hash and refuses a
success result if the source changes during compilation.

The supplied `local-dock-divider-applet.desktop` keeps the existing plugin ID.
Its installation can replace that desktop entry's executable while preserving
the dock's current plugin position and favorites. No dock configuration is
changed by this package or build helper.
