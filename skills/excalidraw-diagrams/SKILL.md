---
name: excalidraw-diagrams
description: "用本地 @excalidraw/cli 把 .excalidraw JSON 渲染成 PNG（无需账号），适合架构图、流程图、示意图。Triggers: Excalidraw、架构图、流程图、示意图、框图、diagram、render excalidraw、excalidraw to png。"
license: Complete terms in LICENSE.txt
---

# Excalidraw Diagrams

用 `.excalidraw` JSON 描述图形，再用本地 CLI 渲染成 PNG。产物是**结构化示意图**
（框、线、箭头、标签），不是海报或艺术构图。

## 依赖与运行条件

- Node.js **22 或更高**（低版本会在启动阶段直接报错）。
- 本机已安装 Chrome / Edge / Chromium，或 Firefox。**CLI 不会下载浏览器**，
  它复用本机已安装的浏览器。
- 调用方式二选一：
  - `npx @excalidraw/cli ...`（无需预装，首次会拉包）
  - 全局安装后直接用 `excalidraw ...`

```bash
node --version          # 期望 v22+
npx @excalidraw/cli render --help
```

## 硬性约束

1. **默认只走本地 render 路径。** 标准调用就一条：

   ```bash
   excalidraw render drawing.excalidraw --out drawing.png
   # 或
   npx @excalidraw/cli render drawing.excalidraw --out drawing.png
   ```

2. **默认不启用 Excalidraw+ workspace API**（`login` / `scenes` / `collections`
   一类云端命令）。本 skill 不提供这些命令的操作步骤。仅当用户**明确要求**
   使用 workspace，且环境里**已经配好 API key** 时，才可以提一句「这需要
   workspace API」并由用户自己提供凭据；不要主动引导注册或登录。

3. 不要把「上传到云端」「分享链接」当作交付物。交付物是本地 PNG 文件。

## 渲染命令与常用选项

```bash
excalidraw render <input.excalidraw> --out <output.png> [options]
```

| 选项 / 变量 | 作用 |
| --- | --- |
| `--out <path>` | 输出 PNG 路径（也可用 `-` 写到 stdout） |
| `--scale <n>` | 缩放倍率，导出高清图时用（如 `--scale 2`） |
| `--theme light\|dark` | 渲染主题 |
| `--transparent` | 透明背景，适合贴进文档或幻灯片 |
| `--browser-path <path>` | 指定浏览器可执行文件 |
| `EXCALIDRAW_BROWSER_PATH` | 等价的浏览器路径环境变量 |
| `EXCALIDRAW_NO_UPDATE_NOTIFIER` | 置 `1` 关闭更新提示，脚本里更干净 |

脚本化调用的典型写法：

```bash
EXCALIDRAW_NO_UPDATE_NOTIFIER=1 \
excalidraw render drawing.excalidraw --out drawing.png --scale 2
```

## 文件格式：最小 element JSON

`.excalidraw` 文件是一个 JSON 对象，顶层字段：

- `type`: 固定 `"excalidraw"`
- `version`: 数字，示例用 `2`
- `elements`: 元素数组，**顺序即绘制顺序**
- `appState`: 画布状态，最小可用 `{ "viewBackgroundColor": "#ffffff" }`
- `files`: 图片资源，无图片时给 `{}`

### rectangle / text / arrow

常用三种元素：

- **rectangle**：框。需要 `x/y/width/height`、描边与填充色。
- **text**：标签。关键字段是 `text` / `originalText` / `fontSize` / `fontFamily`。
  **中文必须用 `"fontFamily": 5`（CJK）。** 用默认手写体（`1`）渲染中文会缺字。
- **arrow**：连线。用 `points` 表示相对位移；`endArrowhead: "arrow"`。

完整可渲染示例见 `references/minimal-scene.json`，可直接：

```bash
excalidraw render references/minimal-scene.json --out /tmp/minimal.png
```

编写复杂图时，先列节点与连线，再填 JSON；不确定字段时对照该最小示例扩写，
不要臆造 CLI 不认识的顶层字段。

## 协作流程（复杂图必走）

1. 主代理先写清节点清单、连线关系、每个框的中文标签。
2. 把这份规格交给 **ds（deepseek-flash）** 起草完整 `elements` JSON。不要用 v4-pro。
3. 主代理逐项核对：坐标是否重叠、箭头起止是否落在框边上、
   **中文标签是否用了 `fontFamily: 5`**、`id` 是否唯一。
4. 渲染后**目视检查 PNG**：文字有没有出框、箭头有没有指错、有没有元素被压住。
5. 有问题就改 JSON 重渲染，不要靠改截图硬凑。

## 与其它 skill 的分工

- 本 skill：结构化示意图（框 + 线 + 箭头 + 标签），可复现、可版本管理。
- `canvas-design` / `design`：海报、封面、艺术构图、版式设计，走视觉设计路线。
- 需要「好看的设计感配图」→ 交给设计类 skill；需要「能对齐、能改的架构图」→ 用本 skill。

## 失败排查

| 现象 | 原因 / 处理 |
| --- | --- |
| 找不到浏览器 / launch 失败 | 本机没有受支持的浏览器。安装 Chrome/Edge/Chromium 或 Firefox；或用 `--browser-path` / `EXCALIDRAW_BROWSER_PATH` 指到可执行文件 |
| Node 版本过低报错 | 升级到 Node.js 22+，切换版本后再跑 |
| JSON 解析失败 | `elements` 语法错误或尾逗号。用 `python -m json.tool x.excalidraw` 先校验 |
| 中文显示为方块 / 缺字 | `fontFamily` 不是 `5`。中文文本统一改成 `5` |
| 输出空白图 | 元素坐标全在可视区外，或 `elements` 为空；检查 x/y 与 width/height |
| 输出被截断 | 元素超出画布范围；调整坐标，或配合 `--scale` / `--max-width` / `--max-height` |

## 许可

CLI 本体为 MIT（`@excalidraw/cli`）。本 skill 文本由本仓库维护，条款见 `LICENSE.txt`。
固定参考的上游 commit 见 `UPSTREAM.json`（不 vendoring CLI 源码）。
