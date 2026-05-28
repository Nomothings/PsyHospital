import sys
import json
from pathlib import Path
from typing import Dict, Any, List, Union

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.llm_api import get_instrument_llm, LLMService
from agents.instrument.prompts import PROMPTS


def create_instrument(
    examination_query: str,
    auxiliary_examinations: str,
    backup: bool = False
) -> LLMService:
    """启动虚拟检查仪器

    根据医生请求的检查项目和已知的辅助检查结果，
    使用INSTRUMENT_API配置实例化Instrument Agent。

    Args:
        examination_query: 医生请求的检查项目JSON数组字符串，
                          如 '["头颅CT", "血液检查"]'
        auxiliary_examinations: 患者全部辅助检查结果JSON对象字符串，
                               如 '{"头颅CT": "未见异常", "脑电图": "正常"}'
        backup: 使用备用API（INSTRUMENT_BACKUP_* 配置）

    Returns:
        LLMService实例（已设置系统prompt和检查信息）
    """
    system_prompt = PROMPTS["Instrument Rule"]
    system_prompt = system_prompt.replace("<EXAMINATION_QUERY>", examination_query)
    system_prompt = system_prompt.replace("<AUXILIARY_EXAMINATIONS>", auxiliary_examinations)

    instrument = get_instrument_llm(system_message=system_prompt, backup=backup)

    instrument.exam_info = {
        "examination_query": examination_query,
        "auxiliary_examinations": auxiliary_examinations
    }

    return instrument


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


def evaluate_examination_metrics(
    response: Union[str, Dict[str, str]],
    examination_query: Union[str, List[str]],
    auxiliary_examinations: Union[str, Dict[str, str]]
) -> Dict[str, Any]:
    """根据Instrument返回结果计算检查推荐指标
    
    当前版本严格按照你现有的评估口径计算：
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
    
    # 特殊情况：如果gold和预测都为空，视为完全一致
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


def chat_and_evaluate_instrument(
    instrument: LLMService,
    user_message: str = "请根据上述信息返回检查结果"
) -> Dict[str, Any]:
    """调用Instrument并返回检查结果 + 评估指标"""
    response = instrument.chat(user_message)
    
    if not hasattr(instrument, "exam_info"):
        raise AttributeError("instrument 实例缺少 exam_info，无法进行评估")
    
    result = evaluate_examination_metrics(
        response=response,
        examination_query=instrument.exam_info["examination_query"],
        auxiliary_examinations=instrument.exam_info["auxiliary_examinations"]
    )
    result["raw_response"] = response
    return result


if __name__ == "__main__":
    print("=" * 50)
    print("测试启动虚拟检查仪器 + 指标计算")
    print("=" * 50)
    
    test_query = '["头颅CT", "血液检查", "MRI扫描", "心电图"]'
    test_examinations = json.dumps({
        "头颅CT": "未见异常",
        "头颅MRI": "正常"
    }, ensure_ascii=False)
    
    try:
        instrument = create_instrument(
            examination_query=test_query,
            auxiliary_examinations=test_examinations
        )
        
        print(f"\n查询项目: {test_query}")
        print(f"已知检查: {test_examinations}")
        print(f"使用模型: {instrument.config.model}")
        
        print("\n" + "-" * 50)
        print("获取检查结果并计算指标")
        print("-" * 50)
        
        result = chat_and_evaluate_instrument(instrument)
        
        print(f"\n原始响应:\n{result['raw_response']}")
        
        print("\n解析结果:")
        for key, value in result["response"].items():
            print(f"  {key}: {value}")
        
        print("\n统计信息:")
        for key, value in result["counts"].items():
            print(f"  {key}: {value}")
        
        print("\n评估指标:")
        for key, value in result["metrics"].items():
            print(f"  {key}: {value}")
        
        if result["warnings"]:
            print("\n警告:")
            for w in result["warnings"]:
                print(f"  - {w}")
        
        print("\n" + "=" * 50)
        print("测试完成")
        print("=" * 50)
        
    except Exception as e:
        print(f"发生错误: {e}")
        import traceback
        traceback.print_exc()