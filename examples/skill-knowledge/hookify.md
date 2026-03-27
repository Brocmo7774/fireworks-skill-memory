# hookify — experience

> Hands-on experience accumulated while using the hookify skill.
> Max 30 entries; oldest are dropped when the limit is reached. Last updated: 2026-03-27

## Entries

- [Rule file location] Hookify rules live in `.claude/hookify.{rule-name}.local.md` (project-level) or `~/.claude/hookify.{rule-name}.local.md` (global). The `.local.md` suffix keeps them out of git by default.
- [Rule file format] YAML frontmatter with `name`, `enabled`, `event`, and `pattern` fields; rule body is the message shown to Claude when the pattern triggers. Event values: `bash`, `file`, `stop`, `prompt`, `all`.
- [Regex pattern field] The `pattern` field is a regex matched against the relevant input (bash command, file path, stop reason, or prompt text). Test your regex with `echo "sample" | grep -P "your-pattern"` before adding.
- [enabled toggle] Set `enabled: false` to pause a rule without deleting it. Useful for debugging whether a rule is causing unexpected behavior.
- [Naming convention] Rule names should be kebab-case action verbs: `warn-dangerous-rm`, `block-console-log`, `require-tests`. This makes the hookify rule list scannable.
- [Scope] hookify rules are local; they do not affect other users of the same repo unless they also install hookify. Document team-wide rules in CLAUDE.md instead.
