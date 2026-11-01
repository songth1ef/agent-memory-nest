# agent-memory-nest

**English** | [中文](README.zh.md)

> **Your agents share one mind.**
> One git repository holds the rules, memory and context for every AI agent you run, on every machine and from every vendor.

## Why

Every coding agent now has some memory, but each one keeps it to itself:

- **Bound to one machine.** Claude Code, Codex and Kimi Code all store memory locally. A new laptop starts from zero.
- **Bound to one vendor.** What Claude learned stays with Claude. Switch to Codex and you explain everything again.
- **Bound to one account.** When a subscription ends or a tool shuts down, the memory goes with it.

agent-memory-nest moves that memory into a git repository you own. Every agent reads from the same nest and writes back to it, so they all work from one shared mind. A hive mind, not a set of strangers.

## What makes it different

- **No server, no daemon.** There is nothing to host and no port to expose. Git is the only transport, so agents on machines behind NAT or offline still sync when they reconnect.
- **More than memory.** The nest also carries rules and direction, with a fixed priority order for resolving conflicts, so a fleet of agents follows the same guidance instead of only sharing notes.
- **Clear write boundaries.** Each agent writes only to its own folder. Shared memory changes only through a reviewed distillation step.
- **Load what the task needs.** A small resident layer loads at session start, and everything else is read on demand, so context stays small as memory grows.
- **Private by design.** The nest is meant to live in a private repository, and can be encrypted end to end with git-crypt.

**Who it's for:** developers who work with several AI agents over the long term, across machines and tools, and want what those agents learn to stay with them rather than with any one vendor.

## How it works

```
   Claude Code     Codex     Gemini CLI     Kimi Code     ...
        │            │            │             │
        └────────────┴─────┬──────┴─────────────┘
                           │  pull at session start
                           │  commit + push on every write
                           ▼
                 ┌────────────────────┐
                 │  your private nest │   rules · memory · context
                 │    (a git repo)    │
                 └────────────────────┘
```

**Priority chain.** When two sources disagree, the higher one wins. They are never merged.

```
rules > strategy > shared memory > agent memory > project notes > workflow notes
```

**Session lifecycle.**

1. **Start.** A session-start hook pulls the nest and loads only the small resident layer: core rules plus a short summary of current goals and recent activity.
2. **Work.** Before each memory write, a hook pulls again. After the write, it commits and pushes. The window for a write conflict shrinks from a whole session to a single write.
3. **End.** A stop hook makes one last commit and push as a safety net. It does nothing if there is nothing to save.

Tools without hooks follow the same steps from a startup instruction file, and sync at the end of the session.

## Compared with other approaches

| | Built-in tool memory | Memory server | Memory SDK / platform | **agent-memory-nest** |
|---|---|---|---|---|
| Examples | Claude Code, Codex memory | ai-memory | mem0, Letta | |
| What you run | Nothing | A server process you host | A library or a hosted service | **Nothing but git** |
| Works across vendors | No | Yes | Built for apps you develop | **Yes** |
| Works across machines | No | Through your server | Depends on deployment | **Through any git remote** |
| Who holds the data | The tool, on one machine | You | You or the provider | **You, in a private repo** |
| Rules and direction for agents | Per tool | Not the focus | Not the focus | **Built in, with a priority chain** |

The trade-off: memory servers offer richer search, automatic capture and cross-tool session handoff. agent-memory-nest keeps memory as plain markdown that agents read and write deliberately, and asks nothing of you beyond a git repository.

*Based on each project's own documentation as of November 2026.*

## FAQ

**Do multiple agents writing at the same time cause conflicts?**
Rarely. Each agent writes only to its own folder, and shared memory changes only during distillation. Every write is preceded by a pull, so a conflict needs two machines writing the same file within the same moment. If that happens, the write is blocked and you merge by hand.

**Can I store API keys in the nest?**
No, not even in a private repository. Account compromise or a mistaken permission would expose them. Keep secrets in environment variables or a dedicated secret store.

**How do I keep private memory confidential?**
Keep the nest in a private repository, and turn on git-crypt if the content must stay unreadable to the git host. Agents read and write plaintext while commits store ciphertext. Encryption protects against the host and anyone holding a clone, not against whoever runs the agent.

**Does it work with tools other than Claude Code?**
Yes. Claude Code, Codex and Kimi Code sync on every write through hooks. Any tool that reads a markdown instruction file at startup can follow the same protocol and sync at the end of the session.

**Will my employer's code end up in the nest?**
No. Nothing from a work project is ingested unless you explicitly opt that project in, and ingested content goes through desensitization and your review before it is written.

## Non-goals

- **No server or sync service.** All sync is git push and pull.
- **No access-control layer.** Visibility comes from your git host's permissions.
- **No real-time collaboration.** Git is asynchronous by design.
- **No GUI.** Everything happens through your agents or the git CLI.

## Status

This project is the new home of **Nestwork**. The protocol, installers and documentation are being migrated here. Until that lands, this repository holds only this README.

## License

To be decided.
