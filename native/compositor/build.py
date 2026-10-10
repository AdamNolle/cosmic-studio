#!/usr/bin/env python3
"""Build the pinned native candidate. Does not install or restart a session."""
import argparse
import importlib.util
from pathlib import Path
import subprocess
import tomllib

HERE = Path(__file__).resolve().parent
COMP = "0fbd4574ef4caf74769a617d205fd1fc909ac9b1"
LIBCOSMIC = "d922ac380134c00208d2acf93947d44fb217eec5"

def run(*args, cwd=None):
    subprocess.run(args, cwd=cwd, check=True)

def source(url, revision, target):
    if target.exists():
        raise SystemExit(f"Refusing to overwrite existing source: {target}")
    run("git", "clone", url, str(target))
    run("git", "checkout", "--detach", revision, cwd=target)
    run("git", "submodule", "update", "--init", "--recursive", cwd=target)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work", type=Path, default=HERE.parents[1] / "work" / "native-compositor")
    parser.add_argument("--jobs", type=int, default=8)
    parser.add_argument("--toolchain", default="stable")
    args = parser.parse_args()
    root = args.work.resolve()
    root.mkdir(parents=True, exist_ok=True)
    library = root / "libcosmic-comp-native"
    compositor = root / "cosmic-comp-native"
    source("https://github.com/pop-os/libcosmic", LIBCOSMIC, library)
    run("git", "apply", str(HERE / "libcosmic-d922-typography.patch"), cwd=library)
    run("python3", str(HERE.parent / "typography/embed_fonts.py"), str(library),
        "--output", str(root / "embedded-fonts.patch"), "--apply")
    run("python3", str(HERE.parent / "typography/prepare_display_roles.py"), str(library),
        "--profile", "native-d922ac38", "--output", str(root / "display-roles.patch"), "--apply")
    run("git", "apply", "--check", str(HERE / "sdk-font-preload.patch"), cwd=library)
    run("git", "apply", str(HERE / "sdk-font-preload.patch"), cwd=library)
    neutral_header = HERE.parent / "typography/comp-neutral-header.patch"
    run("git", "apply", "--check", str(neutral_header), cwd=library)
    run("git", "apply", str(neutral_header), cwd=library)
    run("python3", str(HERE.parent / "window-controls/prepare.py"), str(library))
    source("https://github.com/pop-os/cosmic-comp", COMP, compositor)
    run("git", "apply", str(HERE / "compositor-glass.patch"), cwd=compositor)
    run("python3", str(HERE.parent / "window-controls/prepare.py"), str(compositor), "--compositor")
    # Point every locked native toolkit crate at the reviewed typography fork.
    helper = HERE.parent / "typography/build_core_apps.py"
    spec = importlib.util.spec_from_file_location("native_overrides", helper)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.overrides(compositor, library)
    def registry_pins():
        return {(p["name"], p["version"], p["source"])
                for p in tomllib.loads((compositor / "Cargo.lock").read_text())["package"]
                if p.get("source", "").startswith("registry+")}
    before = registry_pins()
    run("cargo", f"+{args.toolchain}", "check", "-j", str(args.jobs), cwd=compositor)
    if registry_pins() != before:
        raise SystemExit("Unexpected registry dependency changes; inspect the generated lockfile.")
    run("git", "diff", "--check", cwd=compositor)
    run("cargo", f"+{args.toolchain}", "test", "--locked", "--lib", "-j", str(args.jobs), cwd=compositor)
    run("cargo", f"+{args.toolchain}", "build", "--locked", "--release", "-j", str(args.jobs), cwd=compositor)
    print(compositor / "target" / "release" / "cosmic-comp")

if __name__ == "__main__":
    main()
