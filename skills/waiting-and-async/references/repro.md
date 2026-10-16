# 等待反例：先睡一个猜出来的时长

> **状态**：主反例与证伪项**在本机 DSH 上实测过**（2026-10-16）；跨宿主差异列为未测，需自测探针。

## 1. 等条件时先睡一个猜出来的时长（主反例）

```powershell
Set-Content -LiteralPath .\build\start.ps1 -Value '...'   # 刚启动的准备脚本
Start-Sleep -Seconds 15                                   # “保险起见先睡 15 秒”
Test-Path .\build\ready.json                              # 再检查是否就绪
```

- **现象**：准备好可能是 3 秒也可能是 90 秒。猜短了要再睡一轮；猜长了就算 5 秒就够，也照样睡满。等待时间与真实进度完全脱钩，而且失败会以「睡够时间了，假设它好了」的形式被掩盖。
- **正确写法**：锚定真实条件、短间隔、有上限、命中即停：

  ```powershell
  $deadline = (Get-Date).AddSeconds(120)
  while ((Get-Date) -lt $deadline) {
      if (Test-Path -LiteralPath .\build\ready.json) { break }
      Start-Sleep -Seconds 3
  }
  ```

- **依据（本机 DSH 实测）**：同上。

## 2. 等命令结束时另加 sleep（实测证伪）

```powershell
& $exe @argList          # 已经阻塞到结束
Start-Sleep -Seconds 10  # 多余的 10 秒：没有任何东西会因为这一觉而变得更好
```

- **依据（本机 DSH 实测）**：12 秒前台命令设 5 秒超时 → 控制权约 5 秒返回，随后收到完成通知；12 秒后台任务在全程零轮询下也收到完成通知。**等进度不需要 sleep。**

## 3. 未测项：通知的到达时机

同一 harness 上的一个对照观察未能证明「通知一定在你想检查时立刻到达」：那个会话里 agent 在任务完成前约 3 秒先查了一次状态，随后就没有收到自发通知——是「没送达」还是「已被消费」，两种解释无法区分（窗口被自己的轮询截断了）。

**结论**：探针只能证明「无需轮询即可拿到完成通知」，不能推断通知的到达时机。所以第 1 条规则仍然成立：探针失败就退回带上限的短轮询，不要押注通知。

## 4. 与其他规则的边界

- 等**子代理**（派发—等待—取回）不是本技能范围：见 `skills/execute-plan/references/task-loop.md` 的有界等待规则。
- 测试代码里等条件（断言前的条件轮询、按事件等待）见 `skills/systematic-debugging/references/condition-based-waiting.md`；那里的轮询间隔可以到 10ms 级，不要套用本技能的 2~5 秒。
