#!/usr/bin/env python3
"""Emit narrow semantic-title font patches for reviewed, isolated native sources.

Never edit running clients or Cargo caches. Apply after source preparation and
before a build, at a coordinated idle boundary. Body/input/document fonts retain
existing assignments; all point sizes, geometry and keyboard behavior remain.
"""
import argparse
import difflib
import hashlib
import json
from pathlib import Path
import subprocess

from embed_fonts import require_isolated

PROFILES_PATH = Path(__file__).with_name("display-role-profiles.json")


def changes_for(source, profile_name):
    require_isolated(source)
    document = json.loads(PROFILES_PATH.read_text())
    if document.get("schema") != 1:
        raise RuntimeError("Unrecognized display role profile schema.")
    try:
        profile = document["profiles"][profile_name]
    except KeyError:
        raise RuntimeError("Unreviewed semantic display role profile: " + profile_name) from None
    actual = subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"], text=True).strip()
    if actual != profile["revision"]:
        raise RuntimeError("Exact reviewed source revision is required.")
    originals = {}
    for name, digest in profile["files"].items():
        path = source / name
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != digest:
            raise RuntimeError("Unreviewed semantic title source: " + name)
        originals[name] = data.decode()
    if profile["kind"] == "native-library" and "pub fn display()" not in (source / "src/font.rs").read_text():
        raise RuntimeError("Reviewed native display font helper is required first.")
    transformed = dict(originals)
    for role in profile["roles"]:
        name = role["file"]
        if transformed[name].count(role["before"]) != 1:
            raise RuntimeError("Semantic role anchor differs: " + role["role"])
        transformed[name] = transformed[name].replace(role["before"], role["after"], 1)
    return {name: (before, transformed[name]) for name, before in originals.items()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    source = args.source.resolve()
    changes = changes_for(source, args.profile)
    patch = "".join("".join(difflib.unified_diff(before.splitlines(True), after.splitlines(True),
                    fromfile="a/" + name, tofile="b/" + name)) for name, (before, after) in changes.items())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(patch)
    if args.apply:
        for name, (_, after) in changes.items():
            (source / name).write_text(after)
    print(("Applied" if args.apply else "Prepared") + " reviewed semantic title roles: " + args.profile)


if __name__ == "__main__":
    main()
