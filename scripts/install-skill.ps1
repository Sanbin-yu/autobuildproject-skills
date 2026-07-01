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

New-Item -ItemType Directory -Force -Path $targetParent | Out-Null

if (Test-Path $targetLink) {
    $item = Get-Item $targetLink
    if ($item.LinkType -eq "SymbolicLink" -and $item.Target -eq $sourceDir) {
        Write-Host "Skill already installed: $targetLink -> $sourceDir"
        exit 0
    }
    if ($item.LinkType -eq "SymbolicLink") {
        Remove-Item $targetLink
    } else {
        Write-Error "Target already exists and is not a symlink: $targetLink"
    }
}

New-Item -ItemType SymbolicLink -Path $targetLink -Target $sourceDir | Out-Null
Write-Host "Installed $skillName: $targetLink -> $sourceDir"
