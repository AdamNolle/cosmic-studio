#!/usr/bin/env bash
# Development dependencies only: never installs Studio candidates or restarts COSMIC.
set -euo pipefail
if [[ $(id -u) == 0 ]]; then
    echo 'Run as the development desktop user, not root.' >&2
    exit 1
fi
source /etc/os-release
if [[ ${ID:-} != pop || ${VERSION_ID:-} != 24.04 ]]; then
    echo 'This bootstrap supports Pop!_OS 24.04 only.' >&2
    exit 1
fi
# Optional noninteractive authentication for an owned SSH session. The password
# is read once from private stdin, never exported, logged, or placed in argv.
if [[ $# -gt 0 ]]; then
    if [[ $# != 1 || $1 != --sudo-password-stdin || -t 0 ]]; then
        echo 'Usage: bootstrap.sh [--sudo-password-stdin via a private non-TTY pipe]' >&2
        exit 1
    fi
    IFS= read -r studio_sudo_password
    [[ -n $studio_sudo_password ]] || { echo 'Empty sudo credential refused.' >&2; exit 1; }
fi
as_root() {
    if [[ -n ${studio_sudo_password:-} ]]; then
        printf '%s\n' "$studio_sudo_password" | sudo -S -p '' "$@"
    else
        sudo "$@"
    fi
}
as_root apt-get update
as_root env DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends -y \
    build-essential clang cmake meson ninja-build nasm pkg-config git curl ca-certificates \
    python3 python3-venv fontconfig openssh-server \
    libwayland-dev wayland-protocols libxkbcommon-dev libegl1-mesa-dev \
    libgl1-mesa-dev libgles2-mesa-dev libgbm-dev libdrm-dev libinput-dev \
    libudev-dev libseat-dev libdisplay-info-dev libpixman-1-dev \
    libfontconfig1-dev libfreetype-dev libdbus-1-dev libglib2.0-dev \
    libpulse-dev libasound2-dev libpipewire-0.3-dev libpam0g-dev \
    libssl-dev libexpat1-dev libsystemd-dev libpolkit-gobject-1-dev \
    libgtk-3-dev libgdk-pixbuf-2.0-dev libnotify-dev libgstreamer1.0-dev \
    libgstreamer-plugins-base1.0-dev libgstreamer-plugins-bad1.0-dev \
    libavcodec-dev libavformat-dev libavutil-dev libswscale-dev libdav1d-dev \
    libheif-dev libnuma-dev libjxl-dev libwebp-dev liblcms2-dev libsqlite3-dev \
    libarchive-dev libzstd-dev libbz2-dev liblzma-dev libudev-dev \
    libx11-dev libxcursor-dev libxi-dev libxrandr-dev libxinerama-dev \
    libxcb-shape0-dev libxcb-xfixes0-dev libxcb-render0-dev \
    libflatpak-dev libostree-dev libappstream-dev libgudev-1.0-dev \
    libnm-dev libbluetooth-dev libupower-glib-dev libv4l-dev \
    gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-libav \
    weston mesa-utils libegl-mesa0
unset studio_sudo_password
# Retain the official installer in the guest cache, outside source/build evidence.
if ! command -v rustup >/dev/null 2>&1; then
    mkdir -p "$HOME/.cache/studio-vm-bootstrap"
    installer="$HOME/.cache/studio-vm-bootstrap/rustup-init.sh"
    curl --proto '=https' --tlsv1.2 --fail --location https://sh.rustup.rs -o "$installer"
    sha256sum "$installer"
    sh "$installer" -y --profile minimal --default-toolchain stable
fi
source "$HOME/.cargo/env"
rustup toolchain install stable --profile minimal
rustc +stable --version
cargo +stable --version
python3 --version
printf '\nDevelopment dependencies installed; desktop binaries and settings unchanged.\n'
