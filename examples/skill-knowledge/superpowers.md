# superpowers — experience

> Hands-on experience accumulated while using the superpowers skill.
> Max 30 entries; oldest are dropped when the limit is reached. Last updated: 2026-03-27

## Entries

- [Skill invocation is mandatory] The core rule of superpowers: if there's even a 1% chance a skill applies, invoke it before responding. Superpowers installs this as a hard constraint — do not rationalize skipping it.
- [User instructions override skills] CLAUDE.md and explicit user instructions always take priority over any superpowers skill. If they conflict, follow the user.
- [Sub-skills are separate SKILL.md files] Superpowers ships a collection of individual skills (TDD, systematic-debugging, git-worktrees, parallel-agents, etc.). Each is invoked independently via the Skill tool — not all are active at once.
- [Subagent exception] When dispatched as a subagent to perform a specific task, skip the using-superpowers skill entirely (it contains a SUBAGENT-STOP guard).
- [Platform adaptation] Superpowers skill files use Claude Code tool names. On other platforms (Gemini CLI, Codex) use the tool-name mapping in `references/codex-tools.md` before applying skill instructions.
- [TodoWrite integration] Superpowers skills with checklists expect a TodoWrite todo item per checklist item. Create all todos before starting work to track progress visibly.
