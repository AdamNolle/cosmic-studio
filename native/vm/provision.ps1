# Create a separate Pop!_OS development VM. Does not modify existing VMs or Windows features.
[CmdletBinding()]
param(
    [string]$Name = 'COSMIC Studio PopOS',
    [string]$Root = (Join-Path $env:USERPROFILE 'VirtualBox VMs\COSMIC-Studio'),
    [ValidateRange(1024,32768)][int]$MemoryMiB = 16384,
    [ValidateRange(1,24)][int]$CPUs = 8,
    [ValidateRange(32,512)][int]$DiskGiB = 160,
    [ValidateRange(1024,65535)][int]$SSHPort = 2224,
    [switch]$Start,
    [switch]$DownloadOnly
)
$ErrorActionPreference = 'Stop'
$VBox = Join-Path $env:ProgramFiles 'Oracle\VirtualBox\VBoxManage.exe'
if (!(Test-Path $VBox)) { throw 'VirtualBox is required; this script never installs a hypervisor.' }
function Invoke-VBox {
    & $VBox @args
    if ($LASTEXITCODE -ne 0) { throw "VBoxManage failed: $($args -join ' ')" }
}
# Refuse collisions rather than overwrite another machine, disk or port forwarding rule.
$machines = & $VBox list vms
if ($LASTEXITCODE -ne 0) { throw 'Cannot enumerate VirtualBox machines.' }
$machinePath = Join-Path $Root $Name
if (!$DownloadOnly) {
    if ($machines | Where-Object { $_.StartsWith('"' + $Name + '" ') }) { throw "VM already exists: $Name" }
    if (Test-Path $machinePath) { throw "Machine directory already exists: $machinePath" }
    $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, $SSHPort)
    try { $listener.Start() } finally { $listener.Stop() }
}
New-Item -ItemType Directory -Force -Path $Root | Out-Null
$release = Invoke-RestMethod 'https://api.pop-os.org/builds/24.04/generic?arch=amd64'
$uri = [uri]$release.url
if ($uri.Scheme -ne 'https' -or $uri.Host -ne 'iso.pop-os.org' -or $release.sha_sum -notmatch '^[a-fA-F0-9]{64}$') {
    throw 'Unexpected official release metadata; refusing download.'
}
$iso = Join-Path $Root ([IO.Path]::GetFileName($uri.AbsolutePath))
$partial = "$iso.partial"
if (!(Test-Path $iso)) {
    Write-Host "Downloading official Pop!_OS build $($release.build) ($($release.size) bytes)..."
    & curl.exe --fail --location --retry 3 --continue-at - --output $partial $release.url
    if ($LASTEXITCODE -ne 0) { throw 'ISO download failed; partial retained for resume.' }
    if ((Get-Item $partial).Length -ne [long]$release.size) { throw 'ISO size mismatch.' }
    if ((Get-FileHash $partial -Algorithm SHA256).Hash.ToLowerInvariant() -ne $release.sha_sum.ToLowerInvariant()) {
        throw 'ISO checksum mismatch. The file was NOT attached to a VM.'
    }
    Move-Item $partial $iso
}
if ((Get-Item $iso).Length -ne [long]$release.size -or
    (Get-FileHash $iso -Algorithm SHA256).Hash.ToLowerInvariant() -ne $release.sha_sum.ToLowerInvariant()) {
    throw 'Existing ISO does not match official metadata.'
}
$release | ConvertTo-Json | Set-Content -Encoding UTF8 (Join-Path $Root 'iso-release.json')
if ($DownloadOnly) { Write-Host 'OFFICIAL_ISO_VERIFIED'; return }
Invoke-VBox createvm --name $Name --ostype Ubuntu_64 --basefolder $Root --register
Invoke-VBox modifyvm $Name --memory $MemoryMiB --cpus $CPUs --firmware efi --graphicscontroller vmsvga --vram 128 --accelerate3d on --nic1 nat --natpf1 "ssh,tcp,127.0.0.1,$SSHPort,,22" --clipboard-mode disabled --drag-and-drop disabled --boot1 dvd --boot2 disk --boot3 none --boot4 none
Invoke-VBox storagectl $Name --name SATA --add sata --controller IntelAhci --portcount 2
$disk = Join-Path $machinePath 'system.vdi'
Invoke-VBox createmedium disk --filename $disk --size ($DiskGiB * 1024) --format VDI --variant Standard
Invoke-VBox storageattach $Name --storagectl SATA --port 0 --device 0 --type hdd --medium $disk
Invoke-VBox storageattach $Name --storagectl SATA --port 1 --device 0 --type dvddrive --medium $iso
Invoke-VBox setextradata $Name GUI/LastGuestSizeHint '1920,1080'
@{ name=$Name; root=$Root; iso=$iso; sha256=$release.sha_sum; ssh_host='127.0.0.1'; ssh_port=$SSHPort; memory_mib=$MemoryMiB; cpus=$CPUs; disk_gib=$DiskGiB; state='installer-ready' } |
    ConvertTo-Json | Set-Content -Encoding UTF8 (Join-Path $Root 'development-vm.json')
Write-Host 'VM_CREATED_AND_ISO_VERIFIED'
if ($Start) { Invoke-VBox startvm $Name --type gui }
