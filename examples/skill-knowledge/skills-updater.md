# skills-updater — experience

> Hands-on experience accumulated while using the skills-updater skill.
> Max 30 entries; oldest are dropped when the limit is reached. Last updated: 2026-03-27

## Entries

- [Two sources] skills-updater handles two separate sources: Claude plugins (`~/.claude/plugins/`) and npx skills (`~/.skills/`). Always check both when auditing your skill collection.
- [Version tracking] Plugin skills track versions in `~/.claude/plugins/installed_plugins.json`; npx skills use `~/.skills/` directory. Neither source is aware of the other automatically.
- [Locale detection] The skill auto-detects locale from `LANG`/`LC_ALL`/`LANGUAGE` env vars. Force a language with `--lang zh` or `--lang en` if the output language doesn't match your preference.
- [Batch update risk] Batch updating all skills at once may overwrite local edits. Review diffs before confirming batch mode; prefer updating one skill at a time when you have local customizations.
- [Network dependency] Update checks call out to skillsmp.com and skills.sh marketplaces — requires live internet. On restricted networks or VPN environments, updates will fail silently or time out.
- [Check before update] Run the check command before applying updates: `python scripts/check_updates.py`. This surfaces available updates without modifying anything.
