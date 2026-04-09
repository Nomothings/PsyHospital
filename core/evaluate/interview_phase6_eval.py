"""
精神科访谈评估模块 - 第六阶段：Differential Diagnosis Evaluation

使用方法:
    from core.evaluate.interview_phase6_eval import evaluate_phase6
    
    # 从interview_phase6的输出文件中读取数据并评估
    result = evaluate_phase6(
        model_name="qwen-flash",
        case_id="1009904"
    )
    
    # 或者直接传入数据
    result = evaluate_phase6(
        output_file="/path/to/interview_phase6_output.json"
    )
    
    # 结果包含:
    # - set_metrics: 集合匹配指标 (Precision/Recall/F1/Jaccard)
    # - primary_metrics: 主诊断排序指标 (Exact_Match/Hit@K/PRR)
    # - ranking_metrics: 排序一致性指标 (POA/nDCG)
    # - predicted_diagnoses: 预测的最终诊断
    # - true_disorders: 真实的诊断
    # - output_file: 评估结果保存路径
"""

import json
import math
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from itertools import combinations

from core.evaluate.interview_phase1_eval import (
    get_evaluation_dir,
    get_evaluation_output_file,
    save_evaluation_result
)


def load_real_disorders(case_id: str) -> Optional[List[str]]:
    """从ground_truth.jsonl加载真实诊断
    
    Args:
        case_id: 病例ID
        
    Returns:
        真实诊断列表，如果未找到返回None
    """
    ground_truth_file = Path(__file__).parent.parent.parent / "data" / "ground_truth.jsonl"
    
    if not ground_truth_file.exists():
        return None
    
    with open(ground_truth_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                if data.get("id") == case_id:
                    return data.get("realDisorder", [])
            except json.JSONDecodeError:
                continue
    
    return None


def calculate_set_metrics(
    predicted: List[str],
    true: List[str]
) -> Dict[str, float]:
    """计算集合匹配指标（第一部分：诊断对不对）
    
    忽略顺序，只看模型有没有把该想到的诊断想到，以及有没有多报。
    
    Args:
        predicted: 预测的诊断列表
        true: 真实的诊断列表
        
    Returns:
        包含 Precision/Recall/F1/Jaccard 的字典
    """
    pred_set = set(predicted)
    gold_set = set(true)
    
    if len(pred_set) == 0 and len(gold_set) == 0:
        return {
            "precision": 1.0,
            "recall": 1.0,
            "f1": 1.0,
            "jaccard": 1.0
        }
    
    if len(pred_set) == 0:
        return {
            "precision": 0.0,
            "recall": 0.0,
            "f1": 0.0,
            "jaccard": 0.0
        }
    
    if len(gold_set) == 0:
        return {
            "precision": 0.0,
            "recall": 0.0,
            "f1": 0.0,
            "jaccard": 0.0
        }
    
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


def calculate_primary_metrics(
    predicted: List[str],
    true: List[str],
    k: int = 3
) -> Dict[str, Union[float, int]]:
    """计算主诊断排序指标（第二部分2.1：主诊断排得对不对）
    
    重点关注真实列表的第1个诊断（真实主诊断）。
    
    Args:
        predicted: 预测的诊断列表
        true: 真实的诊断列表
        k: Hit@K的K值，默认为3
        
    Returns:
        包含 Primary_Exact_Match/Primary_Hit_at_K/Primary_Reciprocal_Rank 的字典
    """
    if len(true) == 0:
        return {
            "primary_exact_match": 0,
            "primary_hit_at_k": 0,
            "primary_reciprocal_rank": 0.0
        }
    
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


def calculate_pairwise_order_accuracy(
    predicted: List[str],
    true: List[str]
) -> Optional[float]:
    """计算Pairwise Order Accuracy (POA)
    
    只看预测列表和真实列表中共同出现的诊断，比较它们之间的相对顺序。
    
    Args:
        predicted: 预测的诊断列表
        true: 真实的诊断列表
        
    Returns:
        POA值，如果共同命中诊断少于2个返回None
    """
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


def calculate_ndcg(
    predicted: List[str],
    true: List[str]
) -> float:
    """计算nDCG (Normalized Discounted Cumulative Gain)
    
    衡量真实列表中更重要的诊断是否被模型排到了更前面。
    
    Args:
        predicted: 预测的诊断列表
        true: 真实的诊断列表
        
    Returns:
        nDCG值
    """
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


def calculate_ranking_metrics(
    predicted: List[str],
    true: List[str]
) -> Dict[str, Union[float, None]]:
    """计算排序一致性指标（第二部分2.2：共同命中的诊断顺序是否一致）
    
    Args:
        predicted: 预测的诊断列表
        true: 真实的诊断列表
        
    Returns:
        包含 POA/nDCG 的字典
    """
    poa = calculate_pairwise_order_accuracy(predicted, true)
    ndcg = calculate_ndcg(predicted, true)
    
    return {
        "poa": poa,
        "ndcg": ndcg
    }


def evaluate_phase6(
    model_name: str = None,
    case_id: str = None,
    output_file: Union[str, Path] = None,
    phase6_data: Dict[str, Any] = None,
    true_disorders: List[str] = None
) -> Dict[str, Any]:
    """评估第六阶段访谈
    
    可以通过以下方式之一提供数据：
    1. 提供 model_name 和 case_id（从默认路径读取）
    2. 提供 output_file（直接读取指定文件）
    3. 提供 phase6_data（直接使用数据）
    
    Args:
        model_name: 医生模型名称
        case_id: 病例ID
        output_file: interview_phase6输出文件路径
        phase6_data: interview_phase6数据字典
        true_disorders: 真实诊断（可选，如不提供则从ground_truth.jsonl加载）
        
    Returns:
        评估结果字典，包含：
        - set_metrics: 集合匹配指标
        - primary_metrics: 主诊断排序指标
        - ranking_metrics: 排序一致性指标
        - predicted_diagnoses: 预测的最终诊断
        - true_disorders: 真实的诊断
        - output_file: 评估结果保存路径
    """
    if phase6_data is None:
        if output_file is None:
            if model_name is None or case_id is None:
                raise ValueError("必须提供 model_name+case_id 或 output_file 或 phase6_data")
            from core.output_manager import get_phase_output_file
            output_file = get_phase_output_file(model_name, case_id, 6)
        
        output_file = Path(output_file)
        with open(output_file, "r", encoding="utf-8") as f:
            phase6_data = json.load(f)
    
    model_name = phase6_data.get("model_name", model_name)
    case_id = phase6_data.get("case_id", case_id)
    
    if model_name is None or case_id is None:
        raise ValueError("无法确定 model_name 或 case_id")
    
    predicted_diagnoses = phase6_data.get('differential_diagnosis', [])
    status = phase6_data.get('status', 'unknown')
    
    if true_disorders is None:
        true_disorders = load_real_disorders(case_id)
    
    if true_disorders is None:
        true_disorders = []
    
    set_metrics = calculate_set_metrics(predicted_diagnoses, true_disorders)
    primary_metrics = calculate_primary_metrics(predicted_diagnoses, true_disorders)
    ranking_metrics = calculate_ranking_metrics(predicted_diagnoses, true_disorders)
    
    evaluation_data = {
        "set_metrics": set_metrics,
        "primary_metrics": primary_metrics,
        "ranking_metrics": ranking_metrics,
        "predicted_diagnoses": predicted_diagnoses,
        "true_disorders": true_disorders,
        "status": status
    }
    
    eval_output_file = save_evaluation_result(model_name, case_id, 6, evaluation_data)
    
    print(f"\nPhase 6 评估结果:")
    print(f"  状态: {status}")
    print(f"  预测最终诊断: {predicted_diagnoses}")
    print(f"  真实诊断: {true_disorders}")
    
    print(f"\n  集合匹配指标 (set_metrics):")
    print(f"    Precision: {set_metrics['precision']:.4f}")
    print(f"    Recall: {set_metrics['recall']:.4f}")
    print(f"    F1: {set_metrics['f1']:.4f}")
    print(f"    Jaccard: {set_metrics['jaccard']:.4f}")
    
    print(f"\n  主诊断排序指标 (primary_metrics):")
    print(f"    Primary Exact Match: {primary_metrics['primary_exact_match']}")
    print(f"    Primary Hit@3: {primary_metrics['primary_hit_at_k']}")
    print(f"    Primary Reciprocal Rank: {primary_metrics['primary_reciprocal_rank']:.4f}")
    
    print(f"\n  排序一致性指标 (ranking_metrics):")
    print(f"    POA: {ranking_metrics['poa']}")
    print(f"    nDCG: {ranking_metrics['ndcg']:.4f}")
    
    print(f"\n  评估结果保存: {eval_output_file}")
    
    return {
        "set_metrics": set_metrics,
        "primary_metrics": primary_metrics,
        "ranking_metrics": ranking_metrics,
        "predicted_diagnoses": predicted_diagnoses,
        "true_disorders": true_disorders,
        "status": status,
        "output_file": str(eval_output_file),
        "model_name": model_name,
        "case_id": case_id
    }


if __name__ == "__main__":
    print("=" * 60)
    print("测试：Phase 6 评估模块")
    print("=" * 60)
    
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    
    try:
        from core.output_manager import get_output_dir
        
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
                    
                    result = evaluate_phase6(model_name=model_name, case_id=case_id)
                    
                    print("\n" + "=" * 60)
                    print("测试完成")
                    print("=" * 60)
                else:
                    print("未找到病例数据，请先运行 interview_phase6")
            else:
                print("未找到模型数据，请先运行 interview_phase6")
        else:
            print("输出目录不存在，请先运行 interview_phase6")
            
    except Exception as e:
        print(f"发生错误: {e}")
        import traceback
        traceback.print_exc()
