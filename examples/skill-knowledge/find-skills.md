# find-skills — experience

> Hands-on experience accumulated while using the find-skills skill.
> Max 30 entries; oldest are dropped when the limit is reached. Last updated: 2026-03-27

## Entries

- [CLI command] Use `npx skills find <query>` to search interactively; `npx skills add <github-url>` to install directly from GitHub. Both require Node.js / npx in PATH.
- [Install path] Skills installed via `npx skills add` land in `~/.agents/skills/`, which is separate from `~/.claude/skills/`. If Claude Code does not pick up the new skill, add the path to `permissions.additionalDirectories` in `~/.claude/settings.json`.
- [Security ratings] find-skills shows a risk level (Safe / Low / Medium) for each result. Medium Risk means the skill has full agent permissions — review what it does before running it in a production environment.
- [Niche skills] Skills with < 100 installs may have undocumented dependencies or stability issues. Check the README before running for the first time.
- [Network errors] find-skills calls the skills marketplace API; transient `UND_ERR_SOCKET` errors are usually network-related — retry once before debugging further.
- [Duplicate check] Before installing, confirm the skill isn't already in `~/.claude/skills/` or `~/.agents/skills/` to avoid version conflicts.
