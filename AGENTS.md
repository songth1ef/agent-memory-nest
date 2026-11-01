<!-- protocol-version: 1.0 -->
# AGENT-MEMORY-NEST BOOTSTRAP

Every agent that loads this file shares one nest: a private git repository that
holds the rules, memory and context for all of the owner's agents, on every
machine and from every vendor. Follow this protocol in every session.

`$AGENT_NEST_PATH` below is the local clone of that private repository.
The `protocol-version` marker is `MAJOR.MINOR`: a MINOR bump is backward
compatible, a MAJOR bump may need migration.

---

## 1. Session start

Pull first, unless a session-start hook already did it this session:

```bash
git -C $AGENT_NEST_PATH pull --rebase
```

If the pull fails, say why and continue. Then read **only the resident layer**,
skipping any file that does not exist:

1. `queen/agent-rules.md`: behaviour rules
2. `shared/resident.md`: a short summary of who the owner is, current goals and pointers
3. `agents/<host>/<agent-id>/resident.md`: this agent's own short summary
4. `local/recent.md`: recent activity, generated from git history at session start

Everything else is **on demand**: `queen/strategy.md`, shared and agent
`memory.md` with their topic files, `projects/`, `workflow/`, and the mailbox
snapshot `agents/<host>/<agent-id>/local/inbox.md`. Search headings and keywords,
read only the relevant parts, and do not follow links recursively. A missing
resident file never means "load all history instead".

Follow the user's current task. Past work recorded in the nest is context, not
an assignment. When asked to resume or choose work, read the relevant project
notes, the strategy and recent git history, then propose one concrete next step.

If the session-start hook warns that the nest is not on its default branch, tell
the user before relying on anything you read.

## 2. Layout and identity

```
queen/        agent-rules.md, strategy.md      written only by the owner
shared/       resident.md, memory.md, topics   written only by distillation
agents/<host>/<agent-id>/                      written only by that agent
agents/<host>/config.md                        settings for one machine
projects/     one note per project             agents and owner
workflow/     portable methods and lessons     agents and owner
decisions/    decisions about the nest itself
config.md     settings for the whole nest (copy config.example.md)
```

- **host**: the machine's lowercased short hostname. **agent-id**: `<tool>-<4 chars>`
  (for example `claude-a7k2`) or just `<tool>` for one-per-machine tools.
- The installer stores them in `~/.agent_nest_host` and `~/.agent_nest_id_<tool>`.
  `AGENT_NEST_HOST` and `AGENT_NEST_AGENT_ID` override them. This is the only
  state kept outside the nest: a machine must know who it is to find its folder.
- Tunable settings (split limits, resident budget, reminders, switches) live in
  the front matter of `config.md`, overridden per machine by
  `agents/<host>/config.md`. See `config.example.md`. Settings tune behaviour;
  they never change the priority order or the write boundaries below.

## 3. Priority

When sources disagree, the higher one wins. Never merge conflicting instructions.

```
queen/ (rules, then strategy)  >  shared/  >  agents/  >  projects/ and workflow/
```

This is authority, not load order. A resident summary carries the authority of
the source it summarises.

## 4. Writing memory

- **Boundaries.** Write ordinary memory only under `agents/<host>/<agent-id>/`.
  Never write `queen/`. Never write another agent's or machine's folder. Change
  `shared/` only during distillation (section 5). Project and workflow notes may
  be edited when the task calls for it.
- **What to keep.** Decisions, corrections, conventions, lessons and project
  state that will matter again. Not temporary task details or one-off debugging.
  Note the date and the source (a commit, a file, the user's words).
- **Reuse before creating.** Read the index first and extend the file that already
  covers the topic. Create a new file only when none does.
- **Split like a wiki.** A file over `split.max_lines` or `split.max_kb` (config)
  is split: `foo.md` stays as an index of links, the content moves into `foo/`.
  In a memory folder, `memory.md` is the index of the folder's topic files.
- **Describe every topic file.** A topic file starts with front matter whose
  `description` says *when* to read it, because agents pick files by that line:

  ```markdown
  ---
  description: Machine-specific paths and ports; read before changing a host's setup
  updated: 2026-11-01
  ---
  ```

- **Keep indexes current.** Add a link line for every new topic file, remove it
  when a file goes. `resident.md` stays within `resident.max_bytes`.
- **Checked for you.** At the end of each turn the Stop hook runs
  `scripts/maintenance/check-nest.py` on your folder. If it reports problems,
  fix them before finishing. Run it by hand on any folder the same way.

## 5. Distillation

Distillation merges what individual agents learned into `shared/`. It is the one
manual step, triggered by the owner; once a month is enough, and the session-start
hook reminds after `distill.reminder_days`.

1. Read every agent's `memory.md` and topic files, and all of `shared/`.
2. Have a separate reviewer check the candidate for sensitive data, factual
   errors, contradictions and stale entries; it reports, it does not write.
3. Show the review to the owner and wait for confirmation.
4. Merge: drop duplicates, unify consistent facts, keep divergent observations,
   replace superseded facts with dated provenance. Never delete an agent's own memory.
5. Keep `shared/memory.md` as the index, run `check-nest.py --scope shared`, and
   commit as `memory: distill shared`.

`scripts/maintenance/distill.py` prints a ready-made prompt, or runs the merge
with `--run-claude` / `--run-codex` and leaves the result uncommitted for review.

An agent that notices something worth sharing outside a distillation writes it to
its own folder; the next distillation picks it up.

## 6. Sync

Tools with sync hooks (Claude Code, Codex, Kimi Code) need nothing from you:
before each memory write the hook pulls, after it the hook commits and pushes,
and the Stop hook repeats the commit and push as a safety net. Do not duplicate it.

Without hooks, sync your own folder at the end of the session:

```bash
git -C $AGENT_NEST_PATH add agents/<host>/<agent-id>/
git -C $AGENT_NEST_PATH diff --cached --quiet -- agents/<host>/<agent-id>/ || \
  git -C $AGENT_NEST_PATH commit -m "memory: update <host>/<agent-id>" -- agents/<host>/<agent-id>/
git -C $AGENT_NEST_PATH push
```

On a pull conflict: `queen/` and `shared/` take the remote version; your own
folder keeps yours; another agent's folder takes the remote version.

## 7. Privacy and leaks

- **No secrets, ever.** API keys, tokens and passwords never go into the nest,
  a commit message or a mailbox note, encrypted or not. Refer to them by location
  ("the token in the hub's `.env`").
- **The nest stays private.** Never push the nest, a branch of it, or any of its
  history to the public template or any other public remote. One such push
  publishes the whole history, and deleting the branch afterwards does not
  remove it. The installer enables `scripts/git-hooks/pre-push`, which refuses
  these pushes; never bypass it.
- **One-way flow.** Content moves from the template into a nest through
  `scripts/maintenance/update.sh`, never back. Publishing anything from a nest is
  a separate decision by the owner, after desensitising it.
- **Metadata is public to the host.** git-crypt (optional) encrypts file contents,
  but commit messages, file names and paths stay readable by the git host. Keep
  them free of personal details.

## 8. Other parts of the protocol

- **Mailbox.** Agents leave each other tasks and notes as files in their own
  `outbox/`; `scripts/comms/send.sh` and `read.sh` handle it. See `docs/agent-mailbox.md`.
- **Tool memory carryover.** Memory a tool keeps on one machine (Claude Code,
  Codex, Kimi Code and others) can be distilled into
  `agents/<host>/<agent-id>/carryover/<tool>.md`, a cold layer read only when
  restoring. Distil, never mirror. See `docs/tool-memory-carryover.md`.
- **Projects and workflow.** `projects/<name>.md` is a short status note (Current
  Goal, Current State, Next Action, Do Not, Last Verified; copy `projects/_template.md`).
  Deep project knowledge stays in that project's own repository. `workflow/` holds
  methods that survive a change of employer.
- **Ingesting a work directory.** Only when that directory has an
  `agent-nest.config.json`, always proposed by the agent and confirmed by the
  owner, with desensitisation. See `docs/workflow-protocol.md`.

## 9. Upstream updates

The session-start hook compares this file's `protocol-version` with the template's
(cached for a day, three-second timeout, silent when offline) and mentions a newer
version. Relay it and ask before running `bash scripts/maintenance/update.sh`,
which shows the diff, asks for confirmation, and replaces protocol files only:
it never touches `queen/`, `shared/`, `agents/`, `config.md` or your own projects.
