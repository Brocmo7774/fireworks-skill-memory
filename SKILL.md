---
name: fireworks-skill-memory
description: Persistent cross-session experience memory for Claude Code skills. TRIGGER when user asks about skill memory, experience distillation, cross-session learning, skill knowledge injection, Claude memory, session-to-session improvement, or wants to install/configure fireworks-skill-memory.
---

# fireworks-skill-memory

Persistent experience memory for Claude Code skills. Claude remembers what it learned — session after session, skill by skill.

## What It Does

Every Claude Code session starts from zero. The same mistakes repeat — wrong API parameters, broken sequences, proxy pitfalls — because Claude has no memory between sessions.

`fireworks-skill-memory` solves this by automatically:

1. **Injecting past experience** when a skill is invoked (so Claude avoids repeating mistakes)
2. **Distilling new lessons** at session end (using Claude Haiku, async, zero workflow impact)
3. **Growing smarter over time** with HIT-counted entries and age-based eviction

## Installation

### Quick Install (Recommended)

In Claude Code, say:

> "Help me install fireworks-skill-memory from https://github.com/yizhiyanhua-ai/fireworks-skill-memory"

Or run the one-command installer:

```bash
curl -fsSL https://raw.githubusercontent.com/yizhiyanhua-ai/fireworks-skill-memory/main/install.sh | bash
```

### npx skills Install

```bash
npx skills add yizhiyanhua-ai/fireworks-skill-memory -g
```

After installing via npx skills, run the installer to set up hooks:

```bash
curl -fsSL https://raw.githubusercontent.com/yizhiyanhua-ai/fireworks-skill-memory/main/install.sh | bash
```

## How It Works

The system installs 4 Claude Code hooks that run automatically:

| Hook | Trigger | Script | Purpose |
|------|---------|--------|---------|
| `PreToolUse` | Before Skill call | `pre-skill-inject.py` | Inject full KNOWLEDGE.md before skill executes |
| `PostToolUse` | After Read SKILL.md | `inject-skill-knowledge.py` | Inject top-N entries by relevance + capture error seeds |
| `PostToolUse` | After any tool call | `error-seed-capture.py` | Capture error signals to session-scoped file |
| `Stop` | Session end (async) | `update-skills-knowledge.py` | Distill new lessons via Haiku, update KNOWLEDGE.md |

### Data Flow

```
Skill invoked → PreToolUse injects experience → Claude executes with context
                                                    ↓
Session ends → Stop hook reads transcript → Haiku distills 1-3 lessons
                                                    ↓
                              KNOWLEDGE.md updated → Ready for next session
```

### Knowledge Storage

```
~/.claude/skills/<skill-name>/KNOWLEDGE.md  ← Per-skill experience (max 100 entries)
~/.claude/skills-knowledge.md               ← Global cross-skill principles (max 100 entries)
~/.claude/skill-usage-stats.json            ← Usage frequency stats
~/.claude/skill-memory.log                  ← Execution log
```

Each entry is tagged with `[YYYY-MM]` timestamp and `[HIT:N]` usage counter. Low-frequency, old entries are evicted first.

## Configuration (Optional)

All settings are optional, configured via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `SKILLS_KNOWLEDGE_MODEL` | `claude-haiku-4-5` | Model for distillation |
| `SKILL_MAX` | `100` | Max entries per skill |
| `GLOBAL_MAX` | `100` | Max global entries |
| `MIN_TOOL_CALLS` | `5` | Skip sessions with fewer calls (likely summaries) |
| `SKILLS_INJECT_TOP` | `20` | Max entries injected per active invocation |

## Requirements

- Python 3.9+
- Claude Code CLI
- Claude Haiku access (for distillation; falls back through haiku-4-5 → haiku-3-5)

## More Information

- [Full Documentation](README.md)
- [中文文档](README.zh-CN.md)
- [Report Bug](https://github.com/yizhiyanhua-ai/fireworks-skill-memory/issues)
