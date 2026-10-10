# Compact dock icons

Keep the approved artwork at 60 logical pixels inside 66 × 72 pixel buttons, with 7 pixels between buttons and no additional panel padding. The dock uses its original `M` size; its app list supplies larger artwork directly, without the native proportional padding that made `Custom(92)` bulky. Running-app indicators retain space below the artwork. Hover and selection backgrounds sit three pixels inside each icon cell, aligning them with the glass opening. The complete row has an additional 3 pixels above and at each end, balancing the space reserved for running dots below.

`compact-icons.patch` targets cosmic-applets commit `82e7cd814addb0641959b634227fe550374e195b`. Apply it to a prepared native source checkout, then build the standalone app list:

```sh
python3 /path/to/cosmic-studio/native/dock-icons/prepare.py --source "$PWD" --apply
cargo build --locked --release -p cosmic-app-list
python3 /path/to/cosmic-studio/native/dock-icons/install.py install --binary target/release/cosmic-app-list
```

The installer preserves the old wrapper, binary and sizing in a private backup, then reloads only the dock applets. The wrapper falls back to the system applet if the installed COSMIC package changes. This build uses the existing native typography preparation and does not change other applets or applications. Icon button measurements are also used for overflow calculations.

The reviewed native shell build applies this same patch to the exact 82e source
before building the whole `cosmic-applets` dispatcher, with the matching native
Archivo/Instrument Serif and popup glass SDK. `profile.json` pins the source
revision, patch hash, and original/resulting app-list source hashes; preparation
refuses any unreviewed source change. Record the resulting ELF and lockfile after
that build with `prepare.py --source SOURCE --record-binary BINARY --output RECORD`.
The record documents source and output hashes; it does not replace running the
recorded build and checking the resulting candidate.

`native/install.py` preserves the multicall basename and enables both
`COSMIC_STUDIO_COMPACT_DOCK=1` and `COSMIC_STUDIO_POPUP_GLASS=1` for AppList.
The compact installer prefers this shared native dispatcher when its alias and
binary still match an applied native installation of the exact package version
and both reviewed feature gates are linked into the ELF. It then preserves the
shared binary instead of replacing it with an older standalone candidate.
Unowned, changed, restored or nonmatching artifacts are never selected through
this path. Neither installer changes pinned order or icon theme.

Restore the previous applet and size with `python3 native/dock-icons/install.py restore` from the repository root. The icon artwork and pinned order are not modified.

The local Trash launcher has a dedicated context menu containing only **Empty Trash Can**. This invokes the installed launcher action, which asks for confirmation before permanently emptying Trash. Other application menus retain native behavior.

Trash uses a 60 × 72 pixel cell on horizontal docks. Its additional transparent side margins replace the 3-pixel external margins used by the other cells, matching visible edge-to-edge gaps at approximately 24 pixels. The artwork and its scale remain unchanged.
