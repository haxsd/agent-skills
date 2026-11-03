# Pester 测试（v5 / v6）

迁移要点改编自 github/awesome-copilot 的 `pester-migration`（固定版本 e2306b6922220f28d91ef5f7f2eaeb6de99913a0，MIT，Copyright GitHub, Inc.；许可见 `../LICENSES/MIT-github-awesome-copilot.txt`）。本仓中文改写；下面每个示例都在 PowerShell 7 + Pester 6.2.0 上实跑过（Linux 盒子），Windows PowerShell 5.1 的差异按官方文档标注。权威来源：<https://pester.dev/docs/migrations/>。

## 先确认版本

```powershell
Get-Module Pester -ListAvailable | Select-Object Name, Version, Path
```

- Windows PowerShell 5.1 自带签名的 Pester 3.4，`Install-Module` 默认不会覆盖它：装新版用 `Install-Module Pester -Scope CurrentUser -Force -SkipPublisherCheck`，测试脚本里 `Import-Module Pester -MinimumVersion 5.0`，避免悄悄用上 3.x。
- 想停在 v5：`Install-Module Pester -MaximumVersion 5.99.99`。
- 从测试代码判断它写给哪个版本：`Should Be`（无短横线）是 v3；文件顶部直接 dot-source、`$MyInvocation.MyCommand.Path` 是 v4；`Assert-MockCalled` 在 v6 已移除。

## 两阶段：发现 vs 运行（最常见的坑）

v5 起每个文件先“发现”（收集 `Describe`/`It`）再“运行”。写在块外的代码只在发现阶段执行，运行阶段看不到其中定义的函数和变量：

```powershell
# 错：两个测试都会失败（函数找不到、变量为 $null）
. (Join-Path $PSScriptRoot 'Get-Thing.ps1')
$x = 'set-at-discovery'
Describe 'bad' { It 'sees function' { Get-Thing -Name a | Should -Be 'thing:a' } }
```

```powershell
# 对：被测代码放进 BeforeAll；生成用例的数据放进 BeforeDiscovery
BeforeDiscovery {
    $cases = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'cases.json') -Raw | ConvertFrom-Json |
        ForEach-Object { @{ Name = $_.Name; Expected = $_.Expected } }
}
BeforeAll {
    . (Join-Path $PSScriptRoot 'Get-Thing.ps1')
}
Describe 'Get-Thing' {
    It 'returns <Expected> for <Name>' -ForEach $cases {
        Get-Thing -Name $Name | Should -Be $Expected
    }
    It 'throws without a name' {
        { Get-Thing } | Should -Throw '*required*'
    }
}
```

- `-ForEach` 的每一项要是 **hashtable** 才会展开成 `$Name`、`$Expected`；直接传 `ConvertFrom-Json` 得到的对象，变量会是 `$null`（实测），要么像上面转成 hashtable，要么在测试里用 `$_.Name`。
- 定位文件用 `$PSScriptRoot` + `Join-Path`，不用 `$MyInvocation.MyCommand.Path`，也不要手拼 `\`。
- `Should -Throw` 的参数按 `-like` 通配匹配消息，写 `'*关键词*'`。
- v6 中空或 `$null` 的 `-ForEach` 会报错；确实可能为空时加 `-AllowNullOrEmptyForEach`。同一块里重复的 `BeforeAll`/`BeforeEach` 在 v6 也会报错，合并成一个。

## Mock

```powershell
Describe 'Invoke-Tool' {
    BeforeAll { Mock Get-Thing { 'mocked' } }
    It 'uses Get-Thing once' {
        Invoke-Tool -Name x | Should -Be 'tool(mocked)'
        Should -Invoke Get-Thing -Times 1 -Exactly
    }
}
```

- 断言调用用 `Should -Invoke` / `Should -InvokeVerifiable`；`Assert-MockCalled`、`Assert-VerifiableMock` 在 v6 已移除。
- v6 中只带 `-ParameterFilter` 的 mock 遇到不匹配的调用会直接失败（不再回落到真实命令，实测）；需要兜底时再加一个不带过滤器的默认 `Mock`。
- Mock 的作用域跟随定义它的块（`BeforeAll` 在 `Describe` 里就作用于整个 `Describe`）。

## 在 CI / agent 里运行

```powershell
$ErrorActionPreference = 'Stop'
Import-Module Pester -MinimumVersion 5.0
$config = New-PesterConfiguration
$config.Run.Path = $PSScriptRoot
$config.Run.Exit = $true              # 有失败时进程退出码非 0
$config.Output.Verbosity = 'Detailed'
$config.TestResult.Enabled = $true    # NUnit XML，供 CI 展示
$config.TestResult.OutputPath = Join-Path $PSScriptRoot 'testResults.xml'
Invoke-Pester -Configuration $config
```

- 用 `pwsh -NoLogo -NoProfile -NonInteractive -File run-tests.ps1` 调用（见 SKILL.md 的 `-File` 规则），并检查退出码；不加 `Run.Exit` 时失败也可能返回 0。
- 旧的 `Invoke-Pester -Script/-OutputFile/-CodeCoverage` 参数在 v5+ 改为配置对象。

## 迁移纪律

- 先在当前版本跑出基线；一次只跨一个大版本（v4→v5→v6）。
- 迁移只改结构和调用方式，不改断言含义；结果与基线不同且不在已知破坏性变更里，先查原因。
- 批量替换脚本会误改：看 diff、重跑；保留 `*.Tests.ps1` 原编码。
