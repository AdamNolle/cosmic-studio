# Native font coverage

The system font configuration is Archivo, and supported semantic display
headings use Instrument Serif regular. Stock libcosmic has a configurable
`CosmicTk/v1/interface_font` but no independent heading-family key. Native
`font::default`, text-input/dropdown text and applet text read the configured
interface family. Stock title helpers select its bold or semibold weight.
Changing Fontconfig or GTK cannot change those native heading assignments.

The reviewed native patch assigns Instrument Serif to `title1` through
`title4` and `heading`, retaining existing sizes and line heights. Small
caption headings remain Archivo. The embedding patch adds the ten authentic
faces and complete OFL notices to the existing native startup loader. It keeps
Open Sans, Noto Mono and normal native glyph fallback. Configured interface
family overrides remain supported; only the absent-config default becomes
Archivo. Fonts load once through the existing static-byte deduplication, with
no filesystem polling, font conversion, web request or per-frame work.

At the publication checkpoint, the supported Archivo toolkit configuration is
applied and previously built native candidates include authentic startup fonts
and the canonical display helpers. The compiled compositor candidate's native
font-database test passed. The latest additional menu-heading and shell-title
roles are source-prepared and fingerprint-verified, with rebuilds still pending.
These checks do not establish the font of every currently running window.

| Installed component | Exact source revision | Native library revision | Candidate binaries |
|---|---|---|---|
| Menu bar and dock applets | `82e7cd814addb0641959b634227fe550374e195b` | `03c8f93b294ad239ea935f6dd3c14a15acde8d0d` | `cosmic-applets`, `cosmic-panel-button` |
| Notifications | `aa4dac2702506395ab76da1f6755e03b2ccb0db8` | `d921602cde8248c070b493ce43b0edd388e19b9a` | `cosmic-notifications` |
| Volume/brightness OSD | `3faadf56bdaea4b088ea8dc5e808b167cec86de3` | `d921602cde8248c070b493ce43b0edd388e19b9a` | `cosmic-osd` |

The applet library pins Iced `6f1b3a71704c4074fad03b3bd6a4203f69556c9e`;
notifications/OSD pin Iced `87e1787fbb9b924576e6f6ea2ef2f45d0729e63d`.
Use separate isolated clones and initialize their exact Git submodules. Never
patch installed files or Cargo's shared source checkouts. The strict generators
validate revisions, original source hashes/shapes, native preload support and
the authentic font checksums before writing source.

```sh
python3 native/typography/embed_fonts.py /path/to/libcosmic --output /path/to/work/embed.patch --apply
python3 native/typography/patch_libcosmic.py /path/to/libcosmic --output /path/to/work/display.patch
git -C /path/to/libcosmic apply --check /path/to/work/display.patch
git -C /path/to/libcosmic apply /path/to/work/display.patch
python3 native/typography/prepare_components.py /path/to/component --library /path/to/libcosmic --output /path/to/work/component.patch --apply
cargo +stable build --release --offline --bin cosmic-applets --bin cosmic-panel-button -j4
python3 native/typography/prepare_font_tests.py /path/to/libcosmic --client-lock /path/to/component/Cargo.lock
cargo +stable test --release --manifest-path /path/to/libcosmic/Cargo.toml -p libcosmic --lib studio_embedded_font_tests --no-default-features --features applet,applet-token,dbus-config,multi-window,tokio,wayland,desktop-systemd-scope,winit -j4
```

Select the corresponding binary for notifications or OSD. Cargo requires the
native library's own workspace to run its private unit test. The font-test
preparation excludes unrelated examples and copies the client's existing lock;
it changes only private build manifests. The first unit-test dependency fetch
may need network access for native dev dependencies; subsequent runs can use
`--offline`. The first application dependency
fetch may require an online build; retain the original lockfile's registry
versions and external Git revisions. Every native package in the selected library tree must use the same isolated
source, preventing duplicate Iced types. When development headers are unavailable,
a matching distro build prefix can supply them without replacing runtime libraries
or changing system packages.

`cosmic-applets` dispatches by **the basename of `argv[0]`**, not a command-line
subcommand. The normal binary name silently returns without creating a surface.
Its launcher aliases must therefore be real symlinks to the candidate or use a
launcher that explicitly preserves `argv[0]`. The dispatch names are
`cosmic-app-list`, `cosmic-panel-button`, and `cosmic-applet-` followed by
`a11y`, `audio`, `battery`, `bluetooth`, `minimize`, `network`, `notifications`,
`osk`, `power`, `status-area`, `tiling`, `time`, `workspaces`, or `input-sources`.

The native test checks actual Binary-backed font-database entries for all ten
family/weight/style combinations and verifies that a second preload does not
increase the database face count. Merely matching `fc-match` or finding a font
name in binary strings is insufficient native renderer evidence.

Already-running stock processes can keep their startup font collection even
after the toolkit config changes. Staged native candidates activate on the next
natural process launch or desktop login; this work does not close applications,
restart an active compositor or trigger a real lock. Greeter authentication and
the safe isolated preview are documented separately in `native/greeter`.

GTK 3/4 and Qt 5/6 body fonts are configured through their supported settings,
and semantic CSS/QSS uses the regular display face without synthetic bold.
Fractional font sizes, text scaling, code/terminal fonts and separate application
themes are retained. Electron/browser native chrome can cache toolkit font
metrics; embedded website and document fonts remain under their content's
control. A process restarting naturally is distinct from a missing config fix.

The strict embedding generator also supports the installed Store, Monitor, Player
and Viewer library revisions. Their matching client source pins are recorded in
`remaining-system-apps.json`; `prepare_components.py` accepts these exact sources
and requires the original upstream lockfile. All ten faces load through the same
reviewed native startup API, and title bars use the patched semantic heading
helper. Code, fixed-width timer readouts and glyph fonts retain their explicit
font assignments. These preparations do not launch the Initial Setup wizard.

Caffeine uses a private Flatpak configuration without a host CosmicTk mount. The
typography profile conditionally copies the existing host interface font entry
into that already-installed app's private config, backing up its original absence.
It does not change Flatpak permissions or close an active app. Other audited
COSMIC Flatpaks share the host entry and the installed font files.

Third-party applet preparation preserves each installed manifest's exact native
revision. The three modern variants use the existing loader and its byte-pointer
deduplication. Caffeine's older `76c1897` renderer lacks that deduplication; the
strict old profile wraps its existing global native preload in `std::sync::Once`.
Its prepared test accesses the older FontSystem through `write().raw().db()`
and checks the same ten Binary-backed faces and unchanged second-preload count.
These are isolated source preparations, with no Flatpak permission or installed
version changes. Their separate packaging verification remains required.


Launcher, Application Library and Workspaces have exact-version source
preparations with all ten embedded faces, Archivo body text, Instrument Serif
semantic headings and the reviewed popup material. The earlier staged shell
binaries contain the canonical heading change, but do not contain the ten
embedded faces or the latest result/group/window-title roles. These prepared
sources need a new build before natural relaunch can activate their complete
font collection. Workspaces uses the `pop-os/cosmic-workspaces-epoch` repository.

The OSK preparation preserves keyboard input, symbols and its layer/input-method
surfaces; popup styling covers only ordinary tracked popups. OSK and Initial Setup
remain source preparations, and the Initial Setup wizard was never launched.
Screenshot is an Ashpd portal client without a libcosmic renderer: the compositor,
portal and notification clients own its visible text.

The compositor creates native Iced renderers directly instead of using normal
app startup. The separately fingerprinted `prepare_sdk_preload.py` exposes
`cosmic::font::preload()` and calls it before both renderer constructors. This
canonical font collection serves apps and compositor decoration text;
`std::sync::Once` avoids repeat work, including without the SDK's `winit` feature.
The font-database test passed in a compiled compositor candidate: all ten faces
were Binary-backed, and a second preload left the face count unchanged. The later
SDK menu-heading edit is a separate source change awaiting its next rebuild; it
adds no preload or per-frame work.

Typography verification accepts the user's current icon theme instead of requiring a particular icon set. A focused typography application records and verifies the exact icon-theme, monospace-font and dock-favorites files while changing only typography roots. The current Studio Dock icon theme and iA Writer Mono S remain independent of Archivo and Instrument Serif.


The additional semantic-role preparation is separate from the font startup patch. `prepare_display_roles.py` checks the exact Git revision and full input-file hashes before emitting a narrow patch. Reviewed roles are top-level application menu headings, Launcher primary result titles, Application Library group/app-card titles, Workspaces overview window titles and the Calendar's 18px selected-date heading. Descriptions, menu commands, shortcuts, search inputs, date-grid controls, tooltips, OSK keys, document text and fixed-width timers retain their existing assignments.

The menu role is applied to all 16 font-prepared SDK copies in the 19-copy material inventory, plus the separate compositor and greeter SDKs. Three original third-party input copies have no display helper and remain unchanged as provenance inputs. The three shell clients also contain their extra title roles. Each applied patch reverses to its original full-file fingerprint; all frozen glass/material/style fingerprints remain identical. The Calendar role is prepared, with its authoritative source unchanged pending its build owner's queue. These are source changes; typed compilation and activation are separate checks.

`native/build_shell.py` preparation schema 3 applies canonical title helpers, authentic font embedding, then SDK menu roles, followed by the strict popup preparation. The client dark-shell patch precedes its title-role patch. Markers include both role-generator and role-profile hashes, so earlier preparations are rejected before checkout or Cargo. A clean replay of both shell SDKs and all three clients matches the prepared font, role and final neutral glass bytes; Cargo was intercepted for this source check. Header bars, dialogs, Settings sections and selectable headings already delegate to the patched native title helpers, while the greeter's clock/date/name are explicitly covered. `display-role-validation.json` records current scope and test status.
