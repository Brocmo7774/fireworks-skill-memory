# skill-knowledge-extractor — experience

> Hands-on experience accumulated while using the skill-knowledge-extractor skill.
> Max 30 entries; oldest are dropped when the limit is reached. Last updated: 2026-03-27

## Entries

- [No script required for single sessions] For one-off knowledge extraction from a conversation or oral description, Claude extracts patterns directly without needing `scripts/extract_patterns.py`. Use the script only for batch processing many files.
- [Best input formats] Oral description → simplest; paste chat logs or documents → richer patterns. The skill handles all three. If you have a document, paste it directly rather than describing it.
- [Guided questioning] If you're unsure how to describe your workflow, just say what you do — the skill asks targeted follow-up questions ("What do you do first?", "How do you handle X?") to draw out implicit knowledge.
- [Output structure] Extracted knowledge is formatted as a reusable Skill draft (SKILL.md-compatible): trigger description, step-by-step workflow, decision rules, and checklist items. Review and trim before using as a real skill.
- [Pattern types] The skill recognizes 4 pattern types: sales/communication scripts, checklists (for review/QA), decision trees (for diagnosis/triage), and SOP steps. Identifying your pattern type upfront speeds extraction.
- [Iteration expected] First-draft extraction usually captures 70-80% correctly. Always confirm accuracy with the skill and request one refinement pass before finalizing.
