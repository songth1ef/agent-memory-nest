# Troubleshooting

**The session starts without the nest's context.**
Check that the installer ran for this tool and wrote its startup block (for Claude
Code, look for `<!-- agent-nest:begin -->` in `~/.claude/CLAUDE.md`). Tools without
a session-start hook rely on that block alone. If the hook prints a `[!]` warning
about the branch, switch the nest back to its default branch.

**Memory is committed but never pushed.**
Run `git -C <nest> push` by hand and read the error. Usually it is credentials
(`gh auth login`, or an SSH key), or the pre-push guard refusing a public remote,
which is intended.

**"upstream has conflicting changes" blocks a write.**
Another machine changed the same file. Run `git -C <nest> pull --rebase`, resolve
the conflict (keep your own folder's version, take the remote for `queen/` and
`shared/`), then retry the write.

**"autostash conflict" blocks a write.**
Uncommitted changes were parked in `git stash` during a pull. Run
`git -C <nest> stash pop`, resolve, commit, and retry.

**The Stop hook keeps reporting layout problems.**
Run `python3 <nest>/scripts/maintenance/check-nest.py` to see them all: a file over
the split limit, a topic file without `description`, a file missing from its index,
or an index link to a file that is gone. Fix the files; the hook blocks only once per
turn and never loops.

**The agent id differs between machines.**
That is expected: each machine has its own host folder. Within one machine, the ids
live in `~/.agent_nest_host` and `~/.agent_nest_id_<tool>`; override them with
`AGENT_NEST_HOST` and `AGENT_NEST_AGENT_ID`.

**I want to try it without pushing anything.**
Clone the template to a local folder, skip `git remote add`, and install. Everything
works locally; each push prints a warning and is retried until a private remote exists.
