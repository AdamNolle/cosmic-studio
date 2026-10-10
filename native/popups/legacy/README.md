# Exact old Caffeine popup adapter

This separate generator supports only libcosmic
`76c1897d4d9a637c8aa4016483bf05fec5f10ebd` with its original Iced
`7bb364e01d6cd6c07703416828006ab497a082e6`. It requires the separately reviewed
native background-effect backport, whose public blur API and all changed
production source files are fingerprinted in `compatibility.json`. It does not upgrade dependencies, edit the Iced subtree
or relax the modern popup generator's pinned compatibility checks.

The old toolkit has no `Theme.transparent` field and stores three-element popup
tuples. The adapter keeps that lifecycle, derives an owned palette only for a
tracked `SurfaceIdWrapper::Popup`, and clears only that material's native popup
background. Original main-window/layer/input-method themes and fonts remain
unchanged. Palette cache holds at most two retained source Arcs.

Exact cached `COSMIC_STUDIO_POPUP_GLASS=1` opt-in and a non-high-contrast palette
record the desired native region at popup creation, even before capability
announcement. The native backend replays queued masks at popup creation and
corrected Blur capability announcement, and cleans destroyed popup descendants.
Translucent material additionally requires `blur::available()`; absent, unknown
or unsupported protocol stays opaque. Theme/mode/portal refreshes update or
disable requests, including accessibility changes. Backing uses .95, controls
at least .98, active labels fully opaque, unchanged semantic accent/error states
and the configured native corner radius. Ordinary focused HeaderBar icons use
neutral foreground under the same opt-in; high contrast and semantic controls
retain their native colors. No input grabs or popup geometry are altered.

```sh
python3 native/popups/legacy/caffeine.py /absolute/work/library-caffeine-native \
  --output /absolute/work/native-popup-caffeine-legacy.patch --apply
python3 native/popups/check_native_palette.py /absolute/work/library-caffeine-native \
  --legacy-caffeine --lockfile /absolute/work/app-caffeine-native/Cargo.lock \
  --target-dir /absolute/existing/native-target
```

The seven libcosmic input fingerprints must match exactly before any patch is
written. Generation checks patch application first. The compressed source
fixture preserves upstream MPL-2.0 headers; the manifest links its original
commit. Tests cover source rejection, capability fallback, cache reuse,
high-contrast/source identity and semantic controls with the actual Rust helper.
Actual backend/app compilation, native palette tests and private compositor
buffer review are separate gates before deployment.
