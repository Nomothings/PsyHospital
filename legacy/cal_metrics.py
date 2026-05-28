"""
计算模型评估指标均值

使用方法:
    python cal_metrics.py              # 遍历所有模型，输出 results/results.json
    python cal_metrics.py --all        # 同上
    python cal_metrics.py --model gpt-5.5  # 单模型输出到 results/results.json

输出:
    results/results.json — 按 模型→类型（客观/主观）→指标 组织的 JSON 文件
    只保留各指标的均值，即原 table 表中的数值。
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any

RESULTS_DIR = Path(__file__).parent / "data" / "output" / "results"
EVAL_DIR = Path(__file__).parent / "data" / "output" / "evaluation"
OUTPUT_DIR = Path(__file__).parent / "results"


# ───────────────────────── 指标定义 ─────────────────────────

OBJECTIVE_METRICS = [
    ("phase1", [
        ("主诉覆盖", "phase1_cc", "pct"),
        ("精神状态", "phase1_ms", "pct"),
        ("整体覆盖", "phase1_overall", "pct"),
    ]),
    ("phase2", [
        ("Precision", "phase2_precision", "dec4"),
        ("Recall", "phase2_recall", "dec4"),
        ("F1", "phase2_f1", "dec4"),
        ("Jaccard", "phase2_jaccard", "dec4"),
    ]),
    ("phase3", [
        ("总分", "phase3_total", "pct"),
        ("主诉", "phase3_chief_complaint", "dec4"),
        ("体格检查", "phase3_physical_examination", "dec4"),
        ("精神检查", "phase3_mental_examination", "dec4"),
        ("既往史家族史", "phase3_past_family_history", "dec4"),
    ]),
    ("phase4", [
        ("类别 Precision", "phase4_cat_precision", "dec4"),
        ("类别 Recall", "phase4_cat_recall", "dec4"),
        ("类别 F1", "phase4_cat_f1", "dec4"),
        ("类别 Jaccard", "phase4_cat_jaccard", "dec4"),
        ("Exact Match", "phase4_exact_match", "dec4"),
        ("nDCG", "phase4_ndcg", "dec4"),
        ("Reciprocal Rank", "phase4_rr", "dec4"),
    ]),
    ("phase5", [
        ("文本长度", "phase5_length", "int"),
    ]),
]

SUBJECTIVE_METRICS = [
    ("共情", "phase1_empathy"),
    ("专业", "phase1_profession"),
    ("病历质量", "phase3_subjective"),
    ("诊断严谨", "phase4_subjective"),
    ("治疗合理", "phase5_subjective"),
]

# 用于 composite 的关键指标
_KEY_OBJ = {
    "phase1_overall": 100.0,
    "phase2_f1": 1.0,
    "phase3_total": 100.0,
    "phase4_cat_f1": 1.0,
    "phase4_exact_match": 1.0,
    "phase4_ndcg": 1.0,
    "phase4_rr": 1.0,
}
_KEY_SUBJ = [
    "phase1_empathy", "phase1_profession",
    "phase3_subjective", "phase4_subjective", "phase5_subjective",
]


# ───────────────────────── 工具函数 ─────────────────────────

def _avg(scores_list: List[Dict], key: str) -> Optional[float]:
    values = [s[key] for s in scores_list if s.get(key) is not None]
    if not values:
        return None
    return sum(values) / len(values)


# ───────────────────────── 从 evaluation 目录计算指标 ─────────────────────────

def compute_scores_from_eval(model_name: str) -> List[Dict[str, Any]]:
    """从 data/output/evaluation/{model}/{case_id}/ 读取评估文件并计算指标"""
    eval_path = EVAL_DIR / model_name
    if not eval_path.exists():
        return []

    scores_list = []
    for case_dir in sorted(eval_path.iterdir()):
        if not case_dir.is_dir():
            continue
        scores: Dict[str, Any] = {}

        # Phase 1
        p1_file = case_dir / "evaluation_phase1_output.json"
        if p1_file.exists():
            try:
                p1 = json.loads(p1_file.read_text(encoding="utf-8"))
                cov = p1.get("coverage_stats", {})
                scores["phase1_cc"] = cov.get("chief_complaint_coverage")
                scores["phase1_ms"] = cov.get("mental_status_coverage")
                scores["phase1_overall"] = cov.get("overall_coverage")
                emp = p1.get("empathy_evaluation")
                if emp:
                    scores["phase1_empathy"] = emp.get("score")
                pro = p1.get("profession_evaluation")
                if pro:
                    scores["phase1_profession"] = pro.get("score")
            except (json.JSONDecodeError, OSError):
                pass

        # Phase 2
        p2_file = case_dir / "evaluation_phase2_output.json"
        if p2_file.exists():
            try:
                p2 = json.loads(p2_file.read_text(encoding="utf-8"))
                met = p2.get("metrics", {})
                if met:
                    scores["phase2_precision"] = met.get("precision")
                    scores["phase2_recall"] = met.get("recall")
                    scores["phase2_f1"] = met.get("f1")
                    scores["phase2_jaccard"] = met.get("jaccard")
            except (json.JSONDecodeError, OSError):
                pass

        # Phase 3
        p3_file = case_dir / "evaluation_phase3_output.json"
        if p3_file.exists():
            try:
                p3 = json.loads(p3_file.read_text(encoding="utf-8"))
                scores["phase3_total"] = p3.get("total_percentage")
                # 四个维度细粒度覆盖度
                dimensions = p3.get("dimensions", {})
                for dim_key in ["chief_complaint", "physical_examination", "mental_examination", "past_family_history"]:
                    dim_data = dimensions.get(dim_key, {})
                    pct = dim_data.get("percentage")
                    if pct is not None:
                        scores[f"phase3_{dim_key}"] = pct
                subj = p3.get("clinical_note_subjective")
                if subj:
                    scores["phase3_subjective"] = subj.get("score")
            except (json.JSONDecodeError, OSError):
                pass

        # Phase 4
        p4_file = case_dir / "evaluation_phase4_output.json"
        if p4_file.exists():
            try:
                p4 = json.loads(p4_file.read_text(encoding="utf-8"))
                dis_m = p4.get("disorder_metrics", {})
                cat_m = p4.get("category_metrics", {})
                primary_m = p4.get("primary_metrics", {})
                rank_m = p4.get("ranking_metrics", {})
                scores["phase4_cat_precision"] = cat_m.get("precision")
                scores["phase4_cat_recall"] = cat_m.get("recall")
                scores["phase4_cat_f1"] = cat_m.get("f1")
                scores["phase4_cat_jaccard"] = cat_m.get("jaccard")
                if primary_m:
                    scores["phase4_exact_match"] = primary_m.get("primary_exact_match")
                    scores["phase4_rr"] = primary_m.get("primary_reciprocal_rank")
                if rank_m:
                    scores["phase4_ndcg"] = rank_m.get("ndcg")
                    scores["phase4_poa"] = rank_m.get("poa")
                diag_subj = p4.get("diagnostic_rigor_subjective")
                if diag_subj:
                    scores["phase4_subjective"] = diag_subj.get("score")
            except (json.JSONDecodeError, OSError):
                pass

        # Phase 5
        p5_file = case_dir / "evaluation_phase5_output.json"
        if p5_file.exists():
            try:
                p5 = json.loads(p5_file.read_text(encoding="utf-8"))
                subj = p5.get("treatment_subjective")
                if subj:
                    scores["phase5_subjective"] = subj.get("score")
                length = p5.get("treatment_plan_length")
                if length is not None:
                    scores["phase5_length"] = length
            except (json.JSONDecodeError, OSError):
                pass

        if scores:
            scores_list.append(scores)

    return scores_list


# ───────────────────────── 数据加载 ─────────────────────────

def load_scores(model_name: str) -> List[Dict[str, Any]]:
    """加载模型指标数据。

    优先从 evaluation/{model_name}/{case_id}/ 目录读取评估文件计算。
    如果 evaluation 目录无数据，则回退到 results/{model_name}.json 的 per_case。
    """
    scores_list = compute_scores_from_eval(model_name)
    if scores_list:
        return scores_list

    results_path = RESULTS_DIR / f"{model_name}.json"
    if results_path.exists():
        try:
            data = json.loads(results_path.read_text(encoding="utf-8"))
            per_case = data.get("per_case", [])
            if per_case:
                return [r.get("scores", {}) for r in per_case]
        except (json.JSONDecodeError, OSError):
            pass

    return scores_list


def load_all_models() -> List[str]:
    """从 data/output/results/ 目录发现所有模型"""
    models = []
    if RESULTS_DIR.exists():
        for p in sorted(RESULTS_DIR.glob("*.json")):
            models.append(p.stem)
    return models


# ───────────────────────── Composite ─────────────────────────

def _composite_obj(scores_list: List[Dict]) -> Optional[float]:
    vals = []
    for key, cap in _KEY_OBJ.items():
        avg = _avg(scores_list, key)
        if avg is not None:
            vals.append(avg / cap)
    if not vals:
        return None
    return sum(vals) / len(vals)


def _composite_subj(scores_list: List[Dict]) -> Optional[float]:
    vals = []
    for key in _KEY_SUBJ:
        avg = _avg(scores_list, key)
        if avg is not None:
            vals.append(avg)
    if not vals:
        return None
    return sum(vals) / len(vals)


# ───────────────────────── JSON 输出 ─────────────────────────

def build_model_result(model_name: str, scores_list: List[Dict]) -> Dict:
    """为单个模型构建 JSON 结果，只保留各指标的均值（同原 table 中的值）"""

    # ── 客观指标（按阶段分组） ──
    objective = {}
    for phase_key, metrics in OBJECTIVE_METRICS:
        phase_data = {}
        for label, key, fmt_type in metrics:
            avg = _avg(scores_list, key)
            if avg is not None:
                if fmt_type == "pct":
                    phase_data[label] = f"{avg:.2f}%"
                elif fmt_type == "dec4":
                    phase_data[label] = round(avg, 4)
                elif fmt_type == "int":
                    phase_data[label] = int(round(avg))
                else:
                    phase_data[label] = round(avg, 4)
        objective[phase_key] = phase_data

    comp_obj = _composite_obj(scores_list)
    if comp_obj is not None:
        objective["客观综合"] = round(comp_obj, 4)

    # ── 主观指标 ──
    subjective = {}
    for label, key in SUBJECTIVE_METRICS:
        avg = _avg(scores_list, key)
        if avg is not None:
            subjective[label] = round(avg, 2)

    comp_subj = _composite_subj(scores_list)
    if comp_subj is not None:
        subjective["主观综合"] = round(comp_subj, 2)

    return {
        "客观指标": objective,
        "主观指标": subjective,
    }


def export_results(model_names: List[str]):
    """遍历所有模型，输出 results/results.json"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / "results.json"

    results = {}
    for model_name in model_names:
        scores_list = load_scores(model_name)
        if not scores_list:
            print(f"  [跳过] {model_name}: 无可用数据")
            continue
        results[model_name] = build_model_result(model_name, scores_list)
        print(f"  [完成] {model_name}: {len(scores_list)} cases")

    if not results:
        print("[错误] 无可用模型数据")
        sys.exit(1)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({"models": results}, f, ensure_ascii=False, indent=2)

    print(f"\n结果已保存至: {output_path}")


def export_single_model(model_name: str):
    """输出单个模型的 JSON 到 results/results.json"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / "results.json"

    scores_list = load_scores(model_name)
    if not scores_list:
        print(f"[错误] 模型 '{model_name}' 无可用数据")
        sys.exit(1)

    result = build_model_result(model_name, scores_list)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({"models": {model_name: result}}, f, ensure_ascii=False, indent=2)

    print(f"结果已保存至: {output_path}")


# ───────────────────────── 主函数 ─────────────────────────

def main():
    parser = argparse.ArgumentParser(description="计算模型评估指标均值，输出 JSON")
    parser.add_argument("--model", type=str, default=None, help="指定模型名称")
    parser.add_argument("--all", action="store_true", help="遍历所有模型对比输出")
    args = parser.parse_args()

    if args.model:
        print(f"\n正在处理模型: {args.model}")
        export_single_model(args.model)
    else:
        models = load_all_models()
        print(f"\n发现 {len(models)} 个模型，开始计算...\n")
        export_results(models)

    output_path = OUTPUT_DIR / "results.json"
    if output_path.exists():
        data = json.loads(output_path.read_text(encoding="utf-8"))
        print(f"\n共处理 {len(data['models'])} 个模型")
        print(f"输出文件: {output_path}")


if __name__ == "__main__":
    main()
