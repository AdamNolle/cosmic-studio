#!/usr/bin/env python3
"""Build the native separator in an isolated directory; never install or launch it."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tomllib

HERE = Path(__file__).resolve().parent
LIBRARY_REVISION = "03c8f93b294ad239ea935f6dd3c14a15acde8d0d"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def run(*args, cwd=None, env=None):
    subprocess.run([str(arg) for arg in args], cwd=cwd, env=env, check=True)


def library_source_digest(library):
    """Include generated untracked modules and font assets, not build/Git caches."""
    result = hashlib.sha256()
    for folder, directories, files in os.walk(library):
        directories[:] = sorted(name for name in directories if name not in (
            ".git", "target", "__pycache__", "node_modules"
        ))
        for name in sorted(files):
            if name == ".git" or name.startswith(".studio-"):
                continue
            path = Path(folder) / name
            result.update(str(path.relative_to(library)).encode() + b"\0")
            result.update(path.read_bytes())
            result.update(b"\0")
    return result.hexdigest()


def prepare(work, library, lock_source):
    revision = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=library, text=True
    ).strip()
    if revision != LIBRARY_REVISION:
        raise SystemExit(f"Expected libcosmic {LIBRARY_REVISION}; found {revision}.")
    library_diff = subprocess.check_output(["git", "diff", "HEAD"], cwd=library)
    expected = {
        "schema_version": 2,
        "library_commit": revision,
        "library_path": str(library),
        "library_patch_sha256": digest(library_diff),
        "library_source_sha256": library_source_digest(library),
        "manifest_sha256": digest((HERE / "Cargo.toml").read_bytes()),
        "source_sha256": digest((HERE / "src/main.rs").read_bytes()),
        "lock_seed_sha256": digest(lock_source.read_bytes()),
    }
    source = work / "dock-separator"
    marker = source / ".studio-prepared"
    if source.exists():
        try:
            actual = json.loads(marker.read_text())
        except (OSError, ValueError) as error:
            raise SystemExit("Unverified build directory; use a fresh --work directory.") from error
        if actual != expected:
            raise SystemExit("Prepared inputs changed; use a fresh --work directory. Existing files preserved.")
        return source

    source.mkdir(parents=True)
    shutil.copytree(HERE / "src", source / "src")
    shutil.copyfile(lock_source, source / "Cargo.lock")
    manifest = (HERE / "Cargo.toml").read_text()
    crates = {}
    for path in library.rglob("Cargo.toml"):
        if ".git" in path.parts or "target" in path.parts:
            continue
        name = tomllib.loads(path.read_text()).get("package", {}).get("name", "")
        if name == "libcosmic" or name.startswith("iced") or name in (
            "build_helpers", "cosmic-config", "cosmic-config-derive", "cosmic-theme"
        ):
            crates[name] = path.parent
    if "libcosmic" not in crates:
        raise SystemExit("Pinned library workspace is incomplete.")
    # Both URL spellings occur in the toolkit workspace's dependency sources.
    for url in ("https://github.com/pop-os/libcosmic", "https://github.com/pop-os/libcosmic/"):
        manifest += f'\n[patch."{url}"]\n'
        for name, path in sorted(crates.items()):
            manifest += f"{name} = {{ path = {json.dumps(str(path))} }}\n"
    (source / "Cargo.toml").write_text(manifest)
    marker.write_text(json.dumps(expected, indent=2) + "\n")
    return source


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--library", type=Path, required=True, help="Existing pinned native libcosmic source")
    parser.add_argument("--lock-source", type=Path, required=True, help="Pinned cosmic-applets Cargo.lock")
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--jobs", type=int, default=4)
    parser.add_argument("--prepare-only", action="store_true")
    args = parser.parse_args()
    if not 1 <= args.jobs <= 24:
        parser.error("--jobs must be between 1 and 24")
    source = prepare(args.work.resolve(), args.library.resolve(), args.lock_source.resolve())
    if args.prepare_only:
        print(f"Prepared native source: {source}")
        return
    env = os.environ.copy()
    env["CARGO_TARGET_DIR"] = str(args.target.resolve())
    # The upstream lock seed preserves existing transitive versions. Resolve
    # the new root package and local substitutions once, then require the lock.
    run("cargo", "+stable", "check", "-j", args.jobs, cwd=source, env=env)
    run("cargo", "+stable", "test", "--locked", "-j", args.jobs, cwd=source, env=env)
    run("cargo", "+stable", "build", "--release", "--locked", "-j", args.jobs, cwd=source, env=env)
    prepared = json.loads((source / ".studio-prepared").read_text())
    if library_source_digest(args.library.resolve()) != prepared["library_source_sha256"]:
        raise SystemExit("Native library changed during compilation; preserve this candidate and use a fresh --work directory.")
    binary = args.target.resolve() / "release/cosmic-studio-dock-separator"
    ldd = subprocess.check_output(["ldd", str(binary)], text=True)
    if "not found" in ldd:
        raise SystemExit("Candidate has unresolved runtime libraries:\n" + ldd)
    result = {
        "candidate": str(binary),
        "sha256": digest(binary.read_bytes()),
        "library_commit": LIBRARY_REVISION,
        "tests_passed": True,
        "runtime_libraries_resolved": True,
        "installed": False,
        "launched": False,
    }
    (args.work.resolve() / "validation.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
