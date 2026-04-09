"""
精神科访谈评估模块 - 第三阶段：Clinical Formulation Evaluation

使用方法:
    from core.evaluate.interview_phase3_eval import evaluate_phase3
    
    # 从interview_phase3的输出文件中读取数据并评估
    result = evaluate_phase3(
        model_name="qwen-flash",
        case_id="1009904"
    )
    
    # 或者直接传入数据
    result = evaluate_phase3(
        output_file="/path/to/interview_phase3_output.json"
    )
    
    # 结果包含:
    # - total_percentage: 总分百分比
    # - dimensions: 各维度评分详情
    # - output_file: 评估结果保存路径
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

from core.evaluate.interview_phase1_eval import (
    get_evaluation_dir,
    get_evaluation_output_file,
    save_evaluation_result
)

from core.evaluate.utils.phase3.rubrics import RUBRICS


class RubricLoader:
    """Rubric评分标准加载器 - 从rubrics.py加载"""

    def __init__(self):
        self.rubrics = RUBRICS

    def get_rubric(self, rubric_type: str) -> Dict:
        """获取指定类型的rubric"""
        return self.rubrics.get(rubric_type)

    def get_rubric_prompt(self, rubric_type: str) -> str:
        """生成用于LLM评分的rubric提示文本"""
        rubric = self.rubrics.get(rubric_type)
        if not rubric:
            return ""

        prompt = f"【{rubric['rubric_name']}】\n"
        prompt += f"权重: {rubric['weight'] * 100}%\n"
        if 'scoring_notes' in rubric:
            prompt += f"评分说明: {rubric['scoring_notes']}\n"
        prompt += "\n"

        for item in rubric.get('scoring_items', []):
            prompt += f"【评分项 {item['id']}】{item['element']}\n"
            prompt += f"描述: {item['description']}\n"
            prompt += "覆盖度评分 (0或1):\n"
            prompt += f"  1分: {item['coverage_definition']['1']}\n"
            prompt += f"  0分: {item['coverage_definition']['0']}\n"
            prompt += f"  跳过: {item['coverage_definition']['skip']}\n"
            prompt += "准确度评分 (0或1):\n"
            prompt += f"  1分: {item['accuracy_definition']['1']}\n"
            prompt += f"  0分: {item['accuracy_definition']['0']}\n"
            prompt += f"  跳过: {item['accuracy_definition']['skip']}\n\n"

        return prompt


def _dict_to_text(obj, indent=0) -> str:
    """将嵌套字典转换为可读文本"""
    if isinstance(obj, dict):
        lines = []
        for key, value in obj.items():
            if isinstance(value, (dict, list)):
                sub_text = _dict_to_text(value, indent + 1)
                lines.append(f"{key}：{sub_text}")
            else:
                lines.append(f"{key}：{value}")
        return "；".join(lines)
    elif isinstance(obj, list):
        return "、".join(str(item) for item in obj)
    else:
        return str(obj)


class LLMParser:
    """LLM病历划分器 - 使用LLM将病历字符串划分为四个区域"""

    def __init__(self, llm_service):
        self.llm = llm_service

    def parse(self, record_text: str) -> Dict:
        """使用LLM将病历字符串划分为四个区域"""
        prompt = f"""你是一位专业的精神科病历评审专家。请将以下精神科病历文本划分为四个区域，并以JSON格式返回。

病历文本:
{record_text}

【区域划分标准】

1. chief_complaint (主诉)
   - 定义：患者就诊的主要原因，简要概括核心症状及持续时间
   - 示例："敏感多疑3月余，加重3天"
   - 注意：主诉应简短精炼，不超过一句话

2. physical_examination (体格检查)
   - 定义：躯体各系统的客观检查结果
   - 包含：生命体征(T/P/R/BP)、一般情况、皮肤黏膜、头颈部、胸部/心肺、腹部、四肢/神经系统

3. mental_examination (精神检查)
   - 定义：精神科专用的精神状态评估
   - 包含：外观行为、言语、情感、感知觉、思维形式、思维内容、认知功能、自知力

4. past_family_history (既往史家族史)
   - 定义：患者的既往病史和个人背景信息
   - 包含：既往史、个人史(性格/职业/婚姻)、家族史、物质接触史

【划分注意事项】
- 主诉应简短，仅包含核心症状+时间
- "神志清醒"等一般情况属于体格检查，不属于精神检查
- 每个内容只归入一个区域

请严格按照以下JSON格式返回，每个字段的值为字符串类型:
{{
    "chief_complaint": "主诉内容",
    "physical_examination": "体格检查内容",
    "mental_examination": "精神检查内容",
    "past_family_history": "既往史家族史内容"
}}"""

        try:
            response = self.llm.chat(prompt)

            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            elif response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            response = response.strip()

            result = json.loads(response)

            default_result = {
                "chief_complaint": "",
                "physical_examination": "",
                "mental_examination": "",
                "past_family_history": ""
            }
            for key in default_result:
                if key not in result:
                    result[key] = ""
                elif isinstance(result[key], (dict, list)):
                    result[f"{key}_structured"] = result[key]
                    result[key] = _dict_to_text(result[key])

            return result

        except json.JSONDecodeError as e:
            print(f"JSON解析失败: {e}")
            return {
                "chief_complaint": "",
                "physical_examination": "",
                "mental_examination": "",
                "past_family_history": "",
                "parse_error": str(e)
            }
        except Exception as e:
            print(f"划分过程出错: {e}")
            return {
                "chief_complaint": "",
                "physical_examination": "",
                "mental_examination": "",
                "past_family_history": "",
                "parse_error": str(e)
            }


class LLMEvaluator:
    """LLM病历评分器 - 支持多线程并行评估"""

    def __init__(self, llm_service, rubric_loader: RubricLoader):
        self.llm = llm_service
        self.rubric_loader = rubric_loader
        self._lock = threading.Lock()

    def _build_evaluation_prompt(self, rubric_type: str, generated_text: str, true_text: str) -> str:
        """构建评分提示词"""
        rubric = self.rubric_loader.get_rubric(rubric_type)
        rubric_prompt = self.rubric_loader.get_rubric_prompt(rubric_type)
        scoring_items = rubric.get('scoring_items', []) if rubric else []

        prompt = f"""你是一位专业的精神科病历评分专家。请根据以下评分标准，逐项对比标准病历(true)和生成病历(test)。

{rubric_prompt}

=== 标准病历(true) ===
{true_text if true_text else "(空白)"}

=== 待评分的生成病历(test) ===
{generated_text if generated_text else "(空白)"}

=== 评分要求 ===
1. 对每个评分项，先判断true中是否包含该要素
2. 如果true中没有该要素，标记为"skip"，该项不计分
3. 如果true中有该要素，则评估test的覆盖度和准确度
4. 覆盖度：test是否包含true中的该要素（0或1）
5. 准确度：test的描述是否与true一致（0或1）

请以JSON格式返回评分结果，格式如下：
{{
    "scoring_results": [
        {{
            "id": 评分项编号,
            "element": "要素名称",
            "true_has_element": true或false（标准病历是否包含该要素）,
            "coverage_score": 0或1或"skip",
            "accuracy_score": 0或1或"skip",
            "coverage_reasoning": "覆盖度评分理由",
            "accuracy_reasoning": "准确度评分理由"
        }}
    ],
    "total_score": 总得分（所有非skip项的覆盖度+准确度之和）,
    "max_score": 满分（所有非skip项的总数乘以2）,
    "coverage_total": 覆盖度总得分,
    "accuracy_total": 准确度总得分,
    "summary": "整体评价摘要"
}}

请只返回JSON结果，不要返回其他内容。"""

        return prompt

    def evaluate_dimension(self, rubric_type: str, generated_text: str, true_text: str) -> Dict:
        """对单个维度进行评分"""
        prompt = self._build_evaluation_prompt(rubric_type, generated_text, true_text)
        rubric = self.rubric_loader.get_rubric(rubric_type)
        scoring_items = rubric.get('scoring_items', []) if rubric else []

        try:
            response = self.llm.chat(prompt)

            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            elif response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            response = response.strip()

            result = json.loads(response)

            total_score = result.get("total_score", 0)
            max_score = result.get("max_score", 0)
            if max_score > 0:
                result["percentage"] = round(total_score / max_score * 100, 2)
            else:
                result["percentage"] = 0

            result["coverage_percentage"] = round(result.get("coverage_total", 0) / (max_score / 2) * 100, 2) if max_score > 0 else 0
            result["accuracy_percentage"] = round(result.get("accuracy_total", 0) / (max_score / 2) * 100, 2) if max_score > 0 else 0

            return result

        except json.JSONDecodeError as e:
            default_results = []
            for item in scoring_items:
                default_results.append({
                    "id": item.get('id', 0),
                    "element": item.get('element', ''),
                    "true_has_element": False,
                    "coverage_score": "skip",
                    "accuracy_score": "skip",
                    "coverage_reasoning": f"评分解析失败: {str(e)}",
                    "accuracy_reasoning": f"评分解析失败: {str(e)}"
                })
            return {
                "scoring_results": default_results,
                "total_score": 0,
                "max_score": 0,
                "percentage": 0,
                "coverage_percentage": 0,
                "accuracy_percentage": 0,
                "summary": f"评分解析失败: {str(e)}",
                "error": str(e)
            }
        except Exception as e:
            default_results = []
            for item in scoring_items:
                default_results.append({
                    "id": item.get('id', 0),
                    "element": item.get('element', ''),
                    "true_has_element": False,
                    "coverage_score": "skip",
                    "accuracy_score": "skip",
                    "coverage_reasoning": f"评分过程出错: {str(e)}",
                    "accuracy_reasoning": f"评分过程出错: {str(e)}"
                })
            return {
                "scoring_results": default_results,
                "total_score": 0,
                "max_score": 0,
                "percentage": 0,
                "coverage_percentage": 0,
                "accuracy_percentage": 0,
                "summary": f"评分过程出错: {str(e)}",
                "error": str(e)
            }

    def _evaluate_dimension_with_info(self, record_key: str, rubric_type: str, 
                                       generated_text: str, true_text: str) -> tuple:
        """评估单个维度并返回带key的结果（用于多线程）"""
        rubric = self.rubric_loader.get_rubric(rubric_type)
        weight = rubric['weight'] if rubric else 0
        
        eval_result = self.evaluate_dimension(rubric_type, generated_text, true_text)
        
        actual_score = eval_result.get("total_score", 0)
        actual_max = eval_result.get("max_score", 0)

        if actual_max > 0:
            percentage_score = actual_score / actual_max
        else:
            percentage_score = 0

        weighted_score = round(percentage_score * weight, 4)
        
        eval_result["dimension_weight"] = weight
        eval_result["weighted_score"] = weighted_score
        
        return record_key, eval_result, actual_score, actual_max, weighted_score

    def evaluate_record_parallel(self, generated_record: Dict, true_record: Dict) -> Dict:
        """对完整病历进行四维度并行评分"""
        results = {
            "generated_record": generated_record,
            "true_record": true_record,
            "dimensions": {}
        }

        dimensions = [
            ("chief_complaint", "chief_complaint"),
            ("physical_examination", "physical_examination"),
            ("mental_examination", "mental_examination"),
            ("past_family_history", "past_family_history")
        ]

        total_weighted_score = 0.0
        total_actual_score = 0
        total_actual_max = 0

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {}
            
            for record_key, rubric_type in dimensions:
                generated_text = generated_record.get(record_key, "")
                true_text = true_record.get(record_key, "")
                
                future = executor.submit(
                    self._evaluate_dimension_with_info,
                    record_key, rubric_type, generated_text, true_text
                )
                futures[future] = record_key
            
            for future in as_completed(futures):
                record_key, eval_result, actual_score, actual_max, weighted_score = future.result()
                
                with self._lock:
                    results["dimensions"][record_key] = eval_result
                    total_actual_score += actual_score
                    total_actual_max += actual_max
                    total_weighted_score += weighted_score

        results["total_weighted_score"] = round(total_weighted_score, 4)
        results["total_percentage"] = round(total_weighted_score * 100, 2)
        results["total_actual_score"] = total_actual_score
        results["total_actual_max"] = total_actual_max

        return results


def load_ground_truth(case_id: str) -> Optional[str]:
    """从ground_truth.jsonl加载真值病历
    
    Args:
        case_id: 病例ID
        
    Returns:
        真值病历字符串，如果未找到返回None
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
                    return data.get("realFormulation", "")
            except json.JSONDecodeError:
                continue
    
    return None


def evaluate_phase3(
    model_name: str = None,
    case_id: str = None,
    output_file: Union[str, Path] = None,
    phase3_data: Dict[str, Any] = None,
    true_formulation: str = None
) -> Dict[str, Any]:
    """评估第三阶段访谈
    
    可以通过以下方式之一提供数据：
    1. 提供 model_name 和 case_id（从默认路径读取）
    2. 提供 output_file（直接读取指定文件）
    3. 提供 phase3_data（直接使用数据）
    
    Args:
        model_name: 医生模型名称
        case_id: 病例ID
        output_file: interview_phase3输出文件路径
        phase3_data: interview_phase3数据字典
        true_formulation: 真值病历（可选，如不提供则从ground_truth.jsonl加载）
        
    Returns:
        评估结果字典，包含：
        - total_percentage: 总分百分比
        - dimensions: 各维度评分详情
        - output_file: 评估结果保存路径
    """
    if phase3_data is None:
        if output_file is None:
            if model_name is None or case_id is None:
                raise ValueError("必须提供 model_name+case_id 或 output_file 或 phase3_data")
            from core.output_manager import get_phase_output_file
            output_file = get_phase_output_file(model_name, case_id, 3)
        
        output_file = Path(output_file)
        with open(output_file, "r", encoding="utf-8") as f:
            phase3_data = json.load(f)
    
    model_name = phase3_data.get("model_name", model_name)
    case_id = phase3_data.get("case_id", case_id)
    
    if model_name is None or case_id is None:
        raise ValueError("无法确定 model_name 或 case_id")
    
    syntactic_formulation = phase3_data.get('syntactic_formulation', '')
    status = phase3_data.get('status', 'unknown')
    
    if true_formulation is None:
        true_formulation = load_ground_truth(case_id)
    
    if not syntactic_formulation or not true_formulation:
        evaluation_data = {
            "total_percentage": 0,
            "status": status,
            "syntactic_formulation": syntactic_formulation,
            "true_formulation": true_formulation,
            "error": "缺少生成病历或真值病历",
            "dimensions": {}
        }
        eval_output_file = save_evaluation_result(model_name, case_id, 3, evaluation_data)
        
        print(f"\nPhase 3 评估结果:")
        print(f"  状态: {status}")
        print(f"  评分: 0% (缺少必要数据)")
        print(f"  评估结果保存: {eval_output_file}")
        
        return {
            "total_percentage": 0,
            "status": status,
            "output_file": str(eval_output_file),
            "model_name": model_name,
            "case_id": case_id,
            "error": "缺少生成病历或真值病历"
        }
    
    from services.llm_api import LLMService
    
    print(f"\n正在初始化评估器...")
    evaluator_llm = LLMService(role="evaluator")
    
    rubric_loader = RubricLoader()
    parser = LLMParser(evaluator_llm)
    evaluator = LLMEvaluator(evaluator_llm, rubric_loader)
    
    print(f"正在划分生成病历...")
    generated_record = parser.parse(syntactic_formulation)
    
    print(f"正在划分标准病历...")
    true_record = parser.parse(true_formulation)
    
    print(f"正在进行并行评分（4个维度同时评估）...")
    eval_result = evaluator.evaluate_record_parallel(generated_record, true_record)
    
    evaluation_data = {
        "total_percentage": eval_result.get("total_percentage", 0),
        "total_weighted_score": eval_result.get("total_weighted_score", 0),
        "total_actual_score": eval_result.get("total_actual_score", 0),
        "total_actual_max": eval_result.get("total_actual_max", 0),
        "status": status,
        "syntactic_formulation": syntactic_formulation,
        "true_formulation": true_formulation,
        "generated_record": generated_record,
        "true_record": true_record,
        "dimensions": eval_result.get("dimensions", {})
    }
    
    eval_output_file = save_evaluation_result(model_name, case_id, 3, evaluation_data)
    
    print(f"\nPhase 3 评估结果:")
    print(f"  状态: {status}")
    print(f"  总分: {eval_result.get('total_percentage', 0)}%")
    print(f"  加权得分: {eval_result.get('total_weighted_score', 0)}")
    
    if 'dimensions' in eval_result:
        for dim_name, dim_data in eval_result['dimensions'].items():
            weighted_score = dim_data.get('weighted_score', 0)
            weight = dim_data.get('dimension_weight', 0)
            percentage = dim_data.get('percentage', 0)
            print(f"  {dim_name}: {percentage}% (权重{weight*100}%)")
    
    print(f"  评估结果保存: {eval_output_file}")
    
    return {
        "total_percentage": eval_result.get("total_percentage", 0),
        "total_weighted_score": eval_result.get("total_weighted_score", 0),
        "dimensions": eval_result.get("dimensions", {}),
        "status": status,
        "output_file": str(eval_output_file),
        "model_name": model_name,
        "case_id": case_id
    }


if __name__ == "__main__":
    print("=" * 60)
    print("测试：Phase 3 评估模块")
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
                    
                    result = evaluate_phase3(model_name=model_name, case_id=case_id)
                    
                    print("\n" + "=" * 60)
                    print("测试完成")
                    print("=" * 60)
                else:
                    print("未找到病例数据，请先运行 interview_phase3")
            else:
                print("未找到模型数据，请先运行 interview_phase3")
        else:
            print("输出目录不存在，请先运行 interview_phase3")
            
    except Exception as e:
        print(f"发生错误: {e}")
        import traceback
        traceback.print_exc()
