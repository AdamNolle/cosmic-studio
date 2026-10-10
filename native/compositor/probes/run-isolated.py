#!/usr/bin/env python3
"""Plan/run a disposable private-bus compositor; never replace the desktop."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--probes", type=Path, required=True)
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--inside", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--glass", choices=["0", "1"], default="1")
    parser.add_argument("--animate", action="store_true")
    args = parser.parse_args()
    binary, probes = args.binary.resolve(), args.probes.resolve()
    work = args.work.resolve()
    if not args.inside:
        runtime = Path(os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}"))
        display = os.environ.get("WAYLAND_DISPLAY", "wayland-1")
        outer = Path(display) if display.startswith("/") else runtime / display
        print(json.dumps({"binary": str(binary), "outer_wayland_socket": str(outer),
                          "bus": "new private dbus-run-session", "xdg": "fresh private directories",
                          "system_bus": "disabled", "xwayland": False, "run": args.run}), flush=True)
        if not args.run:
            return
        if not binary.is_file() or not outer.is_socket():
            raise SystemExit("Candidate binary or outer Wayland socket unavailable")
        work.mkdir(parents=True, exist_ok=True)
        root = Path(tempfile.mkdtemp(prefix="glass-isolated-", dir=work))
        env = os.environ.copy()
        for key in ["DBUS_SESSION_BUS_ADDRESS", "DBUS_STARTER_ADDRESS", "DBUS_STARTER_BUS_TYPE",
                    "COSMIC_SESSION_SOCK", "NOTIFY_SOCKET", "WAYLAND_SOCKET", "DISPLAY",
                    "XAUTHORITY", "SESSION_MANAGER"]:
            env.pop(key, None)
        for key, suffix in [("XDG_CONFIG_HOME", "config"), ("XDG_CACHE_HOME", "cache"),
                            ("XDG_DATA_HOME", "data"), ("XDG_STATE_HOME", "state"),
                            ("XDG_RUNTIME_DIR", "runtime")]:
            # Unix-domain sockets have a short path limit. Keep only the private
            # runtime in /tmp so a deeply nested --work directory stays usable.
            directory = (Path(tempfile.mkdtemp(prefix="cs-runtime-"))
                         if key == "XDG_RUNTIME_DIR" else root / suffix)
            directory.mkdir(mode=0o700, exist_ok=True)
            env[key] = str(directory)
        env.update(COSMIC_BACKEND="winit", WAYLAND_DISPLAY=str(outer), WINIT_UNIX_BACKEND="wayland",
                   DBUS_SYSTEM_BUS_ADDRESS=f"unix:path={root}/absent-system-bus",
                   COSMIC_STUDIO_LIQUID_GLASS=args.glass, STUDIO_TEST_ROOT=str(root),
                   STUDIO_PRIVATE_TEST="1")
        command = ["dbus-run-session", "--", "/usr/bin/python3", str(Path(__file__).resolve()),
                   "--inside", "--binary", str(binary), "--probes", str(probes),
                   "--work", str(work), "--glass", args.glass]
        if args.animate:
            command.append("--animate")
        print(json.dumps({"test_root": str(root)}), flush=True)
        raise SystemExit(subprocess.run(command, env=env).returncode)

    root = Path(os.environ["STUDIO_TEST_ROOT"])
    children = []
    result = {"glass": args.glass, "animated": args.animate,
              "scope": "Private winit integration probe; complete desktop performance is unmeasured."}
    try:
        with (root / "compositor.log").open("w") as log:
            compositor = subprocess.Popen([str(binary), "--no-xwayland"], stdout=log, stderr=subprocess.STDOUT)
            children.append(compositor)
            deadline = time.monotonic() + 15
            socket = None
            while time.monotonic() < deadline:
                sockets = [item for item in Path(os.environ["XDG_RUNTIME_DIR"]).glob("wayland-*")
                           if item.is_socket()]
                if sockets:
                    socket = sockets[0]
                    break
                if compositor.poll() is not None:
                    raise RuntimeError("Nested compositor exited before its socket was ready")
                time.sleep(0.1)
            if socket is None:
                raise RuntimeError("Nested Wayland socket not available")
            env = os.environ.copy()
            env["WAYLAND_DISPLAY"] = socket.name
            if args.animate:
                env["STUDIO_FIXTURE_ANIMATE"] = "1"
            with (root / "fixture.log").open("w") as fixture_log:
                fixture = subprocess.Popen([str(probes / "fixture")], env=env,
                                           stdout=fixture_log, stderr=subprocess.STDOUT)
                children.append(fixture)
                time.sleep(1)
                try:
                    capture = subprocess.run([str(probes / "capture"), str(root / "capture.ppm")],
                                             env=env, text=True, capture_output=True, timeout=12)
                    (root / "capture.log").write_text(capture.stdout + capture.stderr)
                    result["capture_returncode"] = capture.returncode
                except subprocess.TimeoutExpired:
                    result["capture_timeout"] = True
                fixture.wait(timeout=15)
                result["fixture_returncode"] = fixture.returncode
                result["images"] = [str(item) for item in root.glob("*.ppm")]
    except Exception as error:
        result["error"] = str(error)
    finally:
        for child in reversed(children):
            if child.poll() is None:
                child.terminate()
                try:
                    child.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    child.kill()
                    child.wait(timeout=5)
        (root / "result.json").write_text(json.dumps(result, indent=2))
        print(json.dumps(result), flush=True)
        runtime = Path(os.environ["XDG_RUNTIME_DIR"])
        if runtime.parent == Path(tempfile.gettempdir()) and runtime.name.startswith("cs-runtime-"):
            shutil.rmtree(runtime)

if __name__ == "__main__":
    main()
