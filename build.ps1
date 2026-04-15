# build.ps1 — AutomataLab build & package script
# Usage: .\build.ps1
# Requires: conda environment "lf" with pyinstaller and Pillow installed
#
# Genera en releases\:
#   AutomataLab_v{version}.exe   — ejecutable único (onefile)
#   AutomataLab_v{version}.zip   — carpeta completa (con _internal\)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Root        = $PSScriptRoot
$VersionFile = Join-Path $Root "version.txt"
$SpecFile    = Join-Path $Root "AutomataLab.spec"
$DistDir     = Join-Path $Root "dist\AutomataLab"
$ReleasesDir = Join-Path $Root "releases"

# ─── 1. Read & increment version ──────────────────────────────────────────────
$currentVersion = (Get-Content $VersionFile -Raw).Trim()
$parts = $currentVersion.Split('.')
if ($parts.Count -ne 3) {
    Write-Error "version.txt debe tener formato MAJOR.MINOR.PATCH (encontrado: '$currentVersion')"
    exit 1
}
$major = $parts[0]
$minor = $parts[1]
$patch = [int]$parts[2] + 1
$newVersion = "$major.$minor.$patch"

$exeName  = "AutomataLab_v$newVersion"
$zipName  = "$exeName.zip"
$zipPath  = Join-Path $ReleasesDir "$zipName"
$exePath  = Join-Path $ReleasesDir "$exeName.exe"

Write-Host ""
Write-Host "=================================================="
Write-Host "  AutomataLab Build Script"
Write-Host "  $currentVersion  ->  $newVersion"
Write-Host "=================================================="
Write-Host ""

# ─── 2. Clean old artefacts ───────────────────────────────────────────────────
Write-Host "[1/6] Limpiando artefactos anteriores ..."
foreach ($dir in @("build", "dist")) {
    $path = Join-Path $Root $dir
    if (Test-Path $path) {
        Remove-Item $path -Recurse -Force
        Write-Host "      Eliminado: $dir\"
    }
}
if (-not (Test-Path $ReleasesDir)) {
    New-Item -ItemType Directory -Path $ReleasesDir | Out-Null
}

# ─── 3. Build carpeta (spec existente) ────────────────────────────────────────
Write-Host "[2/6] Build modo CARPETA con PyInstaller (conda env: lf) ..."
Write-Host ""

Push-Location $Root
try {
    conda run -n lf pyinstaller $SpecFile --clean --noconfirm
    if ($LASTEXITCODE -ne 0) {
        Write-Error "PyInstaller (carpeta) fallo con codigo $LASTEXITCODE"
        exit 1
    }
} finally {
    Pop-Location
}
Write-Host ""

# ─── 4. Verify & rename exe en dist ───────────────────────────────────────────
Write-Host "[3/6] Verificando y versionando exe de carpeta ..."
$distExe = Join-Path $DistDir "AutomataLab.exe"
if (-not (Test-Path $distExe)) {
    Write-Error "No se encontro el ejecutable esperado: $distExe"
    exit 1
}
$distExeVersioned = Join-Path $DistDir "$exeName.exe"
Rename-Item $distExe $distExeVersioned
Write-Host "      OK -> dist\AutomataLab\$exeName.exe"

# ─── 5. Build onefile → releases\ ─────────────────────────────────────────────
Write-Host "[4/6] Build modo UNICO (onefile) con PyInstaller ..."
Write-Host ""

Push-Location $Root
try {
    conda run -n lf pyinstaller main.py `
        --onefile --windowed `
        --name $exeName `
        --icon icono.ico `
        --distpath $ReleasesDir `
        --workpath (Join-Path $Root "build\onefile") `
        --noconfirm
    if ($LASTEXITCODE -ne 0) {
        Write-Error "PyInstaller (onefile) fallo con codigo $LASTEXITCODE"
        exit 1
    }
} finally {
    Pop-Location
}
Write-Host ""

if (-not (Test-Path $exePath)) {
    Write-Error "No se genero el exe onefile esperado: $exePath"
    exit 1
}
$exeSizeMB = [math]::Round((Get-Item $exePath).Length / 1MB, 2)
Write-Host "      OK -> releases\$exeName.exe ($exeSizeMB MB)"

# ─── 6. Empaquetar carpeta en ZIP ─────────────────────────────────────────────
Write-Host "[5/6] Empaquetando carpeta en ZIP ..."
if (Test-Path $zipPath) { Remove-Item $zipPath -Force }

# Copiar a temp para evitar bloqueos de Windows Defender
$tempDir = Join-Path $env:TEMP "AutomataLab_release_tmp"
if (Test-Path $tempDir) { Remove-Item $tempDir -Recurse -Force }
robocopy $DistDir $tempDir /E /NFL /NDL /NJH /NJS /nc /ns /np | Out-Null

Add-Type -AssemblyName System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::CreateFromDirectory($tempDir, $zipPath)
Remove-Item $tempDir -Recurse -Force

$zipSizeMB = [math]::Round((Get-Item $zipPath).Length / 1MB, 2)
Write-Host "      OK -> releases\$zipName ($zipSizeMB MB)"

# ─── 7. Save new version ──────────────────────────────────────────────────────
Write-Host "[6/6] Guardando nueva version ..."
Set-Content -Path $VersionFile -Value $newVersion -NoNewline
Write-Host "      OK -> version.txt = $newVersion"

# ─── Summary ──────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "=================================================="
Write-Host "  Build completado con exito"
Write-Host "  Version  : $newVersion"
Write-Host "  EXE      : releases\$exeName.exe ($exeSizeMB MB)"
Write-Host "  ZIP      : releases\$zipName ($zipSizeMB MB)"
Write-Host "=================================================="
Write-Host ""
