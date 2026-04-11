"""
精神科AI问诊系统 - Flask Web API

提供前端所需的REST API接口。
不修改任何现有项目代码，仅新增读取JSON输出并提供API。

启动方式:
    python web/app.py

访问:
    http://localhost:5000
"""

import json
import os
import glob
import sys
from pathlib import Path
from flask import Flask, jsonify, render_template, request

# Add project root to path so we can import patient agent
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from agents.patient.patient import create_patient

app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(__file__), "templates"),
    static_folder=os.path.join(os.path.dirname(__file__), "static"),
)

# ============================================================
# 路径配置
# ============================================================

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = DATA_DIR / "output"
INTERVIEW_DIR = OUTPUT_DIR / "interview"
EVALUATION_DIR = OUTPUT_DIR / "evaluation"
CASES_FILE = DATA_DIR / "cases.jsonl"
GROUND_TRUTH_FILE = DATA_DIR / "ground_truth.jsonl"


# ============================================================
# 工具函数
# ============================================================

def read_json_file(filepath):
    """读取JSON文件"""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def load_cases():
    """加载所有病例"""
    cases = []
    if not CASES_FILE.exists():
        return cases
    with open(CASES_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    cases.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return cases


def get_available_models():
    """获取已有输出结果的模型列表"""
    if not INTERVIEW_DIR.exists():
        return []
    return sorted([d.name for d in INTERVIEW_DIR.iterdir() if d.is_dir()])


def get_available_cases_for_model(model_name):
    """获取指定模型下已有结果的病例ID"""
    model_dir = INTERVIEW_DIR / model_name
    if not model_dir.exists():
        return []
    return sorted([d.name for d in model_dir.iterdir() if d.is_dir()])


# ============================================================
# 页面路由
# ============================================================

@app.route("/")
def index():
    """渲染主页面"""
    return render_template("index.html")


# ============================================================
# API 路由
# ============================================================

@app.route("/api/cases")
def api_cases():
    """获取所有病例列表"""
    cases = load_cases()
    return jsonify({"cases": cases, "total": len(cases)})


@app.route("/api/models")
def api_models():
    """获取已有输出结果的模型列表"""
    models = get_available_models()
    return jsonify({"models": models, "total": len(models)})


@app.route("/api/models/<model_name>/cases")
def api_model_cases(model_name):
    """获取指定模型下已有结果的病例ID"""
    case_ids = get_available_cases_for_model(model_name)
    return jsonify({"model": model_name, "cases": case_ids, "total": len(case_ids)})


@app.route("/api/case/<case_id>/info")
def api_case_info(case_id):
    """获取病例基本信息"""
    cases = load_cases()
    for case in cases:
        if case.get("id") == case_id:
            return jsonify(case)
    return jsonify({"error": "Case not found"}), 404


@app.route("/api/case/<case_id>/summary/<model_name>")
def api_case_summary(case_id, model_name):
    """获取完整流程摘要"""
    summary_file = INTERVIEW_DIR / model_name / case_id / "interview_summary.json"
    if not summary_file.exists():
        return jsonify({"error": "Summary not found"}), 404
    data = read_json_file(summary_file)
    return jsonify(data)


@app.route("/api/case/<case_id>/phase/<int:phase>/<model_name>")
def api_phase(case_id, phase, model_name):
    """获取单个阶段的输出 + 评估结果"""
    interview_file = INTERVIEW_DIR / model_name / case_id / f"interview_phase{phase}_output.json"
    eval_file = EVALUATION_DIR / model_name / case_id / f"evaluation_phase{phase}_output.json"

    result = {"phase": phase, "case_id": case_id, "model_name": model_name}

    if interview_file.exists():
        result["interview"] = read_json_file(interview_file)
    else:
        result["interview"] = None

    if eval_file.exists():
        result["evaluation"] = read_json_file(eval_file)
    else:
        result["evaluation"] = None

    return jsonify(result)


@app.route("/api/ground_truth/<case_id>")
def api_ground_truth(case_id):
    """获取指定病例的ground truth"""
    if not GROUND_TRUTH_FILE.exists():
        return jsonify({"error": "Ground truth file not found"}), 404
    with open(GROUND_TRUTH_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    data = json.loads(line)
                    if data.get("id") == case_id:
                        return jsonify(data)
                except json.JSONDecodeError:
                    continue
    return jsonify({"error": "Case not found in ground truth"}), 404


# ============================================================
# 会话管理 — 存储每个 session 对应的 patient agent
# ============================================================

# In-memory: session_id -> { patient: LLMService, case_id: str, messages: list }
chat_sessions = {}

# In-memory: Phase 3 病历书写记录
case_writings = []

# In-memory: Phase 3 诊断记录
diagnoses = []


@app.route("/api/chat/start", methods=["POST"])
def api_chat_start():
    """开始一段新的问诊会话
    前端发送 case_id，后端创建 patient agent 并返回开场白
    """
    data = request.get_json() or {}
    case_id = data.get("case_id")
    if not case_id:
        return jsonify({"error": "case_id required"}), 400

    # 加载病例数据
    cases = load_cases()
    case_data = None
    for case in cases:
        if case.get("id") == case_id:
            case_data = case
            break

    if not case_data:
        return jsonify({"error": "Case not found"}), 404

    # 创建 patient agent
    try:
        patient = create_patient(
            basic_info=case_data.get("basicInfomation", ""),
            chief_complaint=case_data.get("chiefComplaint", []),
            mental_status=case_data.get("mentalStatus", []),
        )

        session_id = os.urandom(16).hex()
        chat_sessions[session_id] = {
            "patient": patient,
            "case_id": case_id,
            "messages": [],
        }

        # 患者主动开场
        opening_response = patient.chat("请根据患者的主诉，主动自我介绍并描述主要不适。请用中文回复，回复格式为JSON：{\"utterance\": \"患者的话\", \"presentation\": \"外显表现\"}")
        opening = opening_response
        try:
            parsed = json.loads(opening_response)
            opening = parsed.get("utterance", opening_response)
        except json.JSONDecodeError:
            opening = opening_response

        return jsonify({
            "session_id": session_id,
            "case_id": case_id,
            "opening": opening,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/chat/send", methods=["POST"])
def api_chat_send():
    """发送医生消息，获取患者回复"""
    data = request.get_json() or {}
    session_id = data.get("session_id")
    doctor_message = data.get("message", "")

    if not session_id or not doctor_message:
        return jsonify({"error": "session_id and message required"}), 400

    chat_session = chat_sessions.get(session_id)
    if not chat_session:
        return jsonify({"error": "Session not found"}), 404

    patient = chat_session["patient"]
    try:
        response = patient.chat(doctor_message)

        # 解析 JSON 格式的响应
        utterance = response
        presentation = ""
        try:
            parsed = json.loads(response)
            utterance = parsed.get("utterance", response)
            presentation = parsed.get("presentation", "")
        except json.JSONDecodeError:
            pass

        chat_session["messages"].append({
            "role": "doctor",
            "content": doctor_message,
        })
        chat_session["messages"].append({
            "role": "patient",
            "content": utterance,
            "presentation": presentation,
        })

        return jsonify({
            "response": utterance,
            "presentation": presentation,
            "turn": len(chat_session["messages"]) // 2,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/chat/end", methods=["POST"])
def api_chat_end():
    """结束问诊会话，清理资源"""
    data = request.get_json() or {}
    session_id = data.get("session_id")
    if session_id and session_id in chat_sessions:
        del chat_sessions[session_id]
    return jsonify({"status": "ok"})


# ============================================================
# Phase 2: 检查选择匹配 API
# ============================================================

# TODO: 将以下关键词匹配替换为真实的 LLM 匹配逻辑
# 建议接入方式:
#   1. 将所有对话消息 + 疾病分类名发送给 LLM
#   2. 让 LLM 判断该分类是否在对话中有相关证据
#   3. 返回结构化的证据列表

CATEGORY_KEYWORDS = {
    "Neurodevelopmental disorders": [
        "发育", "儿童", "注意力", "多动", "孤独症", "自闭症", "学习障碍",
        "智力", "语言发育", "运动发育", "抽动", "遗尿",
    ],
    "Schizophrenia or other primary psychotic disorders": [
        "幻觉", "幻听", "幻视", "妄想", "被害", "被监视", "被控制",
        "精神分裂", "思维", "思维散漫", "思维破裂", "情感淡漠",
        "阴性症状", "阳性症状", "木僵", "怪异", "妄想",
        "有人要害我", "被监视", "被跟踪", "有人", "他们在",
        "阴谋", "控制我", "他们在控制",
    ],
    "Catatonia": [
        "木僵", "蜡样屈曲", "缄默", "违拗", "刻板动作",
        "模仿动作", "姿势", "不动", "僵硬", "僵住",
    ],
    "Mood disorders": [
        "抑郁", "情绪", "心情", "低落", "悲伤", "绝望", "自杀",
        "双相", "躁狂", "兴奋", "精力旺盛", "睡眠减少", "话多",
        "情绪高涨", "情绪低落", "没意思", "没兴趣", "没动力",
        "想哭", "难过", "伤心", "好难过", "好伤心",
        "活着没意思", "想离开", "没人理解", "没人关心",
        "孤独", "好孤独", "一个人", "很低落",
        "开心", "快乐", "愉快", "情绪波动",
    ],
    "Anxiety or fear-related disorders": [
        "焦虑", "恐惧", "害怕", "恐慌", "紧张", "心慌", "胸闷",
        "出汗", "发抖", "颤抖", "回避", "社交恐惧", "广场恐惧",
        "广泛性焦虑", "惊恐发作", "窒息感", "濒死感",
        "怕人", "怕人看到", "怕自己再也",
    ],
    "Obsessive-compulsive or related disorders": [
        "强迫", "反复", "洗手", "检查", "重复", "仪式",
        "完美主义", "无法控制", "忍不住", "必须要",
        "身体变形", "拔毛", "抓挠", "囤积",
    ],
    "Disorders specifically associated with stress": [
        "创伤", "应激", "闪回", "噩梦", "回避", "警觉",
        "事件", "经历", "地震", "车祸", "暴力", "虐待",
        "适应障碍", "反应性依恋",
        "受不了", "绝望", "活不下去", "不想活", "死了算了",
        "痛苦", "太痛苦", "好痛苦", "我好累", "好累",
    ],
    "Dissociative disorders": [
        "解离", "分离", "遗忘", "人格", "身份", "不真实",
        "恍惚", "断片", "失去意识", "不像自己",
        "灵魂出窍", "旁观者", "麻木",
    ],
    "Feeding or eating disorders": [
        "进食", "暴食", "厌食", "呕吐", "催吐", "节食",
        "体重", "身材", "肥胖", "瘦", "贪食",
        "吃不下", "不想吃", "没胃口", "吃得太多",
    ],
    "Elimination disorders": [
        "尿床", "遗尿", "大便", "失禁", "尿急", "尿频",
        "拉裤子", "憋不住",
    ],
    "Disorders of bodily distress or bodily experience": [
        "躯体化", "躯体", "身体不适", "查不出", "检查正常",
        "疼痛", "头痛", "胃痛", "心悸", "呼吸困难",
        "疑病", "担心生病", "担心有病",
    ],
    "Disorders due to substance use or addictive behaviours": [
        "酒", "烟", "药物", "毒品", "赌博", "游戏成瘾",
        "网络成瘾", "依赖", "戒断", "上瘾", "成瘾",
        "吸食", "注射", "滥用",
    ],
    "Impulse control disorders": [
        "冲动", "无法控制", "爆发性", "攻击", "打人",
        "毁坏", "偷窃", "纵火", "赌博",
        "控制不住自己", "发脾气", "大发脾气",
    ],
    "Disruptive behaviour or dissocial disorders": [
        "对抗", "违抗", "挑衅", "攻击", "破坏",
        "品行", "偷窃", "欺凌", "虐待", "残忍",
        "不遵守", "违反", "逃学", "离家出走",
    ],
    "Personality disorders and related traits": [
        "性格", "人格", "偏执", "分裂样", "边缘型",
        "自恋", "回避型", "依赖型", "强迫型",
        "一直以来", "从小", "总是", "一直", "从不",
        "关系不稳定", "害怕被抛弃", "空虚", "自我伤害",
    ],
    "Paraphilic disorders": [
        "性", "暴露", "窥视", "恋物", "受虐",
        "施虐", "恋童", "不正常", "变态",
    ],
    "Neurocognitive disorders": [
        "记忆", "遗忘", "痴呆", "认知", "意识模糊",
        "糊涂", "认不出", "迷路", "定向",
        "记不清", "想不起来", "记不得", "忘了", "忘记了",
        "搞不懂", "不明白", "我不明白",
    ],
    "Mental or behavioural disorders associated with pregnancy, childbirth or the puerperium": [
        "怀孕", "妊娠", "分娩", "产后", "哺乳",
        "胎儿", "婴儿", "怀孕", "生孩子",
    ],
    "Factitious disorders": [
        "装病", "伪装", "假装", "伪造", "欺骗",
        "故意", "演戏", "假造", "自欺",
    ],
}


@app.route("/api/check/exam", methods=["POST"])
def api_check_exam():
    """查询患者病例中的辅助检查结果

    从病例数据的 auxiliaryExamination 字段中读取。
    如果该检查项目存在则返回结果，否则返回"无"。
    """
    data = request.get_json() or {}
    case_id = data.get("case_id")
    exam_name = data.get("exam_name")

    if not exam_name:
        return jsonify({"error": "exam_name required"}), 400

    cases = load_cases()
    case_data = None
    for case in cases:
        if case.get("id") == case_id:
            case_data = case
            break

    if not case_data:
        return jsonify({"error": "Case not found"}), 404

    aux_exam = case_data.get("auxiliaryExamination", {})

    # 精确匹配
    if exam_name in aux_exam:
        return jsonify({"exam_name": exam_name, "result": aux_exam[exam_name]})

    # 模糊匹配（去除空格后比较）
    for key, value in aux_exam.items():
        if key.replace(" ", "") == exam_name.replace(" ", ""):
            return jsonify({"exam_name": exam_name, "result": value})

    return jsonify({"exam_name": exam_name, "result": "无"})


@app.route("/api/check/category", methods=["POST"])
def api_check_category():
    """检查某个 ICD-11 疾病分类是否在患者病例中有相关证据

    匹配来源：
    1. 患者病例数据（chiefComplaint + mentalStatus）
    2. 对话消息（医生与患者的交流）
    """
    data = request.get_json() or {}
    case_id = data.get("case_id")
    category = data.get("category")
    messages = data.get("messages", [])

    if not category:
        return jsonify({"error": "category required"}), 400

    # 加载病例数据
    cases = load_cases()
    case_data = None
    for case in cases:
        if case.get("id") == case_id:
            case_data = case
            break

    if not case_data:
        return jsonify({"error": "Case not found"}), 404

    # 获取该分类的关键词
    keywords = CATEGORY_KEYWORDS.get(category, [])

    # 构建搜索文本：病例主诉 + 精神状态 + 对话消息
    search_texts = []

    # 1. 病例主诉
    chief_complaints = case_data.get("chiefComplaint", [])
    for cc in chief_complaints:
        search_texts.append({"source": "chiefComplaint", "role": "patient", "content": cc.strip()})

    # 2. 精神状态
    mental_status = case_data.get("mentalStatus", [])
    for ms in mental_status:
        search_texts.append({"source": "mentalStatus", "role": "patient", "content": ms.strip()})

    # 3. 对话消息
    for msg in messages:
        search_texts.append({"source": "conversation", "role": msg.get("role", "unknown"), "content": msg.get("content", "")})

    # 在搜索文本中匹配关键词
    evidence = []
    seen_contents = set()
    for item in search_texts:
        content = item["content"]
        content_lower = content.lower()
        for kw in keywords:
            if kw.lower() in content_lower and content not in seen_contents:
                evidence.append({
                    "role": item["role"],
                    "content": content,
                })
                seen_contents.add(content)
                break

    if evidence:
        return jsonify({
            "category": category,
            "result": {
                "status": "positive",
                "evidence": evidence,
            },
        })
    else:
        return jsonify({
            "category": category,
            "result": "无",
        })


# ============================================================
# Phase 3: 病历书写
# ============================================================

@app.route("/api/case-writing/submit", methods=["POST"])
def api_case_writing_submit():
    """提交 Phase 3 病历书写

    接收前端传来的 case_id 和 case_text，当前存储到内存。
    TODO: 持久化到文件或数据库。
    """
    data = request.get_json() or {}
    case_id = data.get("case_id")
    case_text = data.get("case_text", "")

    if not case_id or not case_text:
        return jsonify({"error": "case_id and case_text required"}), 400

    case_writings.append({"case_id": case_id, "case_text": case_text})

    return jsonify({"status": "ok", "case_id": case_id})


# ============================================================
# Phase 3: 诊断提交
# ============================================================

@app.route("/api/diagnosis/submit", methods=["POST"])
def api_diagnosis_submit():
    """提交 Phase 3 诊断信息

    接收前端传来的 category / disease / reason，
    当前存储到内存并返回。
    TODO: 持久化到文件或数据库。
    """
    data = request.get_json() or {}
    case_id = data.get("case_id")
    category = data.get("category", "")
    disease = data.get("disease", "")
    reason = data.get("reason", "")

    if not case_id or not category or not disease or not reason:
        return jsonify({
            "error": "case_id, category, disease, reason 均不能为空",
        }), 400

    # 暂存到内存（生产环境应写入文件/数据库）
    diagnosis_record = {
        "case_id": case_id,
        "category": category,
        "disease": disease,
        "reason": reason,
    }
    diagnoses.append(diagnosis_record)

    return jsonify({
        "status": "ok",
        "case_id": case_id,
        "category": category,
        "disease": disease,
        "reason": reason,
    })


# ============================================================
if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  精神科AI问诊系统 - Web 前端")
    print("  访问地址: http://localhost:5000")
    print("=" * 60 + "\n")
    app.run(host="0.0.0.0", port=5000, debug=True)
