param(
    [switch]$Copy
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Resolve-Path (Join-Path $scriptDir "..")
$skillName = "springboot-project-generator"
$sourceDir = Join-Path $repoRoot "skills\$skillName"
$codexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $HOME ".codex" }
$targetParent = Join-Path $codexHome "skills"
$targetLink = Join-Path $targetParent $skillName

if (-not (Test-Path $sourceDir -PathType Container)) {
    Write-Error "Skill directory not found: $sourceDir"
}

$sourceDir = (Resolve-Path $sourceDir).Path

New-Item -ItemType Directory -Force -Path $targetParent | Out-Null

if (Test-Path $targetLink) {
    $item = Get-Item $targetLink
    if ($item.LinkType -eq "SymbolicLink" -and $item.Target -eq $sourceDir) {
        Write-Host "Skill already installed: $targetLink -> $sourceDir"
        exit 0
    }
    if ($item.LinkType -eq "SymbolicLink" -or $item.LinkType -eq "Junction") {
        Remove-Item $targetLink -Force
    } else {
        Write-Error "Target already exists and is not a link: $targetLink"
    }
}

if ($Copy) {
    Copy-Item -Path $sourceDir -Destination $targetLink -Recurse
    Write-Host "Installed $skillName by copy: $targetLink"
    exit 0
}

try {
    New-Item -ItemType SymbolicLink -Path $targetLink -Target $sourceDir | Out-Null
    Write-Host "Installed $skillName: $targetLink -> $sourceDir"
    exit 0
} catch {
    Write-Host "SymbolicLink failed, trying Junction: $($_.Exception.Message)"
}

try {
    New-Item -ItemType Junction -Path $targetLink -Target $sourceDir | Out-Null
    Write-Host "Installed $skillName as Junction: $targetLink -> $sourceDir"
    exit 0
} catch {
    Write-Host "Junction failed, falling back to Copy-Item: $($_.Exception.Message)"
}

Copy-Item -Path $sourceDir -Destination $targetLink -Recurse
Write-Host "Installed $skillName by Copy-Item: $targetLink"
