"""
精神科访谈评估模块 - 第四阶段：Definitive Diagnosis Evaluation

评估口径：
- disorder_metrics: 病症诊断集合匹配指标 (Precision/Recall/F1/Jaccard)
- category_metrics: 类别诊断集合匹配指标 (Precision/Recall/F1/Jaccard)
- primary_metrics: 主诊断排序指标 (Exact_Match/Hit@K/PRR)
- ranking_metrics: 排序一致性指标 (POA/nDCG)

使用方法:
    from core.evaluate.interview_phase4_eval import evaluate_phase4

    result = evaluate_phase4(model_name="qwen-flash", case_id="1009904")
"""

import json
import math
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Set
from itertools import combinations

from core.evaluate.interview_phase1_eval import (
    get_evaluation_dir,
    get_evaluation_output_file,
    save_evaluation_result
)

CASES_FILE = Path(__file__).parent.parent.parent / "data" / "cases.jsonl"
MAPPING_FILE = Path(__file__).parent.parent.parent / "data" / "mapping.json"


# ────────────────────── Data Loading ──────────────────────

def _load_mapping() -> Dict[str, List[str]]:
    """加载 disorder → category 映射"""
    if not MAPPING_FILE.exists():
        return {}
    with open(MAPPING_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _build_disorder_to_category(mapping: Dict[str, List[str]]) -> Dict[str, str]:
    """构建 disorder_name → category_name 的反向映射"""
    result = {}
    for category, disorders in mapping.items():
        for disorder in disorders:
            result[disorder] = category
    return result


def load_case_data(case_id: str) -> Optional[Dict[str, Any]]:
    """从 cases.jsonl 加载指定 case 的完整数据"""
    if not CASES_FILE.exists():
        return None
    with open(CASES_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                if data.get("id") == case_id:
                    return data
            except json.JSONDecodeError:
                continue
    return None


def load_real_disorders(case_id: str) -> Optional[List[str]]:
    """从 cases.jsonl 加载真实病症诊断"""
    case = load_case_data(case_id)
    if case is None:
        return None
    return case.get("realDisorder", [])


def load_real_categories(case_id: str) -> Optional[List[str]]:
    """从 cases.jsonl 加载真实类别诊断"""
    case = load_case_data(case_id)
    if case is None:
        return None
    return case.get("realCategory", [])


# ────────────────────── Category Mapping ──────────────────────

def disorders_to_categories(disorders: List[str], mapping: Dict[str, List[str]]) -> List[str]:
    """将病症列表映射为类别列表

    对每个 disorder，通过 mapping 查找其所属 category。
    如果 disorder 在 mapping 中找不到（未知病症），则跳过。
    返回去重后的类别列表（保持首次出现的顺序）。
    """
    disorder_to_cat = _build_disorder_to_category(mapping)
    seen: Set[str] = set()
    result = []
    for d in disorders:
        cat = disorder_to_cat.get(d)
        if cat and cat not in seen:
            seen.add(cat)
            result.append(cat)
    return result


# ────────────────────── Metrics ──────────────────────

def calculate_set_metrics(predicted: List[str], true: List[str]) -> Dict[str, float]:
    """计算集合匹配指标（忽略顺序，只看是否命中）"""
    pred_set = set(predicted)
    gold_set = set(true)

    if len(pred_set) == 0 and len(gold_set) == 0:
        return {"precision": 1.0, "recall": 1.0, "f1": 1.0, "jaccard": 1.0}

    if len(pred_set) == 0 or len(gold_set) == 0:
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0, "jaccard": 0.0}

    intersection = pred_set & gold_set
    union = pred_set | gold_set

    precision = len(intersection) / len(pred_set)
    recall = len(intersection) / len(gold_set)
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    jaccard = len(intersection) / len(union)

    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "jaccard": round(jaccard, 4)
    }


def calculate_primary_metrics(predicted: List[str], true: List[str], k: int = 3) -> Dict[str, Union[float, int]]:
    """计算主诊断排序指标（关注真实主诊断是否排在预测前列）"""
    if len(true) == 0:
        return {"primary_exact_match": 0, "primary_hit_at_k": 0, "primary_reciprocal_rank": 0.0}

    primary_gold = true[0]

    exact_match = 1 if len(predicted) > 0 and predicted[0] == primary_gold else 0
    hit_at_k = 1 if primary_gold in predicted[:k] else 0

    reciprocal_rank = 0.0
    for i, pred in enumerate(predicted):
        if pred == primary_gold:
            reciprocal_rank = 1.0 / (i + 1)
            break

    return {
        "primary_exact_match": exact_match,
        "primary_hit_at_k": hit_at_k,
        "primary_reciprocal_rank": round(reciprocal_rank, 4)
    }


def calculate_pairwise_order_accuracy(predicted: List[str], true: List[str]) -> Optional[float]:
    """计算Pairwise Order Accuracy (POA)"""
    pred_set = set(predicted)
    true_set = set(true)
    common = list(pred_set & true_set)

    if len(common) < 2:
        return None

    pred_order = {item: i for i, item in enumerate(predicted) if item in common}
    true_order = {item: i for i, item in enumerate(true) if item in common}

    pairs = list(combinations(common, 2))
    consistent_count = 0

    for a, b in pairs:
        pred_rel = pred_order[a] < pred_order[b]
        true_rel = true_order[a] < true_order[b]
        if pred_rel == true_rel:
            consistent_count += 1

    poa = consistent_count / len(pairs)
    return round(poa, 4)


def calculate_ndcg(predicted: List[str], true: List[str]) -> float:
    """计算nDCG"""
    if len(true) == 0:
        return 0.0

    relevance = {item: 1.0 / (i + 1) for i, item in enumerate(true)}

    dcg = 0.0
    for i, pred in enumerate(predicted):
        rel = relevance.get(pred, 0.0)
        dcg += rel / math.log2(i + 2)

    idcg = 0.0
    for i, item in enumerate(true):
        rel = 1.0 / (i + 1)
        idcg += rel / math.log2(i + 2)

    if idcg == 0:
        return 0.0

    ndcg = dcg / idcg
    return round(ndcg, 4)


def calculate_ranking_metrics(predicted: List[str], true: List[str]) -> Dict[str, Union[float, None]]:
    """计算排序一致性指标"""
    poa = calculate_pairwise_order_accuracy(predicted, true)
    ndcg = calculate_ndcg(predicted, true)

    return {"poa": poa, "ndcg": ndcg}


# ────────────────────── Main Evaluation ──────────────────────

def evaluate_phase4(
    model_name: str = None,
    case_id: str = None,
    output_file: Union[str, Path] = None,
    phase4_data: Dict[str, Any] = None,
    true_disorders: List[str] = None
) -> Dict[str, Any]:
    """评估第四阶段（Definitive Diagnosis）

    可以通过以下方式之一提供数据：
    1. 提供 model_name 和 case_id（从默认路径读取）
    2. 提供 output_file（直接读取指定文件）
    3. 提供 phase4_data（直接使用数据）
    """
    if phase4_data is None:
        if output_file is None:
            if model_name is None or case_id is None:
                raise ValueError("必须提供 model_name+case_id 或 output_file 或 phase4_data")
            from core.output_manager import get_phase_output_file
            output_file = get_phase_output_file(model_name, case_id, 4)

        output_file = Path(output_file)
        with open(output_file, "r", encoding="utf-8") as f:
            phase4_data = json.load(f)

    model_name = phase4_data.get("model_name", model_name)
    case_id = phase4_data.get("case_id", case_id)

    if model_name is None or case_id is None:
        raise ValueError("无法确定 model_name 或 case_id")

    predicted_diagnoses = phase4_data.get('definitive_diagnosis', [])
    status = phase4_data.get('status', 'unknown')

    # 加载真实病症诊断
    if true_disorders is None:
        true_disorders = load_real_disorders(case_id)
    if true_disorders is None:
        true_disorders = []

    # 加载真实类别诊断
    true_categories = load_real_categories(case_id)
    if true_categories is None:
        true_categories = []

    # 加载映射，将预测病症映射为类别
    mapping = _load_mapping()
    predicted_categories = disorders_to_categories(predicted_diagnoses, mapping)

    # === 病症层面评估 ===
    disorder_metrics = calculate_set_metrics(predicted_diagnoses, true_disorders)
    primary_metrics = calculate_primary_metrics(predicted_diagnoses, true_disorders)
    ranking_metrics = calculate_ranking_metrics(predicted_diagnoses, true_disorders)

    # === 类别层面评估 ===
    category_metrics = calculate_set_metrics(predicted_categories, true_categories)

    evaluation_data = {
        "disorder_metrics": disorder_metrics,
        "category_metrics": category_metrics,
        "primary_metrics": primary_metrics,
        "ranking_metrics": ranking_metrics,
        "predicted_diagnoses": predicted_diagnoses,
        "true_disorders": true_disorders,
        "predicted_categories": predicted_categories,
        "true_categories": true_categories,
        "status": status
    }

    eval_output_file = save_evaluation_result(model_name, case_id, 4, evaluation_data)

    print(f"\nPhase 4 (Definitive Diagnosis) 评估结果:")
    print(f"  状态: {status}")
    print(f"  预测病症诊断: {predicted_diagnoses}")
    print(f"  真实病症诊断: {true_disorders}")
    print(f"  预测类别诊断: {predicted_categories}")
    print(f"  真实类别诊断: {true_categories}")

    print(f"\n  [病症诊断] 集合匹配指标 (disorder_metrics):")
    print(f"    Precision: {disorder_metrics['precision']:.4f}")
    print(f"    Recall: {disorder_metrics['recall']:.4f}")
    print(f"    F1: {disorder_metrics['f1']:.4f}")
    print(f"    Jaccard: {disorder_metrics['jaccard']:.4f}")

    print(f"\n  [类别诊断] 集合匹配指标 (category_metrics):")
    print(f"    Precision: {category_metrics['precision']:.4f}")
    print(f"    Recall: {category_metrics['recall']:.4f}")
    print(f"    F1: {category_metrics['f1']:.4f}")
    print(f"    Jaccard: {category_metrics['jaccard']:.4f}")

    print(f"\n  主诊断排序指标 (primary_metrics):")
    print(f"    Primary Exact Match: {primary_metrics['primary_exact_match']}")
    print(f"    Primary Hit@3: {primary_metrics['primary_hit_at_k']}")
    print(f"    Primary Reciprocal Rank: {primary_metrics['primary_reciprocal_rank']:.4f}")

    print(f"\n  排序一致性指标 (ranking_metrics):")
    print(f"    POA: {ranking_metrics['poa']}")
    print(f"    nDCG: {ranking_metrics['ndcg']:.4f}")

    print(f"\n  评估结果保存: {eval_output_file}")

    # ========== 主观评估：Diagnostic Rigor ==========
    diagnostic_rigor_subjective = None

    # 提取诊断理由：[BEGIN_DEFINITIVE_DIAGNOSIS] 之前的内容
    reasoning_text = phase4_data.get('diagnosis_reasoning', '')
    raw_response = phase4_data.get('raw_response', '')

    if not reasoning_text and raw_response:
        import re as _re
        match = _re.search(
            r'(.*?)\[BEGIN_DEFINITIVE_DIAGNOSIS\]',
            raw_response,
            _re.DOTALL | _re.IGNORECASE
        )
        if match:
            reasoning_text = match.group(1).strip()

    if reasoning_text and reasoning_text.strip():
        try:
            from core.evaluate.subjective_assessment.subjective_evaluator import SubjectiveEvaluator
            from core.evaluate.subjective_assessment.prompt import PROMPTS as SUBJECTIVE_PROMPTS

            print(f"\n开始主观评估：诊断严谨性（5 评估器并行）...")
            rubric = SUBJECTIVE_PROMPTS["Diagnostic Rigor"]

            diagnostic_rigor_subjective = SubjectiveEvaluator.evaluate_multi(
                rubric_content=rubric,
                test_context=reasoning_text
            )

            evaluation_data["diagnostic_rigor_subjective"] = diagnostic_rigor_subjective

            try:
                from core.evaluate.trajectory_collector import collect_from_evaluation_result
                evaluation_data["diagnostic_rigor_trajectory"] = collect_from_evaluation_result(
                    "Diag", diagnostic_rigor_subjective, case_id, test_model=model_name
                )
            except Exception as e:
                print(f"  诊断严谨性轨迹收集失败: {e}")

            score = diagnostic_rigor_subjective.get('score', 'N/A')
            scores = diagnostic_rigor_subjective.get('scores', [])
            print(f"  诊断严谨性均分: {score}/5 (各评分: {scores}) (成功解析: {diagnostic_rigor_subjective.get('parsed_count')}/5)")

            save_evaluation_result(model_name, case_id, 4, evaluation_data)
        except Exception as e:
            print(f"  诊断严谨性主观评估失败: {e}")
            import traceback
            traceback.print_exc()

    return {
        "disorder_metrics": disorder_metrics,
        "category_metrics": category_metrics,
        "primary_metrics": primary_metrics,
        "ranking_metrics": ranking_metrics,
        "diagnostic_rigor_subjective": diagnostic_rigor_subjective,
        "predicted_diagnoses": predicted_diagnoses,
        "true_disorders": true_disorders,
        "predicted_categories": predicted_categories,
        "true_categories": true_categories,
        "status": status,
        "output_file": str(eval_output_file),
        "model_name": model_name,
        "case_id": case_id
    }


if __name__ == "__main__":
    print("=" * 60)
    print("测试：Phase 4 (Definitive Diagnosis) 评估模块")
    print("=" * 60)

    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

    try:
        output_base = Path(__file__).parent.parent.parent / "data" / "output" / "interview"

        if output_base.exists():
            model_dirs = list(output_base.iterdir())
            if model_dirs:
                model_dir = model_dirs[0]
                case_dirs = list(model_dir.iterdir())
                if case_dirs:
                    case_dir = case_dirs[0]
                    model_name = model_dir.name
                    case_id = case_dir.name

                    print(f"\n使用现有数据测试:")
                    print(f"  模型: {model_name}")
                    print(f"  病例: {case_id}")

                    result = evaluate_phase4(model_name=model_name, case_id=case_id)

                    print("\n" + "=" * 60)
                    print("测试完成")
                    print("=" * 60)
                else:
                    print("未找到病例数据，请先运行 interview_phase4")
            else:
                print("未找到模型数据，请先运行 interview_phase4")
        else:
            print("输出目录不存在，请先运行 interview_phase4")

    except Exception as e:
        print(f"发生错误: {e}")
        import traceback
        traceback.print_exc()
