# Native popup material

The default package changes native Iced/libcosmic XDG popup surfaces. It preserves
ordinary window material and opaque work areas while making ordinary focused
HeaderBar icons neutral under the same opt-in. An optional, separately gated native GUI
profile gives approved application windows a stronger backing, described below.
Neither profile changes preferences, icons or compositor rendering. The compositor
separately supplies native GPU backdrop effects for surfaces requesting blur.

`COSMIC_STUDIO_POPUP_GLASS=1` is an exact, process-start opt-in, cached once with
`LazyLock`. No environment lookup occurs during a redraw. The desktop wrapper
must export this variable for a rebuilt client; this generator does not install
wrappers or set the user's environment.

## Material and capability contract

- `Cosmic::theme(id)` recognizes only tracked `SurfaceIdWrapper::Popup` IDs.
  Other IDs keep the existing active theme. A popup receives its own theme clone;
  global `THEME`, `Core::frosted`, and `frosted_windows` remain unchanged.
- Popup automatic blur can opt in independently of whole-window frosting.
  Explicit `LiveSettings.blur` takes priority over automatic policy during
  creation, popup opening and all five theme/config/capability refresh paths.
- Protocol support must be confirmed by the existing native `BlurEnabled` event.
  If support is absent or the surface disables blur, the popup remains opaque.
- High-contrast palettes always retain their exact original opaque containers,
  including when the protocol is available and a surface explicitly asks for
  blur. They receive no tint, palette derivative or automatic blur request.
- Popup requests use `iced_winit::commands::blur::blur` for the actual Wayland
  surface. Ordinary windows retain the native window dispatcher. Requests are
  bounded to the existing popup size/region lifecycle.
- Popup background, primary and secondary container tints use alpha **0.95**;
  neutral container/menu controls use at least **0.98** in their resting,
  hover and pressed states. Active labels remain fully opaque. Ordinary text
  buttons use neutral labels; links, suggested actions, focus and selected
  states retain their native semantic accent. Disabled labels retain native
  differentiation. Palette hues, fonts and the user's corner radii are retained.
  Neutral divider alpha is capped at 0.24 so there is no opaque black rim.
  Configured corners retain their exact native shape. This introduces no custom corner radius.
- The tinted palette cache holds at most two entries and retains the source Arc
  to prevent pointer reuse. Theme changes rebuild a palette; ordinary redraws
  clone an Arc. Main content, documents, terminal/editor text and font caches
  receive no extra rendering work.
- Popup clear styling uses that popup's palette even when its main window is
  maximized. An opaque main-window clear cannot hide the popup material.
- Ordinary focused HeaderBar icons use the native background foreground color
  when the popup opt-in is enabled and high contrast is off. This also covers
  opaque Editor/Terminal windows, unknown IDs and original parent palettes;
  it does not require window glass or private material-cache identity. Native
  inactive chrome, high-contrast colors and semantic button/link/focus/selected/
  destructive states retain their exact style. Each original HeaderBar source
  is strictly fingerprinted before this one class rule changes.

In-window overlay dialogs/popovers share their parent buffer and keep existing
opaque styling. A compositor cannot refract content within that opaque client
buffer. They require promotion to a distinct XDG popup or a separate native
client render pass; this patch does not apply whole-window opacity to imitate it.
Third-party clients that paint their popups opaque are also outside this native
client patch.

## Optional native GUI windows

`--window-glass` adds a separate `COSMIC_STUDIO_WINDOW_GLASS=1` process-start
opt-in. It is supported only for six inspected toolkit revisions used by Files,
Settings, Store, Monitor, Player and Viewer. Deployment should export this flag
only in their reviewed application wrappers after native compile/palette checks;
Edit, Terminal and document applications retain their existing opaque material,
even when they share a patched toolkit. The popup flag stays independent.

Native `Core::frosted` and `Core::blur` window policy can opt in without changing
the user's global `frosted_windows` preference. The client still requires the
native background-effect capability before enabling transparency. High contrast
keeps the exact original opaque palette. Maximized, fullscreen and tiled windows
follow the native `frosted_maximized_apps` policy; native geometry events refresh
the exact window blur request, including disabling a previous request.

Only Window IDs receive window material. Popups use their independent profile;
layer and input-method surfaces are excluded and retain their native clear style.
Untracked IDs must be the actual main window; additional windows use native
AppWindow/get_window registration. A
tracked non-window type always takes priority. Opaque Window fallbacks own an
exact source-palette clone whose Arc identity gates the Window clear style, so
a Files desktop layer cannot be mistaken for an opaque window. Explicit surface blur overrides
remain authoritative for requests, and high contrast/maximized policy can keep
the foreground opaque. The window clear style uses its actual per-surface theme
so stale global state cannot defeat an opaque fallback during a geometry change.

Window/background chrome uses **0.95** backing; primary/secondary content and
neutral controls use at least **1.00**. Active labels stay opaque, ordinary text
labels are neutral, and native links, selection, keyboard focus, suggested and
destructive states retain their semantic colors. Native header-bar controls keep
their existing neutral hover/pressed state machine and the user's corner radii.
The palette cache is keyed by source, Popup/Window profile and opacity, bounded
to four entries. The default popup-only output is independent
from the optional window additions.

## Strict pinned compatibility

`compatibility.json` records complete upstream commit IDs, primary source URLs,
and SHA-256 fingerprints of the seven checked inputs for thirteen toolkit versions:

| Native family | libcosmic revision |
| --- | --- |
| Panel and Store | `23f5d63fed2a370f3c2f54b90ec8f0896fe82105` |
| Launcher and app library | `8cb86195ec576064ac8e59e9200315714d17dc55` |
| Workspaces | `8cb10bf6e24b86a7d2a9cf8c662d3e0154db1b21` |
| Files, Edit, Terminal | `08a09e3dfa1f729d52585fcedd6e731130235363` |
| Settings | `d77e99fb1555e2728297677de61e23ada4d9d09b` |
| Panel applets and Monitor | `03c8f93b294ad239ea935f6dd3c14a15acde8d0d` |
| Notifications and OSD | `d921602cde8248c070b493ce43b0edd388e19b9a` |
| Player | `9cc82abd9ca5601bb0341edd12a9acbc97e77801` |
| Viewer | `eaa7a5a24c4359ebeaab507855388942e8984d5d` |
| External-monitor brightness applet | `dc1cf9f00cbe2902a52166492654bb9fee8a73d1` |
| System information applet | `1f8d8786940cc6db59d412153c5a03f69a20375c` |
| Status Hub applet | `a401af8b1c54a8abd393b8c5b7c8809402f83850` |
| OSK managed popups only | `87ab8179e1bd9880239c340855ae8862034bd0e8` |

The generator requires an explicit revision. When Git metadata is present its
HEAD must match; for a source copy without Git metadata the checked files must
match the declared revision's fingerprints exactly. It refuses upstream shape
changes, already prepared inputs, installed system sources and Cargo checkouts.
Font patches in unrelated source files remain intact.

## Generate and review

Use an isolated checkout or source copy; build it with its original locked
dependencies and native features. Python 3.11+, Git and the Rust toolchain are
required for generation/build/validation.

```sh
python3 native/popups/prepare.py work/libcosmic-native \
  --revision 23f5d63 \
  --output work/native-popup-23f5d63.patch
```

Inspect the emitted patch, then use the same arguments with `--apply` to apply it
to that isolated source. Generation runs `git apply --check` before applying.
Reversal uses `git apply -R` on that exact patch in the same isolated directory.
Build and deployment remain separate. This script does not launch clients or
restart any user session component.

For the separately gated window profile, add `--window-glass` when preparing the
fresh supported native GUI source. Apply authentic embedded fonts first using
the pinned typography generator; its unrelated source edits are preserved.

## Tests and limits

```sh
python3 -m unittest discover -s native/popups/tests -v
```

Tests apply generated patches to all thirteen original pinned source snapshots,
preserve unrelated font work, reject changed/repeated inputs, and compile/run
the actual Rust policy/material functions. They cover exact cached opt-in,
override precedence, absent-protocol/high-contrast opaque fallback, light/dark
neutral controls and fully opaque active text, preserved semantic accents and
configured corner radii, unchanged source palette, retained preference and Arc reuse.
Optional-window tests additionally check strict six-version support, profile
cache separation, independent opt-in and native maximized/accessibility policy.
The actual palette check uses prepared native `cosmic-theme` code, the native
application's lockfile and its existing target cache:

```sh
python3 native/popups/check_native_palette.py /absolute/isolated/libcosmic \
  --lockfile /absolute/native-application/Cargo.lock \
  --target-dir /absolute/existing/native-target
```

It tests actual light/dark foreground contrast against black, white and saturated
backdrops for all container layers and neutral controls, requiring at least 4.5.
It also checks exact high-contrast fallback, original opaque content containers,
corner radii and semantic accent/error/icon/link colors. This runs a native unit
test binary and opens no graphical client. The stronger 0.95/0.98 popup backing follows the user’s request for much
less transparent glass. The earlier 0.86/0.94 variant passed the native
contrast checks; a 0.78/0.90 study failed the dark-on-white check.
The compressed original-source fixtures retain their upstream MPL-2.0 headers;
the corresponding commit/source URL is in the compatibility manifest.

At the publication checkpoint, 15 portable tests pass across the strict modern
and legacy adapters. The latest 0.95 material is mirrored with exact generated
bytes into 19 isolated SDK copies. The separate font-role inventory records
16 applied source updates and three intentionally pristine font inputs; these
are source statuses rather than completed application rebuilds.

The native `08a09e3` specimen passes an optimized release build and real
HeaderBar class tests with the popup flag unset and set. Each test covers 24
original/Popup/Window palette combinations across light/dark/high contrast and
transparent/opaque states, without a window flag or material-cache identity.
Its actual native palette tests pass three checks: minimum dark contrast is
6.3254 for popups and 7.2507 for windows; light contrast is 11.7030 for both.
High-contrast fallback, configured radii and semantic colors remain exact.

Store passed a locked check with its stock PackageKit feature before the final
neutral-header/0.95 refinement. Final Store/Monitor/Player/Viewer checks and
per-SDK palette tests remain pending. Their four original lock graphs were
preserved during local native package alias resolution: all unrelated package
names, versions, sources and checksums remain unchanged. The latest native
compositor suite has passed 12 tests and the panel suite six, but the newest
native-corner optics and final optimized combined capture still need review.
None of this source/build evidence certifies main-session deployment.

These tests do not prove rendered popup layout, native GLES shader behavior,
damage propagation, grabs/dismissal or fractional-scale output. Those require
the combined compositor/client private Wayland fixture and review of the actual
buffer output before deployment.
