---
# Copy this file to config.md and keep only the lines you change.
# Every key below shows its default.
split:
  max_lines: 300
  max_kb: 32
resident:
  max_bytes: 4096
distill:
  reminder_days: 30
check_on_stop: true
recent_digest: true
mailbox: true
upstream_check: true
# public_remotes: "github.com/me/some-public-repo"
---

# Nest configuration

Settings for the whole nest live in the front matter above. Scripts read only
that block; this text is for people.

A single machine can override any of them in `agents/<host>/config.md`, using
the same front-matter format. Order of precedence, last wins: built-in defaults,
then `config.md`, then `agents/<host>/config.md`.

Machine identity (which host this is, and each tool's agent id) is the one thing
that stays outside the nest, in `~/.agent_nest_host` and `~/.agent_nest_id_<tool>`:
a machine has to know who it is before it can find its own folder.

Secrets never go in any config file.

| Key | Default | What it controls |
|---|---|---|
| `split.max_lines` | 300 | A context file over this many lines must be split wiki-style |
| `split.max_kb` | 32 | Same, by size |
| `resident.max_bytes` | 4096 | Byte budget for each `resident.md`, loaded at every session start |
| `distill.reminder_days` | 30 | Session start reminds you to distill after this many days; `0` turns it off |
| `check_on_stop` | true | Run the layout checker on the agent's folder at the end of each turn |
| `recent_digest` | true | Rebuild `local/recent.md` from git history at session start |
| `mailbox` | true | Refresh the agent's unread messages at session start |
| `upstream_check` | true | Tell you when the template has a newer protocol version |
| `public_remotes` | none | Extra public remote URLs the pre-push guard refuses, comma-separated |
