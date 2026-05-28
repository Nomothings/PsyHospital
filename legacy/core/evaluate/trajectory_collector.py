"""
轨迹收集模块 - MentalEval SFT/DPO 训练数据生成

目录结构:
    data/output/eval_trajectory/
    ├── sft/
    │   ├── Emp/
    │   │   ├── 01343170_deepseek-v4-pro_a3k9x2.json
    │   │   └── 01821854_claude-haiku-4-5_b7m2q1.json
    │   ├── Pro/
    │   ├── Note/
    │   ├── Diag/
    │   └── Treat/
    └── dpo/
        ├── Emp/
        │   └── 01343170_deepseek-v4-pro_c4n8w5.json
        ├── Pro/
        ├── Note/
        ├── Diag/
        └── Treat/

文件命名: {case_id}_{evaluator_model_name}_{6位随机戳}.json
避免多模型评估时的文件名冲突。

SFT 单文件格式（每个 high_quality 轨迹一个文件）:
    {"case_id": "...", "score": 3, "test_model": "...", "evaluate_model": "...",
     "instruction": "...", "input": "", "output": "..."}

DPO 单文件格式（每个 case 一个文件，含所有 evaluator）:
    {"case_id": "...", "score": [1,2,3,4,5],
     "test_model": "...",
     "evaluate_model": ["eval1", "eval2", "eval3", "eval4", "eval5"],
     "instruction": "...", "input": "",
     "output": ["resp1", "resp2", "resp3", "resp4", "resp5"]}

自适应 mode 阈值:
    - 5 个有效评估器: mode >= 3 -> 分高/低质量
    - 3-4 个有效评估器: mode >= 2 -> 分高/低质量
    - < 3 个有效评估器: 全部丢弃

SFT 仅收集 high_quality 轨迹。
DPO 收集所有有效评估器的响应。
"""

import json
import os
import random
import string
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional


def _random_stamp(n: int = 6) -> str:
    """生成 n 位随机字母数字串"""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=n))


TRAJECTORY_DIR = Path(__file__).parent.parent.parent / "data" / "output" / "eval_trajectory"

DIMENSION_NAMES = {
    "Emp": "Empathy",
    "Pro": "Professionalism",
    "Note": "ClinicalNote",
    "Diag": "DiagnosticRigor",
    "Treat": "TreatmentAppropriateness",
}

_MODE_THRESHOLD = {
    5: 3,
    4: 2,
    3: 2,
}
_MIN_EVALUATORS = 3


# 获取 evaluator 模型名称
_evaluator_models_cache: Dict[int, str] = {}


def _get_evaluator_model_name(evaluator_id: int) -> str:
    """获取指定编号评估器的模型名称"""
    if evaluator_id not in _evaluator_models_cache:
        from services.llm_api import LLMConfigManager
        config = LLMConfigManager.get_config(f"evaluator{evaluator_id}")
        _evaluator_models_cache[evaluator_id] = config.model
    return _evaluator_models_cache[evaluator_id]


class TrajectoryCollector:
    """轨迹收集器 - 基于众数策略的 SFT/DPO 数据生成

    每个轨迹一个独立 JSON 文件，目录按维度组织。
    """

    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir or TRAJECTORY_DIR
        for dim in DIMENSION_NAMES:
            (self.output_dir / "sft" / dim).mkdir(parents=True, exist_ok=True)
            (self.output_dir / "dpo" / dim).mkdir(parents=True, exist_ok=True)

    def collect(
        self,
        dimension: str,
        user_prompt: str,
        individual_results: List[Dict],
        case_id: str = None,
        test_model: str = None,
    ) -> Dict:
        """收集一次评估的轨迹数据并写入独立文件

        Args:
            dimension: 维度简称 (Emp/Pro/Note/Diag/Treat)
            user_prompt: 注入到评估器的完整 prompt
            individual_results: 各评估器的结果列表
            case_id: 病例 ID
            test_model: 被测模型名称

        Returns:
            {"mode": int, "mode_count": int, "n_valid": int, "quality": str,
             "sft_files": List[str], "dpo_file": str | None}
        """
        if dimension not in DIMENSION_NAMES:
            raise ValueError(f"未知维度: {dimension}，可选: {list(DIMENSION_NAMES.keys())}")

        valid_results = [r for r in individual_results if r.get("score") is not None]
        n_valid = len(valid_results)

        if n_valid < _MIN_EVALUATORS:
            return {"mode": None, "mode_count": 0, "n_valid": n_valid,
                    "quality": "discard_few_evaluators", "sft_files": [], "dpo_file": None}

        scores = [r["score"] for r in valid_results]
        score_counter = Counter(scores)
        mode_count = max(score_counter.values())
        mode_values = [s for s, c in score_counter.items() if c == mode_count]

        # 处理平票: 多个众数 -> 一致性低，存 DPO
        if len(mode_values) > 1:
            return self._collect_low_agreement(
                dimension, user_prompt, valid_results, case_id, test_model,
                quality_reason="low_agreement_tie",
            )

        mode = mode_values[0]
        threshold = _MODE_THRESHOLD.get(n_valid, 3)

        if mode_count < threshold:
            return self._collect_low_agreement(
                dimension, user_prompt, valid_results, case_id, test_model,
                quality_reason="low_agreement_split",
            )

        # mode_count >= threshold -> 一致性高 -> 只存 SFT（众数分数的轨迹）
        high_quality = [r for r in valid_results if r["score"] == mode]

        sft_files = []
        dpo_file = None

        # SFT: 从众数分数的 evaluator 中随机选一条写入
        if high_quality:
            chosen = random.choice(high_quality)
            f = self._save_sft(dimension, user_prompt, chosen, case_id, test_model)
            sft_files.append(f)

        # 高一致性场景：只保留 SFT，不存 DPO
        return {"mode": mode, "mode_count": mode_count, "n_valid": n_valid,
                "quality": "high_agreement_sft", "sft_files": sft_files, "dpo_file": None}

    def _collect_low_agreement(
        self,
        dimension: str,
        user_prompt: str,
        valid_results: List[Dict],
        case_id: str,
        test_model: str,
        quality_reason: str,
    ) -> Dict:
        """一致性不够 -> 只存 DPO（所有 evaluator 的响应）"""
        valid_results.sort(key=lambda r: r["evaluator_id"])
        dpo_file = self._save_dpo(dimension, user_prompt, valid_results, case_id, test_model)
        return {"mode": None, "mode_count": 0, "n_valid": len(valid_results),
                "quality": quality_reason, "sft_files": [], "dpo_file": dpo_file}

    def _sft_dir(self, dimension: str) -> Path:
        return self.output_dir / "sft" / dimension

    def _dpo_dir(self, dimension: str) -> Path:
        return self.output_dir / "dpo" / dimension

    def _save_sft(self, dimension: str, user_prompt: str, result: Dict, case_id: str, test_model: str) -> str:
        """保存一条 SFT 轨迹到独立文件

        命名: {case_id}_{evaluator_model}_{6位随机戳}.json
        """
        evaluator_name = _get_evaluator_model_name(result["evaluator_id"])
        stamp = _random_stamp()
        cid = case_id if case_id else "unknown"
        filename = f"{cid}_{evaluator_name}_{stamp}"
        filepath = self._sft_dir(dimension) / f"{filename}.json"

        entry = {
            "case_id": case_id,
            "score": result["score"],
            "test_model": test_model,
            "evaluate_model": evaluator_name,
            "instruction": user_prompt,
            "input": "",
            "output": result["raw_response"],
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(entry, f, ensure_ascii=False, indent=2)

        return str(filepath)

    def _save_dpo(self, dimension: str, user_prompt: str, valid_results: List[Dict], case_id: str, test_model: str) -> str:
        """保存一条 DPO 轨迹（所有 evaluator 响应）到独立文件

        命名: {case_id}_{first_evaluator_model}_{6位随机戳}.json
        """
        first_eval_model = _get_evaluator_model_name(valid_results[0]["evaluator_id"])
        stamp = _random_stamp()
        cid = case_id if case_id else "unknown"
        filename = f"{cid}_{first_eval_model}_{stamp}"
        filepath = self._dpo_dir(dimension) / f"{filename}.json"

        entry = {
            "case_id": case_id,
            "score": [r["score"] for r in valid_results],
            "test_model": test_model,
            "evaluate_model": [_get_evaluator_model_name(r["evaluator_id"]) for r in valid_results],
            "instruction": user_prompt,
            "input": "",
            "output": [r["raw_response"] for r in valid_results],
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(entry, f, ensure_ascii=False, indent=2)

        return str(filepath)


def collect_from_evaluation_result(
    dimension: str,
    evaluation_result: Dict,
    case_id: str = None,
    test_model: str = None,
) -> Dict:
    """便捷函数：从 SubjectiveEvaluator.evaluate_multi() 的结果中提取数据并收集轨迹

    Args:
        dimension: 维度简称 (Emp/Pro/Note/Diag/Treat)
        evaluation_result: SubjectiveEvaluator.evaluate_multi() 的返回值
        case_id: 病例 ID
        test_model: 被测模型名称

    Returns:
        分类结果字典
    """
    individual_results = evaluation_result.get("individual_results", [])
    if not individual_results:
        return {"error": "no individual_results available", "sft_files": [], "dpo_file": None}

    user_prompt = evaluation_result.get("metadata", {}).get("user_prompt", "")
    if not user_prompt:
        return {"error": "user_prompt not available", "sft_files": [], "dpo_file": None}

    collector = TrajectoryCollector()
    return collector.collect(
        dimension=dimension,
        user_prompt=user_prompt,
        individual_results=individual_results,
        case_id=case_id,
        test_model=test_model,
    )
