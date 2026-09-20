<#
.SYNOPSIS
  agent-skills 安装器：把本仓库的 skill 以「目录联接（junction）」挂进各 agent 的技能目录。

.DESCRIPTION
  幂等操作。设计要点：
  - 仓库是唯一事实来源；技能目录里只放联接，不放副本，避免再次出现同名 skill 内容分叉。
  - 用 junction 而非 symlink：Windows 上 junction 不需要管理员权限或开发者模式，也不需要
    在 git 里保存链接（git for Windows 存 symlink 会退化成文本文件）。
  - 覆盖真实目录前先备份，绝不静默删除用户的现有内容。

.PARAMETER Target
  agents = %USERPROFILE%\.agents\skills
  codex  = %USERPROFILE%\.codex\skills
  all    = 按 manifest.json 里的 defaultTargets 各就各位（默认）

.PARAMETER Only
  只处理指定名字的 skill，便于灰度。

.PARAMETER DryRun
  只打印将要做什么，不落盘。

.PARAMETER Uninstall
  只删除本仓库建立的联接，不动真实目录。

.EXAMPLE
  .\install.ps1 -DryRun
.EXAMPLE
  .\install.ps1 -Only systematic-debugging,writing-plans
.EXAMPLE
  .\install.ps1 -Uninstall
#>
[CmdletBinding()]
param(
  [ValidateSet('agents', 'codex', 'all')]
  [string]$Target = 'all',

  [string[]]$Only,

  [switch]$DryRun,

  [switch]$Uninstall
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$RepoRoot     = $PSScriptRoot
$SkillsRoot   = Join-Path $RepoRoot 'skills'
$ManifestPath = Join-Path $RepoRoot 'manifest.json'
$SharedSrc    = Join-Path $RepoRoot 'shared'

if (-not (Test-Path $SkillsRoot))   { throw "找不到 skills 目录：$SkillsRoot" }
if (-not (Test-Path $ManifestPath)) { throw "找不到 manifest.json：$ManifestPath" }

$TargetDirs = [ordered]@{
  agents = Join-Path $env:USERPROFILE '.agents\skills'
  codex  = Join-Path $env:USERPROFILE '.codex\skills'
}

# ~/tools/shared 被 skill 正文当作权威来源引用，同样用联接接管。
$SharedDst = Join-Path $env:USERPROFILE 'tools\shared'

$Manifest = Get-Content $ManifestPath -Raw | ConvertFrom-Json
$SkillMap = @{}
foreach ($entry in $Manifest.skills) { $SkillMap[$entry.name] = $entry }

function Test-IsReparsePoint {
  param([string]$Path)
  $item = Get-Item -LiteralPath $Path -Force -ErrorAction SilentlyContinue
  if (-not $item) { return $false }
  return [bool]($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint)
}

function Get-LinkTarget {
  param([string]$Path)
  $item = Get-Item -LiteralPath $Path -Force -ErrorAction SilentlyContinue
  if (-not $item) { return $null }
  return ($item.Target | Select-Object -First 1)
}

function New-DirJunction {
  param([string]$Path, [string]$Destination)
  if ($DryRun) { Write-Host "  [dry-run] junction  $Path  ->  $Destination"; return }
  $parent = Split-Path -Parent $Path
  if (-not (Test-Path $parent)) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }
  New-Item -ItemType Junction -Path $Path -Target $Destination | Out-Null
}

$stamp   = Get-Date -Format 'yyyyMMdd-HHmmss'
$summary = [ordered]@{ linked = 0; skipped = 0; backedUp = 0; missing = 0 }

Write-Host ""
Write-Host "仓库:   $RepoRoot"
Write-Host "模式:   $(if ($Uninstall) { '卸载' } elseif ($DryRun) { '演练' } else { '安装' })"
Write-Host ""

# ---------- 1. shared/ ----------
if ((Test-Path $SharedSrc)) {
  Write-Host "[shared]"
  $sameTarget = (Test-IsReparsePoint $SharedDst) -and ((Get-LinkTarget $SharedDst) -eq $SharedSrc)

  if ($Uninstall) {
    if ($sameTarget) { if ($DryRun) { Write-Host "  [dry-run] 删除联接 $SharedDst" } else { (Get-Item $SharedDst -Force).Delete(); Write-Host "  已删除联接 $SharedDst" } }
    else { Write-Host "  跳过（不是本仓库建的联接）：$SharedDst" }
  }
  elseif ($sameTarget) {
    Write-Host "  已就位：$SharedDst"
    $summary.skipped++
  }
  else {
    if ((Test-Path $SharedDst) -and -not (Test-IsReparsePoint $SharedDst)) {
      $bk = "$SharedDst.backup-$stamp"
      if ($DryRun) { Write-Host "  [dry-run] 备份 $SharedDst -> $bk" } else { Move-Item -LiteralPath $SharedDst -Destination $bk; Write-Host "  已备份 -> $bk" }
      $summary.backedUp++
    }
    New-DirJunction -Path $SharedDst -Destination $SharedSrc
    if (-not $DryRun) { Write-Host "  已联接 $SharedDst -> $SharedSrc" }
    $summary.linked++
  }
  Write-Host ""
}

# ---------- 2. skills ----------
$names = Get-ChildItem $SkillsRoot -Directory | Select-Object -ExpandProperty Name
if ($Only) { $names = $names | Where-Object { $_ -in $Only } }
if (-not $names) { throw "没有匹配的 skill（检查 -Only 的拼写）" }

foreach ($dirName in ($TargetDirs.Keys)) {
  if ($Target -ne 'all' -and $Target -ne $dirName) { continue }
  $root = $TargetDirs[$dirName]
  Write-Host "[$dirName]  $root"

  foreach ($name in $names) {
    $entry = if ($SkillMap.ContainsKey($name)) { $SkillMap[$name] } else { $null }
    $defaults = if ($entry) { @($entry.defaultTargets) } else { @('agents') }

    # -Target all 时按 manifest 各就各位；显式指定 -Target 时以命令行为准。
    if ($Target -eq 'all' -and ($defaults -notcontains $dirName)) { continue }

    $src = Join-Path $SkillsRoot $name
    $dst = Join-Path $root $name
    $already = (Test-IsReparsePoint $dst) -and ((Get-LinkTarget $dst) -eq $src)

    if ($Uninstall) {
      if ($already) {
        if ($DryRun) { Write-Host "  [dry-run] 删除联接 $name" }
        else { (Get-Item -LiteralPath $dst -Force).Delete(); Write-Host "  已删除联接 $name" }
        $summary.linked++
      }
      continue
    }

    if ($already) { Write-Host "  = $name（已就位）"; $summary.skipped++; continue }

    if ((Test-Path $dst) -and -not (Test-IsReparsePoint $dst)) {
      $bkRoot = "$root.backup-$stamp"
      $bkDst  = Join-Path $bkRoot $name
      if ($DryRun) { Write-Host "  [dry-run] 备份 $name -> $bkRoot\" }
      else {
        New-Item -ItemType Directory -Path $bkRoot -Force | Out-Null
        Move-Item -LiteralPath $dst -Destination $bkDst
        Write-Host "  ~ $name 已备份到 $bkRoot\"
      }
      $summary.backedUp++
    }
    elseif (Test-Path $dst) {
      # 指向别处的旧联接：直接替换，无需备份真实内容。
      if ($DryRun) { Write-Host "  [dry-run] 替换旧联接 $name" } else { (Get-Item -LiteralPath $dst -Force).Delete() }
    }

    New-DirJunction -Path $dst -Destination $src
    if (-not $DryRun) { Write-Host "  + $name" }
    $summary.linked++
  }
  Write-Host ""
}

Write-Host "----"
Write-Host ("联接/删除 {0}  |  已就位 {1}  |  备份 {2}" -f $summary.linked, $summary.skipped, $summary.backedUp)
if ($summary.backedUp -gt 0 -and -not $DryRun) {
  Write-Host "备份目录以 .backup-$stamp 结尾，确认无碍后可自行删除。"
}
if ($DryRun) { Write-Host "这是演练，未改动任何文件。去掉 -DryRun 才会真正执行。" }
