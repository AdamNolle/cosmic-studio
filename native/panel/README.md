# Native panel material and adaptive geometry

`panel-glass.patch` targets cosmic-panel `b5cc19e351b82eed999097ced1ff267d27bf8e7a`. `COSMIC_STUDIO_GLASS=1` enables the native material.

The dock has 6 logical px outer corners, a 3 px transparent inset and 3 px inner corners, with no black outline. Dock tint backing is 0.82 of configured opacity; panel backing is 0.96. Latest configurations use 0.86 and 0.92 respectively. The compositor supplies refraction independently. Native text, icons and input regions remain above the material.

Panel configuration floats with 6 px corners and an 8 px margin. A visible maximized or fullscreen window on the output invokes native square, flush geometry. Minimized windows are excluded. Cached toplevel metadata is updated for output/workspace/state transitions. Restoration uses the normal configuration.

The material is cached when geometry/palette are unchanged, with no timer, backdrop bitmap or input overlay. Tiny/vertical layouts clamp inset and corner sizes. Native Wayland blur/corner forwarding handles initial replay, changed state and unchanged commits without redundant requests.

Preserve approved compact geometry: medium size, padding 0, spacing 4, 60 px icons inside 66 × 72 px cells. The production applet source patch is documented in [dock-icons](../dock-icons/README.md).

Five actual native tests passed and the latest panel release built successfully. Source preparation and patch replay are recorded at the publication checkpoint. Combined main-desktop deployment, mixed-scale behavior, output/workspace transitions and final compositor optics remain runtime checks. Existing user windows and compositor were not restarted.
