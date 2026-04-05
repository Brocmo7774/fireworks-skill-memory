#!/usr/bin/env python3
"""
fireworks-skill-memory: Pre-Skill Knowledge Injector
=====================================================
Hook type : PreToolUse on Skill
Trigger   : Before any Skill tool call
Action    : Injects the corresponding KNOWLEDGE.md into model context
            BEFORE the skill executes — so Claude sees past experience
            during planning, not after the skill has already started.

Why this matters:
  The PostToolUse/Read hook fires when SKILL.md is read, which happens
  *after* the Skill tool is invoked. By then Claude is already executing.
  This PreToolUse hook fires *before* execution, giving Claude a chance
  to apply lessons learned before making mistakes.
"""

import json
import os
import re
import sys
from pathlib import Path

# ── Configuration ──────────────────────────────────────────────────────────────
SKILLS_DIR = Path(
    os.environ.get("SKILLS_KNOWLEDGE_DIR", Path.home() / ".claude" / "skills")
)

SKILL_PATH_PATTERNS = [
    r'/.claude/skills/([^/]+)',
    r'/.skills/([^/]+)',
    r'/.agents/skills/([^/]+)',
]

# ── Read hook input ────────────────────────────────────────────────────────────
try:
    hook_input = json.loads(sys.stdin.read())
except Exception:
    sys.exit(0)

if hook_input.get("tool_name") != "Skill":
    sys.exit(0)

# ── Extract skill name ─────────────────────────────────────────────────────────
skill_name = hook_input.get("tool_input", {}).get("skill", "")
if not skill_name:
    sys.exit(0)

# Strip namespace prefix (e.g. "document-skills:pdf" → "pdf", "baoyu-translate" → "baoyu-translate")
# Try exact match first, then strip namespace
def find_skill_dir(name: str) -> Path | None:
    # Direct match
    candidate = SKILLS_DIR / name
    if candidate.exists():
        return candidate
    # Strip namespace (e.g. "ns:skill" → "skill")
    if ":" in name:
        short = name.split(":")[-1]
        candidate = SKILLS_DIR / short
        if candidate.exists():
            return candidate
    return None

skill_dir = find_skill_dir(skill_name)
if not skill_dir:
    sys.exit(0)

# ── Load KNOWLEDGE.md ──────────────────────────────────────────────────────────
knowledge_file = skill_dir / "KNOWLEDGE.md"
if not knowledge_file.exists():
    sys.exit(0)

knowledge_content = knowledge_file.read_text(encoding="utf-8").strip()
if not knowledge_content:
    sys.exit(0)

# ── Inject into model context ──────────────────────────────────────────────────
output = {
    "hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "additionalContext": (
            f"\n---\n"
            f"📚 **[fireworks-skill-memory] {skill_name} — past experience** (pre-execution inject)\n\n"
            f"{knowledge_content}\n"
            f"---\n"
        ),
    }
}

print(json.dumps(output, ensure_ascii=False))
