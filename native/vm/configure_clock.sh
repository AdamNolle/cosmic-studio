#!/usr/bin/env bash
# Reversible clock candidate for the identified Pop!_OS VirtualBox guest only.
# Run through normal sudo; account password must never appear in argv.
set -euo pipefail
[[ $(id -u) == 0 ]] || { echo 'Requires ordinary sudo in the owned guest.' >&2; exit 1; }
[[ $(systemd-detect-virt) == oracle ]] || { echo 'VirtualBox guest required.' >&2; exit 1; }
source /etc/os-release
[[ ${ID:-} == pop && ${VERSION_ID:-} == 24.04 ]] || exit 1
[[ $(< /sys/devices/system/clocksource/clocksource0/current_clocksource) == acpi_pm ]] || {
    echo 'Validate a temporary acpi_pm boot before persistence.' >&2; exit 1;
}
[[ $(uname -r) == 7.0.11-76070011-generic ]] || {
    echo 'This candidate has only been validated on the recorded generic28 kernel.' >&2; exit 1;
}
state=/var/lib/cosmic-studio-vm/boot-original
[[ ! -e $state ]] || { echo 'Original boot backup already exists; refusing overwrite.' >&2; exit 1; }
install -d -m 0700 "$state"
cp -a /etc/kernelstub/configuration "$state/kernelstub-configuration"
cp -a /boot/efi/loader "$state/loader"
printf '%s\n' 'Rollback: sudo kernelstub -d "clocksource=acpi_pm tsc=unstable"' > "$state/ROLLBACK.txt"
# Keep all distro options; add only the successfully tested VM clock options.
kernelstub -a 'clocksource=acpi_pm tsc=unstable'
kernelstub -p
printf '%s\n' 'CLOCK_CANDIDATE_APPLIED_REPEAT_BOOT_PENDING'
