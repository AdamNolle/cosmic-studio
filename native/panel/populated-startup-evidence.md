# Populated native panel startup and protocol evidence

Iteration 47 delivered the first authenticated populated native panel startup,
verifying that both the panel and native applet successfully connect, map, attach
buffers, and receive frame completion callbacks under genuine panel manager
supervision.

## 1. Verified private no-activation bus boundary

As audited in [Iteration 46](helper-bus-contract.md), running `dbus-run-session`
without a custom configuration file inherits default session service directories,
causing `sctk-adwaita`'s synchronous decoration queries to auto-activate
`xdg-desktop-portal` services.

In Iteration 47, an explicit private bus configuration (`BUS_CONFIG`) was deployed
and verified:
- `unix:tmpdir=/tmp` listening socket.
- `EXTERNAL` authentication.
- Strict connection limits (64 completed, 16 incomplete, 32 per user).
- **Omission of `<standard_session_servicedirs/>` and activation helpers.**

### Bus probe evidence
Two negative bus queries were executed on the guest:
1. `org.gnome.desktop.wm.preferences button-layout`
2. `org.freedesktop.appearance color-scheme`

Both queries returned exit code 1 in <0.02s with:
`Error org.freedesktop.DBus.Error.ServiceUnknown: The name org.freedesktop.portal.Desktop was not provided by any .service files`
Process table scans verified **zero portal processes** were spawned (`portal_spawned: false`).

## 2. Narrow helper admission and refusal profiles

Rather than blanket-allowing descendants or disabling decoration features, a
narrow helper validation policy was enforced:
- Helper must be a direct child of the native application (`ppid == native_pid`).
- Executable must be `/usr/bin/dbus-send`.
- Maximum helper count <= 2.
- Arguments must match exact decoration queries (`button-layout` or `color-scheme`).
- Any unapproved executable, parent, argv, or count > 2 is refused and reaped.

Seven fixture cases verified this policy:
- Valid button layout: accepted.
- Valid appearance query: accepted.
- Unexpected executable (`/usr/bin/id`): refused.
- Unexpected parent PID: refused.
- Unapproved argv (`ListNames`): refused.
- Count limit exceeded (count >= 2): refused.
- Unapproved descendant fork: reaped and verified clean.

## 3. Populated native panel diagnostic execution

The complete diagnostic hierarchy was executed under independent dual supervision
(outer supervisor and surviving guardian):
- Host/compositor: `weston` (headless pixman) -> `cosmic-comp` (Winit Wayland backend).
- Original panel: `cosmic-panel` (compiled Iteration 39 release).
- Native applet: `caffeine-applet` (locked Iteration 16 native ELF).
- Override: Desktop entry `Exec` redirected to `executed-manager-wrapper.py`.

### Identity authentication
- Panel PID directly parented the diagnostic wrapper.
- `SO_PEERCRED` on inherited `WAYLAND_SOCKET` matched exact panel PID, start ticks, and UID/GID (1000:1000).
- Wrapper authenticated initial environment, designated FD 45 / socket inode 31100, and limits (64 MiB file size, 0 core).
- Dual supervisors independently authenticated exactly one wrapper and one native child.

### Wayland protocol stream observations
1. **Native Caffeine Applet (`wl_surface#36`)**:
   - Created surface, bound `xdg_wm_base`, created `xdg_surface#21` and `xdg_toplevel#22`.
   - Set app ID `com.github.codevardhan.caffeine-applet`, acknowledged configure.
   - Bound fractional scale, viewporter, and subcompositor (`wl_subsurface#27`).
   - Attached shared-memory 32x32 buffers: `wl_surface#36.attach(wl_buffer#105, 0, 0)` and `wl_surface#36.attach(wl_buffer#103, 0, 0)`.
   - Damaged buffer (`damage_buffer(0, 0, 32, 32)`) and committed (`wl_surface#36.commit()`).
   - Requested surface frame callbacks (`wl_surface#36.frame(new id wl_callback#101)`).
   - Received frame completion callbacks: `wl_callback#101.done(1113)` and `wl_callback#101.done(1327)`.
   - Handled buffer releases: `wl_buffer#105.release()`.

2. **Panel Layer Surface (`wl_surface#37`)**:
   - Bound `zwlr_layer_shell_v1`, created `zwlr_layer_surface_v1#38`.
   - Configured exclusive zone 40, size 1280x40 (`anchor Top`, `size XS`, `padding 4`).
   - Attached Mesa EGL buffers: `wl_surface#37.attach(wl_buffer#52, 0, 0)` and `wl_surface#37.attach(wl_buffer#55, 0, 0)`.
   - Damaged buffer and committed layer surface.
   - Requested and completed frame callbacks: `wl_surface#37.frame(new id wl_callback#55)`.

3. **Subsurface Integration**:
   - Applet surface `wl_surface#36` was placed as subsurface of panel hierarchy, entered outputs `WINIT-0`, scale 1.

### Clean teardown and absence verification
- At diagnostic deadline (8s native applet / 12s renderer observation), processes were signaled and reaped cleanly.
- `child_returncode_before_cleanup: null` (applet was healthy and running throughout the diagnostic).
- `status: "child-observed"`, `timed_out: true`, `cleanup_verified: true`.
- Zero lingering processes in `/proc`.
- Ephemeral XDG runtime directory removed.
- Stock configuration (`~/.config`) and state (`~/.local/state`) verified unchanged.

## 4. Open gates and remaining scope

This milestone establishes genuine buffer attachment and surface frame callback
completion under authentic panel manager supervision. It does **not** certify:
- Interactive pointer/keyboard click and toggle events.
- Popup dropdown menu rendering or positioning.
- Accessibility / screen-reader traversal.
- Full desktop session or multi-window stability.
- Physical GPU / KMS hardware presentation.
