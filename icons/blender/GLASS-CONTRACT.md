# Studio Glass construction and review contract

Purpose: instant app identification in the daily COSMIC dock and launcher,
including 24–64px displays on pale and dark backgrounds.

Art direction: a coherent collection of cast-glass app objects, near frontal,
with clear silhouettes, app-specific pigment, a concentrated upper-left white
reflection, a restrained opposing edge reflection, and beveled material marks.

Reference role: Parakeet supplies the relationships between identifying shape,
optical size, controlled depth, quiet space, and material. Lighting, geometry,
palette, and housing construction are original. No portfolio artwork is used.
The user's `design-ui` skill's icon and brand-evidence instructions are followed.

Surface system: continuous superellipse squares and selected circular objects;
shared camera and light direction; physical polished glass (IOR 1.46), shallow
biconvex volume, pigmented depth gradients, and beveled shallow mark relief.
Glass reflection belongs mainly at the boundary and upper-left corner. App
identity owns the center. There is no procedural grain to collapse into noise
at dock size. Distinct applications do not automatically share one generic
metaphor: Flameshot, GIMP, HandBrake, Kdenlive, Antigravity, and other vendor apps
retain their own identifying artwork.

Asset plan: exact identifying artwork from installed application resources,
vendor-published vectors, and original geometric utility metaphors. Each source
is recorded locally with creator, original location, SHA-256, license scope,
and edits. Vendor trademark rights remain with their owners. Local generated
vendor assets are not published from this repository.

Composition: roughly two-thirds optical mark height inside the housing, with
perceptual correction through source proportions; no stretched logos. Marks
have their own relief and contact shadow. Glass is a real closed 3D volume,
not a rim gradient. The near-frontal camera preserves recognizable contour.

Native integration and performance: all rendering occurs offline. The desktop
reads fixed PNGs at requested physical sizes through standard freedesktop icon
lookup. No renderer backend is forced. Launcher overrides preserve Wayland
Exec flags and other keys. Symbolic controls stay independent monochrome SVGs.

Review gates: representative Ghostty, Brave, ChatGPT, and Settings renders were
reviewed before propagation. A gray face and heavy colored rim were corrected
to clear optical volume, brighter pigment, stronger mark relief, and credible
reflection/contact. Full-family review then checks individual assets, nested
vendor tile removal, small-size identity, alpha edges on light and dark, and
each launcher lookup. Large highlights remain subordinate at dock size.
An artwork-quality judgment is distinct from technical build/test success.
