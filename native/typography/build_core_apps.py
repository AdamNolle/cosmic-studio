#!/usr/bin/env python3
"""Build pinned COSMIC applications with the native display-font helper.

No application is installed, launched or stopped by this script.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import tomllib

HERE = Path(__file__).resolve().parent

def run(*args, cwd=None, env=None):
    subprocess.run(args, cwd=cwd, env=env, check=True)

def clone(url, revision, target):
    if target.exists():
        raise SystemExit(f"Refusing to overwrite an existing source: {target}")
    run("git", "clone", url, str(target))
    run("git", "checkout", "--detach", revision, cwd=target)
    run("git", "submodule", "update", "--init", "--recursive", cwd=target)

def overrides(application, library):
    lock = tomllib.loads((application / "Cargo.lock").read_text())
    packages = [item for item in lock["package"] if "github.com/pop-os/libcosmic" in item.get("source", "")]
    names = {item["name"] for item in packages}
    urls = {item["source"].removeprefix("git+").split("#")[0].split("?")[0] for item in packages}
    paths = {}
    for manifest in library.rglob("Cargo.toml"):
        if ".git" in manifest.parts:
            continue
        package = tomllib.loads(manifest.read_text()).get("package", {}).get("name")
        if package in names:
            paths[package] = manifest.parent.relative_to(library)
    if names - paths.keys():
        raise SystemExit(f"Missing pinned native workspace packages: {names - paths.keys()}")
    text = (application / "Cargo.toml").read_text()
    for url in sorted(urls):
        text += f'\n[patch."{url}"]\n'
        for package in sorted(paths):
            relative = os.path.relpath(library / paths[package], application)
            text += f'{package} = {{ path = "{relative}" }}\n'
    (application / "Cargo.toml").write_text(text)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--apps", nargs="+", choices=["files", "edit", "term", "settings"],
                        default=["files", "edit", "term", "settings"])
    parser.add_argument("--jobs", type=int, default=6)
    parser.add_argument("--toolchain", default="stable")
    args = parser.parse_args()
    work = args.work.resolve()
    work.mkdir(parents=True, exist_ok=True)
    metadata = json.loads((HERE / "core-app-sources.json").read_text())
    sources = {item["component"]: item for item in metadata}
    libraries = {}
    env = os.environ.copy()
    env["CARGO_TARGET_DIR"] = str(work / "target")
    built = []
    for app in args.apps:
        component = f"cosmic-{app}"
        source = sources[component]
        library_revision = source["native_library_source"].split("#")[-1]
        if library_revision not in libraries:
            library = work / f"libcosmic-{library_revision[:8]}"
            clone("https://github.com/pop-os/libcosmic", library_revision, library)
            patch = work / f"typography-{library_revision[:8]}.patch"
            run("python3", str(HERE / "patch_libcosmic.py"), str(library), "--output", str(patch))
            run("git", "apply", "--check", str(patch), cwd=library)
            run("git", "apply", str(patch), cwd=library)
            run("python3", str(HERE / "embed_fonts.py"), str(library),
                "--output", str(work / f"embedded-fonts-{library_revision[:8]}.patch"), "--apply")
            run("python3", str(HERE / "prepare_display_roles.py"), str(library),
                "--profile", f"native-{library_revision[:8]}",
                "--output", str(work / f"display-roles-{library_revision[:8]}.patch"), "--apply")
            run("python3", str(HERE.parent / "popups/prepare.py"), str(library),
                "--revision", library_revision, "--window-glass",
                "--output", str(work / f"materials-{library_revision[:8]}.patch"), "--apply")
            run("python3", str(HERE.parent / "window-controls/prepare.py"), str(library))
            libraries[library_revision] = library
        application = work / component
        clone(f"https://github.com/pop-os/{component}", source["source_commit"], application)
        if app == "files":
            labels = HERE / "files-desktop-labels.patch"
            run("git", "apply", "--check", str(labels), cwd=application)
            run("git", "apply", str(labels), cwd=application)
        overrides(application, libraries[library_revision])
        packages = ["-p", component] + (["-p", "cosmic-files-applet"] if app == "files" else [])
        run("cargo", f"+{args.toolchain}", "build", "--release", *packages,
            "-j", str(args.jobs), cwd=application, env=env)
        # Override resolution changes the source locations in Cargo.lock once.
        # Verify the resulting lock is complete and fixed for subsequent builds.
        run("cargo", f"+{args.toolchain}", "build", "--release", "--locked", *packages,
            "-j", str(args.jobs), cwd=application, env=env)
        run("git", "diff", "--check", cwd=application)
        built.append(str(work / "target" / "release" / component))
        if app == "files":
            built.append(str(work / "target/release/cosmic-files-applet"))
    print(json.dumps({"candidates": built, "installed": False}, indent=2))

if __name__ == "__main__":
    main()
