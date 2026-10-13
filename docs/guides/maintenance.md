# 维护与检查

新增或更新技能时，保留上游许可证与版本来源，更新 `catalog.json` 的分类、价值、问题和验收场景；在 `manifest.json` 只维护名字、原始归属和安装目标。不要把实时描述、文件数和字节数再手工缓存一份。

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
