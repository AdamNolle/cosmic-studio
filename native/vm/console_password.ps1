# Submit a locally retained development password only to a CONFIRMED protected prompt.
# Uses the owned VM's COM keyboard API: never password/scancode command arguments.
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$CredentialFile,
    [switch]$PasswordPromptConfirmed,
    [string]$ExpectedUser = 'studio'
)
$ErrorActionPreference = 'Stop'
if (-not $PasswordPromptConfirmed) { throw 'First visually confirm the owned VM protected password prompt.' }
$sourceRoot = (Get-Item $PSScriptRoot).Parent.Parent.FullName
$path = [IO.Path]::GetFullPath($CredentialFile)
if ($path.StartsWith($sourceRoot + '\', [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Private credentials must be outside the repository.'
}
$credential = [IO.File]::ReadAllText($path) | ConvertFrom-Json
if ($credential.username -ne $ExpectedUser -or $credential.password -cnotmatch '^[A-Za-z0-9]{20,64}$') {
    throw 'Expected the dedicated account and generated alphanumeric development credential.'
}
$keys = @{
    a=0x1e; b=0x30; c=0x2e; d=0x20; e=0x12; f=0x21; g=0x22; h=0x23; i=0x17
    j=0x24; k=0x25; l=0x26; m=0x32; n=0x31; o=0x18; p=0x19; q=0x10; r=0x13
    s=0x1f; t=0x14; u=0x16; v=0x2f; w=0x11; x=0x2d; y=0x15; z=0x2c
    '1'=0x02; '2'=0x03; '3'=0x04; '4'=0x05; '5'=0x06
    '6'=0x07; '7'=0x08; '8'=0x09; '9'=0x0a; '0'=0x0b
}
$vb = New-Object -ComObject VirtualBox.VirtualBox
$machine = $vb.FindMachine('COSMIC Studio PopOS')
if ($machine.State -ne 6) { throw 'The owned COSMIC Studio VM must be running.' }
$session = New-Object -ComObject VirtualBox.Session
try {
    $machine.LockMachine($session, 1) # Shared console access; does not alter other VMs.
    $keyboard = $session.Console.Keyboard
    foreach ($character in $credential.password.ToCharArray()) {
        $code = $keys[[string][char]::ToLowerInvariant($character)]
        $scan = @()
        if ([char]::IsUpper($character)) { $scan += 0x2a }
        $scan += [int]$code, ([int]$code -bor 0x80)
        if ([char]::IsUpper($character)) { $scan += 0xaa }
        $count = $keyboard.PutScancodes([int[]]$scan)
        if ($count -ne $scan.Count) { throw 'Private console input was not fully accepted; do not retry blindly.' }
        Start-Sleep -Milliseconds 60
    }
    [void]$keyboard.PutScancodes([int[]](0x1c,0x9c))
    Write-Output 'Private credential submitted to the confirmed prompt; value/key codes not logged.'
} finally {
    if ($session.State -eq 1) { $session.UnlockMachine() }
    $credential = $null
}
