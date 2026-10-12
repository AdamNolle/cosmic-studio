# Native COSMIC compositor candidate

This candidate adds native optical glass behind `Panel`, `Dock`, tracked XDG popups and six explicitly opted-in system application windows. It is built from the installed compositor revision `0fbd4574ef4caf74769a617d205fd1fc909ac9b1`; it uses Smithay, GLES and COSMIC's native background-effect protocol and Dual Kawase blur. It does not run a web renderer, GNOME extension, screen-recording loop or overlay application.

`COSMIC_STUDIO_LIQUID_GLASS=1` opts in when the candidate starts. Exact layer names `Panel` and `Dock` are eligible. The client must request a blur region; that mask remains authoritative. Tracked XDG popups and native launcher, app-library, dialog and OSD layers use a readable surface profile when they request native blur. The separate window profile uses exact native app IDs for Files, Settings, Store, Monitor, Player and Viewer; their rebuilt client wrappers independently opt in to window glass. Input-method popups, the lock screen, notification parent layers and other opaque application surfaces retain their existing paths. A renamed panel needs an explicit source change to the allowlist. Layer namespace matching selects a visual style, not a security boundary.

The shader analytically traces screen-space rays through a curved front interface and a flat rear interface using Snell refraction, then intersects the cached backdrop plane. Three transmission samples produce restrained RGB dispersion; a fourth reflection sample and Schlick Fresnel produce edge reflections. Stable fine grain and directional specular complete the material. This is a native GLES screen-space lens, with no hardware ray-tracing pipeline or 3D scene. The latest dock geometry uses a 6 logical pixel outer corner, a 3-pixel inner corner/inset and up to 18 logical pixels of displacement. The top bar is bounded to 5 logical pixels; native popup displacement is bounded to 8 and window edges use a quieter 3-pixel profile. Popup/window optical corners follow the client's committed native corner state rather than a fixed guessed radius. The current native theme map gives ordinary windows 8-pixel corners and managed popups 6-pixel corners, while native maximized/fullscreen policy preserves sharp geometry. The optical hull follows the requested blur-region bounds intersected with the padded layer canvas, so a dock anchor gap does not form a second reflection band. Individual region rectangles remain the drawing mask. Text and icons render afterward through their existing paths; they are not filtered through this optical shader.

The compositor's existing region capture, output transforms and framebuffer damage dependencies are retained. Refraction expands the capture margin by 18 logical pixels for the dock, 5 for the bar, 8 for popups and 3 for the six opted-in window types in addition to the native blur kernel, including fractional and high display scales. Both blur ping-pong textures now stay in the renderer-owned cache and are replaced when size or renderer context changes. The shader requires four final texture samples, has no animated time uniform and reads no pixels back to the CPU. Shader compilation failure falls back to native frosting with an explicit log warning. Use a low nonzero native blur setting to preserve the visible lens bend; zero disables backdrop elements through the original compositor path.

The latest client material uses 0.95 popup/window surrounds, at least 0.98 popup controls and opaque window primary/secondary content plates and controls. Active text remains opaque; high contrast and unavailable-protocol paths retain their original opaque palettes. Ordinary native HeaderBar icons are neutral under the popup opt-in, with semantic focus/link/selected/error colors preserved. These backing values come from native Rust palette code, not whole-window opacity. The latest panel source/config increases panel backing to about 0.8832 and dock backing to about 0.7052; adaptive panel geometry and the new native-corner optics still require the final optimized combined review.

The patch also preserves the earlier audited inactive-window 0.8 logical-pixel filter and 12-pixel resize target. Those use a separate stable render identity and expanded neighboring damage. This patch explicitly initializes ordinary backdrop clipping uniforms to avoid sharing stale defocus or clip parameters. The inactive filter still renders each client surface independently rather than flattening a complete subsurface tree.

The compositor's pinned libcosmic revision is `d922ac380134c00208d2acf93947d44fb217eec5`, which differs from the panel's dependency revision. Its typography fork embeds the authentic native font faces and preloads them for manual renderer creation; Instrument Serif supplies title/heading helpers and stacked window titles. Archivo supplies interface text, while code and symbols retain their font roles. A separate 19-copy SDK role inventory records 16 applied source updates and three intentionally pristine font inputs. That inventory describes source preparation, not 19 completed application releases or rendered role checks.

### Candidate-only Winit binding repair (owned VM iteration19)

The retained pristine trace motivates a narrow binding correction, not a driver reset
claim. `EGL_EXT_buffer_age` requires the queried surface to be the current draw
surface; version-tag Mesa26.1.6 checks that same binding for plain/damaged swaps.
The downloaded Mesa reference is not authenticated as identical to the installed
Pop package. The original pinned Winit code queries age and submits without
restoring its owned window after offscreen work.

`prepare_winit_binding.py` requires byte-exact original Winit, compositor HEAD and
locked Smithay identity. It resizes through the original backend bind before age,
then restores the same owned display/context/window surface before age and submit.
Failures read the actual EGL error; no new context, surface, thread or SDK patch.
The helper borrows only the backend so the original borrowed damage remains intact.
An initial whole-State borrow failed real Rust checking with E0499 and is retained;
the corrected fresh pipeline passes locked checking (49.69s) and all 12 original
native compositor tests. Its optimized locked release completes in87s; native
release/test ELFs are independently frozen/hash-verified, and the683 original
foreign dependency entries remain unchanged. These phases do not certify EGL/rendering. Three source guards (including real fixture `git apply`) pass on
Windows/Linux, not runtime. The compressed original fixture retains its upstream
GPL-3.0-only notice and full `pinned-winit.LICENSE`, not the repository MIT license.
Pristine package builds remain unchanged. Iteration20 then performs one bounded
changed-candidate glass-enabled private capture. Fixture/capture return0, but the
1280x800 image is uniform and the unchanged strict harness returns1. The earlier
submission/BAD_SURFACE markers are absent from this log; initialization/fallback
warnings remain. Absence is not proof of correct binding, presentation or optics.
All raw artifacts and independently rerunnable rejection are retained; owned child
reaped/parent stopped/private runtimes removed. No second trial or deployment.

Build into a new work directory:

```sh
python3 native/compositor/build.py --work work/native-compositor
```

The command clones the exact revisions, initializes libcosmic submodules, applies the reviewed candidate changes (including the exact Winit repair), runs locked compositor checking/library tests and builds an optimized release binary. It refuses to overwrite an existing source directory. System build dependencies and Rust must already be available. Building does not install a binary, change the current session or restart the compositor.

Earlier candidates passed Cargo checking and optimized release builds. The native compositor suite has passed 12 tests covering optics/routing, native font loading and application chrome policy; the latest panel suite has passed six native tests. The newest committed-corner optical source still awaits its final optimized build and combined GPU review at this publication checkpoint. The geometry tests cover eligible shell namespaces, optical hulls excluding an anchor margin, output transforms and capture padding at scales 1, 1.25, 1.5, 2, 4 and 8. An isolated winit compositor on a fresh private session bus compiled an earlier lens shader on OpenGL ES 3.2 / NVIDIA 595.84 / RTX 5080. A deterministic offscreen GLES probe compiled, linked and drew the lens material and recorded GPU timer queries without a disjoint timer result. `material-timing.json` measures that shader pass only: 3,000 draws for each surface, divided into ten query batches. It excludes blur, framebuffer capture, client rendering, KMS presentation and complete desktop frame latency. It neither certifies the latest corner-source performance nor measures total desktop performance.

Compile and run that probe:

```sh
python3 native/compositor/probes/build.py --out work/glass-probes
work/glass-probes/gles-probe native/compositor/liquid-glass.frag work/material.ppm
```

The Wayland probes include a SHM background and shell-layer fixture plus an `ext_image_copy_capture_v1` capture client. They are intended for a disposable compositor with a fresh private bus and private XDG directories. They do not add or modify production protocols. Their screenshot decoder respects the returned Wayland transform. Early nesting directly under the current desktop produced inconsistent completion; nesting under private headless Weston subsequently captured the real panel and dock on the preserved forest wallpaper with active Conflux assets. Earlier popup candidates were also captured; the newest 0.95 specimen has passed an optimized native release build, real HeaderBar class tests and palette contrast checks, but its final combined optical capture remains pending. These results do not establish live-session rollout or daily KMS behavior. The main desktop bus owner and compositor were left unchanged throughout the private testing.

The Windows-hosted VM continuation exercised the real frozen candidate under private headless Weston (Mesa llvmpipe). Native fixture configuration/image-copy completed, but a glass-off frame coincided with EGL context/frame loss and the glass-on image was blank. These are retained failures, not combined rendering evidence. `probes/capture_gate.py` now rejects blank/near-uniform fixture captures, malformed P6 payloads and fatal frame/context-loss log markers; `run-isolated.py` returns nonzero on those failures. Missing-key private-default theme warnings remain visible, not silently interpreted as success. The disabled system-bus address uses the short private runtime path instead of a deep work path that exceeds Unix socket limits. Three portable fixture guards are source tests, not live runtime passes.

A later bounded VM-only comparison used a private pixman headless-Weston parent with the genuine pristine exact-source package ELF and candidate glass off/on. All three were rejected (blankness and/or EGL frame/context/submission failure); protocol exits stayed zero but the strict harness correctly exited one. Failure also occurs in pristine upstream code, so this nesting route cannot alone attribute failure to Studio or certify its rendering. Complete negative artifacts and an independent externally rerunnable rejection review are retained privately. No installed session/packages, host/security settings or source pins were changed.

The alternate private X11 route uses the already-installed rootful Xwayland with SHM, dynamic display, owned0600 MIT-cookie authorization and no TCP (never `-ac`). `run-isolated.py --backend x11` requires proof of that exact owned process/socket/auth file and refuses ordinary desktop DISPLAY; default Wayland behavior is unchanged. An unauthorized client was rejected and an authorized client accepted, but all three pristine/candidate fixture captures still failed the strict EGL/frame gate. Those raw failures and cleanup/auth evidence are preserved; no Xorg upgrade, source-pin change, native desktop/auth or rendering pass is credited.

Read-only inspection of exact original comp/locked Smithay code confirms window/display/surface ownership survives dropping the borrowed framebuffer. Binding a GLES target alone does not make its EGL surface current. The retained failures follow BAD_SURFACE at query/swap, then BAD_ALLOC during native surface recreation; Smithay maps any recreation error to its generic “context lost” label, not necessarily EGL_CONTEXT_LOST or a power-management reset. Actual invalidation remains unresolved. Before another trial, trace surface/context/display lifetimes and current draw/read targets around the first failure; do not repeat unchanged routes or weaken capture gates. No new runtime trial or compositor/SDK patch was performed for this diagnosis.

Before daily deployment, review the full compositor and panel together at login, including fractional scale, output rotation, two monitors, dock auto-hide, partial updates behind the dock, popups and session locking. The source and binary are a candidate until those checks pass. Use the repo's recoverable native installation tooling to stage a future session; never kill or replace the running compositor. Preserve the distro session as a recovery option.

COSMIC compositor code is GPL-3.0-only. This original optical shader is also GPL-3.0-only. Its visual concepts were informed by the MIT-licensed [Liquid Glass reference](https://github.com/ryohsuke1231/liquid-glass), the [LiquidGlass WebGL demo](https://liquid-glass.ybouane.com/) and [Aave's glass design article](https://aave.com/design/building-glass-for-the-web) and [Sama's optical glass example](https://glass.samasante.com/). Their web/GNOME lifecycle code is not installed or linked. libcosmic typography changes retain that project's MPL-2.0 notices.


The application chrome policy uses the exact confirmed native Wayland Spotify app ID `spotify` (also exact `com.spotify.Client`) to select one cached native dark palette: an opaque #121212 frame with #181818 primary controls. Other apps retain the selected system theme, and high-contrast mode takes precedence. It updates at creation, identity/theme events and active-stack changes without reading pixels, sampling content or polling per frame. The pinned Wayland toplevel/decoration protocol exposes no client light/dark preference; client-owned decorations still follow their application. This is a server-decoration policy, not a universal CSD recoloring claim. Provenance and event coverage are recorded in `app-chrome-policy.json`; five native policy tests complement the compositor font-database test.

`ssd-theme-specimen.c` is a local blank Wayland client for isolated validation. It requests server-side decoration and exposes either the confirmed Spotify ID over #121212 content or a light unlisted work-app ID over #f6f4ee content. It refuses the main user runtime and requires the task's private runtime under `work/`. Build it with the generated xdg-shell and xdg-decoration protocol C/H files and Wayland client library, then run `ssd-theme-specimen spotify`, `spotify-maximized`, `spotify-fullscreen` or `light` against the private compositor. Maximized/fullscreen requests precede the first commit; configure events print the accepted state and rebuild the local SHM buffer to the proposed size, bounded to 8192px per axis. This supports actual per-output dock and corner checks. No account, network, authentication or user-window controls are involved. Compilation with warnings treated as errors and all main-runtime refusals pass; rendering evidence comes from the separate private compositor harness.
