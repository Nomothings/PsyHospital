"""SFT 数据解析工具

从拼接后的 instruction 中解耦出 Rubric 内容和 Test Context（对话轨迹）。
"""

# 精确边界字符串（与 prompt.py 中拼接方式严格对应）
_RUBRIC_START = '\n---\n## Rubric细则：\n'
_TEST_START = '\n---\n\n---\n## 评测输入：\n'
_TEST_END = '\n\n---\n\n你的任务是：基于 Rubric 进行评分分析，并在分析结束后输出最终等级： [DECISION_START]X[DECISION_END]\n'


def parse_instruction(instruction: str) -> dict:
    """将 SFT instruction 拆分为 rubric_content 和 test_context。

    instruction 的拼接结构：
        [通用评分原则]
        ---
        ## Rubric细则：
        <Rubric 具体评分标准>
        ---

        ---
        ## 评测输入：
        <对话轨迹/测试上下文>
        ---

        你的任务是：基于 Rubric 进行评分分析，并在分析结束后输出最终等级： [DECISION_START]X[DECISION_END]

    通过精确字符串匹配切割，返回解耦后的内容。

    Returns:
        {
            "rubric_content": str,   # Rubric 评分标准部分
            "test_context": str,     # 对话轨迹部分
        }
    """
    idx1 = instruction.find(_RUBRIC_START)
    idx2 = instruction.find(_TEST_START)
    idx3 = instruction.find(_TEST_END)

    if idx1 == -1 or idx2 == -1:
        raise ValueError(f"未找到边界标记: RUBRIC_START={idx1}, TEST_START={idx2}")

    rubric_content = instruction[idx1 + len(_RUBRIC_START):idx2]

    if idx3 != -1:
        test_context = instruction[idx2 + len(_TEST_START):idx3]
    else:
        # 兜底：取到末尾
        test_context = instruction[idx2 + len(_TEST_START):]

    return {
        "rubric_content": rubric_content,
        "test_context": test_context,
    }


def parse_sft_item(item: dict) -> dict:
    """解析单个 SFT 条目，返回解耦后的各部分。

    Args:
        item: {"instruction": str, "input": str, "output": str, "score": int}

    Returns:
        {
            "rubric_content": str,
            "test_context": str,
            "input": str,
            "output": str,
            "score": int,
        }
    """
    parsed = parse_instruction(item["instruction"])
    return {
        "rubric_content": parsed["rubric_content"],
        "test_context": parsed["test_context"],
        "input": item.get("input", ""),
        "output": item.get("output", ""),
        "score": item.get("score", 0),
    }


def batch_parse_sft(items: list) -> list:
    """批量解析 SFT 条目列表。"""
    return [parse_sft_item(item) for item in items]
