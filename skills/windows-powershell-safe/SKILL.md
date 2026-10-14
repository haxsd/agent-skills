---
name: windows-powershell-safe
description: 在 Windows 上写或运行 PowerShell 时使用（含 agent 壳 / pwsh / powershell 会话）；涉及 native program、引号与 escaping、编码、退出码、路径、Start-Process、文件操作或命令失败排查时触发。
license: Complete terms in LICENSE.txt
---

# Windows PowerShell Safe

改编自 Misaka-Mikoto-Tech/agent-skills 的 powershell-safe-invocation，并借鉴 agent-shells 的 stop rules；本仓 slim。

## 宿主：pwsh vs powershell

- `pwsh.exe` = PowerShell 7；`powershell.exe` = Windows PowerShell 5.1。
- 装了 PowerShell 7 并不会让 `powershell.exe` 变成 7。不确定当前壳时先看 `$PSVersionTable.PSVersion`。
- 同一命令在 5.1 与 7 上参数可能不同；依赖版本相关参数前先 `Get-Command <cmdlet> -Syntax`。

## 调用原生程序

参数能分开传，就不要拼成一条大字符串。

```powershell
$exe = 'C:\Path With Spaces\tool.exe'
$argList = @('--input', 'C:\Data Folder\input.json', '--flag')

& $exe @argList

$exitCode = $LASTEXITCODE
if ($exitCode -ne 0) { throw "$exe failed with exit code $exitCode" }
```

- 每个 native 参数作为数组的一项；变量里的可执行文件路径用 `&` 调用。
- `$LASTEXITCODE` 必须紧接着取；不要用 `$args` 当自己的数组名（自动变量），用 `$argList` / `$nativeArgs`。
- 不用 `Invoke-Expression`；不要只为启动 exe 而套一层 `cmd.exe /c`；不要用 Bash 风格的 `\"` 转义。

## Cmdlet

用 hashtable splatting，具体路径用 `-LiteralPath`：

```powershell
$params = @{
    LiteralPath = 'C:\Data[1]\input.txt'
    Destination = 'C:\Output'
    Force       = $true
    ErrorAction = 'Stop'
}
Copy-Item @params
```

- 只支持 `-Path` 的 cmdlet（如 `New-Item`）就用 `-Path`；不确定先 `Get-Command <cmdlet> -Syntax`。
- 判断 cmdlet 成功与否用终止错误（`$ErrorActionPreference = 'Stop'`），不要看 `$LASTEXITCODE`。
- 参数值里的表达式要加括号或先赋值：`Select-Object -Index (100..120)`。

## 复杂命令走 -File

含多行、嵌套引号、JSON、正则、管道、重定向、非 ASCII 路径时：先写临时 `.ps1`，再执行。

```text
pwsh.exe -NoLogo -NoProfile -NonInteractive -File script.ps1
```

超过一个短表达式就优先 `-File` 而不是 `-Command`。确实要用 `-Command` 且外层也是 PowerShell 时，外层用单引号包裹脚本字符串，避免外层先展开 `$p`、`$env:...`。跨多层解释器或包装器时，停止加引号，改写 `.ps1`。不要不加判断地加 `-ExecutionPolicy Bypass`。

## 编码底线

- 新写给别的工具消费的文本文件，显式指定其所需编码（通常 `utf8`）。
- 改已有文本文件前先确认并保留原编码；GBK、UTF-16、对 BOM 敏感的不要静默转换，不清楚就查或问。
- 不默认设置 `Console.InputEncoding` / `Console.OutputEncoding`，仅在确认终端或原生程序编码不匹配时设置；`$OutputEncoding` 控制的是发给原生程序的文本。
- 二进制文件不要套文本编码选项，用字节 API。

## Start-Process 慎用

普通前台执行用 `& $exe @argList`。仅当需要提权、新窗口/隐藏窗口、分离启动或 shell 行为时才用 `Start-Process`。

`Start-Process -ArgumentList` 会把值拼成命令行字符串，不是可靠的结构化传参。参数边界重要时用 `ProcessStartInfo.ArgumentList`（**.NET Core / PowerShell 7**；Windows PowerShell 5.1 / .NET Framework **没有**该 API，勿在 5.1 上硬用）：

```powershell
$psi = [System.Diagnostics.ProcessStartInfo]::new()
$psi.FileName = $exe
$psi.UseShellExecute = $false
foreach ($arg in $argList) { $psi.ArgumentList.Add($arg) }
$process = [System.Diagnostics.Process]::Start($psi)
$process.WaitForExit()
if ($process.ExitCode -ne 0) { throw "exit code $($process.ExitCode)" }
```

## 决策顺序

1. PowerShell cmdlet。
2. `& $exe @argList`。
3. 临时 `.ps1` + `pwsh.exe -File`。
4. `ProcessStartInfo.ArgumentList`。
5. 需要其特殊行为时才 `Start-Process`。
6. 只有确实需要 cmd 语义才 `cmd.exe /c`。
7. `Invoke-Expression` 仅作严格受控的最后手段。

## Stop rules

- 同一失败形状不要原样重试。
- 换了形状第二次仍失败就停下报告，除非有新证据改变判断。
- 破坏性操作（递归删除/移动、大范围覆盖）先解析并校验绝对路径，确认目标在预期根内，拒绝空路径与根级路径。
- 不要把私密的原始失败日志提交进仓库。

常见翻车样例（经验/文档归纳，未在本机 Windows 复跑）见 `references/repros.md`。

<!-- provenance:start -->
> 创作归属：原创改进（基于上游）。来源、署名与许可见 [来源说明](../../ATTRIBUTION.md#windows-powershell-safe)。
<!-- provenance:end -->
