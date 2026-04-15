"""
精神科AI问诊系统 - Flask Web API

提供前端所需的REST API接口。
采用分层架构：routes -> services -> repositories

启动方式:
    python web/app.py

访问:
    http://localhost:5000
"""
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from flask import Flask, jsonify, render_template, request

# Add project root to path so we can import patient agent
PROJECT_ROOT = Path(__file__).parent.parent
import sys
sys.path.insert(0, str(PROJECT_ROOT))

# Add web directory to path for web-specific modules
WEB_DIR = Path(__file__).parent
sys.path.insert(0, str(WEB_DIR))

# ============================================================
# 路径配置
# ============================================================

PROJECT_ROOT = Path(__file__).parent.parent
BASE_DIR = PROJECT_ROOT
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = DATA_DIR / "output"
INTERVIEW_DIR = OUTPUT_DIR / "interview"
EVALUATION_DIR = OUTPUT_DIR / "evaluation"

# Web 应用数据目录
WEB_DATA_DIR = Path(__file__).parent / "data"
WEB_DATA_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR = WEB_DATA_DIR / "logs"
RECORDS_DIR = WEB_DATA_DIR / "records"
DIAGNOSES_DIR = WEB_DATA_DIR / "diagnoses"
HISTORY_DIR = WEB_DATA_DIR / "history"
HISTORY_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# 初始化日志
# ============================================================

from service_layer.logging_config import setup_logging
setup_logging(LOG_DIR, level="INFO")

import logging
logger = logging.getLogger(__name__)

# ============================================================
# 初始化服务层
# ============================================================

from service_layer.case_service import CaseService
from service_layer.record_service import RecordService
from service_layer.diagnosis_service import DiagnosisService

case_service = CaseService(DATA_DIR)
record_service = RecordService(RECORDS_DIR)
diagnosis_service = DiagnosisService(DIAGNOSES_DIR)

# ============================================================
# 初始化路由层
# ============================================================

from routes.case_routes import register_case_routes
from routes.record_routes import register_record_routes
from routes.diagnosis_routes import register_diagnosis_routes
from routes.chat_routes import register_chat_routes
from routes.check_routes import register_check_routes
from routes.case_writing_routes import register_case_writing_routes
from routes.treatment_routes import register_treatment_routes

# ============================================================
# Flask 应用
# ============================================================

app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(__file__), "templates"),
    static_folder=os.path.join(os.path.dirname(__file__), "static"),
)

# 注册 Blueprint 路由（每个 Blueprint 独立 url_prefix，互不干扰）
app.register_blueprint(register_case_routes(case_service))
app.register_blueprint(register_record_routes(record_service))
app.register_blueprint(register_diagnosis_routes(diagnosis_service))
app.register_blueprint(register_chat_routes(case_service))
app.register_blueprint(register_check_routes(case_service))
app.register_blueprint(register_case_writing_routes(record_service))
app.register_blueprint(register_treatment_routes(record_service))

# ============================================================
# 页面路由
# ============================================================

@app.route("/")
def index():
    """渲染主页面"""
    return render_template("index.html")


# ============================================================
# API 路由 — 兼容旧接口（供 Phase View 等页面使用）
# ============================================================

def _read_json_safe(filepath):
    """安全读取 JSON 文件，失败返回 None"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"读取文件 {filepath} 失败: {e}")
        return None


@app.route("/api/cases")
def api_cases():
    """获取所有病例列表"""
    cases = case_service.get_all_cases()
    return jsonify({"cases": cases, "total": len(cases)})


@app.route("/api/models")
def api_models():
    """获取已有输出结果的模型列表"""
    if not INTERVIEW_DIR.exists():
        return jsonify({"models": [], "total": 0})
    models = sorted([d.name for d in INTERVIEW_DIR.iterdir() if d.is_dir()])
    return jsonify({"models": models, "total": len(models)})


@app.route("/api/models/<model_name>/cases")
def api_model_cases(model_name):
    """获取指定模型下已有结果的病例ID"""
    model_dir = INTERVIEW_DIR / model_name
    if not model_dir.exists():
        return jsonify({"model": model_name, "cases": [], "total": 0})
    case_ids = sorted([d.name for d in model_dir.iterdir() if d.is_dir()])
    return jsonify({"model": model_name, "cases": case_ids, "total": len(case_ids)})


@app.route("/api/case/<case_id>/info")
def api_case_info(case_id):
    """获取病例基本信息"""
    case = case_service.get_case(case_id)
    if not case:
        return jsonify({"error": "Case not found"}), 404
    return jsonify(case)


@app.route("/api/case/<case_id>/summary/<model_name>")
def api_case_summary(case_id, model_name):
    """获取完整流程摘要"""
    summary_file = INTERVIEW_DIR / model_name / case_id / "interview_summary.json"
    data = _read_json_safe(summary_file)
    if data is None:
        return jsonify({"error": "Summary not found"}), 404
    return jsonify(data)


@app.route("/api/case/<case_id>/phase/<int:phase>/<model_name>")
def api_phase(case_id, phase, model_name):
    """获取单个阶段的输出 + 评估结果"""
    interview_file = INTERVIEW_DIR / model_name / case_id / f"interview_phase{phase}_output.json"
    eval_file = EVALUATION_DIR / model_name / case_id / f"evaluation_phase{phase}_output.json"

    result = {"phase": phase, "case_id": case_id, "model_name": model_name}

    interview_data = _read_json_safe(interview_file)
    result["interview"] = interview_data

    eval_data = _read_json_safe(eval_file)
    result["evaluation"] = eval_data

    return jsonify(result)


@app.route("/api/ground_truth/<case_id>")
def api_ground_truth(case_id):
    """获取指定病例的ground truth"""
    ground_truth_file = DATA_DIR / "ground_truth.jsonl"
    if not ground_truth_file.exists():
        return jsonify({"error": "Ground truth file not found"}), 404
    try:
        with open(ground_truth_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        data = json.loads(line)
                        if data.get("id") == case_id:
                            return jsonify(data)
                    except json.JSONDecodeError:
                        continue
    except Exception as e:
        logger.error(f"读取 ground truth 失败: {e}")
    return jsonify({"error": "Case not found in ground truth"}), 404


# ============================================================
# 历史记录 API — 读取真实问诊记录 (records/)
# ============================================================

@app.route("/api/history/list")
def api_history_list():
    """列出所有问诊历史记录（从 records 目录读取真实数据）"""
    histories = []
    for f in sorted(RECORDS_DIR.glob("*.json")):
        try:
            with open(f, "r", encoding="utf-8") as fp:
                data = json.load(fp)
            conversation = data.get("conversation", [])
            turns = len(conversation) // 2 if conversation else 0
            # 提取患者基本信息
            case_info = data.get("caseInfo", {})
            basic_info = case_info.get("basicInfomation", "")
            has_diagnosis = bool(data.get("diagnosis"))
            record_id = f.stem  # 文件名即 record_id
            # 提取原始 case_id（新格式：{case_id}_{YYYYMMDD}_{HHMMSS}）
            raw_case_id = data.get("original_case_id") or data.get("case_id", f.stem)
            histories.append({
                "record_id": record_id,
                "case_id": raw_case_id,
                "saved_at": data.get("updated_at") or data.get("created_at", ""),
                "created_at": data.get("created_at", ""),
                "turns": turns,
                "has_diagnosis": has_diagnosis,
                "basic_info": basic_info,
            })
        except Exception as e:
            logger.warning(f"读取记录文件 {f} 失败: {e}")
    return jsonify({"histories": histories, "total": len(histories)})


@app.route("/api/history/<record_id>")
def api_history_detail(record_id):
    """查看单条问诊历史详情（从 records 读取完整问诊数据）"""
    if not re.match(r'^[a-zA-Z0-9_\-\.]+$', record_id):
        return jsonify({"error": "Invalid record_id"}), 400

    record_file = RECORDS_DIR / f"{record_id}.json"
    if not record_file.exists():
        return jsonify({"error": "History not found"}), 404
    data = _read_json_safe(record_file)
    if data is None:
        return jsonify({"error": "Failed to read history"}), 500
    # 适配前端字段：messages 对应 conversation
    data["messages"] = data.get("conversation", [])
    return jsonify(data)


@app.route("/api/history/<record_id>", methods=["DELETE"])
def api_history_delete(record_id):
    """删除单条问诊历史"""
    if not re.match(r'^[a-zA-Z0-9_\-\.]+$', record_id):
        return jsonify({"error": "Invalid record_id"}), 400

    record_file = RECORDS_DIR / f"{record_id}.json"
    if not record_file.exists():
        return jsonify({"error": "History not found"}), 404
    try:
        record_file.unlink()
        logger.info(f"问诊历史已删除: {record_id}")
        return jsonify({"status": "ok"})
    except Exception as e:
        logger.error(f"删除问诊历史失败: {e}")
        return jsonify({"error": str(e)}), 500


# ============================================================
# 阶段评价 API — 调用 core.evaluate 模块
# ============================================================

@app.route("/api/evaluate/<int:phase>", methods=["POST"])
def api_evaluate(phase):
    """对当前问诊会话进行阶段评价。

    Request body:
        case_id: str
        messages: list of {role, content}  (Phase 1 必需)
        exam_results: dict  (Phase 2 可选)
        case_form: dict  (Phase 3 可选)
        diagnosis: dict  (Phase 3 可选)
        treatment: dict  (Phase 4 可选)
    """
    try:
        body = request.get_json()
        case_id = body.get("case_id", "")

        if not case_id:
            return jsonify({"error": "缺少 case_id"}), 400

        evaluator_fns = {
            1: _evaluate_phase1_live,
            2: _evaluate_phase2_live,
            3: _evaluate_phase3_live,
            4: _evaluate_phase4_live,
        }
        fn = evaluator_fns.get(phase)
        if fn is None:
            return jsonify({"error": f"不支持的阶段编号: {phase}"}), 400

        result = fn(case_id, body)
        return jsonify(result)

    except Exception as e:
        logger.error(f"评价阶段 {phase} 失败: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


def _format_conversation(messages):
    """将前端消息格式转换为评估模块格式"""
    lines = []
    for idx, turn in enumerate(messages, 1):
        role = turn.get("role", "unknown")
        content = turn.get("content", "")
        label = {"doctor": "医生", "patient": "患者"}.get(role, role)
        lines.append(f"[第{idx}轮] {label}：{content}")
    return "\n\n".join(lines)


def _evaluate_phase1_live(case_id, body):
    """Phase 1 实时评估 — 基于对话统计和 LLM 评估"""
    from core.evaluate.utils.phase1 import evaluate_empathy, evaluate_profession

    messages = body.get("messages", [])
    conversation_stats = {
        "total_turns": len([m for m in messages if m["role"] == "patient"]),
        "doctor_turns": len([m for m in messages if m["role"] == "doctor"]),
        "patient_turns": len([m for m in messages if m["role"] == "patient"]),
        "conversation_length": len(messages),
    }

    conversation_text = _format_conversation(messages)

    empathy_result = None
    profession_result = None
    try:
        empathy_result = evaluate_empathy(conversation_text)
    except Exception as e:
        logger.warning(f"共情度评估失败: {e}")
    try:
        profession_result = evaluate_profession(conversation_text)
    except Exception as e:
        logger.warning(f"专业度评估失败: {e}")

    result = {
        "phase": 1,
        "case_id": case_id,
        "phase_name": "病史采集",
        "conversation_stats": conversation_stats,
    }
    if empathy_result:
        result["empathy_evaluation"] = {
            "empathy_level": empathy_result.get("empathy_level"),
            "why_this_level": empathy_result.get("why_this_level", ""),
            "evidence": empathy_result.get("evidence", ""),
            "level_count": empathy_result.get("level_count", 0),
        }
    if profession_result:
        result["profession_evaluation"] = {
            "total_score": profession_result.get("total_score", 0),
            "average_score": profession_result.get("average_score", 0),
            "question_count": profession_result.get("question_count", 0),
        }
    return result


def _evaluate_phase2_live(case_id, body):
    """Phase 2 实时评估 — 检查选择评价"""
    exam_results = body.get("exam_results", {})

    # 统计检查数据
    total_examined = len(exam_results)
    positive_count = sum(1 for v in exam_results.values() if v and v != "无")
    negative_count = sum(1 for v in exam_results.values() if not v or v == "无")

    # 尝试使用核心评价器计算指标
    metrics = {}
    try:
        from core.evaluate.interview_phase2_eval import calculate_examination_metrics

        case_data = case_service.get_case_for_interview(case_id)
        if case_data:
            gold_exams = case_data.get("auxiliaryExamination", {})
            if gold_exams and exam_results:
                import json
                exam_query = json.dumps(list(exam_results.keys()), ensure_ascii=False)
                gold_str = json.dumps(gold_exams, ensure_ascii=False)
                exam_results_str = json.dumps(exam_results, ensure_ascii=False)

                result = calculate_examination_metrics(
                    response=exam_results_str,
                    examination_query=exam_query,
                    auxiliary_examinations=gold_str,
                )
                metrics = result.get("metrics", {})
    except Exception as e:
        logger.warning(f"Phase 2 核心评价器调用失败: {e}")

    return {
        "phase": 2,
        "case_id": case_id,
        "phase_name": "检查选择",
        "exam_stats": {
            "total_examined": total_examined,
            "positive_results": positive_count,
            "negative_results": negative_count,
        },
        "metrics": metrics if metrics else None,
    }


@app.route("/api/evaluate/phase2-accuracy", methods=["POST"])
def api_evaluate_phase2_accuracy():
    """Phase 2 检查选择 — 仅返回正确率（Precision）。

    Request body:
        case_id: str
        exam_results: dict  { "检查名": "结果" | "无" }
    """
    try:
        body = request.get_json()
        case_id = body.get("case_id", "")
        exam_results = body.get("exam_results", {})

        logger.info(f"[Phase2Accuracy] case_id={case_id}, exam_results_keys={list(exam_results.keys())}")

        if not case_id:
            return jsonify({"error": "缺少 case_id"}), 400

        accuracy = 0.0
        try:
            case_data = case_service.get_case_for_interview(case_id)
            if case_data:
                gold_exams = case_data.get("auxiliaryExamination", {})
                logger.info(f"[Phase2Accuracy] gold_exams_keys={list(gold_exams.keys())}")
                if gold_exams and exam_results:
                    exam_query = json.dumps(list(exam_results.keys()), ensure_ascii=False)
                    gold_str = json.dumps(gold_exams, ensure_ascii=False)
                    exam_results_str = json.dumps(exam_results, ensure_ascii=False)

                    from core.evaluate.interview_phase2_eval import calculate_examination_metrics
                    result = calculate_examination_metrics(
                        response=exam_results_str,
                        examination_query=exam_query,
                        auxiliary_examinations=gold_str,
                    )
                    accuracy = result.get("metrics", {}).get("recall", 0.0)
                    logger.info(f"[Phase2Accuracy] calculated accuracy={accuracy}")
                else:
                    logger.warning(f"[Phase2Accuracy] gold_exams empty={not gold_exams}, exam_results empty={not exam_results}")
            else:
                logger.warning(f"[Phase2Accuracy] case_data is None for case_id={case_id}")
        except Exception as e:
            logger.warning(f"Phase 2 正确率计算失败: {e}")

        logger.info(f"[Phase2Accuracy] returning accuracy={accuracy}")
        return jsonify({"accuracy": round(accuracy, 4)})

    except Exception as e:
        logger.error(f"Phase 2 正确率接口异常: {e}")
        return jsonify({"error": str(e)}), 500


def _evaluate_phase3_live(case_id, body):
    """Phase 3 实时评估 — 病历书写 + 诊断评价

    病历书写：使用 core.evaluate.interview_phase3_eval 的 LLMParser + LLMEvaluator（LLM rubric评分）
    诊断评价：使用 core.evaluate.interview_phase4_eval.calculate_category_metrics（统计计算）
    """
    case_form = body.get("case_form", {})
    diagnosis = body.get("diagnosis", {})

    # ===== 第一部分：病历书写 LLM 评价（50%） =====
    case_writing_eval = _evaluate_case_writing_llm(case_id, case_form)

    # ===== 第二部分：诊断评价（50%） =====
    diagnosis_eval = _evaluate_diagnosis_core(case_id, diagnosis)

    # ===== 综合评分 =====
    writing_score = case_writing_eval.get("total_percentage", 0) / 100.0
    diagnosis_score = diagnosis_eval.get("total_score", 0)
    overall_score = round((writing_score * 0.5 + diagnosis_score * 0.5), 2)

    return {
        "phase": 3,
        "case_id": case_id,
        "phase_name": "病历书写与诊断",
        "overall_score": overall_score,
        "case_writing": case_writing_eval,
        "diagnosis": diagnosis_eval,
    }


def _load_ground_truth(case_id):
    """从 ground_truth.jsonl 加载指定病例的真实诊断"""
    gt_file = DATA_DIR / "ground_truth.jsonl"
    if not gt_file.exists():
        return None
    try:
        with open(gt_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        data = json.loads(line)
                        if data.get("id") == case_id:
                            return data
                    except json.JSONDecodeError:
                        continue
    except Exception as e:
        logger.warning(f"读取 ground truth 失败: {e}")
    return None


def _evaluate_case_writing_llm(case_id, case_form):
    """使用核心后端 LLM 评价器进行病历书写评分

    直接构造 generated_record（用户表单字段）和 true_record（LLMParser 解析 gold），
    然后调用 LLMEvaluator.evaluate_record_parallel 进行 4 维度并行评分。
    """
    from services.llm_api import LLMService
    from core.evaluate.interview_phase3_eval import (
        RubricLoader, LLMParser, LLMEvaluator, load_ground_truth
    )

    case_data = case_service.get_case_for_interview(case_id)
    if not case_data:
        return {
            "total_percentage": 0,
            "total_score": 0,
            "dimensions": {},
            "warning": "无法获取病例数据",
        }

    # 构造 generated_record（从用户表单字段）
    generated_record = {
        "chief_complaint": (case_form.get("chiefComplaint") or "").strip(),
        "physical_examination": (case_form.get("physicalExam") or "").strip(),
        "mental_examination": (case_form.get("mentalExam") or "").strip(),
        "past_family_history": (
            "既往史：" + (case_form.get("pastHistory") or "").strip()
            + "；家族史：" + (case_form.get("familyHistory") or "").strip()
        ),
    }

    # 加载 ground truth 的 realFormulation
    true_formulation = load_ground_truth(case_id)
    if not true_formulation:
        # 回退：用病例数据构造 true_record
        true_record = {
            "chief_complaint": " ".join(case_data.get("chiefComplaint", [])),
            "physical_examination": case_data.get("physicalExamination", ""),
            "mental_examination": " ".join(case_data.get("mentalStatus", [])),
            "past_family_history": case_data.get("basicInfomation", ""),
        }
        return {
            "total_percentage": 0,
            "total_score": 0,
            "dimensions": {},
            "warning": "未找到 ground truth 中的 realFormulation",
            "true_record": true_record,
        }

    try:
        # 初始化 LLM 评价器
        evaluator_llm = LLMService(role="evaluator")
        rubric_loader = RubricLoader()
        parser = LLMParser(evaluator_llm)
        evaluator = LLMEvaluator(evaluator_llm, rubric_loader)

        # 解析标准病历（只需要调用一次 LLMParser）
        logger.info(f"[Phase3-CaseWriting] 正在解析标准病历 realFormulation...")
        true_record = parser.parse(true_formulation)

        # 4 维度并行评分
        logger.info(f"[Phase3-CaseWriting] 正在进行 4 维度并行 LLM 评分...")
        eval_result = evaluator.evaluate_record_parallel(generated_record, true_record)

        return {
            "total_percentage": eval_result.get("total_percentage", 0),
            "total_score": round(eval_result.get("total_percentage", 0) / 100, 2),
            "total_weighted_score": eval_result.get("total_weighted_score", 0),
            "total_actual_score": eval_result.get("total_actual_score", 0),
            "total_actual_max": eval_result.get("total_actual_max", 0),
            "dimensions": _format_case_writing_dimensions(eval_result.get("dimensions", {})),
            "true_record": true_record,
        }

    except Exception as e:
        logger.error(f"[Phase3-CaseWriting] LLM 评价失败: {e}")
        import traceback
        traceback.print_exc()
        # 回退到简易评分
        return _evaluate_case_writing_fallback(case_id, case_form, case_data)


def _format_case_writing_dimensions(dimensions):
    """将 LLMEvaluator 返回的维度格式化为前端可展示的格式"""
    result = {}
    name_map = {
        "chief_complaint": "主诉",
        "physical_examination": "体格检查",
        "mental_examination": "精神检查",
        "past_family_history": "既往史与家族史",
    }

    for key, dim_data in dimensions.items():
        percentage = dim_data.get("percentage", 0)
        weighted = dim_data.get("weighted_score", 0)
        coverage_pct = dim_data.get("coverage_percentage", 0)
        accuracy_pct = dim_data.get("accuracy_percentage", 0)

        # 提取各评分项的摘要
        scoring_results = dim_data.get("scoring_results", [])
        total_items = len(scoring_results)
        scored_items = sum(
            1 for r in scoring_results
            if r.get("coverage_score") not in ("skip", None)
            and r.get("accuracy_score") not in ("skip", None)
        )

        result[key] = {
            "section_name": name_map.get(key, key),
            "score": round(percentage / 100, 2) if percentage else 0,
            "percentage": percentage,
            "coverage_percentage": coverage_pct,
            "accuracy_percentage": accuracy_pct,
            "weighted_score": weighted,
            "detail": f"覆盖度 {coverage_pct:.0f}%，准确度 {accuracy_pct:.0f}%，{scored_items}/{total_items} 个评分项有效",
            "scoring_results": scoring_results,
        }

    return result


def _evaluate_case_writing_fallback(case_id, case_form, case_data):
    """LLM 评价失败时的回退：简易关键词匹配评分"""
    sections = {}

    # 主诉
    user_chief = (case_form.get("chiefComplaint") or "").strip()
    gold_chief = " ".join(case_data.get("chiefComplaint", []))
    if user_chief and gold_chief:
        gold_keywords = _extract_keywords(gold_chief)
        if gold_keywords:
            matched = sum(1 for kw in gold_keywords if kw in user_chief)
            score = round(matched / len(gold_keywords), 2)
        else:
            score = 0.5
        sections["chief_complaint"] = {
            "section_name": "主诉",
            "score": score,
            "detail": f"关键词覆盖 {matched}/{len(gold_keywords)}",
        }
    else:
        sections["chief_complaint"] = {"section_name": "主诉", "score": 0, "detail": "未填写"}

    # 体格检查
    user_physical = (case_form.get("physicalExam") or "").strip()
    gold_physical = case_data.get("physicalExamination", "")
    if user_physical and gold_physical:
        vital_signs = ["T", "P", "R", "BP", "体温", "脉搏", "呼吸", "血压"]
        found = sum(1 for v in vital_signs if v in user_physical)
        total = sum(1 for v in vital_signs if v in gold_physical)
        score = round(found / max(total, 1), 2) if total > 0 else 0.3
        sections["physical_examination"] = {
            "section_name": "体格检查",
            "score": score,
            "detail": f"生命体征覆盖 {found}/{total}",
        }
    else:
        sections["physical_examination"] = {"section_name": "体格检查", "score": 0, "detail": "未填写"}

    # 精神检查
    user_mental = (case_form.get("mentalExam") or "").strip()
    gold_mental = " ".join(case_data.get("mentalStatus", []))
    if user_mental and gold_mental:
        score = round(_text_overlap(user_mental, gold_mental), 2)
        sections["mental_examination"] = {
            "section_name": "精神检查",
            "score": score,
            "detail": f"文本相似度 {score:.0%}",
        }
    else:
        sections["mental_examination"] = {"section_name": "精神检查", "score": 0, "detail": "未填写"}

    # 既往史家族史
    user_past = (case_form.get("pastHistory") or "").strip()
    user_family = (case_form.get("familyHistory") or "").strip()
    past_score = 0.5 if user_past else 0
    family_score = 0.5 if user_family else 0
    sections["past_family_history"] = {
        "section_name": "既往史与家族史",
        "score": round((past_score + family_score) / 2, 2),
        "detail": f"既往史{'已填' if user_past else '未填'}，家族史{'已填' if user_family else '未填'}",
    }

    total_score = round(sum(s["score"] for s in sections.values()) / len(sections), 2)

    return {
        "total_percentage": round(total_score * 100, 2),
        "total_score": total_score,
        "dimensions": sections,
        "fallback": True,
    }


def _evaluate_diagnosis_core(case_id, diagnosis):
    """使用核心后端评价器进行诊断评价

    - 疾病类型：使用 interview_phase4_eval.calculate_category_metrics（Precision/Recall/F1/Jaccard）
    - 具体疾病：对比 realDisorder，计算 Recall（召回率）
    - 诊断理由：检查是否填写 + 是否包含关键术语
    """
    from core.evaluate.interview_phase4_eval import (
        calculate_category_metrics, load_real_categories
    )

    diagnoses_list = diagnosis.get("diagnoses", [])
    reason = (diagnosis.get("reason") or "").strip()

    # 提取用户选择的所有类别和疾病
    user_categories = []
    user_diseases = set()
    for cat in diagnoses_list:
        cat_name = cat.get("category", "")
        if cat_name:
            user_categories.append(cat_name)
        for dis in cat.get("diseases", []):
            user_diseases.add(dis)

    # === 1. 疾病类型评价（使用 calculate_category_metrics） ===
    true_categories = load_real_categories(case_id)
    if true_categories is None:
        true_categories = []

    category_metrics = calculate_category_metrics(user_categories, true_categories)

    # === 2. 具体疾病评价（对比 realDisorder） ===
    gt = _load_ground_truth(case_id)
    gt_disorders = set()
    if gt:
        gt_disorders = set(gt.get("realDisorder", []))

    if gt_disorders and user_diseases:
        matched = user_diseases & gt_disorders
        disorder_recall = len(matched) / len(gt_disorders)
        # FP 惩罚
        false_positives = user_diseases - gt_disorders
        if false_positives and disorder_recall > 0:
            penalty = len(false_positives) / len(user_diseases)
            disorder_recall = round(disorder_recall * (1 - penalty * 0.5), 4)
    elif gt_disorders:
        disorder_recall = 0.0
    else:
        disorder_recall = 0.5

    # === 3. 诊断理由评价 ===
    reason_score = 0.0
    reason_detail = ""
    if reason:
        reason_score = 0.6
        # 检查理由中是否包含关键诊断术语
        gt_terms = set()
        for dis in gt_disorders:
            parts = dis.split(" ", 1)
            if len(parts) > 1:
                gt_terms.add(parts[1].lower())
            gt_terms.add(parts[0].lower())
        reason_lower = reason.lower()
        matched_terms = sum(1 for t in gt_terms if t in reason_lower)
        if matched_terms > 0:
            reason_score = min(1.0, 0.6 + matched_terms * 0.1)
            reason_detail = f"包含 {matched_terms} 个关键诊断术语"
        else:
            reason_detail = "已填写但未包含关键术语"
    else:
        reason_detail = "未填写"

    # === 综合 ===
    total_score = round(
        category_metrics.get("recall", 0) * 0.35
        + disorder_recall * 0.45
        + reason_score * 0.2,
        2,
    )

    return {
        "total_score": total_score,
        "disease_type": {
            "score": category_metrics.get("recall", 0),
            "metrics": category_metrics,
            "predicted": user_categories,
            "true": true_categories,
            "detail": f"Recall {category_metrics.get('recall', 0):.0%}, Precision {category_metrics.get('precision', 0):.0%}, F1 {category_metrics.get('f1', 0):.0%}",
        },
        "diagnostic_correctness": {
            "score": disorder_recall,
            "detail": f"具体疾病 Recall {disorder_recall:.0%}" + (f"（{len(user_diseases & gt_disorders)}/{len(gt_disorders)} 项匹配）" if gt_disorders else ""),
        },
        "diagnostic_reasoning": {
            "score": reason_score,
            "detail": reason_detail,
        },
        "comprehensive": {
            "score": total_score,
            "detail": "类型权重 35%，正确性 45%，理由 20%",
        },
    }


def _extract_keywords(text):
    """从文本中提取关键词（简单分词）"""
    if not text:
        return []
    import re
    cn_words = re.findall(r'[\u4e00-\u9fff]{2,}', text)
    num_units = re.findall(r'\d+\s*[年月周天次小时]', text)
    return list(set(cn_words + num_units))


def _text_overlap(text1, text2):
    """计算两个文本的字符级 Jaccard 相似度"""
    if not text1 or not text2:
        return 0.0
    set1 = set(text1)
    set2 = set(text2)
    intersection = set1 & set2
    union = set1 | set2
    if not union:
        return 0.0
    return len(intersection) / len(union)


def _evaluate_phase4_live(case_id, body):
    """Phase 4 实时评估 — 诊疗方案评价"""
    treatment = body.get("treatment", {})

    # 统计治疗方案填写情况
    treatment_categories = [
        "药物治疗", "心理治疗", "神经调控与其他躯体治疗",
        "社会心理干预与康复治疗", "辅助治疗",
    ]
    filled_count = sum(
        1 for v in treatment.values() if v and v != "无" and v.strip()
    )
    empty_count = len(treatment_categories) - filled_count

    return {
        "phase": 4,
        "case_id": case_id,
        "phase_name": "诊疗",
        "treatment_stats": {
            "filled_categories": filled_count,
            "empty_categories": empty_count,
            "total_categories": len(treatment_categories),
            "details": treatment,
        },
    }


# ============================================================
if __name__ == "__main__":
    debug_mode = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    print("\n" + "=" * 60)
    print("  精神科AI问诊系统 - Web 前端")
    print("  访问地址: http://localhost:5000")
    print(f"  Debug 模式: {debug_mode}")
    print("=" * 60 + "\n")
    app.run(host="0.0.0.0", port=5000, debug=debug_mode)
