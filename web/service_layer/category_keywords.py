"""
ICD-11 disease category keyword configuration

Used for keyword matching in the /api/check/category endpoint.
Each category maps to a set of Chinese keywords for searching evidence in case data and conversations.
"""

CATEGORY_KEYWORDS = {
    "Neurodevelopmental disorders": [
        "发育", "儿童", "注意力", "多动", "孤独症", "自闭症", "学习障碍",
        "智力", "语言发育", "运动发育", "抽动", "遗尿",
    ],
    "Schizophrenia or other primary psychotic disorders": [
        "幻觉", "幻听", "幻视", "妄想", "被害", "被监视", "被控制",
        "精神分裂", "思维", "思维散漫", "思维破裂", "情感淡漠",
        "阴性症状", "阳性症状", "木僵", "怪异",
        "有人要害我", "被跟踪", "有人", "他们在",
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
        "毁坏", "偷窃", "纵火",
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
        "胎儿", "婴儿", "生孩子",
    ],
    "Factitious disorders": [
        "装病", "伪装", "假装", "伪造", "欺骗",
        "故意", "演戏", "假造", "自欺",
    ],
}
