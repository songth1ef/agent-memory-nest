# Changelog

**English** | [中文](CHANGELOG.zh.md)

Protocol versions are `MAJOR.MINOR`: a minor version is backward compatible, a
major version may need migration. Numbering restarts at 1.0 with the new name;
history before it belongs to Nestwork, whose last protocol was 3.2.

## 1.0.0 (protocol 1.0) — agent-memory-nest

Nestwork is renamed to agent-memory-nest and the protocol is simplified.
Existing nests migrate with [docs/migrating-from-nestwork.md](docs/migrating-from-nestwork.md).

### Changed

- **Renamed.** Repository, scripts, environment variables and identity files move
  from `nestwork` to `agent-nest` / `AGENT_NEST_*`. Installers read the old identity
  files, so a machine keeps its host and agent ids, and they replace old hooks,
  startup blocks and Kimi config blocks instead of adding second copies.
- **Shorter protocol.** `AGENTS.md` goes from 530 to about 185 lines.
- **Four priority levels** instead of six: `queen/` > `shared/` > `agents/` >
  `projects/` and `workflow/`. Strategy now sits with the rules in `queen/`.
- **One splitting rule for every file.** A file over the configured limit is split
  like a wiki: `foo.md` becomes an index, the content moves into `foo/`. Agents keep
  the indexes themselves.
- **Settings in `config.md`.** Split limits, the resident budget, the distillation
  reminder and feature switches live in the front matter of `config.md`, overridden
  per machine by `agents/<host>/config.md`. They replace `queen/limits.md` and
  `agents/<host>/settings.json`.

### Added

- `scripts/maintenance/check-nest.py`: checks split limits, resident budgets,
  topic descriptions and index links. The Stop hook runs it on the agent's folder
  and, in Claude Code, hands any problem back to the agent to fix.
- `scripts/git-hooks/pre-push`: a private nest refuses to push to the public
  template (or other remotes listed in `public_remotes`). Installers enable it.
- A session-start reminder when shared memory has not been distilled for
  `distill.reminder_days` (30 by default).
- `config.example.md`, `LICENSE` (MIT), and docs for migration and troubleshooting.

### Removed

- `memory-index.py` (index generation) and `check-resident.py`, replaced by the checker.
- Local history sync to per-agent orphan branches, and the claude-mem export.
- The upstream-sync GitHub workflow; `scripts/maintenance/update.sh` remains.
- Search-oriented landing pages and the blog from the old repository.
