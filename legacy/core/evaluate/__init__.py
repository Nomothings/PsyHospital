"""
精神科访谈评估模块

包含各阶段的评估逻辑，与对话流程完全解耦。

使用方法:
    from core.evaluate import evaluate_phase1, evaluate_phase2, evaluate_phase3, evaluate_phase4, evaluate_phase5

    # 评估 Phase 1
    result1 = evaluate_phase1(model_name="qwen-flash", case_id="1009904")

    # 评估 Phase 2
    result2 = evaluate_phase2(model_name="qwen-flash", case_id="1009904", case_data=case_data)

    # 评估 Phase 3
    result3 = evaluate_phase3(model_name="qwen-flash", case_id="1009904")

    # 评估 Phase 4
    result4 = evaluate_phase4(model_name="qwen-flash", case_id="1009904")

    # 评估 Phase 5
    result5 = evaluate_phase5(model_name="qwen-flash", case_id="1009904")
"""

from core.evaluate.interview_phase1_eval import evaluate_phase1
from core.evaluate.interview_phase2_eval import evaluate_phase2
from core.evaluate.interview_phase3_eval import evaluate_phase3
from core.evaluate.interview_phase4_eval import evaluate_phase4
from core.evaluate.interview_phase5_eval import evaluate_phase5

__all__ = [
    "evaluate_phase1",
    "evaluate_phase2",
    "evaluate_phase3",
    "evaluate_phase4",
    "evaluate_phase5"
]
