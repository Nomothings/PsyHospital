"""
Phase 1 评估核心逻辑

包含专业度评估和共情度评估的核心实现
从 scales.py 加载量表定义
"""

import re
from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from services.llm_api import get_evaluator_llm
from core.evaluate.utils.phase1.scales import EMPATHY_SCALE, PROFESSION_SCALE
from core.evaluate.utils.phase1.prompts import (
    EMPATHY_SYSTEM_PROMPT,
    PROFESSION_SYSTEM_PROMPT,
    get_empathy_user_prompt,
    get_profession_user_prompt
)


def parse_empathy_level_from_response(response: str) -> Dict[str, Any]:
    """从响应中解析共情等级评估结果
    
    Args:
        response: LLM 响应文本
        
    Returns:
        解析结果字典
    """
    import re
    
    result = {
        "empathy_level": None,
        "why_this_level": "",
        "why_not_higher_levels": "",
        "why_not_lower_levels": "",
        "evidence": ""
    }
    
    # 提取 empathy_level
    level_match = re.search(r'empathy_level:\s*([\d.]+)', response)
    if level_match:
        try:
            result["empathy_level"] = float(level_match.group(1))
        except ValueError:
            pass
    
    # 提取 why_this_level
    why_this_match = re.search(r'why_this_level:\s*\n?(.*?)(?=\n\nwhy_not_higher_levels:|\Z)', response, re.DOTALL)
    if why_this_match:
        result["why_this_level"] = why_this_match.group(1).strip()
    
    # 提取 why_not_higher_levels
    why_higher_match = re.search(r'why_not_higher_levels:\s*\n?(.*?)(?=\n\nwhy_not_lower_levels:|\Z)', response, re.DOTALL)
    if why_higher_match:
        result["why_not_higher_levels"] = why_higher_match.group(1).strip()
    
    # 提取 why_not_lower_levels
    why_lower_match = re.search(r'why_not_lower_levels:\s*\n?(.*?)(?=\n\nevidence:|\Z)', response, re.DOTALL)
    if why_lower_match:
        result["why_not_lower_levels"] = why_lower_match.group(1).strip()
    
    # 提取 evidence
    evidence_match = re.search(r'evidence:\s*\n?(.*?)(?=\Z)', response, re.DOTALL)
    if evidence_match:
        result["evidence"] = evidence_match.group(1).strip()
    
    return result


def parse_scores_from_response(raw_response: str) -> List[int]:
    """从模型响应中解析分数
    
    Args:
        raw_response: 模型的原始响应
        
    Returns:
        分数列表
    """
    scores = [int(s) for s in re.findall(r"(?mi)^\s*score\s*[:：]\s*([012])\s*$", raw_response)]
    return scores


def calculate_score_variance(scores: List[int]) -> float:
    """计算分数方差
    
    Args:
        scores: 分数列表
        
    Returns:
        方差值
    """
    if not scores:
        return 0.0
    mean_score = sum(scores) / len(scores)
    variance = sum((x - mean_score) ** 2 for x in scores) / len(scores)
    return variance


def evaluate_empathy(conversation_text: str) -> Dict[str, Any]:
    """评估共情度（等级评估）
    
    Args:
        conversation_text: 对话文本
        
    Returns:
        评估结果字典，包含：
        - scale_path: 量表文件路径
        - level_count: 等级数量
        - system_prompt: 系统提示词
        - user_prompt: 用户提示词
        - raw_response: 原始响应
        - empathy_level: 共情等级
        - why_this_level: 为什么属于这个等级
        - why_not_higher_levels: 为什么不属于更高等级
        - why_not_lower_levels: 为什么不属于更低等级
        - evidence: 关键证据
    """
    if not conversation_text or not conversation_text.strip():
        raise ValueError("conversation_text 不能为空。")
    
    # 使用 prompts.py 中的函数生成提示词
    system_prompt = EMPATHY_SYSTEM_PROMPT
    user_prompt = get_empathy_user_prompt(conversation_text, EMPATHY_SCALE)
    
    # 调用评估器
    evaluator_llm = get_evaluator_llm(system_message=system_prompt)
    raw_response = evaluator_llm.chat(user_prompt)
    
    # 解析等级评估结果
    parsed_result = parse_empathy_level_from_response(raw_response)
    
    return {
        "scale_path": "core.evaluate.utils.phase1.scales.EMPATHY_SCALE",
        "level_count": len(EMPATHY_SCALE),
        "system_prompt": system_prompt,
        "user_prompt": user_prompt,
        "raw_response": raw_response,
        **parsed_result
    }


def evaluate_profession(conversation_text: str) -> Dict[str, Any]:
    """评估专业度
    
    Args:
        conversation_text: 对话文本
        
    Returns:
        评估结果字典，包含：
        - scale_path: 量表文件路径
        - question_count: 题目数量
        - system_prompt: 系统提示词
        - user_prompt: 用户提示词
        - raw_response: 原始响应
        - parsed_scores: 解析的分数列表
        - total_score: 总分
        - average_score: 平均分
    """
    if not conversation_text or not conversation_text.strip():
        raise ValueError("conversation_text 不能为空。")
    
    # 使用 prompts.py 中的函数生成提示词
    system_prompt = PROFESSION_SYSTEM_PROMPT
    user_prompt = get_profession_user_prompt(conversation_text, PROFESSION_SCALE)
    
    # 调用评估器
    evaluator_llm = get_evaluator_llm(system_message=system_prompt)
    raw_response = evaluator_llm.chat(user_prompt)
    
    # 解析结果
    parsed_scores = parse_scores_from_response(raw_response)
    
    total_score = sum(parsed_scores) if parsed_scores else 0
    average_score = total_score / len(parsed_scores) if parsed_scores else 0.0
    
    return {
        "scale_path": "core.evaluate.utils.phase1.scales.PROFESSION_SCALE",
        "question_count": len(PROFESSION_SCALE),
        "system_prompt": system_prompt,
        "user_prompt": user_prompt,
        "raw_response": raw_response,
        "parsed_scores": parsed_scores,
        "total_score": total_score,
        "average_score": round(average_score, 4)
    }


def evaluate_both(conversation_text: str, parallel: bool = True) -> Dict[str, Any]:
    """同时评估共情度和专业度
    
    Args:
        conversation_text: 对话文本
        parallel: 是否并行评估（默认 True）
        
    Returns:
        评估结果字典，包含：
        - empathy: 共情度评估结果
        - profession: 专业度评估结果
    """
    if parallel:
        with ThreadPoolExecutor(max_workers=2) as executor:
            future_empathy = executor.submit(evaluate_empathy, conversation_text)
            future_profession = executor.submit(evaluate_profession, conversation_text)
            
            empathy_result = future_empathy.result()
            profession_result = future_profession.result()
    else:
        empathy_result = evaluate_empathy(conversation_text)
        profession_result = evaluate_profession(conversation_text)
    
    return {
        "empathy": empathy_result,
        "profession": profession_result
    }
