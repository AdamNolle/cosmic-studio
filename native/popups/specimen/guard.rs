// Copyright 2026 COSMIC Studio contributors
// SPDX-License-Identifier: MPL-2.0

use std::os::unix::fs::{FileTypeExt, MetadataExt};
use std::path::{Path, PathBuf};

pub fn validate(runtime: &Path, display: &Path, config: &Path, data: &Path,
                user_id: u32, host_home: &Path) -> Result<(), String> {
    let resolve = |p: &Path| p.canonicalize().map_err(|e| format!("cannot resolve private {}: {e}", p.display()));
    let runtime = resolve(runtime)?;
    let info = runtime.metadata().map_err(|e| e.to_string())?;
    if runtime.starts_with("/run/user") || !runtime.file_name().is_some_and(|n| n.to_string_lossy().starts_with("cs-panel-"))
        || info.uid() != user_id || info.mode() & 0o777 != 0o700 || !info.is_dir() {
        return Err("runtime must be owned private cs-panel-* mode0700 outside /run/user".into());
    }
    let socket = resolve(&if display.is_absolute() { display.to_path_buf() } else { runtime.join(display) })?;
    let socket_info = socket.metadata().map_err(|e| e.to_string())?;
    if socket.parent() != Some(runtime.as_path()) || !socket_info.file_type().is_socket() || socket_info.uid() != user_id {
        return Err("Wayland socket must resolve directly under the owned private runtime".into());
    }
    let config = resolve(config)?;
    let data = resolve(data)?;
    let host_config = resolve_or_original(&host_home.join(".config"));
    let host_data = resolve_or_original(&host_home.join(".local/share"));
    if [&config, &data].into_iter().any(|p| p.starts_with(&host_config) || p.starts_with(&host_data)) || config == data
        || config.starts_with("/run/user") || data.starts_with("/run/user") {
        return Err("fixture config/data must be distinct from host XDG paths".into());
    }
    for p in [&config, &data] {
        let info = p.metadata().map_err(|e| e.to_string())?;
        if info.uid() != user_id || !info.is_dir() {
            return Err("private config/data must be owned directories".into());
        }
    }
    Ok(())
}

fn resolve_or_original(path: &Path) -> PathBuf {
    path.canonicalize().unwrap_or_else(|_| path.to_path_buf())
}
