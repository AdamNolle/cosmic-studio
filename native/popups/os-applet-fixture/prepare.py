#!/usr/bin/env python3
"""Copy exact native OS applet inputs and add guarded, one-shot popup triggers."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

HERE = Path(__file__).resolve().parent
TIME = 'cosmic-applet-time/src/window.rs'
TOOLTIP = 'src/widget/wayland/tooltip/widget.rs'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def inventory(root):
    result = {}
    for path in sorted(root.rglob('*')):
        relative = path.relative_to(root)
        if path.is_file() and not any(name in ('.git', 'target', '__pycache__') for name in relative.parts):
            result[str(relative)] = digest(path.read_bytes())
    return result


def copy_inputs(applets, library, output):
    profile = json.loads((HERE/'profile.json').read_text())
    for source, name, field, path in ((applets, 'cosmic-applets', 'applets_revision', TIME),
                                     (library, 'libcosmic-applets', 'library_revision', TOOLTIP)):
        revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=source, text=True).strip()
        if revision != profile[field] or digest((source/path).read_bytes()) != profile['preimages'][name+'/'+path]:
            raise RuntimeError('Fixture input differs from the reviewed native source: '+name)
    if output.exists():
        raise RuntimeError('Refusing to overwrite an existing fixture copy: '+str(output))
    for source in (applets, library):
        if output.resolve().is_relative_to(source.resolve()):
            raise RuntimeError('Fixture destination must be separate from production source.')
    before = {'applets': inventory(applets), 'library': inventory(library)}
    output.mkdir(parents=True)
    try:
        shutil.copytree(applets, output/'cosmic-applets', ignore=shutil.ignore_patterns('.git', 'target', '__pycache__'))
        shutil.copytree(library, output/'libcosmic-applets', ignore=shutil.ignore_patterns('.git', 'target', '__pycache__'))
        guard = (HERE/'guard.rs').read_text()
        time_path = output/'cosmic-applets'/TIME
        text = time_path.read_text()
        old = '            Task::none(),\n        )\n    }\n\n    fn core(&self)'
        new = '''            if studio_private_fixture("STUDIO_PRIVATE_AUTO_CALENDAR") {
                Task::perform(
                    async { tokio::time::sleep(std::time::Duration::from_millis(1200)).await },
                    |_| cosmic::Action::App(Message::TogglePopup),
                )
            } else {
                Task::none()
            },
        )
    }

    fn core(&self)'''
        if text.count(old) != 1:
            raise RuntimeError('Native calendar init no longer matches its reviewed fixture hook.')
        time_path.write_text(text.replace(old, new)+'\n'+guard)
        tooltip_path = output/'libcosmic-applets'/TOOLTIP
        text = tooltip_path.read_text()
        old = ') {\n    match event {\n        Event::Touch(touch::Event::FingerLifted { .. })'
        new = ''') {
    // One input event through the actual native tooltip widget and popup path.
    static HOVER_SENT: std::sync::atomic::AtomicBool = std::sync::atomic::AtomicBool::new(false);
    let bounds = layout.bounds();
    let (event, cursor) = if studio_private_fixture("STUDIO_PRIVATE_AUTO_TOOLTIP")
        && settings.is_some()
        && bounds.width > 0.0 && bounds.height > 0.0
        && !HOVER_SENT.swap(true, std::sync::atomic::Ordering::Relaxed)
    {
        eprintln!("studio private fixture: native tooltip cursor injection");
        let position = bounds.center();
        (Event::Mouse(mouse::Event::CursorMoved { position }), mouse::Cursor::Available(position))
    } else { (event, cursor) };
    match event {
        Event::Touch(touch::Event::FingerLifted { .. })'''
        if text.count(old) != 1:
            raise RuntimeError('Native tooltip event dispatcher no longer matches its reviewed fixture hook.')
        tooltip_path.write_text(text.replace(old, new)+'\n'+guard)
        after = {'applets': inventory(output/'cosmic-applets'), 'library': inventory(output/'libcosmic-applets')}
        changed = {name: [path for path in before[name] if before[name][path] != after[name].get(path)] for name in before}
        if changed != {'applets': [TIME], 'library': [TOOLTIP]}:
            raise RuntimeError('Fixture changed files outside its two approved hooks: '+str(changed))
        report = dict(profile, source_applets=str(applets.resolve()), source_library=str(library.resolve()),
                      before=before, after=after, changed=changed, deployable=False,
                      generator_sha256=digest(Path(__file__).read_bytes()), guard_sha256=digest(guard.encode()))
        (output/'fixture-source.json').write_text(json.dumps(report, indent=2)+'\n')
        return {'fixture': str(output), 'changed': changed, 'deployable': False}
    except BaseException:
        shutil.rmtree(output)
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--applets', type=Path, required=True)
    parser.add_argument('--library', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(copy_inputs(args.applets, args.library, args.output), indent=2))
