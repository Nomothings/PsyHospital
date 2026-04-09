"""
精神科访谈评估模块 - 第四阶段：Diagnostic Category Identification Evaluation

使用方法:
    from core.evaluate.interview_phase4_eval import evaluate_phase4
    
    # 从interview_phase4的输出文件中读取数据并评估
    result = evaluate_phase4(
        model_name="qwen-flash",
        case_id="1009904"
    )
    
    # 或者直接传入数据
    result = evaluate_phase4(
        output_file="/path/to/interview_phase4_output.json"
    )
    
    # 结果包含:
    # - metrics: 评估指标 (Precision/Recall/F1/Jaccard)
    # - predicted_categories: 预测的诊断类别
    # - true_categories: 真实的诊断类别
    # - output_file: 评估结果保存路径
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

from core.evaluate.interview_phase1_eval import (
    get_evaluation_dir,
    get_evaluation_output_file,
    save_evaluation_result
)


def load_real_categories(case_id: str) -> Optional[List[str]]:
    """从ground_truth.jsonl加载真实诊断类别
    
    Args:
        case_id: 病例ID
        
    Returns:
        真实诊断类别列表，如果未找到返回None
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
                    return data.get("realCategory", [])
            except json.JSONDecodeError:
                continue
    
    return None


def calculate_category_metrics(
    predicted: List[str],
    true: List[str]
) -> Dict[str, float]:
    """计算诊断类别的评估指标
    
    Args:
        predicted: 预测的诊断类别列表
        true: 真实的诊断类别列表
        
    Returns:
        包含 Precision/Recall/F1/Jaccard 的字典
    """
    predicted_set = set(predicted)
    true_set = set(true)
    
    if len(predicted_set) == 0 and len(true_set) == 0:
        return {
            "precision": 1.0,
            "recall": 1.0,
            "f1": 1.0,
            "jaccard": 1.0
        }
    
    if len(predicted_set) == 0:
        return {
            "precision": 0.0,
            "recall": 0.0,
            "f1": 0.0,
            "jaccard": 0.0
        }
    
    if len(true_set) == 0:
        return {
            "precision": 0.0,
            "recall": 0.0,
            "f1": 0.0,
            "jaccard": 0.0
        }
    
    intersection = predicted_set & true_set
    union = predicted_set | true_set
    
    tp = len(intersection)
    fp = len(predicted_set - true_set)
    fn = len(true_set - predicted_set)
    
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    jaccard = len(intersection) / len(union) if len(union) > 0 else 0.0
    
    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "jaccard": round(jaccard, 4)
    }


def evaluate_phase4(
    model_name: str = None,
    case_id: str = None,
    output_file: Union[str, Path] = None,
    phase4_data: Dict[str, Any] = None,
    true_categories: List[str] = None
) -> Dict[str, Any]:
    """评估第四阶段访谈
    
    可以通过以下方式之一提供数据：
    1. 提供 model_name 和 case_id（从默认路径读取）
    2. 提供 output_file（直接读取指定文件）
    3. 提供 phase4_data（直接使用数据）
    
    Args:
        model_name: 医生模型名称
        case_id: 病例ID
        output_file: interview_phase4输出文件路径
        phase4_data: interview_phase4数据字典
        true_categories: 真实诊断类别（可选，如不提供则从ground_truth.jsonl加载）
        
    Returns:
        评估结果字典，包含：
        - metrics: 评估指标
        - predicted_categories: 预测的诊断类别
        - true_categories: 真实的诊断类别
        - output_file: 评估结果保存路径
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
    
    predicted_categories = phase4_data.get('diagnostic_categories', [])
    status = phase4_data.get('status', 'unknown')
    
    if true_categories is None:
        true_categories = load_real_categories(case_id)
    
    if true_categories is None:
        true_categories = []
    
    metrics = calculate_category_metrics(predicted_categories, true_categories)
    
    evaluation_data = {
        "metrics": metrics,
        "predicted_categories": predicted_categories,
        "true_categories": true_categories,
        "status": status
    }
    
    eval_output_file = save_evaluation_result(model_name, case_id, 4, evaluation_data)
    
    print(f"\nPhase 4 评估结果:")
    print(f"  状态: {status}")
    print(f"  预测类别: {predicted_categories}")
    print(f"  真实类别: {true_categories}")
    print(f"  评估指标:")
    print(f"    Precision: {metrics['precision']:.4f}")
    print(f"    Recall: {metrics['recall']:.4f}")
    print(f"    F1: {metrics['f1']:.4f}")
    print(f"    Jaccard: {metrics['jaccard']:.4f}")
    print(f"  评估结果保存: {eval_output_file}")
    
    return {
        "metrics": metrics,
        "predicted_categories": predicted_categories,
        "true_categories": true_categories,
        "status": status,
        "output_file": str(eval_output_file),
        "model_name": model_name,
        "case_id": case_id
    }


if __name__ == "__main__":
    print("=" * 60)
    print("测试：Phase 4 评估模块")
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
