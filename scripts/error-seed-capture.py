#!/usr/bin/env python3
"""
fireworks-skill-memory: Error Seed Capture
==========================================
Hook type : PostToolUse (all tools)
Trigger   : After every tool call
Action    : Detects error signals in tool results and writes them to a
            session-scoped temp file (~/.claude/error-seeds/<session_id>.txt).
            The Stop hook (update-skills-knowledge.py) reads this file for
            high-quality distillation signals.

Why a separate script?
  The original error-seed capture in inject-skill-knowledge.py only fires
  when a SKILL.md is read — missing errors from Bash, Edit, Read, etc.
  This script covers ALL tool calls, giving the Stop hook a complete picture.
"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

# ── Configuration ──────────────────────────────────────────────────────────────
SEEDS_DIR = Path(os.environ.get("SKILLS_SEEDS_DIR", Path.home() / ".claude" / "error-seeds"))
MAX_SEED_SIZE = 800  # chars per seed entry

ERROR_SIGNALS = re.compile(
    r'error|failed|failure|exception|traceback|errno|'
    r'invalid|not found|permission denied|timeout|refused|'
    r'错误|失败|异常|无效|报错',
    re.IGNORECASE
)

# Tools whose errors are worth capturing (skip noisy ones)
SKIP_TOOLS = {"TodoRead", "TodoWrite", "TaskList", "TaskGet", "TaskCreate", "TaskUpdate"}

# ── Read hook input ────────────────────────────────────────────────────────────
try:
    hook_input = json.loads(sys.stdin.read())
except Exception:
    sys.exit(0)

session_id = hook_input.get("session_id", "")
tool_name = hook_input.get("tool_name", "")

if not session_id or not tool_name:
    sys.exit(0)

if tool_name in SKIP_TOOLS:
    sys.exit(0)

# ── Extract tool result text ───────────────────────────────────────────────────
tool_result = hook_input.get("tool_result", {})
result_content = ""

if isinstance(tool_result, str):
    result_content = tool_result
elif isinstance(tool_result, dict):
    content_field = tool_result.get("content", "")
    if isinstance(content_field, list):
        for block in content_field:
            if isinstance(block, dict):
                result_content += block.get("text", "")
    elif isinstance(content_field, str):
        result_content = content_field

if not result_content.strip():
    sys.exit(0)

# ── Check for error signal ─────────────────────────────────────────────────────
if not ERROR_SIGNALS.search(result_content):
    sys.exit(0)

# ── Write seed to session-scoped file ─────────────────────────────────────────
try:
    SEEDS_DIR.mkdir(parents=True, exist_ok=True)
    seed_file = SEEDS_DIR / f"{session_id}.txt"
    with seed_file.open("a", encoding="utf-8") as f:
        ts = datetime.now().isoformat(timespec="seconds")
        f.write(f"\n--- [{ts}] tool={tool_name} ---\n")
        f.write(result_content[:MAX_SEED_SIZE])
        f.write("\n")
except Exception:
    pass
