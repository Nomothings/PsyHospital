"""
指标收集与 checkpoint 管理模块

功能：
1. 将每 case 的核心指标提取为扁平 dict 并追加到 metrics.jsonl
2. 检查某 case 是否已完成评估（checkpoint 续传）
3. 读取 metrics.jsonl 计算模型均值

metrics.jsonl 路径：data/output/evaluation/{MODEL_NAME}/metrics.jsonl
"""

import json
import threading
from pathlib import Path
from typing import Dict, Any, Optional

_lock = threading.Lock()

# 指标精简映射：从各 phase eval 结果中提取的 key 路径
# 格式: (目标 key, [源路径], 默认值)


def extract_metrics(
    case_id: str,
    phase1_eval: Optional[Dict],
    phase2_eval: Optional[Dict],
    phase3_eval: Optional[Dict],
    phase4_eval: Optional[Dict],
    phase5_eval: Optional[Dict],
) -> Dict[str, Any]:
    """从 5 个阶段的评估结果中提取精简指标

    返回扁平 dict，适合存入 jsonl 一行。
    """
    m = {"case_id": case_id}

    # ── Phase 1 ──
    if phase1_eval:
        cov = phase1_eval.get("coverage_stats", {})
        m["p1_cc_coverage"] = cov.get("chief_complaint_coverage")
        m["p1_ms_coverage"] = cov.get("mental_status_coverage")
        m["p1_overall_coverage"] = cov.get("overall_coverage")

        emp = phase1_eval.get("empathy_evaluation")
        if emp:
            m["p1_empathy"] = emp.get("score")

        pro = phase1_eval.get("profession_evaluation")
        if pro:
            m["p1_profession"] = pro.get("score")

    # ── Phase 2 ──
    if phase2_eval:
        met = phase2_eval.get("metrics", {})
        m["p2_precision"] = met.get("precision")
        m["p2_recall"] = met.get("recall")
        m["p2_f1"] = met.get("f1")
        m["p2_jaccard"] = met.get("jaccard")

    # ── Phase 3 ──
    if phase3_eval:
        m["p3_total_percentage"] = phase3_eval.get("total_percentage")

        subj = phase3_eval.get("clinical_note_subjective")
        if subj:
            m["p3_subjective"] = subj.get("score")

    # ── Phase 4 ──
    if phase4_eval:
        dis = phase4_eval.get("disorder_metrics", {})
        m["p4_disorder_precision"] = dis.get("precision")
        m["p4_disorder_recall"] = dis.get("recall")
        m["p4_disorder_f1"] = dis.get("f1")
        m["p4_disorder_jaccard"] = dis.get("jaccard")

        cat = phase4_eval.get("category_metrics", {})
        m["p4_category_precision"] = cat.get("precision")
        m["p4_category_recall"] = cat.get("recall")
        m["p4_category_f1"] = cat.get("f1")
        m["p4_category_jaccard"] = cat.get("jaccard")

        pri = phase4_eval.get("primary_metrics", {})
        m["p4_primary_exact_match"] = pri.get("primary_exact_match")
        m["p4_primary_hit3"] = pri.get("primary_hit_at_k")
        m["p4_primary_rr"] = pri.get("primary_reciprocal_rank")

        rank = phase4_eval.get("ranking_metrics", {})
        m["p4_poa"] = rank.get("poa")
        m["p4_ndcg"] = rank.get("ndcg")

        diag_subj = phase4_eval.get("diagnostic_rigor_subjective")
        if diag_subj:
            m["p4_subjective"] = diag_subj.get("score")

    # ── Phase 5 ──
    if phase5_eval:
        treat_subj = phase5_eval.get("treatment_subjective")
        if treat_subj:
            m["p5_subjective"] = treat_subj.get("score")

    return m


# ── JSONL 读写 ──

def _get_metrics_path(model_name: str) -> Path:
    return Path(__file__).parent.parent.parent / "data" / "output" / "evaluation" / model_name / "metrics.jsonl"


def _read_jsonl(path: Path) -> Dict[str, Dict]:
    """读取 jsonl，返回 {case_id: record} 字典"""
    records = {}
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                    cid = rec.get("case_id")
                    if cid:
                        records[cid] = rec
                except json.JSONDecodeError:
                    continue
    return records


def case_is_complete(model_name: str, case_id: str) -> bool:
    """检查某 case 是否已在 metrics.jsonl 中有完整记录"""
    path = _get_metrics_path(model_name)
    records = _read_jsonl(path)
    return case_id in records


def append_metrics(model_name: str, case_id: str, metrics: Dict[str, Any]) -> Path:
    """追加指标到 metrics.jsonl（线程安全）

    如果该 case_id 已存在，则覆盖该行（幂等操作）。
    """
    path = _get_metrics_path(model_name)
    path.parent.mkdir(parents=True, exist_ok=True)

    with _lock:
        # 读取现有记录
        records = _read_jsonl(path)

        # 更新或插入
        records[case_id] = metrics

        # 写回
        with open(path, "w", encoding="utf-8") as f:
            for rec in records.values():
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    return path
