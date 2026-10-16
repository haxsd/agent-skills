# Windows agent × shell 最小翻车样例

> **状态**：第 1~8 条为「经验/文档」归纳，**未在本机 Windows 复跑**；第 9 条不同——它在**本机 DSH 上实测过**（见该条「依据」）。两类证据不要互相顶替：第 9 条可当本机事实，第 1~8 条仍只作避坑提示，不作 CI 断言。

依据：toolkit-map / AGENTS.md、win-cli-scan（powershell-safe-invocation）、Microsoft about_Character_Encoding、.NET ProcessStartInfo 文档。  
**主题一句话**：agent 翻车集中在「当 bash 写 Windows」「powershell≠pwsh」「引号叠层」「编码默认值」「退出码拿错对象」。

---

### 1. 把 `powershell.exe` 当 PS7，并写 `&&`
- **翻车命令**：`powershell -NoProfile -Command "npm ci && npm test"`
- **现象**：宿主仍是 Windows PowerShell **5.1**；`&&` 在 5.1 是语法错误（ParserError），整句不跑。机器上装了 `pwsh` 也不会让 `powershell.exe` 变成 7。
- **正确写法**：明确用 7：`pwsh -NoProfile -Command 'npm ci; if ($LASTEXITCODE -eq 0) { npm test }'`；若必须 5.1，拆成两次调用，不要用 `&&`。
- **依据**：经验/文档（powershell-safe-invocation：`powershell.exe`=5.1 / `pwsh.exe`=7；PS7 才有 pipeline chain）

### 2. `cmd /c` 再套 `pwsh -Command "..."`，引号三层爆炸
- **翻车命令**：`cmd.exe /c pwsh -NoProfile -Command "python -c \"import json; print(json.dumps({'a': 'b c'}))\""`
- **现象**：cmd → pwsh → 目标进程各解一层引号；bash 式 `\"` 在 PowerShell 不可靠；JSON/带空格参数被拆或吞掉，表现为 Unexpected token 或参数残缺。
- **正确写法**：复杂逻辑写成 `.ps1`，用 `pwsh -NoLogo -NoProfile -NonInteractive -File .\task.ps1`；原生参数用 `& $exe @argList`，不要为了“方便”再套 `cmd /c`。
- **依据**：经验/文档（powershell-safe-invocation：避免 `cmd.exe /c pwsh -Command`；`-File` 优先于 `-Command`）

### 3. 外层 PowerShell 先展开 `$变量`，内层拿到空串
- **翻车命令**（外层已在 PowerShell 里）：`pwsh -NoProfile -Command "Write-Host path=$env:USERPROFILE; Test-Path $p"`
- **现象**：外层先把 `$env:USERPROFILE` / `$p` 展开完再交给子进程；变量未定义时内层收到空，agent 还以为参数传进去了。
- **正确写法**：外层脚本字符串用**单引号**：`pwsh -NoProfile -Command 'Write-Host path=$env:USERPROFILE'`；更稳：写临时 `.ps1` + `-File`。
- **依据**：经验/文档（powershell-safe-invocation：outer `-Command` 会先展开 `$`）

### 4. 把 bash heredoc 直接贴进 PowerShell
- **翻车命令**：
```text
python - <<'PY'
print("hi")
PY
```
- **现象**：PowerShell 不认 `<<`；`<` 按重定向/解析错误处理，整段 ParserError，脚本不执行。
- **正确写法**：
```powershell
@'
print("hi")
'@ | python -
```
或写临时 `.py` 再 `python .\tmp.py`。
- **依据**：经验/文档（powershell-safe-invocation：禁止 bash heredoc）

### 5. 路径含空格：拼成一大串，或迷信 `Start-Process -ArgumentList`
- **翻车命令**：
```powershell
$exe = 'C:\Program Files\Foo\foo.exe'
& $exe "--in C:\My Data\a.json"   # 一整串
# 或
Start-Process -FilePath $exe -ArgumentList @('--in','C:\My Data\a.json')
```
- **现象**：一整串会被原生程序再按空格切开；`Start-Process -ArgumentList` 实质是拼命令行字符串，空格/空参数易翻车。PS5.1 跑在 .NET Framework 上，**没有** `ProcessStartInfo.ArgumentList`（那是 .NET Core 2.1+），不能指望“结构化 ArgumentList API”。
- **正确写法**（前台执行优先）：
```powershell
$exe = 'C:\Program Files\Foo\foo.exe'
$argList = @('--in','C:\My Data\a.json','--out','C:\My Data\out.json')
& $exe @argList
$exitCode = $LASTEXITCODE
```
- **依据**：经验/文档（powershell-safe-invocation；MS/.NET：ArgumentList 非 Framework）

### 6. `Start-Process` 不带 `-Wait`，去读 `ExitCode` 得到空
- **翻车命令**：
```powershell
$p = Start-Process -FilePath $exe -ArgumentList $argStr -PassThru
if ($p.ExitCode -ne 0) { throw 'failed' }   # 立刻读
```
- **现象**：进程还没结束时 `ExitCode` 常为 `$null`；agent 误判成功/失败。再叠加 `-ArgumentList` 拼串问题，排障更难。
- **正确写法**：普通前台任务不要用 `Start-Process`，改 `& $exe @argList` + `$LASTEXITCODE`。若必须分进程：`-Wait -PassThru` 后再读 `ExitCode`。
- **依据**：经验/文档（powershell-safe-invocation：Start-Process 仅用于提权/新窗口/脱离；前台用 call operator）

### 7. 编码默认值：5.1 的 `>` / `Out-File` = UTF-16LE；中文机 `Set-Content` 默认可是 ANSI/GBK
- **翻车命令**：
```powershell
"{ `"ok`": true }" | Out-File .\config.json          # 或 echo ... > config.json
# 或在中文 Windows 上：
Set-Content .\notes.txt '中文内容'                   # 未指定 -Encoding
```
- **现象**：PS5.1 下 `Out-File` / `>` / `>>` 默认 **UTF-16LE**；`Set-Content` 新建文件默认是系统 **ANSI**（中文区常见 GBK）。Node/Python/git 当 UTF-8 读 → BOM/乱码/JSON 解析失败。PS7 默认多为 UTF-8 无 BOM，同一段 agent 代码换宿主结果不同。另：5.1 的 `-Encoding utf8` 仍会带 BOM。
- **正确写法**：显式编码；跨工具文本优先 UTF-8。5.1 可用 `[IO.File]::WriteAllText($path, $text, [Text.UTF8Encoding]::new($false))` 写无 BOM UTF-8；或 `Set-Content -Encoding utf8`（有 BOM，需下游能容忍）。改已有文件前先确认原编码，勿默默转码。
- **依据**：经验/文档（Microsoft about_Character_Encoding；powershell-safe-invocation Encoding 节）

### 8. `Get-Command python3` 能找到，跑起来退出码 9009（商店别名）
- **翻车命令**：
```powershell
$py = (Get-Command python3).Source
& $py -c "print(1)"
# agent 只看到“命令存在”就宣布环境 OK
```
- **现象**：`WindowsApps\python3.exe` 常是 **0 字节应用执行别名**：`Get-Command` 有路径，未装商店版/非交互时执行无输出、**退出码 9009**。注意：同目录 `pwsh.exe`/`winget.exe` 也可能是 0 字节但能跑——**不能只看文件长度**，必须真跑版本命令。另：`$LASTEXITCODE` 只对原生程序；cmdlet 成败看异常 / `$ErrorActionPreference`，别混用。
- **正确写法**：
```powershell
$py = (Get-Command python -ErrorAction SilentlyContinue)?.Source
& $py --version
if ($LASTEXITCODE -ne 0) { throw "python 不可用，exit=$LASTEXITCODE" }
# 或走 toolkit-map：map.ps1 find python -Json，看 verification，勿盲信 PATH 第一个
```
- **依据**：经验/文档（toolkit-map AGENTS.md / platform-notes：存在≠可用；0 字节≠一定坏）

### 9. 等条件时先睡一个猜出来的时长（如 `Start-Sleep -Seconds 30`）
- **翻车命令**：
```powershell
Set-Content -LiteralPath .\build\start.ps1 -Value '...'   # 刚启动的准备脚本
Start-Sleep -Seconds 30                                   # “保险起见先睡 30 秒”
Test-Path .\build\ready.json                              # 再检查是否就绪
```
- **现象**：准备好可能是 3 秒也可能是 90 秒；猜短了要再睡一轮，猜长了就算 5 秒就够了也照样睡满。这不是 token 成本，而是**纯墙钟浪费**——等待时间与真实进度完全脱钩。反过来，宿主本来就会在命令结束时通知 agent，这 30 秒可能一秒都不必花。
- **正确写法**：要结果就直接前台跑（阻塞到结束，不加 sleep）；要等外部条件就短轮询，命中有上限、命中即停：
```powershell
$deadline = (Get-Date).AddSeconds(120)
while ((Get-Date) -lt $deadline) {
    if (Test-Path -LiteralPath .\build\ready.json) { break }
    Start-Sleep -Seconds 3
}
```
- **依据（本机 DSH 实测）**：起一个 12 秒后台任务，全程不调用任何读取接口，完成通知自行到达；一条 12 秒前台命令设 5 秒超时后，控制权仅约 5 秒就返回，随后同样收到完成通知。即「等命令结束」不需要 sleep，只有「等条件满足」才需要短轮询。参见 SKILL.md「等待与异步：不要猜时长」。

---

**可选附录（toolkit-map 特有，未算进主 8 条）**：PS5.1 上 `@($list)` 作用于 `List[object]` 会 `Argument types do not match`，要用 `$list.ToArray()`（AGENTS.md 坑 5）。
