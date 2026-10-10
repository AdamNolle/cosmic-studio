# Native COSMIC application typography

The four core applications are rebuilt from the exact source revisions recorded
in the installed desktop packages. Each application uses its original pinned
libcosmic and original default features. The shared title and heading helpers
select Instrument Serif; body text uses the configured Archivo interface font.
Captions, terminal content, editor content and explicitly selected fonts keep
their existing font choices.

| Application | Application revision | libcosmic revision |
| --- | --- | --- |
| Files | `d1f0af78e64f9e8ddb52c486913d53a234ce3cf2` | `08a09e3dfa1f729d52585fcedd6e731130235363` |
| Edit | `bfc98bf21930fe5d9c32b7c238442499191b6319` | `08a09e3dfa1f729d52585fcedd6e731130235363` |
| Terminal | `9129277bed1e810418a3138d683c1bc15656234f` | `08a09e3dfa1f729d52585fcedd6e731130235363` |
| Settings | `7421ff0ab482c942eef23fbe9280edacfbeb35cc` | `d77e99fb1555e2728297677de61e23ada4d9d09b` |

The source matrix is also available as `core-app-sources.json`. The two
`core-libcosmic-*.patch` files preserve the exact display-font changes used for
these builds. This changes native Rust widgets directly; it adds no GTK shim,
browser rendering, screenshot overlay or per-frame font work.

## Reproduce

Use a fresh directory with sufficient space for Rust dependencies and the
original native Wayland/WGPU build dependencies. The build host needs Git,
Python 3.11 or newer, rustup with the stable toolchain, a C/C++ compiler, pkg-config
and the development packages required by the original applications (including
Wayland, xkbcommon, EGL, fontconfig, dbus, GLib, libdav1d 1.3 or newer and the
relevant GVFS libraries).
The script leaves dependency resolution to each pinned upstream Cargo lockfile.

```sh
python3 native/typography/build_core_apps.py --work work/native-core-apps --jobs 6
```

To build only selected applications:

```sh
python3 native/typography/build_core_apps.py --work work/native-core-edit-term --apps edit term --jobs 6
```

The script clones exact commits and submodules into the fresh work directory,
generates the strict display-font patch, maps every libcosmic workspace package
found in that application's lockfile to the isolated native library, and builds
release binaries. It then verifies the release build with `--locked` and runs
`git diff --check`. Binaries are under the supplied directory's `target/release`.
It refuses to overwrite existing sources and does not install, open or restart
applications.

## Validation scope

The initial desktop builds retained the default features, including native
Wayland/WGPU and the original application integrations. They are release
candidates for the existing desktop installer. Compilation does not prove every
view uses a title helper: applications with custom typography can still use their
explicit font. Existing processes load their original binary and fonts until the
user opens the rebuilt application again. No current application or main
compositor was restarted to prepare these candidates.
