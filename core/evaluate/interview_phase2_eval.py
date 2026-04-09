"""
精神科访谈评估模块 - 第二阶段：Examination Recommendation Evaluation

使用方法:
    from core.evaluate.interview_phase2_eval import evaluate_phase2
    
    # 从interview_phase2的输出文件中读取数据并评估
    result = evaluate_phase2(
        model_name="qwen-flash",
        case_id="1009904"
    )
    
    # 或者直接传入数据
    result = evaluate_phase2(
        output_file="/path/to/interview_phase2_output.json"
    )
    
    # 结果包含:
    # - metrics: 评估指标 (Precision/Recall/F1/Jaccard)
    # - counts: 统计信息
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


def _parse_json_array(data: Union[str, List[Any]], field_name: str) -> List[Any]:
    """解析JSON数组"""
    if isinstance(data, list):
        return data
    if isinstance(data, str):
        try:
            parsed = json.loads(data)
        except json.JSONDecodeError as e:
            raise ValueError(f"{field_name} 不是合法JSON数组字符串: {e}")
        if not isinstance(parsed, list):
            raise ValueError(f"{field_name} 解析后不是数组类型")
        return parsed
    raise TypeError(f"{field_name} 必须是 list 或 JSON 数组字符串")


def _parse_json_object(data: Union[str, Dict[str, Any]], field_name: str) -> Dict[str, Any]:
    """解析JSON对象"""
    if isinstance(data, dict):
        return data
    if isinstance(data, str):
        try:
            parsed = json.loads(data)
        except json.JSONDecodeError as e:
            raise ValueError(f"{field_name} 不是合法JSON对象字符串: {e}")
        if not isinstance(parsed, dict):
            raise ValueError(f"{field_name} 解析后不是对象类型")
        return parsed
    raise TypeError(f"{field_name} 必须是 dict 或 JSON 对象字符串")


def calculate_examination_metrics(
    response: Union[str, Dict[str, str]],
    examination_query: Union[str, List[str]],
    auxiliary_examinations: Union[str, Dict[str, str]]
) -> Dict[str, Any]:
    """根据Instrument返回结果计算检查推荐指标
    
    当前版本严格按照以下评估口径计算：
    - TP = 非 NONE 的返回数量
    - FP = NONE 的数量
    - FN = gold数量 - TP
    
    进一步得到：
    - Precision = TP / (TP + FP)
    - Recall = TP / (TP + FN)
    - F1 = 2PR / (P + R)
    - Jaccard = TP / (TP + FP + FN)
    
    Args:
        response: Instrument返回的JSON对象或JSON字符串
        examination_query: 医生请求的检查项目数组或JSON字符串
        auxiliary_examinations: gold辅助检查对象或JSON字符串
        
    Returns:
        包含统计信息与指标的字典
    """
    response_dict = _parse_json_object(response, "response")
    query_list = _parse_json_array(examination_query, "examination_query")
    gold_dict = _parse_json_object(auxiliary_examinations, "auxiliary_examinations")
    
    predicted_count = len(query_list)
    gold_count = len(gold_dict)
    response_count = len(response_dict)
    
    none_count = sum(
        1 for v in response_dict.values()
        if isinstance(v, str) and v.strip().upper() == "NONE"
    )
    
    tp = predicted_count - none_count
    fp = none_count
    fn = max(gold_count - tp, 0)
    
    if predicted_count == 0 and gold_count == 0:
        precision = 1.0
        recall = 1.0
        f1 = 1.0
        jaccard = 1.0
    else:
        precision = tp / predicted_count if predicted_count > 0 else 0.0
        recall = tp / gold_count if gold_count > 0 else 0.0
        f1 = (
            2 * precision * recall / (precision + recall)
            if (precision + recall) > 0 else 0.0
        )
        jaccard = tp / (tp + fp + fn) if (tp + fp + fn) > 0 else 0.0
    
    warnings = []
    if response_count != predicted_count:
        warnings.append(
            f"response中的键值对数量({response_count})与医生请求数量({predicted_count})不一致。"
        )
    
    return {
        "counts": {
            "gold_count": gold_count,
            "predicted_count": predicted_count,
            "response_count": response_count,
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "none_count": none_count,
            "correct_count": tp,
            "redundant_count": fp,
            "missed_count": fn
        },
        "metrics": {
            "precision": round(precision, 6),
            "recall": round(recall, 6),
            "f1": round(f1, 6),
            "jaccard": round(jaccard, 6)
        },
        "response": response_dict,
        "warnings": warnings
    }


def evaluate_phase2(
    model_name: str = None,
    case_id: str = None,
    output_file: Union[str, Path] = None,
    phase2_data: Dict[str, Any] = None,
    case_data: Dict[str, Any] = None
) -> Dict[str, Any]:
    """评估第二阶段访谈
    
    可以通过以下方式之一提供数据：
    1. 提供 model_name 和 case_id（从默认路径读取）
    2. 提供 output_file（直接读取指定文件）
    3. 提供 phase2_data（直接使用数据）
    
    Args:
        model_name: 医生模型名称
        case_id: 病例ID
        output_file: interview_phase2输出文件路径
        phase2_data: interview_phase2数据字典
        case_data: 病例数据（用于获取gold辅助检查）
        
    Returns:
        评估结果字典，包含：
        - metrics: 评估指标
        - counts: 统计信息
        - output_file: 评估结果保存路径
    """
    if phase2_data is None:
        if output_file is None:
            if model_name is None or case_id is None:
                raise ValueError("必须提供 model_name+case_id 或 output_file 或 phase2_data")
            from core.output_manager import get_phase_output_file
            output_file = get_phase_output_file(model_name, case_id, 2)
        
        output_file = Path(output_file)
        with open(output_file, "r", encoding="utf-8") as f:
            phase2_data = json.load(f)
    
    model_name = phase2_data.get("model_name", model_name)
    case_id = phase2_data.get("case_id", case_id)
    
    if model_name is None or case_id is None:
        raise ValueError("无法确定 model_name 或 case_id")
    
    examinations = phase2_data.get('examinations', [])
    examination_results = phase2_data.get('examination_results', {})
    status = phase2_data.get('status', 'unknown')
    
    evaluation_metrics = {}
    counts = {}
    warnings = []
    
    if case_data and examinations:
        auxiliary_examination = case_data.get("auxiliaryExamination", {})
        
        if auxiliary_examination:
            examination_query = json.dumps(examinations, ensure_ascii=False)
            auxiliary_examinations_str = json.dumps(auxiliary_examination, ensure_ascii=False)
            
            result = calculate_examination_metrics(
                response=examination_results,
                examination_query=examination_query,
                auxiliary_examinations=auxiliary_examinations_str
            )
            
            evaluation_metrics = result.get("metrics", {})
            counts = result.get("counts", {})
            warnings = result.get("warnings", [])
    
    evaluation_data = {
        "metrics": evaluation_metrics,
        "counts": counts,
        "status": status,
        "examinations": examinations,
        "examination_results": examination_results,
        "warnings": warnings
    }
    
    eval_output_file = save_evaluation_result(model_name, case_id, 2, evaluation_data)
    
    print(f"\nPhase 2 评估结果:")
    print(f"  推荐项目数: {len(examinations)}")
    if evaluation_metrics:
        print(f"  评估指标:")
        print(f"    Precision: {evaluation_metrics.get('precision', 0):.4f}")
        print(f"    Recall: {evaluation_metrics.get('recall', 0):.4f}")
        print(f"    F1: {evaluation_metrics.get('f1', 0):.4f}")
        print(f"    Jaccard: {evaluation_metrics.get('jaccard', 0):.4f}")
    if warnings:
        print(f"  警告:")
        for w in warnings:
            print(f"    - {w}")
    print(f"  评估结果保存: {eval_output_file}")
    
    return {
        "metrics": evaluation_metrics,
        "counts": counts,
        "status": status,
        "output_file": str(eval_output_file),
        "model_name": model_name,
        "case_id": case_id,
        "warnings": warnings
    }


if __name__ == "__main__":
    print("=" * 60)
    print("测试：Phase 2 评估模块")
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
                    
                    result = evaluate_phase2(model_name=model_name, case_id=case_id)
                    
                    print("\n" + "=" * 60)
                    print("测试完成")
                    print("=" * 60)
                else:
                    print("未找到病例数据，请先运行 interview_phase2")
            else:
                print("未找到模型数据，请先运行 interview_phase2")
        else:
            print("输出目录不存在，请先运行 interview_phase2")
            
    except Exception as e:
        print(f"发生错误: {e}")
        import traceback
        traceback.print_exc()
