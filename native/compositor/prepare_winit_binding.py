#!/usr/bin/env python3
"""Exact-source candidate-only Winit EGL binding repair; never patch Smithay/stock."""
import argparse
import difflib
import hashlib
import json
from pathlib import Path
import subprocess
import tomllib

COMP = '0fbd4574ef4caf74769a617d205fd1fc909ac9b1'
SMITHAY_SOURCE = 'git+https://github.com/smithay/smithay.git?rev=e3d461a#e3d461a057ba244d213a8498ec372b0799cca103'
INPUT_SHA256 = 'd0e6421880113f1095c439c607f9bb8f3001e1ee6282cfe5878d8dd8db2b583a'
RELATIVE = Path('src/backend/winit.rs')


def transform(original):
    if hashlib.sha256(original).hexdigest() != INPUT_SHA256:
        raise ValueError('Changed/repeated original Winit source; refusing candidate repair.')
    text = original.decode('utf-8')
    old = '''    pub fn render_output(&mut self, state: &mut Common) -> Result<()> {
        let age = self.backend.buffer_age().unwrap_or(0);'''
    new = '''    pub fn render_output(&mut self, state: &mut Common) -> Result<()> {
        // Winit bind resizes before a MakeCurrent can latch the backbuffer, but
        // the pinned GLES Bind implementation only constructs a borrowed target.
        let (_, fb) = self.backend.bind().context("Failed to prepare window buffer")?;
        std::mem::drop(fb);
        Self::make_window_current(&mut self.backend)?;
        let age = self.backend.buffer_age().unwrap_or(0);'''
    submit = '''                std::mem::drop(fb);
                self.backend
                    .submit'''
    fixed = '''                std::mem::drop(fb);
                // Offscreen work and the no-damage path can leave a surfaceless
                // context current. EGL requires this window as the draw surface.
                Self::make_window_current(&mut self.backend)?;
                self.backend
                    .submit'''
    helper = '''    /// Restore only this backend's owned EGL window/context on its event-loop
    /// thread. Do not cache handles, create resources or change render damage.
    fn make_window_current(backend: &mut WinitGraphicsBackend<GlowRenderer>) -> Result<()> {
        use smithay::backend::egl::ffi::egl;

        let surface = backend.egl_surface().get_surface_handle();
        let context = backend.renderer().egl_context();
        let display = context.display().get_display_handle();
        // SAFETY: these handles remain owned by this same backend for the whole
        // call. Rendering and submission run on the existing event-loop thread;
        // no context is shared/moved to another thread or retained by this helper.
        let current = unsafe {
            egl::MakeCurrent(**display, surface, surface, context.get_context_handle())
        };
        if current != egl::TRUE {
            // Read the actual failed caller's EGL error; never infer ContextLost.
            let error = unsafe { egl::GetError() };
            anyhow::bail!("Failed to make owned Winit window current: EGL error 0x{error:04x}");
        }
        Ok(())
    }

'''
    anchor = '    pub fn all_outputs(&self) -> Vec<Output> {'
    for old_text in (old, submit, anchor):
        if text.count(old_text) != 1:
            raise ValueError('Exact original Winit anchor mismatch.')
    return text.replace(old, new).replace(submit, fixed).replace(anchor, helper+anchor).encode('utf-8')


def prepare(application, output, apply=False):
    application = application.resolve()
    source = application/RELATIVE
    if source.is_symlink() or not source.resolve().is_relative_to(application):
        raise ValueError('Owned source path required, not a symlink.')
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=application, text=True).strip()
    if head != COMP:
        raise ValueError('Wrong compositor revision; no branch/latest substitution.')
    original = subprocess.check_output(['git', 'show', 'HEAD:'+RELATIVE.as_posix()], cwd=application)
    if source.read_bytes() != original:
        raise ValueError('Winit input must match original Git HEAD bytes.')
    lock = tomllib.loads((application/'Cargo.lock').read_text(encoding='utf-8'))
    packages = [p for p in lock['package'] if p['name'] == 'smithay']
    if len(packages) != 1 or packages[0].get('source') != SMITHAY_SOURCE or packages[0]['version'] != '0.7.0':
        raise ValueError('Wrong original Smithay identity; no foreign dependency override.')
    updated = transform(original)
    patch = ''.join(difflib.unified_diff(original.decode().splitlines(True),
        updated.decode().splitlines(True), fromfile='a/'+RELATIVE.as_posix(), tofile='b/'+RELATIVE.as_posix()))
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x', encoding='utf-8', newline='\n') as file:
        file.write(patch)
    if apply:
        subprocess.run(['git', 'apply', '--check', str(output.resolve())], cwd=application, check=True)
        subprocess.run(['git', 'apply', str(output.resolve())], cwd=application, check=True)
        if source.read_bytes() != updated:
            raise ValueError('Applied Winit postimage differs from generated bytes.')
    return {'scope': 'Candidate-only Winit binding; no stock/Smithay/codecs/features/locks changed',
            'source_commit': head, 'input_sha256': INPUT_SHA256,
            'postimage_sha256': hashlib.sha256(updated).hexdigest(),
            'patch_sha256': hashlib.sha256(patch.encode()).hexdigest(), 'applied': apply}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('application', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    print(json.dumps(prepare(args.application, args.output, args.apply), indent=2))


if __name__ == '__main__':
    main()
