#!/usr/bin/env python3
"""Compile small native Wayland and EGL probes without touching the desktop."""
import argparse
import os
from pathlib import Path
import shlex
import subprocess

HERE = Path(__file__).resolve().parent

def run(*args):
    subprocess.run(args, check=True)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    root = args.out.resolve()
    root.mkdir(parents=True, exist_ok=True)
    cargo = Path(os.environ.get("CARGO_HOME", Path.home() / ".cargo"))
    layers = list((cargo / "registry" / "src").glob("*/wayland-protocols-wlr-*/wlr-protocols/unstable/wlr-layer-shell-unstable-v1.xml"))
    if not layers:
        raise SystemExit("Build COSMIC once to populate the Wayland protocol Cargo sources.")
    protocols = Path("/usr/share/wayland-protocols")
    sources = {
        "layer-shell": layers[-1],
        "background-effect": protocols / "staging/ext-background-effect/ext-background-effect-v1.xml",
        "xdg-shell": protocols / "stable/xdg-shell/xdg-shell.xml",
        "image-source": protocols / "staging/ext-image-capture-source/ext-image-capture-source-v1.xml",
        "image-copy": protocols / "staging/ext-image-copy-capture/ext-image-copy-capture-v1.xml",
        "foreign-toplevel": protocols / "staging/ext-foreign-toplevel-list/ext-foreign-toplevel-list-v1.xml",
    }
    for name, xml in sources.items():
        run("wayland-scanner", "client-header", str(xml), str(root / f"{name}.h"))
        run("wayland-scanner", "private-code", str(xml), str(root / f"{name}.c"))
    for name, generated in [
        ("fixture", ["layer-shell", "background-effect", "xdg-shell"]),
        ("capture", ["image-source", "image-copy", "foreign-toplevel"]),
    ]:
        run("cc", "-O2", "-Wall", "-Wextra", "-I", str(root), str(HERE / f"{name}.c"),
            *[str(root / f"{item}.c") for item in generated], "-lwayland-client", "-o", str(root / name))
    flags = subprocess.check_output(["pkg-config", "--cflags", "--libs", "egl", "glesv2"], text=True)
    run("cc", "-O2", "-Wall", "-Wextra", str(HERE / "gles-probe.c"), *shlex.split(flags), "-o", str(root / "gles-probe"))
    print(root)

if __name__ == "__main__":
    main()
