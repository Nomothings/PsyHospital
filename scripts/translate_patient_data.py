#!/usr/bin/env python3
"""Translate data_patient/ + cases.jsonl Chinese → English using DeepSeek LLM.

Keeps ``cases.jsonl`` chiefComplaint items and ``skill.md`` event names in sync.

Usage::

    python scripts/translate_patient_data.py --case 814481              # dry-run
    python scripts/translate_patient_data.py --case 814481 --apply      # single
    python scripts/translate_patient_data.py --all --apply              # all 16
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List, Optional

from openai import OpenAI

# ---- Config ----
API_BASE = "https://api.deepseek.com/v1"
API_KEY = "sk-xxx"  # replace with your own key
MODEL = "deepseek-v4-flash"

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PATIENT_DIR = PROJECT_ROOT / "data" / "data_patient"
CASES_FILE = PROJECT_ROOT / "data" / "cases.jsonl"

client = OpenAI(base_url=API_BASE, api_key=API_KEY)


# ---------------------------------------------------------------------------
# LLM translator
# ---------------------------------------------------------------------------

_SYSTEM = (
    "You are a professional Chinese→English medical translator. "
    "Translate psychiatric patient data accurately. "
    "Keep medical terminology precise. Output ONLY the English translation, no explanation."
)


def _tr(text: str) -> str:
    """Translate Chinese text to English via LLM, with retry."""
    if not text or not text.strip():
        return text
    if not re.search(r"[一-鿿]", text):
        return text  # no Chinese characters, skip

    for attempt in range(3):
        try:
            resp = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": _SYSTEM},
                    {"role": "user", "content": text},
                ],
                max_tokens=1024,
                temperature=0.1,
            )
            result = resp.choices[0].message.content.strip()
            time.sleep(0.5)
            return result
        except Exception as exc:
            print(f"    [retry {attempt+1}/3] {exc}")
            time.sleep(3 * (attempt + 1))
    print(f"    [FAILED] keeping original: {text[:60]}...")
    return text


def _tr_batch(texts: List[str]) -> List[str]:
    """Translate a list of short texts in one API call (more efficient)."""
    if not texts:
        return []
    # Only translate Chinese texts
    to_translate = [(i, t) for i, t in enumerate(texts) if re.search(r"[一-鿿]", t)]
    if not to_translate:
        return texts

    result = list(texts)
    numbered = "\n".join(f"{idx+1}. {t}" for idx, (_, t) in enumerate(to_translate))
    prompt = (
        "Translate each numbered Chinese text below to English. "
        "Keep the same numbering. Output ONLY the numbered English translations:\n\n"
        f"{numbered}"
    )

    for attempt in range(3):
        try:
            resp = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": _SYSTEM},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=4096,
                temperature=0.1,
            )
            output = resp.choices[0].message.content.strip()
            time.sleep(1.0)

            # Parse numbered list
            lines = output.split("\n")
            translated: Dict[int, str] = {}
            for line in lines:
                m = re.match(r"(\d+)[.)]\s*(.+)", line.strip())
                if m:
                    idx = int(m.group(1)) - 1
                    if 0 <= idx < len(to_translate):
                        translated[idx] = m.group(2).strip()

            for batch_idx, (orig_idx, _) in enumerate(to_translate):
                if batch_idx in translated:
                    result[orig_idx] = translated[batch_idx]
                else:
                    # fallback: single translate
                    result[orig_idx] = _tr(texts[orig_idx])
            return result
        except Exception as exc:
            print(f"    [batch retry {attempt+1}/3] {exc}")
            time.sleep(3 * (attempt + 1))

    # All retries failed — translate individually
    return [_tr(t) for t in texts]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_fn(text: str) -> str:
    """Convert translated English text to a safe, LLM-friendly filename.

    The LLM naturally lowercases and uses underscores in SEARCH tags
    (e.g. ``[SEARCH_poor_sleep]``), so we match that convention.
    """
    for ch in "/:*?\"<>|'":
        text = text.replace(ch, "")
    text = re.sub(r"\s+", "_", text).strip().lower()
    text = re.sub(r"_+", "_", text).strip("_")
    if len(text) > 200:
        text = text[:197] + "..."
    return text


def parse_event_list(skill_text: str) -> List[str]:
    events: List[str] = []
    in_section = False
    for line in skill_text.split("\n"):
        s = line.strip()
        if "主诉列表" in s or "可查询事件" in s:
            in_section = True
            continue
        if in_section:
            if s.startswith("---") or s.startswith("# "):
                break
            if s.startswith("- "):
                ev = s[2:].strip()
                if ev:
                    events.append(ev)
    return events


def replace_event_list(skill_text: str, old: List[str], new: List[str]) -> str:
    for o, n in zip(old, new):
        skill_text = skill_text.replace(f"- {o}", f"- {n}")
    return skill_text


def translate_skill_md(skill_text: str, event_map: Dict[str, str]) -> str:
    """Translate skill.md while preserving the event list section.

    The event list is already English (replaced by ``replace_event_list``),
    so only the narrative + search trigger sections need LLM translation.
    """
    # Split into blocks by "---" or "# " headers
    # Structure: [frontmatter] [# 患者当前精神状态] [# 主诉列表...] [---] [# 检索触发]
    lines = skill_text.split("\n")
    result_blocks: List[str] = []
    current_block: List[str] = []
    in_event_section = False

    for line in lines:
        s = line.strip()
        # Detect section boundaries
        if "主诉列表" in s or "可查询事件" in s or "chief complaint" in s.lower() or "queryable event" in s.lower():
            # Flush previous block
            if current_block:
                result_blocks.append("\n".join(current_block))
                current_block = []
            in_event_section = True
            current_block.append(line)
            continue

        if in_event_section:
            current_block.append(line)
            # End of event section: next "---" or "# " header that's NOT an event list item
            if (s.startswith("---") and len(current_block) > 1) or \
               (s.startswith("#") and "主诉" not in s and "事件" not in s and "complaint" not in s.lower() and "event" not in s.lower()):
                result_blocks.append("\n".join(current_block))
                current_block = []
                in_event_section = False
            continue

        current_block.append(line)

    if current_block:
        result_blocks.append("\n".join(current_block))

    # Translate each non-event block
    translated_blocks = []
    for i, block in enumerate(result_blocks):
        # Skip event list blocks (they're already English)
        if any(kw in block for kw in ["主诉列表", "可查询事件", "chief complaint", "queryable event"]):
            translated_blocks.append(block)
        else:
            translated_blocks.append(_tr(block))

    return "\n".join(translated_blocks)


# ---------------------------------------------------------------------------
# cases.jsonl I/O
# ---------------------------------------------------------------------------

def load_cases() -> List[Dict[str, Any]]:
    cases: List[Dict[str, Any]] = []
    with open(CASES_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                cases.append(json.loads(line))
    return cases


def save_cases(cases: List[Dict[str, Any]], path: Optional[Path] = None) -> None:
    p = path or CASES_FILE
    with open(p, "w", encoding="utf-8") as f:
        for c in cases:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------------------
# Main processing
# ---------------------------------------------------------------------------

def process_case(case: Dict[str, Any], *, apply: bool = False) -> Dict[str, Any]:
    case_id = case["id"]
    skill_path = PATIENT_DIR / case_id / "skill.md"
    exp_dir = PATIENT_DIR / case_id / "experience"
    rf = case.get("realFormulation", {})
    chief_cn: List[str] = rf.get("chiefComplaint", [])

    print(f"\n{'='*60}")
    print(f"[{case_id}] {len(chief_cn)} events, skill={'OK' if skill_path.exists() else 'MISS'}")
    print(f"{'='*60}")

    # ---- Step 1: batch-translate chiefComplaint → English event names ----
    print("  [1/4] Translating chiefComplaint / event names...")
    chief_en = _tr_batch(chief_cn)
    event_map: Dict[str, str] = {}
    for cn, en in zip(chief_cn, chief_en):
        safe = _safe_fn(en)
        event_map[cn] = safe
        print(f"    {cn[:50]} → {safe}")

    # ---- Step 2: translate cases.jsonl fields ----
    print("  [2/4] Translating cases.jsonl fields...")
    new_case = deepcopy(case)
    rf_new = new_case.setdefault("realFormulation", {})

    rf_new["chiefComplaint"] = chief_en
    new_case["basicInfomation"] = _tr(case.get("basicInfomation", ""))

    for key in ("mentalStatus", "physicalExamination", "pastHistory", "familyHistory", "medicationHistory"):
        items = rf.get(key)
        if isinstance(items, list) and items:
            rf_new[key] = _tr_batch(items)

    aux = rf.get("auxiliaryExamination")
    if isinstance(aux, dict) and aux:
        keys_en = _tr_batch(list(aux.keys()))
        vals_en = _tr_batch(list(aux.values()))
        rf_new["auxiliaryExamination"] = dict(zip(keys_en, vals_en))

    # ---- Step 3: translate skill.md + experience files ----
    if skill_path.exists():
        print("  [3/4] Translating skill.md...")
        skill_text = skill_path.read_text(encoding="utf-8")
        skill_text = replace_event_list(skill_text, chief_cn, list(event_map.values()))
        skill_text = translate_skill_md(skill_text, event_map)
        if apply:
            skill_path.write_text(skill_text, encoding="utf-8")

    if exp_dir.exists():
        print(f"  [4/4] Translating {len(event_map)} experience files...")
        existing = {f.stem: f for f in exp_dir.glob("*.md")}

        # Batch process experience file content
        exp_items: List[tuple] = []  # (old_cn, new_safe, src_path)
        for old_cn, new_safe in event_map.items():
            src = existing.get(old_cn)
            if src is None:
                src = existing.get(old_cn.replace("**", "__"))
            if src is None:
                src = existing.get(old_cn.replace("__", "**"))
            if src is None:
                print(f"    [WARN] No file for: {old_cn[:40]}")
                continue
            exp_items.append((old_cn, new_safe, src))

        # Translate all content in batch
        if exp_items:
            contents = [item[2].read_text(encoding="utf-8") for item in exp_items]
            translated_contents = _tr_batch(contents)

            if apply:
                for (old_cn, new_safe, src), en_content in zip(exp_items, translated_contents):
                    dst = exp_dir / f"{new_safe}.md"
                    dst.write_text(en_content, encoding="utf-8")
                    if src != dst:
                        src.unlink()

                # Cleanup stale files
                safe_names = set(event_map.values())
                for f in exp_dir.glob("*.md"):
                    if f.stem not in safe_names:
                        print(f"    [CLEANUP] removing: {f.name}")
                        f.unlink()
            print(f"    {'[WROTE]' if apply else '[DRY-RUN]'} {len(exp_items)} experience files")

    return new_case


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Translate data_patient/ + cases.jsonl Chinese → English (LLM)"
    )
    parser.add_argument("--all", action="store_true", help="Process all cases")
    parser.add_argument("--case", type=str, default=None, help="Single case ID")
    parser.add_argument("--apply", action="store_true", help="Actually write files")
    args = parser.parse_args()

    if not args.case and not args.all:
        print("Examples:")
        print("  python scripts/translate_patient_data.py --case 814481 --apply")
        print("  python scripts/translate_patient_data.py --all --apply")
        sys.exit(0)

    if not CASES_FILE.exists():
        print(f"ERROR: {CASES_FILE} not found")
        sys.exit(1)

    cases = load_cases()
    print(f"Loaded {len(cases)} cases")

    target = {args.case} if args.case else None
    updated: List[Dict[str, Any]] = []
    ok = 0

    for case in cases:
        if target and case["id"] not in target:
            updated.append(case)
            continue
        try:
            new_case = process_case(case, apply=args.apply)
            updated.append(new_case)
            ok += 1
        except Exception as exc:
            print(f"[{case['id']}] FAILED: {exc}")
            import traceback
            traceback.print_exc()
            updated.append(case)

    if args.apply:
        out = CASES_FILE.parent / "cases.jsonl.translated"
        save_cases(updated, out)
        out.replace(CASES_FILE)
        print(f"\n[WROTE] cases.jsonl ({len(updated)} cases)")

    print(f"\nDone. {ok} cases processed ({'APPLIED' if args.apply else 'DRY-RUN'}).")
    if not args.apply:
        print("Add --apply to write changes.")


if __name__ == "__main__":
    main()
