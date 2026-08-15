param(
    [string]$Version = "0.1.8",
    [string]$IsccPath = "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe",
    [switch]$InstallerOnly
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = Join-Path $root ".venv\Scripts\python.exe"
$releaseDir = Join-Path $root "dist\release"
$portableZip = Join-Path $releaseDir "SpeechBubbleComicEditorApp-v$Version-win-x64-portable.zip"
$installer = Join-Path $releaseDir "SpeechBubbleComicEditorApp-v$Version-win-x64-setup.exe"
$checksums = Join-Path $releaseDir "SHA256SUMS.txt"

if ($Version -notmatch '^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$') {
    throw "Version must use semantic version format, for example 0.1.0."
}
$tempRoot = [IO.Path]::GetFullPath([IO.Path]::GetTempPath())
$shortBuildRoot = Join-Path $tempRoot "SBE-v$Version-build"
$shortBuildRoot = [IO.Path]::GetFullPath($shortBuildRoot)
if (-not $shortBuildRoot.StartsWith($tempRoot, [StringComparison]::OrdinalIgnoreCase)) {
    throw "Temporary build path must remain inside Windows Temp."
}
$stageRoot = Join-Path $shortBuildRoot "stage"
$workRoot = Join-Path $shortBuildRoot "work"
$portableDir = Join-Path $stageRoot "SpeechBubbleComicEditorApp"
if (-not (Test-Path -LiteralPath $IsccPath -PathType Leaf)) {
    throw "Inno Setup 6 was not found: $IsccPath"
}
if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {
    throw "The Desktop build environment was not found. Run setup_and_start.cmd first."
}

Push-Location $root
try {
    & $python -m pip install --disable-pip-version-check -r requirements-build.txt
    if ($LASTEXITCODE -ne 0) {
        throw "Build dependency installation failed with exit code $LASTEXITCODE."
    }

    foreach ($path in @($stageRoot, $workRoot)) {
        if (Test-Path -LiteralPath $path) {
            Remove-Item -LiteralPath $path -Recurse -Force
        }
    }
    & $python -m PyInstaller --noconfirm --clean --distpath $stageRoot --workpath $workRoot SpeechBubbleComicEditorApp.spec
    if ($LASTEXITCODE -ne 0) {
        throw "Portable build failed with exit code $LASTEXITCODE."
    }
    foreach ($name in @("README.md", "LICENSE", "PRIVACY.md", "SECURITY.md", "THIRD-PARTY-NOTICES.md")) {
        Copy-Item -LiteralPath (Join-Path $root $name) -Destination (Join-Path $portableDir $name) -Force
    }

    New-Item -ItemType Directory -Path $releaseDir -Force | Out-Null
    if (-not $InstallerOnly) {
        if (Test-Path -LiteralPath $portableZip) {
            Remove-Item -LiteralPath $portableZip -Force
        }
        Compress-Archive -LiteralPath $portableDir -DestinationPath $portableZip -CompressionLevel Optimal
    }

    $windowsVersion = (($Version -replace '[-+].*$', '') + '.0')
    & $IsccPath "/DMyAppVersion=$Version" "/DMyAppWindowsVersion=$windowsVersion" "/DMySourceDir=$portableDir" (Join-Path $root "packaging\SpeechBubbleComicEditorApp.iss")
    if ($LASTEXITCODE -ne 0) {
        throw "Installer build failed with exit code $LASTEXITCODE."
    }
    if (-not (Test-Path -LiteralPath $installer -PathType Leaf)) {
        throw "Installer output was not created: $installer"
    }

    $artifacts = if ($InstallerOnly) { @($installer) } else { @($installer, $portableZip) }
    $lines = foreach ($path in $artifacts) {
        $hash = Get-FileHash -Algorithm SHA256 -LiteralPath $path
        "$($hash.Hash.ToLowerInvariant())  $([IO.Path]::GetFileName($path))"
    }
    Set-Content -LiteralPath $checksums -Value $lines -Encoding ASCII

    Write-Output ""
    Write-Output "Release artifacts:"
    Write-Output $installer
    if (-not $InstallerOnly) {
        Write-Output $portableZip
    }
    Write-Output $checksums
}
finally {
    Pop-Location
    if (Test-Path -LiteralPath $shortBuildRoot) {
        Remove-Item -LiteralPath $shortBuildRoot -Recurse -Force
    }
}
