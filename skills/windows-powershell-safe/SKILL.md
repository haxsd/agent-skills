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

## 等待与异步：不要猜时长

命令的耗时要么被观测，要么不存在——凭感觉挑一个 sleep 时长是按猜测付账：

- 猜短了条件未满足，还得再睡一次。
- 猜长了就算条件早就满足，也要睡满。**这不是 token 成本，是纯墙钟浪费。**

先分清两件事：

- **有进度可等**：命令完成会返回或自己唤醒你 → 下面的 1/2 条。
- **只有条件可等**：端口就绪、文件出现、日志出现某行 → 下面的第 3 条轮询。

| 情形 | 做法 |
|---|---|
| 短命令、你要它的结果才能往下走 | 前台执行（阻塞到结束），**不要**另加 `Start-Sleep` |
| 长命令、等它完成 | 前台执行 + 合理超时；被转后台后由完成通知唤醒你 |
| 长命令、等待期间有别的事做 | `run_in_background` 后台执行，先去做别的事；完成通知会到 |
| 等外部条件（端口/文件/日志） | 短间隔轮询并设上限，命中即停 |
| 真要等一段固定时间（限流退避） | 才 `Start-Sleep`，且时长有依据，不凭感觉 |

1. **前台阻塞就是等待方式。** 你要结果才能继续，就直接跑；跑完自然返回，不需要任何 sleep。超时值只是保险丝：设「不应该超过」的上限，不要为了「保险」放大它——宿主会在超时后转后台，并在完成时通知你。

    ```powershell
    & $exe @argList    # 阻塞到结束；快命令不要在这里再 Start-Sleep
    ```

2. **完成通知通常已经存在——先用 10 秒探针验证，再决定要不要睡。** 本机（DSH）实测：命令结束时会送达一条完成通知，**不需要任何轮询**；超时被转后台的任务，结束时同样送达。（证据：12 秒后台任务，未调用任何读取接口，通知自行到达；12 秒前台命令设 5 秒超时后仅约 5 秒返回，随后收到完成通知。）换宿主时先复测：起一个 10 秒任务、不做任何轮询，看通知是否自己到达。有通知 → 不需要 sleep；没有 → 按第 3 条轮询。注意通知是按自身时机送达的，不保证在你刚好想检查时立刻到达；手上没有别的事时，让轮次结束、等通知或条件就绪再继续，也比睡满一个猜测时长好。

3. **必须轮询就短轮询，锚定真实条件。** 间隔 2~5 秒（最慢 10 秒），条件一满足立刻停：

    ```powershell
    $deadline = (Get-Date).AddSeconds(120)
    while ((Get-Date) -lt $deadline) {
        if (Test-Path -LiteralPath $token) { break }
        Start-Sleep -Seconds 3
    }
    ```

4. **超时要报进度，不要静默睡满。** 一次 `Start-Sleep` 超过约 30 秒，或同一等待重复超过两轮，就换成带上限的短轮询并说明在等什么——否则失败会以「睡够时间了，假设它好了」的形式被掩盖过去。

5. **判断等待是否浪费，看时间线。** 等完用 `Get-Date` 记下起止；没有这行证据，就不算验证过等待策略。

平台无关的等待纪律（含探针与反例）见 `skills/waiting-and-async/SKILL.md`；这里只保留 Windows 命令执行特有的部分。

## Stop rules

- 同一失败形状不要原样重试。
- 换了形状第二次仍失败就停下报告，除非有新证据改变判断。
- 破坏性操作（递归删除/移动、大范围覆盖）先解析并校验绝对路径，确认目标在预期根内，拒绝空路径与根级路径。
- 不要把私密的原始失败日志提交进仓库。

常见翻车样例（经验/文档归纳，未在本机 Windows 复跑）见 `references/repros.md`。

<!-- provenance:start -->
> 创作归属：原创改进（基于上游）。来源、署名与许可见 [来源说明](../../ATTRIBUTION.md#windows-powershell-safe)。
<!-- provenance:end -->
