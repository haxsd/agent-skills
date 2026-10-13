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
  agents = %USERPROFILE%\.agents\skills   （Cursor 与 Devin 都读这个目录，是公共交集）
  cursor = %USERPROFILE%\.cursor\skills
  devin  = %USERPROFILE%\.devin\skills
  claude = %USERPROFILE%\.claude\skills
  codex  = %USERPROFILE%\.codex\skills
  all    = 按 manifest.json 里的 defaultTargets 各就各位（默认）

  说明：manifest 里标为 `agents` 的是「通用技能」，会展开到上面四个平台
  （agents / cursor / devin / claude 内容同一份）；标为 `codex` 的只进 Codex。
  另外 external.json 里登记的是「自己独立成库」的技能（例如 toolkit-map），
  同样只挂联接、不复制内容。

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
  [ValidateSet('agents', 'cursor', 'devin', 'claude', 'codex', 'all')]
  [string]$Target = 'all',

  [string[]]$Only,

  [switch]$DryRun,

  [switch]$Uninstall
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

# Windows PowerShell 5.1 默认按 ANSI 代码页写非 ASCII 输出（中文机器上是 GBK），
# 按 UTF-8 捕获输出的调用方（CI、tests/test_install.py、agent）会解码失败。
# pwsh 7 默认已是 UTF-8，这里是幂等的显式声明；无控制台句柄时忽略即可。
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch { }

# -File 调用（cmd、CI、agent 起新进程）时 "a,b,c" 会作为单个字符串传进来，
# 命令行并不做逗号切分；会话内调用才会得到真正的数组。这里把两种都归一成数组，
# 否则多值 -Only 只在交互式会话里能用。
$Only = @($Only | ForEach-Object { $_ -split ',' } | Where-Object { $_ })

$RepoRoot     = $PSScriptRoot
$SkillsRoot   = Join-Path $RepoRoot 'skills'
$ManifestPath = Join-Path $RepoRoot 'manifest.json'
$SharedSrc    = Join-Path $RepoRoot 'shared'

if (-not (Test-Path $SkillsRoot))   { throw "找不到 skills 目录：$SkillsRoot" }
if (-not (Test-Path $ManifestPath)) { throw "找不到 manifest.json：$ManifestPath" }

$TargetDirs = [ordered]@{
  agents = Join-Path $env:USERPROFILE '.agents\skills'
  cursor = Join-Path $env:USERPROFILE '.cursor\skills'
  devin  = Join-Path $env:USERPROFILE '.devin\skills'
  claude = Join-Path $env:USERPROFILE '.claude\skills'
  codex  = Join-Path $env:USERPROFILE '.codex\skills'
}

# manifest 里标为 agents 的「通用技能」展开到这里列的每个平台：
#   .agents  —— Cursor 与 Devin 的公共交集（两边的代码都读它）
#   .cursor  —— Cursor 的用户级技能目录
#   .devin   —— Devin 的用户级技能目录（见其 sessions.desktop.main.js）
#   .claude  —— Claude 的用户级目录，Cursor / Devin 也把 .claude/skills 当兼容目录读
$UniversalTargets = @('agents', 'cursor', 'devin', 'claude')

# ~/tools/shared 被 skill 正文当作权威来源引用，同样用联接接管。
$SharedDst = Join-Path $env:USERPROFILE 'tools\shared'

# -Encoding UTF8 是必需的：Windows PowerShell 5.1 在无 BOM 时按 ANSI 代码页读取，
# 会把 manifest/external 里的中文解码成乱码，导致 ConvertFrom-Json 直接失败。
$Manifest = Get-Content $ManifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
$SkillMap = @{}
foreach ($entry in $Manifest.skills) { $SkillMap[$entry.name] = $entry }

$names = @(Get-ChildItem -LiteralPath $SkillsRoot -Directory | Select-Object -ExpandProperty Name)
$ExternalPath = Join-Path $RepoRoot 'external.json'
$externals = @()
if (Test-Path -LiteralPath $ExternalPath) {
  # 不能用管道接 ConvertFrom-Json：Windows PowerShell 5.1 的 ConvertFrom-Json 不展开
  # JSON 数组，管道里是一个嵌套 Object[]，Where-Object 与 Select-Object -ExpandProperty
  # 都拿不到 name/path。foreach 在 5.1 与 pwsh 7 上都逐项枚举。
  $parsedExternals = Get-Content -LiteralPath $ExternalPath -Raw -Encoding UTF8 | ConvertFrom-Json
  foreach ($entry in $parsedExternals) {
    if ($entry.name -and $entry.path) { $externals += $entry }
  }
}
if ($Only) {
  $known = @($names) + @($externals | Select-Object -ExpandProperty name)
  $unknown = @($Only | Where-Object { $_ -notin $known })
  if ($unknown.Count) { throw "未知 skill：$($unknown -join ', ')" }
  $names = @($names | Where-Object { $_ -in $Only })
  $externals = @($externals | Where-Object { $_.name -in $Only })
}

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
if ((Test-Path $SharedSrc) -and (-not $Only -or 'token-efficient-workflow' -in $Only)) {
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
    elseif (Test-IsReparsePoint $SharedDst) {
      if ($DryRun) { Write-Host "  [dry-run] 替换旧联接 $SharedDst" }
      else { (Get-Item -LiteralPath $SharedDst -Force).Delete() }
    }
    New-DirJunction -Path $SharedDst -Destination $SharedSrc
    if (-not $DryRun) { Write-Host "  已联接 $SharedDst -> $SharedSrc" }
    $summary.linked++
  }
  Write-Host ""
}

# ---------- 2. 清理孤儿联接 ----------
# 归档/改名会让旧联接指向本仓库里已不存在的 skills/ 路径。这里只清理这类失效联接：
# 不碰真实目录，也不碰指向别处的联接。各机器 pull 后跑一次安装即完成迁移。
Write-Host "[orphans]"
$orphans = 0
foreach ($dirName in ($TargetDirs.Keys)) {
  if ($Target -ne 'all' -and $Target -ne $dirName) { continue }
  $root = $TargetDirs[$dirName]
  if (-not (Test-Path -LiteralPath $root)) { continue }
  foreach ($item in @(Get-ChildItem -LiteralPath $root -Force)) {
    if (-not [bool]($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint)) { continue }
    $linkTarget = Get-LinkTarget $item.FullName
    if (-not $linkTarget) { continue }
    $norm = [IO.Path]::GetFullPath($linkTarget)
    if ($norm -notlike "$SkillsRoot\*") { continue }
    if (Test-Path -LiteralPath $norm) { continue }
    if ($DryRun) { Write-Host "  [dry-run] 清理孤儿联接 $($item.Name)（源已不存在：$linkTarget）" }
    else { (Get-Item -LiteralPath $item.FullName -Force).Delete(); Write-Host "  - $($item.Name)（旧联接，源已归档/移走）" }
    $orphans++
  }
}
if ($orphans -eq 0) { Write-Host "  无孤儿联接" }
Write-Host ""
# ---------- 3. skills ----------
foreach ($dirName in ($TargetDirs.Keys)) {
  if ($Target -ne 'all' -and $Target -ne $dirName) { continue }
  $root = $TargetDirs[$dirName]
  Write-Host "[$dirName]  $root"

  foreach ($name in $names) {
    $entry = if ($SkillMap.ContainsKey($name)) { $SkillMap[$name] } else { $null }
    $defaults = if ($entry) { @($entry.defaultTargets) } else { @('agents') }
    # 'agents' = 通用技能组 → 展开成四个平台；'codex' = Codex 专属，不展开。
    $effective = @()
    foreach ($d in $defaults) {
      if ($d -eq 'agents') { $effective += $UniversalTargets } else { $effective += $d }
    }

    # -Target all 时按 manifest 各就各位；显式指定 -Target 时以命令行为准。
    if ($Target -eq 'all' -and ($effective -notcontains $dirName)) { continue }

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

# ---------- 4. 外部技能 ----------
# external.json 里登记的是「自己独立成库」的技能（例如 toolkit-map 有自己的仓库和发布节奏）。
# 做法仍然是挂联接、不复制内容——README 里记过内容分叉的教训。
if ($externals.Count) {
  if ($externals.Count) {
    Write-Host "[external]"
    foreach ($ext in $externals) {
      $externalSource = [Environment]::ExpandEnvironmentVariables($ext.path)
      if (-not [IO.Path]::IsPathRooted($externalSource)) { $externalSource = Join-Path $RepoRoot $externalSource }
      $externalSource = [IO.Path]::GetFullPath($externalSource)
      if (-not (Test-Path -LiteralPath $externalSource)) { Write-Host "  ! $($ext.name)：源不存在 $externalSource"; $summary.missing++; continue }
      $extTargets = if ($Target -ne 'all') { @($Target) } elseif ($ext.targets) { @($ext.targets) } else { $UniversalTargets }
      foreach ($dirName in $extTargets) {
        if (-not $TargetDirs.Contains($dirName)) { continue }
        if ($Target -ne 'all' -and $Target -ne $dirName) { continue }
        $src     = $externalSource
        $dst     = Join-Path $TargetDirs[$dirName] $ext.name
        if ([IO.Path]::GetFullPath($src) -eq [IO.Path]::GetFullPath($dst)) {
          Write-Host "  = $($ext.name)（源已在目标目录，保留真实目录）"
          $summary.skipped++
          continue
        }
        $already = (Test-IsReparsePoint $dst) -and ((Get-LinkTarget $dst) -eq $src)

        if ($Uninstall) {
          if ($already) {
            if ($DryRun) { Write-Host "  [dry-run] 删除联接 $($ext.name)（$dirName）" }
            else { (Get-Item -LiteralPath $dst -Force).Delete(); Write-Host "  已删除联接 $($ext.name)（$dirName）" }
            $summary.linked++
          }
          continue
        }
        if ($already) { Write-Host "  = $($ext.name)（$dirName 已就位）"; $summary.skipped++; continue }

        if ((Test-Path $dst) -and -not (Test-IsReparsePoint $dst)) {
          $bkRoot = "$($TargetDirs[$dirName]).backup-$stamp"
          if ($DryRun) { Write-Host "  [dry-run] 备份 $($ext.name)（$dirName）-> $bkRoot\" }
          else {
            New-Item -ItemType Directory -Path $bkRoot -Force | Out-Null
            Move-Item -LiteralPath $dst -Destination (Join-Path $bkRoot $ext.name)
            Write-Host "  ~ $($ext.name)（$dirName）已备份到 $bkRoot\"
          }
          $summary.backedUp++
        }
        elseif (Test-Path $dst) {
          if ($DryRun) { Write-Host "  [dry-run] 替换旧联接 $($ext.name)（$dirName）" }
          else { (Get-Item -LiteralPath $dst -Force).Delete() }
        }

        New-DirJunction -Path $dst -Destination $src
        if (-not $DryRun) { Write-Host "  + $($ext.name)（$dirName）" }
        $summary.linked++
      }
    }
    Write-Host ""
  }
}

Write-Host "----"
Write-Host ("联接/删除 {0}  |  已就位 {1}  |  备份 {2}  |  源缺失 {3}" -f $summary.linked, $summary.skipped, $summary.backedUp, $summary.missing)
if ($summary.backedUp -gt 0 -and -not $DryRun) {
  Write-Host "备份目录以 .backup-$stamp 结尾，确认无碍后可自行删除。"
}
if ($DryRun) { Write-Host "这是演练，未改动任何文件。去掉 -DryRun 才会真正执行。" }
