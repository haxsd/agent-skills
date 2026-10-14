# 维护与检查

新增或更新技能时，在 `docs/sources/skill-provenance.json` 登记每项的创作归属：

- `upstream`：第三方引入，标作者和原始来源，保留许可证。
- `original`：本仓独立编写，写清原创贡献；外部工具依赖单独列出，不冒充技能文本上游。
- `derived`：原创改进（基于上游），同时写上游来源与本仓贡献，保留原作者和许可。
- `unverified`：来源证据不足，保留已知线索与待核验项，不默认算原创或已获再分发授权。

已有固定版本继续由 `upstreamFiles` 引用各项 `UPSTREAM.json`；原创 wrapper 的工具来源用 `dependencyFiles`。
历史来源未找回确切提交时用 `sources` 标注作者、URL、已知许可和待核验版本，不能拿当前上游 HEAD 充当原收录版本。
格式、路径、安装或编码适配本身不意味着整项原创；原创改进声明仅覆盖本仓新增部分。

`ATTRIBUTION.md`、`docs/catalog.md` 和每项 `SKILL.md` 的来源提示由 audit 从登记自动生成，不要手动改这些区块。
`--check` 会检查来源覆盖、非法重标原创、越界来源路径和生成内容漂移。新增技能必须先登记来源。

同时更新 `catalog.json` 的分类、价值、问题和验收场景；在 `manifest.json` 只维护名字、原始目录归属和安装目标。
`manifest.origin` 是安装来源目录，不是作者或著作权归属。不要把实时描述、文件数和字节数再手工缓存一份。

## 新增前的检查

引入第三方技能时先用 [skill-scanner](../../skills/skill-scanner/SKILL.md) 做只读风险检查，再人工复核提示指令、脚本、权限和覆盖缺口。
扫描不运行目标，不安装其依赖；无命中不代表安全，超限、内部链接或不可读内容须如实保留。
扫描器与本页的一致性 audit 分工不同，前者检查可疑行为，后者检查登记与文档。

新增还是升级按触发条件、输入和产出判断：职责独立才建新入口；增强既有任务时优先在原路径新增按需参考。
例如 skill-scanner（技能引入检查）与 variant-analysis（已知缺陷同族排查）独立启用；技能写作、通用审查和环境诊断的增强留在原有入口。

## 运行仓库检查

用已确认的 Python 与 Node 绝对路径运行：

```powershell
python scripts/audit_skills.py --write
python scripts/audit_skills.py --check
python scripts/check_docs.py
python -m unittest discover -s tests -q
python scripts/smoke_skills.py --node '<Node 的绝对路径>'
```

audit 生成分类目录、逐项审查和静态 JSON；修改人工源后重新生成，避免手改派生文档。check_docs 检查当前入口和文档的本地链接，不检查历史快照、上游技能参考或远程链接。已有超长入口和引用线索会作为提示保留。

CI 在 Ubuntu 和 Windows 上运行这些离线检查、UI/UX 数据校验，以及 Windows 临时目录里的安装器回归。CI 不需要任何模型密钥，不调用付费 API、不连接数据库、不启动浏览器测试。

技能里的测试并不全部属于仓库维护测试。UI/UX 的两个维护测试模块仍缺对应脚本；这些已知问题以及逐项审查、验证记录由维护者在内部维护，不随仓库公开。局部数据/工具检查通过不等于所有技能已做生产验证。

合并或归档技能前，先检查调用者、迁移必要资源与署名、验证验收场景，再更新 manifest/catalog。保留 `skills/<name>/` 稳定路径，分类通过索引完成。归档内容默认不安装。
