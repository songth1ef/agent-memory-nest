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

## How it works

```
   Claude Code     Codex     Gemini CLI     Kimi Code     ...
        │            │            │             │
        └────────────┴─────┬──────┴─────────────┘
                           │  pull at session start
                           │  commit + push on every write
                           ▼
                 ┌───────────────────┐
                 │  your private nest │   rules · memory · context
                 │   (a git repo)     │
                 └───────────────────┘
```

## Status

This project is the new home of **Nestwork**. The protocol, installers and documentation are being migrated here. Until that lands, this repository holds only this README.

## License

To be decided.
