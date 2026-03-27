#!/usr/bin/env python3
"""
fireworks-skill-memory: Knowledge Base Updater
===============================================
Hook type : Stop (async: true — never blocks the session)
Trigger   : Every time a Claude Code session ends
Action    : Reads the session transcript, detects which skills were used,
            calls a lightweight model (haiku) to distil new learnings,
            and writes them back into the appropriate KNOWLEDGE.md.

Architecture
------------
  ~/.claude/skills-knowledge.md          ← global cross-skill principles  (≤ 20 entries)
  ~/.claude/skills/{name}/KNOWLEDGE.md   ← per-skill API/tool experience  (≤ 30 entries)
  ~/.claude/skills/{name}/.error_seeds   ← error+fix seeds captured mid-session

Optimizations
-------------
  v2:
  [1] Context-compression detection: skips distillation when the transcript
      looks like a summary-only session (no tool calls in last N lines),
      preventing low-quality lessons from summary text.
  [4] Frequency-weighted eviction: entries tagged [HIT:N] accumulate usage
      counts; on overflow, entries with lowest (hits × recency) are evicted
      instead of simple FIFO.

  v3:
  [5] Error-signal heuristic pre-filter: distillation (haiku) calls are only
      made when the transcript contains error/fix signal patterns, avoiding
      wasted inference on routine sessions. SKILL_KEYWORDS removed.
  [6] Multi-path skill detection: skills are detected from /.claude/skills/,
      /.skills/, and /.agents/skills/ paths (not just /.claude/skills/).
  [7] Timestamp [YYYY-MM] prefix + age-based decay: new entries are tagged
      with their creation month. Entries older than 3 months receive an
      eviction penalty, combining with HIT counts for smarter eviction.

Installation
------------
Add to ~/.claude/settings.json under hooks.Stop:

  {
    "hooks": [{
      "type": "command",
      "command": "python3 /path/to/update-skills-knowledge.py",
      "async": true
    }]
  }

Configuration (env vars, optional)
-----------------------------------
SKILLS_KNOWLEDGE_DIR     Path to skills directory
                         Default: ~/.claude/skills
SKILLS_KNOWLEDGE_GLOBAL  Path to the global knowledge file
                         Default: ~/.claude/skills-knowledge.md
SKILLS_KNOWLEDGE_MODEL   Claude model used for distillation
                         Default: claude-haiku-4-5
GLOBAL_MAX               Max entries in the global file   (default: 20)
SKILL_MAX                Max entries per skill file        (default: 30)
TRANSCRIPT_LINES         How many recent transcript lines to scan (default: 300)
MIN_TOOL_CALLS           Min tool calls required to proceed (default: 5)
                         Sessions below this threshold are likely summary-only
                         and will be skipped to avoid low-quality distillation.
"""

import json
import os
import re
import sys
import subprocess
from datetime import datetime
from pathlib import Path

# ── Configuration ──────────────────────────────────────────────────────────────
SKILLS_DIR = Path(
    os.environ.get("SKILLS_KNOWLEDGE_DIR", Path.home() / ".claude" / "skills")
)
GLOBAL_KNOWLEDGE = Path(
    os.environ.get(
        "SKILLS_KNOWLEDGE_GLOBAL",
        Path.home() / ".claude" / "skills-knowledge.md",
    )
)
DISTILL_MODEL = os.environ.get("SKILLS_KNOWLEDGE_MODEL", "claude-haiku-4-5")
GLOBAL_MAX = int(os.environ.get("GLOBAL_MAX", "20"))
SKILL_MAX = int(os.environ.get("SKILL_MAX", "30"))
TRANSCRIPT_LINES = int(os.environ.get("TRANSCRIPT_LINES", "300"))
# [Opt-1] Minimum real tool calls to consider this a non-summary session
MIN_TOOL_CALLS = int(os.environ.get("MIN_TOOL_CALLS", "5"))

# [Opt-5] Error/fix signal detection — used as a heuristic pre-filter for distillation.
# Only sessions containing these signals are worth distilling (avoids wasting haiku calls
# on routine sessions with no debugging/error content).
ERROR_SIGNAL_PATTERNS = re.compile(
    r'error|failed|failure|exception|traceback|bug|fix|workaround|'
    r'retry|timeout|denied|refused|rejected|deprecated|breaking|'
    r'调试|报错|失败|修复|踩坑|回退',
    re.IGNORECASE
)

# [Opt-6] Multi-path skill detection — support skills installed under various paths
SKILL_PATH_PATTERNS = [
    r'/.claude/skills/([^/]+)/',
    r'/.skills/([^/]+)/',
    r'/.agents/skills/([^/]+)/',
]

# ── Read hook input ────────────────────────────────────────────────────────────
try:
    hook_input = json.loads(sys.stdin.read())
except Exception:
    hook_input = {}

session_id = hook_input.get("session_id", "")
if not session_id:
    sys.exit(0)

# ── Locate session transcript ──────────────────────────────────────────────────
projects_dir = Path.home() / ".claude" / "projects"
transcript_file: Path | None = None
for proj_dir in projects_dir.iterdir():
    candidate = proj_dir / f"{session_id}.jsonl"
    if candidate.exists():
        transcript_file = candidate
        break

if not transcript_file:
    sys.exit(0)

# ── Parse transcript (last N lines) ───────────────────────────────────────────
try:
    lines = transcript_file.read_text(encoding="utf-8", errors="ignore").splitlines()[
        -TRANSCRIPT_LINES:
    ]
except Exception:
    sys.exit(0)

tool_uses: list[str] = []
assistant_texts: list[str] = []
tool_result_texts: list[str] = []  # [Opt-5] collect tool_result blocks for error signal detection
skill_invocations: set[str] = set()
real_tool_call_count: int = 0  # [Opt-1] count actual tool calls (not summary lines)

for raw in lines:
    try:
        entry = json.loads(raw)
        msg = entry.get("message", {})
        role = msg.get("role", "")
        content = msg.get("content", [])
        if not isinstance(content, list):
            continue
        for block in content:
            if not isinstance(block, dict):
                continue
            btype = block.get("type", "")
            if role == "assistant" and btype == "tool_use":
                name = block.get("name", "")
                inp = block.get("input", {})
                tool_uses.append(name)
                real_tool_call_count += 1  # [Opt-1] count every real tool_use block
                if name == "Skill":
                    sn = inp.get("skill", "")
                    if sn:
                        skill_invocations.add(sn)
                elif name == "Read":
                    fp = inp.get("file_path", "")
                    for pattern in SKILL_PATH_PATTERNS:
                        m = re.search(pattern.replace('([^/]+)/', r'([^/]+)/SKILL\.md'), fp)
                        if m:
                            skill_invocations.add(m.group(1))
                            break
            elif role == "assistant" and btype == "text":
                txt = block.get("text", "")
                if len(txt) > 80:
                    assistant_texts.append(txt[:400])
            # [Opt-5] Collect tool_result text for error signal detection
            elif btype == "tool_result" or (role == "tool" and btype == "text"):
                txt = block.get("text", "")
                if txt:
                    tool_result_texts.append(txt[:400])
    except Exception:
        continue

# [Opt-1] Context-compression detection:
# A session restored from a summary has very few real tool calls in the transcript.
# Distilling from summary text produces low-quality, generic lessons — skip it.
if real_tool_call_count < MIN_TOOL_CALLS:
    sys.exit(0)

# [Opt-5] Error-signal heuristic: only sessions with error/fix signals are worth distilling.
# Routine sessions without debugging content produce low-quality lessons.
all_text = " ".join(tool_uses + assistant_texts + tool_result_texts)
has_error_signal = bool(ERROR_SIGNAL_PATTERNS.search(all_text))

# Collect error snippets for higher-quality distillation prompts
error_snippets = ""
if has_error_signal:
    snippets = [t for t in tool_result_texts if ERROR_SIGNAL_PATTERNS.search(t)]
    error_snippets = "\n".join(snippets[:5])[:1500]

# Skip sessions with no skill invocations AND no error signals
if not skill_invocations and not has_error_signal:
    sys.exit(0)

# ── Helper functions ───────────────────────────────────────────────────────────

def read_entries(path: Path) -> list[str]:
    """Return bullet entries (lines starting with '- ') from a knowledge file."""
    if not path.exists():
        return []
    return [
        ln.strip()
        for ln in path.read_text(encoding="utf-8").splitlines()
        if ln.strip().startswith("- ")
    ]


def _get_hit_count(entry: str) -> int:
    """[Opt-4] Extract [HIT:N] counter from an entry, defaulting to 0."""
    m = re.search(r"\[HIT:(\d+)\]", entry)
    return int(m.group(1)) if m else 0


def _set_hit_count(entry: str, count: int) -> str:
    """[Opt-4] Set or update [HIT:N] counter in an entry."""
    tag = f"[HIT:{count}]"
    if re.search(r"\[HIT:\d+\]", entry):
        return re.sub(r"\[HIT:\d+\]", tag, entry)
    return entry + f"  {tag}"


def _get_entry_age_months(entry: str) -> float:
    """[Opt-7] Extract [YYYY-MM] timestamp from an entry and return age in months.
    Returns 999 if no timestamp is found (treated as very old)."""
    m = re.search(r"\[(\d{4})-(\d{2})\]", entry)
    if not m:
        return 999.0  # No timestamp = assume very old
    try:
        entry_year, entry_month = int(m.group(1)), int(m.group(2))
        now = datetime.now()
        age_months = (now.year - entry_year) * 12 + (now.month - entry_month)
        return max(0.0, float(age_months))
    except (ValueError, OverflowError):
        return 999.0


def _evict_entries(entries: list[str], max_count: int) -> list[str]:
    """[Opt-4+7] Frequency-weighted eviction with age-based decay.
    Combines HIT counts with age: entries older than 3 months get a penalty,
    making them more likely to be evicted. Score = hits - age_penalty.
    Entries with lowest combined score are evicted first."""
    if len(entries) <= max_count:
        return entries
    overflow = len(entries) - max_count

    def _eviction_score(entry: str, index: int) -> tuple[float, int]:
        hits = _get_hit_count(entry)
        age = _get_entry_age_months(entry)
        # Age penalty: 0 for entries <= 3 months, increases linearly after
        age_penalty = max(0.0, (age - 3.0) * 0.5)
        score = hits - age_penalty
        return (score, index)  # ties broken by position (older = lower index)

    indexed = sorted(
        enumerate(entries),
        key=lambda x: _eviction_score(x[1], x[0]),
    )
    evict_indices = {idx for idx, _ in indexed[:overflow]}
    return [e for i, e in enumerate(entries) if i not in evict_indices]


def write_knowledge(
    path: Path,
    entries: list[str],
    max_count: int,
    title: str,
    subtitle: str,
) -> None:
    """Write (or overwrite) a knowledge file, applying frequency-weighted eviction."""
    entries = _evict_entries(entries, max_count)
    now = datetime.now().strftime("%Y-%m-%d")
    body = "\n".join(entries)
    content = (
        f"{title}\n\n"
        f"> {subtitle}\n"
        f"> Max {max_count} entries; low-frequency entries are evicted first."
        f" Last updated: {now}\n\n"
        f"## Entries\n\n"
        f"{body}\n"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def merge_entries(existing: list[str], new_insights: str) -> list[str]:
    """Append new bullet entries while deduplicating against existing ones.
    [Opt-4] Also increments [HIT:N] counters on matched existing entries.
    [Opt-7] Adds [YYYY-MM] timestamp prefix to new entries for age tracking."""
    month_tag = datetime.now().strftime("[%Y-%m]")
    for line in new_insights.splitlines():
        line = line.strip()
        if not line.startswith("- "):
            continue
        key = line[2:37].lower()
        matched = False
        for i, e in enumerate(existing):
            if key[:20] in e.lower():
                # Entry already exists — bump its hit count
                existing[i] = _set_hit_count(e, _get_hit_count(e) + 1)
                matched = True
                break
        if not matched:
            # [Opt-7] Add [YYYY-MM] prefix if not already present
            entry_body = line[2:]  # strip leading "- "
            if not re.match(r"\[\d{4}-\d{2}\]", entry_body):
                line = f"- {month_tag} {entry_body}"
            existing.append(line)
    return existing


def ask_model(prompt: str) -> str:
    """Call the distillation model via the Claude CLI."""
    try:
        result = subprocess.run(
            ["claude", "-p", prompt, "--model", DISTILL_MODEL],
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.stdout.strip()
    except Exception:
        return "SKIP"


# ── Update per-skill KNOWLEDGE.md files ───────────────────────────────────────
for skill_name in skill_invocations:
    skill_dir = SKILLS_DIR / skill_name
    if not skill_dir.exists():
        continue

    knowledge_file = skill_dir / "KNOWLEDGE.md"
    existing = read_entries(knowledge_file)
    context = "\n".join(assistant_texts[:6])
    tools = ", ".join(set(tool_uses[:15]))

    # [Opt-2] Load error seeds captured mid-session by the inject hook
    seed_file = skill_dir / ".error_seeds"
    error_seed_text = ""
    if seed_file.exists():
        try:
            error_seed_text = seed_file.read_text(encoding="utf-8").strip()[-1200:]
            seed_file.unlink()  # Consume seeds — don't re-use next session
        except Exception:
            pass

    seed_section = (
        f"\n\nError/fix seeds captured mid-session (high-quality signals):\n{error_seed_text}"
        if error_seed_text else ""
    )

    # [Opt-5] Include error snippets from tool_result blocks for richer distillation
    snippet_section = (
        f"\n\nError snippets from tool results:\n{error_snippets}"
        if error_snippets else ""
    )

    # [Opt-5] Skip haiku call if no error signal AND no error seeds —
    # the error_seeds mechanism works independently from transcript-level signals
    if not has_error_signal and not error_seed_text:
        continue

    prompt = (
        f'You are an experience-distillation assistant. Below is a snippet of a Claude '
        f'Code session that used the "{skill_name}" skill.\n\n'
        f"Tools called: {tools}\n\n"
        f"Assistant output (excerpt):\n{context[:1500]}"
        f"{seed_section}"
        f"{snippet_section}\n\n"
        f"Already recorded (avoid duplicates):\n"
        f"{chr(10).join(existing[-10:]) if existing else '(none)'}\n\n"
        f"Extract 1-3 concrete, actionable lessons specifically about the \"{skill_name}\" "
        f"skill from this session. Requirements:\n"
        f"- Must be a real new finding: a bug, gotcha, workaround, or API detail\n"
        f"- Prefer lessons from the error/fix seeds section — they are ground truth\n"
        f"- Start each entry with '- [YYYY-MM] [Tag]' where YYYY-MM is the current month "
        f"and Tag names the specific API/feature\n"
        f"- If nothing new was found, output only: SKIP\n"
        f"Output only the bullet list or SKIP."
    )

    insights = ask_model(prompt)
    if insights and insights != "SKIP" and insights.startswith("-"):
        existing = merge_entries(existing, insights)
        write_knowledge(
            knowledge_file,
            existing,
            SKILL_MAX,
            f"# {skill_name} — experience",
            f"Hands-on API/tool experience accumulated while using the {skill_name} skill.",
        )

# ── Update global cross-skill knowledge file ──────────────────────────────────
# [Opt-5] Only distill global knowledge when error signals are present AND skills were used
if has_error_signal and len(skill_invocations) > 0:
    global_existing = read_entries(GLOBAL_KNOWLEDGE)
    context = "\n".join(assistant_texts[:4])

    global_prompt = (
        "You are an experience-distillation assistant reviewing a Claude Code session.\n\n"
        f"Tools called: {', '.join(set(tool_uses[:10]))}\n\n"
        f"Assistant output (excerpt):\n{context[:800]}\n\n"
        f"Current global principles (avoid duplicates):\n"
        f"{chr(10).join(global_existing)}\n\n"
        "Decide if this session produced any insight worth adding to the **global "
        "cross-skill principles** file. Criteria: applicable across multiple skills "
        "(e.g. error-handling strategy, debugging method, upload pattern) — NOT "
        "a single-API detail.\n\n"
        "If yes, output 1-2 entries starting with '- [Tag]'; otherwise output only: SKIP."
    )

    global_insights = ask_model(global_prompt)
    if global_insights and global_insights != "SKIP" and global_insights.startswith("-"):
        global_existing = merge_entries(global_existing, global_insights)
        if len(global_existing) > GLOBAL_MAX:
            global_existing = global_existing[-GLOBAL_MAX:]
        now = datetime.now().strftime("%Y-%m-%d")
        header = (
            "# Global Skills Principles\n\n"
            "> **Scope**: Cross-skill principles and quality guidelines.\n"
            "> For skill-specific API details, see each skill's `KNOWLEDGE.md`.\n"
            f"> Auto-maintained. Max {GLOBAL_MAX} entries. Last updated: {now}\n\n"
            "## Principles\n\n"
        )
        GLOBAL_KNOWLEDGE.write_text(
            header + "\n".join(global_existing) + "\n",
            encoding="utf-8",
        )
