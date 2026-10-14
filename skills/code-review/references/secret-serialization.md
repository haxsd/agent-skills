<!--
本文件基于 Sentry skills（commit d18b7aa8ba878354e5c348310230e652f7690f9c）的 secret-serialization 改写。
Copyright 2025 Functional Software, Inc. dba Sentry；许可：Apache-2.0。
完整许可文本见 ../LICENSES/Apache-2.0.txt；版权与修改说明见 ../NOTICE.txt。
本仓修改：中文重写，合并上游 python 与 javascript-typescript 两个参考的要点；只读审查，不运行目标代码。
-->

# 凭据序列化检查

找"类型自己会序列化、上游又把整个对象交给汇点"造成的凭据泄露。一次泄露通常需要两处同时成立：

1. **持有者**：凭据存在带生成序列化路径的类型字段上（`__repr__`/`__str__`、`asdict`、`model_dump`、`toJSON`、属性枚举）。
2. **汇点**：日志、追踪、错误上报、缓存、队列或接口响应把整对象或全部 kwargs 序列化（`str(value)`、`span.set_data(key, obj)`、`logger.info("%s", obj)`、`JSON.stringify(args)`、`default=vars`）。

两端常由不同作者相隔数月写成。**任一端单独也可报**；搜另一侧时要点是搜整个仓库，不只搜 diff——汇点常常早已在主干上。

## 边界

- 本文件管生成序列化与整对象汇点造成的**间接**泄露；token 直接插值进日志消息、硬编码字面量和已提交的 `.env` 不属于这里，归通用安全审查。
- 静态审查，不运行目标代码；证据只用字段名、类型、路径和调用点，**不输出真实凭据值**（已出现的真实值也不要复述）。

## 凭据字段识别

字段名、类型或来源任一说"是凭据"就按凭据处理：

- 名称含 secret、token、password、passwd、api_key、access_key、private_key、client_secret、bearer、credential、authorization、cookie、session_key、dsn、connection_string、webhook_secret、hmac、refresh_token 等。
- 类型是 `SecretStr`、`SecretBytes` 等包装。
- 值来自环境变量、秘密管理器，或来自以上述命名的构造参数。

## 生成路径 vs 原始属性访问

- **生成路径**由类型自己产生：`__repr__`/`__str__`、`asdict`、`model_dump`、`toJSON`、可枚举属性遍历（`JSON.stringify`、`util.inspect`、展开运算符）。这是持有者的责任。
- **原始属性访问**直接读存储值：`vars(obj)`、`obj.__dict__`、`pickle`、`json.dumps(obj, default=vars)`。字段用什么机制都挡不住；只能当作汇点处理——仓库里有人对凭据实例这么做才报。

| 机制 | 挡住 | 仍包含该字段 |
|---|---|---|
| `dataclasses.field(repr=False)`、`attrs.field(repr=False)` | `__repr__`、`__str__` | `asdict`、`astuple`、原始访问 |
| Pydantic `Field(repr=False)` | `__repr__`、`__str__` | `model_dump`、`model_dump_json`、响应序列化、原始访问 |
| Pydantic `Field(exclude=True)` | `model_dump`、`model_dump_json`、响应序列化 | `__repr__`、`__str__`、原始访问 |
| Pydantic `Field(repr=False, exclude=True)` | 全部生成路径 | 原始访问 |
| JS `#private` 字段 | 全部生成路径 | 类体外无（显式读取也不可得） |
| `Object.defineProperty(..., {enumerable: false})` | 全部生成路径 | 显式属性读取 |
| 手写 `__repr__`/`__str__`/`toJSON` 并省略该字段 | 仅被覆盖的那条路径 | 其余生成路径、原始访问 |
| 脱敏包装（`SecretStr` 等） | 全部生成路径 | `pickle` 与递归 `__dict__` 遍历（如 `default=vars`）可达包装内部的值 |
| 不存到对象上（方法内读取或闭包持有） | 全部 | 无 |

**不算防护**：下划线命名、TS `private`、`__slots__`、类型注解、注释、`init=False`、仍会赋值的自定义 `__init__`。

## 排查步骤

1. 读改动 hunk：找新增/修改的凭据字段（持有者），以及把对象或 kwargs 序列化进日志、span、错误上下文、缓存、队列、响应的新代码（汇点）。
2. 对每个凭据字段读完整类、装饰器、基类和模型配置，列出全部生成路径，对照上表确认哪些被挡住。
3. 搜实例的构造与传递点：交给装饰器、`**kwargs`、工具调用参数、任务载荷或中间件的实例会到达通用汇点。
4. 搜全仓库汇点（不只 diff）：`str(value)`、`repr(`、`asdict(`、`model_dump(`、`set_data(`、`set_attribute(`、`set_context(`、`set_extra(`、`JSON.stringify(`、`util.inspect(`、以对象为参数的日志调用，以及 `vars(`、`__dict__`、`pickle.dumps(`、`default=vars`。
5. 改动的是汇点时，查它是否有标量键白名单、按凭据名脱敏、或把对象替换为类型名；再搜把凭据对象传进来的调用方。
6. 测试只用来确认有没有"断言序列化结果不含凭据"；缺测试是修复建议，不是发现。
7. 确认代码会上线：fixture、示例、生成代码、测试专用辅助不算。

## 判定与报告

| 情形 | 报告条件 |
|---|---|
| 未排除的凭据字段 | 凭据字段新增/移动到带生成序列化的类型上，且没有任何机制挡住其路径 |
| 部分排除 | 至少一条生成路径仍包含该字段，且仓库里有汇点对其实例使用那条路径 |
| 原始属性汇点 | 汇点对存储凭据的实例使用 `vars`/`__dict__`/`pickle`/`default=vars`，无论字段是否被排除或包装 |
| 凭据移入持有者 | 重构把凭据从延迟读取或闭包移到对象字段 |
| 整对象汇点 | 新增/修改的遥测、日志、错误上下文、缓存或响应代码序列化全部 kwargs、全部属性或整对象，且无白名单与脱敏 |
| 汇点失去过滤 | 改动删除或削弱已有汇点的脱敏、白名单或对象转类型名 |
| 对象交给遥测 | 客户端、配置或设置对象被传给会字符串化它的 span/日志/错误上下文调用 |

**严重程度**（与置信度分开写）：

- **高**：凭据在仓库任何位置到达汇点（日志行、span 属性、错误事件、缓存项、持久化行、队列载荷、接口响应）；另一端早于本次 diff 也算。新增整对象汇点且既有调用方会传入凭据对象同理。
- **中**：未排除的凭据字段，实例会离开构造模块，但全仓搜索没找到汇点；或没有白名单、也没追到凭据调用方的整对象汇点。
- **低**：未排除的凭据字段，实例从不离开构造作用域。

如果可达性依赖未证实的前提，取较低一档并说明。**不因持有者或汇点在 diff 之外而降级**——那正是这类问题的常态。

## 不报告

- 完全排除的字段（除非原始属性汇点会收到该实例）；仓库里没有汇点使用未挡路径的部分排除。
- 方法内读取、从不存到实例上的凭据；测试/fixture 中的占位值。
- 无生成序列化、也无 `__dict__`/枚举汇点的类型；已有白名单、按名脱敏或对象转类型名的汇点。
- diff 未触及、也没有被 diff 连起来的既有字段与汇点；风格、命名、缺测试类观察。

## 修复方向（每项发现给一条）

- 持有者：挡住全部生成路径（如 pydantic 同时 `repr=False, exclude=True`）、换成脱敏包装、或不存到对象上。
- 原始属性汇点：改为序列化显式白名单 dict，或不再在该对象上存凭据；字段标志或包装修不了它。
- 汇点：允许标量键白名单、按凭据名脱敏，对非标量值记录 `type(value).__name__` 而不是 `str(value)`。
- 回归测试：用汇点同款序列化（如 `json.dumps(asdict(obj))`、`JSON.stringify(obj)`、`util.inspect(obj)`、目标 SDK 的 serializer）序列化实例，断言凭据字符串不在结果里。

## 发现格式

- 标题：点名字段或汇点与泄露路径，如 "`_shared_secret` 进入 `RpcClient` 的 `asdict` 输出"。
- 描述：一至两句，说明哪条生成路径暴露凭据、实例流向哪里、怎么修。
- 证据：2–5 条，列出类、装饰器、检查过的生成路径、找过的排除机制，以及追过的每个汇点或调用方（含 diff 之外的）。
