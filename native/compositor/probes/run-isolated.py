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
from capture_gate import validate as validate_capture


def private_x11(env, work):
    """Require the caller's authenticated owned Xwayland, never a desktop DISPLAY."""
    display = env.get('DISPLAY', '')
    pid = env.get('STUDIO_PRIVATE_X11_PID', '')
    if not display.startswith(':') or not display[1:].isdigit() or not pid.isdigit():
        raise ValueError('Explicit owned private Xwayland display/PID required')
    auth = Path(env.get('XAUTHORITY', '')).resolve()
    if not auth.is_relative_to(work.parent) or not auth.is_file():
        raise ValueError('Private Xauthority must be inside the owned probe tree')
    owner = os.getuid()
    if auth.stat().st_uid != owner or auth.stat().st_mode & 0o777 != 0o600:
        raise ValueError('Private Xauthority requires owned mode0600')
    process = Path('/proc')/pid
    args = (process/'cmdline').read_bytes().decode().rstrip('\0').split('\0')
    socket = Path('/tmp/.X11-unix')/('X'+display[1:])
    if process.stat().st_uid != owner or not socket.is_socket() or socket.stat().st_uid != owner:
        raise ValueError('Xwayland process/socket is not owned')
    if Path(args[0]).resolve() != Path('/usr/bin/Xwayland').resolve() or '-ac' in args:
        raise ValueError('Only authenticated private Xwayland is supported')
    if '-displayfd' not in args or '-shm' not in args or '-nolisten' not in args:
        raise ValueError('Private Xwayland must use dynamic display, SHM and no TCP')
    if args[args.index('-nolisten')+1] != 'tcp' or '-auth' not in args or Path(args[args.index('-auth')+1]).resolve() != auth:
        raise ValueError('Private Xwayland authorization/listener mismatch')
    return {'DISPLAY': display, 'XAUTHORITY': str(auth), 'STUDIO_PRIVATE_X11_PID': pid}


def wait_fixture_ready(fixture, log, count, timeout=12):
    """Wait for buffer commits and initial frame callbacks, not a fixed sleep.

    Callback delivery is a prerequisite only, never pixel/presentation proof.
    """
    marker = f'STUDIO_FIXTURE_READY count={count} configured={count} callbacks={count}'
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if log.stat().st_size > 2 * 1024 * 1024:
            raise RuntimeError('Oversized fixture readiness log')
        lines = log.read_text(encoding='utf-8', errors='replace').splitlines()
        if marker in lines and fixture.poll() is None:
            return {'count': count, 'configured': count, 'initial_frame_callbacks': count,
                    'scope': 'Fixture readiness prerequisite only; visible pixels remain unproven.'}
        if fixture.poll() is not None:
            raise RuntimeError('Fixture exited before capture readiness was established')
        time.sleep(0.05)
    raise RuntimeError('Fixture readiness timeout; capture not attempted')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--probes", type=Path, required=True)
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--inside", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--glass", choices=["0", "1"], default="1")
    parser.add_argument("--animate", action="store_true")
    parser.add_argument("--backend", choices=['wayland', 'x11'], default='wayland',
                        help='X11 requires an authenticated owned private Xwayland; never a desktop DISPLAY')
    args = parser.parse_args()
    binary, probes = args.binary.resolve(), args.probes.resolve()
    work = args.work.resolve()
    if not args.inside:
        runtime = Path(os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}"))
        display = os.environ.get("WAYLAND_DISPLAY", "wayland-1")
        outer = Path(display) if display.startswith("/") else runtime / display
        x11 = private_x11(os.environ, work) if args.backend == 'x11' else None
        print(json.dumps({"binary": str(binary), "backend": args.backend,
                          "outer_wayland_socket": str(outer) if x11 is None else None,
                          "bus": "new private dbus-run-session", "xdg": "fresh private directories",
                          "system_bus": "disabled", "xwayland": False, "run": args.run}), flush=True)
        if not args.run:
            return
        if not binary.is_file() or (x11 is None and not outer.is_socket()):
            raise SystemExit("Candidate binary or private outer socket unavailable")
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
                   DBUS_SYSTEM_BUS_ADDRESS=f"unix:path={env['XDG_RUNTIME_DIR']}/absent-system-bus",
                   COSMIC_STUDIO_LIQUID_GLASS=args.glass, STUDIO_TEST_ROOT=str(root),
                   STUDIO_PRIVATE_TEST="1")
        if x11 is not None:
            env.pop('WAYLAND_DISPLAY', None)
            env.update(x11, WINIT_UNIX_BACKEND='x11')
        command = ["dbus-run-session", "--", "/usr/bin/python3", str(Path(__file__).resolve()),
                   "--inside", "--binary", str(binary), "--probes", str(probes),
                   "--work", str(work), "--glass", args.glass, '--backend', args.backend]
        if args.animate:
            command.append("--animate")
        print(json.dumps({"test_root": str(root)}), flush=True)
        raise SystemExit(subprocess.run(command, env=env).returncode)

    root = Path(os.environ["STUDIO_TEST_ROOT"])
    children = []
    result = {"glass": args.glass, "animated": args.animate, 'backend': args.backend,
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
                count = 1 if 'STUDIO_FIXTURE_BACKGROUND_ONLY' in env else 3
                result['fixture_readiness'] = wait_fixture_ready(fixture, root / 'fixture.log', count)
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
                if result.get("capture_returncode") != 0 or fixture.returncode != 0 or not result["images"]:
                    raise RuntimeError("Native fixture/capture did not complete successfully")
                result["capture_validation"] = validate_capture(
                    result["images"][0], root / "compositor.log")
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
    return 1 if result.get("error") or "capture_validation" not in result else 0

if __name__ == "__main__":
    raise SystemExit(main())
