# 更新日志

[English](CHANGELOG.md) | **中文**

协议版本号为 `主版本.次版本`：次版本向后兼容，主版本可能需要迁移。4.0 之前的历史属于 Nestwork。

## 4.0.0（协议 4.0）—— agent-memory-nest

Nestwork 改名为 agent-memory-nest，并精简协议。已有的巢按
[docs/migrating-from-nestwork.md](docs/migrating-from-nestwork.md) 迁移。

### 变更

- **改名。** 仓库、脚本、环境变量和身份文件从 `nestwork` 改为 `agent-nest` / `AGENT_NEST_*`。
  安装脚本会读取旧的身份文件，所以每台机器保留原来的主机名和 agent id；
  旧的 hook、启动指令块和 Kimi 配置块会被原地替换，不会多出第二份。
- **协议变短。** `AGENTS.md` 从 530 行减到约 185 行。
- **优先级从 6 层减到 4 层：** `queen/` > `shared/` > `agents/` > `projects/` 和 `workflow/`。
  战略和规则一起放在 `queen/`。
- **所有文件只有一条拆分规则。** 超过配置上限的文件像 wiki 一样拆：
  `foo.md` 变成索引，内容移进 `foo/`。索引由 agent 自己维护。
- **设置统一放进 `config.md`。** 拆分上限、常驻层预算、蒸馏提醒和功能开关写在 `config.md`
  的开头，单台机器用 `agents/<host>/config.md` 覆盖。取代了 `queen/limits.md` 和
  `agents/<host>/settings.json`。

### 新增

- `scripts/maintenance/check-nest.py`：检查拆分上限、常驻层预算、主题描述和索引链接。
  Stop hook 在每回合结束时检查该 agent 的目录；在 Claude Code 里，发现问题会交回给 agent 去修。
- `scripts/git-hooks/pre-push`：私有巢拒绝推送到公开模板（以及 `public_remotes` 里列出的仓库）。
  安装脚本会自动启用。
- 共享记忆超过 `distill.reminder_days`（默认 30 天）没有蒸馏时，会话开始时提醒。
- `config.example.md`、`LICENSE`（MIT），以及迁移和故障排查文档。

### 移除

- `memory-index.py`（索引生成）和 `check-resident.py`，由检查器取代。
- 把本地历史同步到每个 agent 孤儿分支的功能，以及 claude-mem 导出。
- 上游同步的 GitHub workflow；`scripts/maintenance/update.sh` 保留。
- 旧仓库里面向搜索引擎的落地页和博客。
