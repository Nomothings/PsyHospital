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
# 历史记录持久化 API
# ============================================================

@app.route("/api/history/save", methods=["POST"])
def api_history_save():
    """保存问诊历史快照

    每次问诊结束后调用，将完整的会话数据持久化到文件。
    请求体: { session_id, case_id, messages, phase_results }
    """
    data = request.get_json() or {}
    session_id = data.get("session_id")
    case_id = data.get("case_id")
    if not session_id or not case_id:
        return jsonify({"error": "session_id and case_id required"}), 400

    if not re.match(r'^[a-zA-Z0-9_\-\.]+$', case_id):
        return jsonify({"error": "Invalid case_id"}), 400
    if not re.match(r'^[a-zA-Z0-9]+$', session_id):
        return jsonify({"error": "Invalid session_id"}), 400

    history_file = HISTORY_DIR / f"{case_id}_{session_id}.json"
    history_data = {
        "session_id": session_id,
        "case_id": case_id,
        "messages": data.get("messages", []),
        "phase_results": data.get("phase_results", {}),
        "saved_at": datetime.now(timezone.utc).isoformat(),
    }

    try:
        with open(history_file, "w", encoding="utf-8") as f:
            json.dump(history_data, f, ensure_ascii=False, indent=2)
        logger.info(f"问诊历史已保存: {history_file.name}")
        return jsonify({"status": "ok", "file": history_file.name})
    except Exception as e:
        logger.error(f"保存问诊历史失败: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/history/list")
def api_history_list():
    """列出所有保存的问诊历史"""
    histories = []
    for f in sorted(HISTORY_DIR.glob("*.json")):
        try:
            with open(f, "r", encoding="utf-8") as fp:
                data = json.load(fp)
            histories.append({
                "file": f.name,
                "session_id": data.get("session_id"),
                "case_id": data.get("case_id"),
                "saved_at": data.get("saved_at"),
                "turns": len(data.get("messages", [])) // 2,
            })
        except Exception as e:
            logger.warning(f"读取历史文件 {f} 失败: {e}")
    return jsonify({"histories": histories, "total": len(histories)})


@app.route("/api/history/<filename>")
def api_history_detail(filename):
    """查看单条问诊历史详情"""
    if not re.match(r'^[a-zA-Z0-9_\-\.]+\.json$', filename):
        return jsonify({"error": "Invalid filename"}), 400

    history_file = HISTORY_DIR / filename
    if not history_file.exists():
        return jsonify({"error": "History not found"}), 404
    data = _read_json_safe(history_file)
    if data is None:
        return jsonify({"error": "Failed to read history"}), 500
    return jsonify(data)


@app.route("/api/history/<filename>", methods=["DELETE"])
def api_history_delete(filename):
    """删除单条问诊历史"""
    if not re.match(r'^[a-zA-Z0-9_\-\.]+\.json$', filename):
        return jsonify({"error": "Invalid filename"}), 400

    history_file = HISTORY_DIR / filename
    if not history_file.exists():
        return jsonify({"error": "History not found"}), 404
    try:
        history_file.unlink()
        logger.info(f"问诊历史已删除: {filename}")
        return jsonify({"status": "ok"})
    except Exception as e:
        logger.error(f"删除问诊历史失败: {e}")
        return jsonify({"error": str(e)}), 500


# ============================================================
if __name__ == "__main__":
    debug_mode = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    print("\n" + "=" * 60)
    print("  精神科AI问诊系统 - Web 前端")
    print("  访问地址: http://localhost:5000")
    print(f"  Debug 模式: {debug_mode}")
    print("=" * 60 + "\n")
    app.run(host="0.0.0.0", port=5000, debug=debug_mode)
