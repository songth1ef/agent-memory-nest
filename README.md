# agent-memory-nest

**English** | [中文](README.zh.md)

> **Your agents share one mind.**
> One git repository holds the rules, memory and context for every AI agent you run, on every machine and from every vendor.

## Why

Every coding agent now has some memory, but each one keeps it to itself:

- **Bound to one machine.** Claude Code, Codex, Gemini CLI, Kimi Code, Antigravity, Hermes and OpenClaw all store memory locally. A new laptop starts from zero.
- **Bound to one vendor.** What Claude learned stays with Claude. Switch to Codex and you explain everything again.
- **Bound to one account.** When a subscription ends, an account is banned or a tool shuts down, the memory goes with it.

agent-memory-nest moves that memory into a git repository you own. Every agent reads from the same nest and writes back to it, so they all work from one shared mind. A hive mind, not a set of strangers.

## Why memory is worth keeping

**Writing memory for your agents is the highest-compounding habit in AI-assisted work.** Every correction, every convention and every pitfall you record is one you never have to explain again. The more your agents remember, the better they know your habits and your projects, the smoother they are to work with, and the less time you spend correcting the same mistakes. And what you build up belongs to you: it does not disappear with a tool, an account or a job.

**Who it's for:** everyone who gets work done with AI agents. All you need is git and a command-line agent such as Claude Code or Codex.

## What makes it different

- **Easy to start, no server.** All you need is a private git repository: nothing to deploy, no daemon, no port to open. After setup you use your agents exactly as before, with nothing new to learn. Git is the only transport, so machines behind NAT or offline still sync when they reconnect.
- **More than memory.** The nest also carries rules and direction, with a fixed priority order for resolving conflicts, so a fleet of agents follows the same guidance instead of only sharing notes.
- **Clear write boundaries.** Each agent writes only to its own folder. Shared memory changes only through a reviewed distillation step.
- **Load what the task needs.** A small resident layer loads at session start, and everything else is read on demand, so context stays small as memory grows.
- **Private by design.** The nest is meant to live in a private repository, and can be encrypted end to end with git-crypt.

## How you use it

Once it is set up, you keep working the way you already do:

- **Agents remember as they work.** When a decision is made, a lesson is learned or a project moves on, the agent writes it down, on its own or when you say "remember this".
- **Sync takes care of itself.** Pulling, committing and pushing all happen through hooks. You never touch git for memory.
- **Any machine, any tool, same context.** Open a new session on your laptop, a cloud server, or in a different agent, and it picks up from the same nest.

A typical week:

- **At the office**, an agent records the project's progress and the working rules you agreed on.
- **At home**, a new session continues from that context instead of rebuilding it.
- **On a cloud server**, another agent picks up the same project state and decisions.

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

**Near-zero maintenance.** Agents write memory as they work, and hooks handle all syncing. The one manual step is **distillation**: merging what individual agents learned into shared memory, with a review before anything is written. Running it **once a month** is enough.

## Loads only what the task needs

Memory keeps growing, but a session should not have to read all of it. Measured on the author's own nest (November 2026; tokens estimated):

| What a session loads | Files | Size | Tokens |
|---|---|---|---|
| Everything, the old way: rules, strategy, all shared and agent memory | 37 | 254 KB | ~79,000 |
| **Resident layer only, the default start** | 4 | 5 KB | **~1,600** |
| Resident layer plus the topic a task needs | 6 | 18 KB | ~5,400 |
| Every memory file in the nest | 283 | 1.6 MB | ~480,000 |

A default session start reads about **1/50** of what full loading would, and the whole nest would no longer fit in most context windows. That is why history is searched when a task needs it rather than loaded up front.

## More than shared notes

- **Bring your existing memory along.** Memory that Claude Code, Codex or Kimi Code already keep on one machine can be distilled into the nest, so a new machine, a banned account or a discontinued tool no longer means starting over.
- **Agents can message each other.** A git-based mailbox lets one agent leave a task or a note for another, on the same machine or a different one, with no extra service.
- **Upgrades never touch your data.** Your nest is a private copy of a public template. Protocol updates replace only protocol files and never touch your rules, memory or projects.
- **A versioned protocol.** The protocol carries a `MAJOR.MINOR` version. Minor versions are backward compatible, and only a major version asks you to migrate.

## Real-world scenarios

**Several machines, one project.** You start a feature on your desktop, continue on your laptop in the evening, and let an agent on a cloud server run the long test suite overnight. Each one reads the same project state and the same decisions, and each writes back what it did.

**Switching tools.** You move from Claude Code to Codex for a task. Codex starts with your rules, your preferences and the project's history already loaded, because they live in the nest, not in Claude.

**Losing an account or a tool.** A subscription lapses, an account is banned, or a tool shuts down. Your memory was never stored only there, so the next agent you install carries on from where the last one stopped.

## Battle-tested

The author has run this setup every day since April 2026: **10 machines** (Windows, macOS, Linux servers and an Android phone), **10 different agent tools** and **more than 30 agent instances**, all sharing one nest. The protocol's rules come from problems hit in that daily use, not from a design document.

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
