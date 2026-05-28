"""
主观 Rubric 评估器

核心功能：
1. 将 Rubric 标准 + 测试内容 注入 "Rubric Format" 模板
2. 调用 LLM-as-a-Judge 进行逐级评分
3. 从 [DECISION_START]X[DECISION_END] 解析最终分数
4. 保留完整的评估分析文本
5. 支持多评估器并行评估并取均值
"""

import re
from typing import Dict, Optional, List
from concurrent.futures import ThreadPoolExecutor, as_completed
from services.llm_api import get_evaluator_llm
from core.evaluate.subjective_assessment.prompt import PROMPTS as SUBJECTIVE_PROMPTS

NUM_EVALUATORS = 5


class SubjectiveEvaluator:
    """基于 Rubric Format 模板的主观评估器"""

    def evaluate(
        self,
        rubric_content: str,
        test_context: str,
    ) -> Dict:
        """执行 Rubric 评估

        Args:
            rubric_content: 评分量表内容（如 Communication Empathy 的完整打分标准）
            test_context: 被评估的测试文本（如医患对话、病历正文等）

        Returns:
            {
                "score": 1-5 整数,
                "full_analysis": 完整评估分析文本,
                "raw_response": LLM 原始响应,
                "score_parsed": 是否成功解析出分数,
            }
        """
        if not rubric_content or not rubric_content.strip():
            raise ValueError("rubric_content 不能为空")
        if not test_context or not test_context.strip():
            raise ValueError("test_context 不能为空")

        # 构建 prompt：将 rubric 和 context 注入 Rubric Format 模板
        template = SUBJECTIVE_PROMPTS["Rubric Format"]
        user_prompt = template.replace("<RUBRIC_CONTENT>", rubric_content)
        user_prompt = user_prompt.replace("<TEST_CONTEXT>", test_context)

        # 调用评估 LLM
        evaluator_llm = get_evaluator_llm()
        raw_response = evaluator_llm.chat(user_prompt)

        # 解析分数
        score = self._parse_score(raw_response)

        return {
            "score": score,
            "full_analysis": raw_response,
            "raw_response": raw_response,
            "score_parsed": score is not None,
        }

    def _parse_score(self, response: str) -> Optional[int]:
        """从 LLM 响应中提取 [DECISION_START]X[DECISION_END] 中的分数"""
        match = re.search(r'\[DECISION_START\]\s*(\d)\s*\[DECISION_END\]', response)
        if match:
            score = int(match.group(1))
            if 1 <= score <= 5:
                return score
        return None

    @staticmethod
    def _evaluate_single(
        evaluator_id: int, rubric_content: str, test_context: str, user_prompt: str
    ) -> Dict:
        """单个评估器的评估（供并行调用）"""
        try:
            llm = get_evaluator_llm(evaluator_id=evaluator_id)
            raw_response = llm.chat(user_prompt)
            match = re.search(r'\[DECISION_START\]\s*(\d)\s*\[DECISION_END\]', raw_response)
            score = int(match.group(1)) if match and 1 <= int(match.group(1)) <= 5 else None
            return {
                "evaluator_id": evaluator_id,
                "score": score,
                "raw_response": raw_response,
                "score_parsed": score is not None,
            }
        except Exception as e:
            return {
                "evaluator_id": evaluator_id,
                "score": None,
                "raw_response": f"Error: {e}",
                "score_parsed": False,
                "error": str(e),
            }

    @staticmethod
    def evaluate_multi(
        rubric_content: str,
        test_context: str,
    ) -> Dict:
        """使用 5 个评估器并行评估，返回均值结果

        Args:
            rubric_content: 评分量表内容
            test_context: 被评估的测试文本

        Returns:
            {
                "score": float — 5 个评估器分数的均值（保留两位小数）,
                "scores": List[int] — 每个评估器的原始分数,
                "analyses": List[str] — 每个评估器的完整分析文本,
                "parsed_count": int — 成功解析出分数的评估器数量,
            }
        """
        if not rubric_content or not rubric_content.strip():
            raise ValueError("rubric_content 不能为空")
        if not test_context or not test_context.strip():
            raise ValueError("test_context 不能为空")

        template = SUBJECTIVE_PROMPTS["Rubric Format"]
        user_prompt = template.replace("<RUBRIC_CONTENT>", rubric_content)
        user_prompt = user_prompt.replace("<TEST_CONTEXT>", test_context)

        results: List[Dict] = []
        with ThreadPoolExecutor(max_workers=NUM_EVALUATORS) as executor:
            futures = {}
            for i in range(1, NUM_EVALUATORS + 1):
                fut = executor.submit(
                    SubjectiveEvaluator._evaluate_single, i, rubric_content, test_context, user_prompt
                )
                futures[fut] = i

            for fut in as_completed(futures):
                results.append(fut.result())

        # 按 evaluator_id 排序
        results.sort(key=lambda r: r["evaluator_id"])

        scores = [r["score"] for r in results]
        valid_scores = [s for s in scores if s is not None]
        avg_score = round(sum(valid_scores) / len(valid_scores), 2) if valid_scores else None

        return {
            "score": avg_score,
            "scores": scores,
            "analyses": [r.get("raw_response", "") for r in results],
            "parsed_count": len(valid_scores),
            "individual_results": results,
            "metadata": {"user_prompt": user_prompt},
        }
