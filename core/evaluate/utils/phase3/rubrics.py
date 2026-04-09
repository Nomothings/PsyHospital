"""
Phase 3 临床病历评估评分标准

评分维度：
- chief_complaint: 主诉评分标准 (25%)
- physical_examination: 体格检查评分标准 (25%)
- mental_examination: 精神检查评分标准 (25%)
- past_family_history: 既往史家族史评分标准 (25%)

每个评分项包含：
- 覆盖度评分 (0或1): test是否包含true中的该要素
- 准确度评分 (0或1): test的描述是否与true一致
"""

RUBRICS = {}

RUBRICS["chief_complaint"] = {
    "rubric_name": "主诉评分标准",
    "weight": 0.25,
    "scoring_notes": "以true为基准进行对比评分。若true中未提及某要素，则该项不参与评分，满分相应减少。",
    "scoring_items": [
        {
            "id": 1,
            "element": "起病时间",
            "description": "症状开始的时间描述，包括具体时间点和病程时长",
            "coverage_definition": {
                "1": "test中明确提及起病时间或病程时长",
                "0": "true中有提及但test中未提及或表述不清",
                "skip": "true中未提及该要素，该项不计分"
            },
            "accuracy_definition": {
                "1": "与true中的起病时间一致，表述准确",
                "0": "与true不一致或存在明显错误",
                "skip": "true中未提及该要素，该项不计分"
            }
        },
        {
            "id": 2,
            "element": "主要症状",
            "description": "患者就诊的核心症状，如敏感多疑、幻觉、妄想等",
            "coverage_definition": {
                "1": "test中包含true提及的主要症状",
                "0": "true中有但test遗漏该主要症状",
                "skip": "true中未提及该要素，该项不计分"
            },
            "accuracy_definition": {
                "1": "症状描述与true一致，无错误",
                "0": "症状描述与true不一致或存在错误",
                "skip": "true中未提及该要素，该项不计分"
            }
        },
        {
            "id": 3,
            "element": "症状表现",
            "description": "症状的具体表现形式和特点",
            "coverage_definition": {
                "1": "test描述了true中提及的症状具体表现",
                "0": "true中有但test遗漏症状表现细节",
                "skip": "true中未提及该要素，该项不计分"
            },
            "accuracy_definition": {
                "1": "症状表现描述与true一致",
                "0": "症状表现描述与true不一致或错误",
                "skip": "true中未提及该要素，该项不计分"
            }
        },
        {
            "id": 4,
            "element": "伴随症状",
            "description": "伴随主要症状出现的其他症状，如睡眠问题、行为异常等",
            "coverage_definition": {
                "1": "test包含true中的伴随症状",
                "0": "true中有但test遗漏伴随症状",
                "skip": "true中未提及该要素，该项不计分"
            },
            "accuracy_definition": {
                "1": "伴随症状描述与true一致",
                "0": "伴随症状描述与true不一致或错误",
                "skip": "true中未提及该要素，该项不计分"
            }
        },
        {
            "id": 5,
            "element": "病程演变",
            "description": "症状的发展变化过程",
            "coverage_definition": {
                "1": "test提及true中的病程演变信息",
                "0": "true中有但test遗漏病程演变",
                "skip": "true中未提及该要素，该项不计分"
            },
            "accuracy_definition": {
                "1": "病程演变描述与true一致",
                "0": "病程演变描述与true不一致或错误",
                "skip": "true中未提及该要素，该项不计分"
            }
        },
        {
            "id": 6,
            "element": "加重因素",
            "description": "导致症状加重的情况或时间点",
            "coverage_definition": {
                "1": "test提及true中的加重因素",
                "0": "true中有但test遗漏加重因素",
                "skip": "true中未提及该要素，该项不计分"
            },
            "accuracy_definition": {
                "1": "加重因素描述与true一致",
                "0": "加重因素描述与true不一致或错误",
                "skip": "true中未提及该要素，该项不计分"
            }
        }
    ]
}

RUBRICS["physical_examination"] = {
    "rubric_name": "体格检查评分标准",
    "weight": 0.25,
    "scoring_notes": "以true为基准进行对比评分。若true中未提及某要素，则该项不参与评分，满分相应减少。",
    "scoring_items": [
        {
            "id": 1,
            "element": "生命体征",
            "description": "体温(T)、脉搏(P)、呼吸(R)、血压(BP)四项基本生命体征",
            "coverage_definition": {
                "1": "test中包含true提及的生命体征项目",
                "0": "true中有但test遗漏生命体征项目",
                "skip": "true中未提及生命体征，该项不计分"
            },
            "accuracy_definition": {
                "1": "生命体征数值与true一致，表述准确",
                "0": "生命体征数值与true不一致或存在错误",
                "skip": "true中未提及生命体征，该项不计分"
            }
        },
        {
            "id": 2,
            "element": "一般情况",
            "description": "神志、发育、营养、体位、步态、合作程度等一般状况",
            "coverage_definition": {
                "1": "test中包含true提及的一般情况项目",
                "0": "true中有但test遗漏一般情况项目",
                "skip": "true中未提及一般情况，该项不计分"
            },
            "accuracy_definition": {
                "1": "一般情况描述与true一致",
                "0": "一般情况描述与true不一致或错误",
                "skip": "true中未提及一般情况，该项不计分"
            }
        },
        {
            "id": 3,
            "element": "皮肤黏膜",
            "description": "皮肤黏膜、浅表淋巴结的检查结果",
            "coverage_definition": {
                "1": "test中包含true提及的皮肤黏膜检查内容",
                "0": "true中有但test遗漏皮肤黏膜检查内容",
                "skip": "true中未提及皮肤黏膜，该项不计分"
            },
            "accuracy_definition": {
                "1": "皮肤黏膜描述与true一致",
                "0": "皮肤黏膜描述与true不一致或错误",
                "skip": "true中未提及皮肤黏膜，该项不计分"
            }
        },
        {
            "id": 4,
            "element": "头颈部",
            "description": "头颅、颈部的检查结果",
            "coverage_definition": {
                "1": "test中包含true提及的头颈部检查内容",
                "0": "true中有但test遗漏头颈部检查内容",
                "skip": "true中未提及头颈部，该项不计分"
            },
            "accuracy_definition": {
                "1": "头颈部描述与true一致",
                "0": "头颈部描述与true不一致或错误",
                "skip": "true中未提及头颈部，该项不计分"
            }
        },
        {
            "id": 5,
            "element": "胸部/心肺",
            "description": "胸廓、肺部、心脏的检查结果",
            "coverage_definition": {
                "1": "test中包含true提及的胸部心肺检查内容",
                "0": "true中有但test遗漏胸部心肺检查内容",
                "skip": "true中未提及胸部心肺，该项不计分"
            },
            "accuracy_definition": {
                "1": "胸部心肺描述与true一致",
                "0": "胸部心肺描述与true不一致或错误",
                "skip": "true中未提及胸部心肺，该项不计分"
            }
        },
        {
            "id": 6,
            "element": "腹部",
            "description": "腹部的检查结果",
            "coverage_definition": {
                "1": "test中包含true提及的腹部检查内容",
                "0": "true中有但test遗漏腹部检查内容",
                "skip": "true中未提及腹部，该项不计分"
            },
            "accuracy_definition": {
                "1": "腹部描述与true一致",
                "0": "腹部描述与true不一致或错误",
                "skip": "true中未提及腹部，该项不计分"
            }
        },
        {
            "id": 7,
            "element": "四肢/神经系统",
            "description": "四肢、神经反射的检查结果",
            "coverage_definition": {
                "1": "test中包含true提及的四肢神经系统检查内容",
                "0": "true中有但test遗漏四肢神经系统检查内容",
                "skip": "true中未提及四肢神经系统，该项不计分"
            },
            "accuracy_definition": {
                "1": "四肢神经系统描述与true一致",
                "0": "四肢神经系统描述与true不一致或错误",
                "skip": "true中未提及四肢神经系统，该项不计分"
            }
        }
    ]
}

RUBRICS["mental_examination"] = {
    "rubric_name": "精神检查评分标准",
    "weight": 0.25,
    "scoring_notes": "以true为基准进行对比评分。若true中未提及某要素，则该项不参与评分，满分相应减少。",
    "scoring_items": [
        {
            "id": 1,
            "element": "外观行为",
            "description": "外貌、仪态、行为表现、合作程度等",
            "coverage_definition": {
                "1": "test中包含true提及的外观行为内容",
                "0": "true中有但test遗漏外观行为内容",
                "skip": "true中未提及外观行为，该项不计分"
            },
            "accuracy_definition": {
                "1": "外观行为描述与true一致",
                "0": "外观行为描述与true不一致或错误",
                "skip": "true中未提及外观行为，该项不计分"
            }
        },
        {
            "id": 2,
            "element": "言语",
            "description": "言语的速度、量、连贯性等",
            "coverage_definition": {
                "1": "test中包含true提及的言语相关内容",
                "0": "true中有但test遗漏言语内容",
                "skip": "true中未提及言语，该项不计分"
            },
            "accuracy_definition": {
                "1": "言语描述与true一致",
                "0": "言语描述与true不一致或错误",
                "skip": "true中未提及言语，该项不计分"
            }
        },
        {
            "id": 3,
            "element": "情感",
            "description": "情绪状态、情感反应、情感协调性等",
            "coverage_definition": {
                "1": "test中包含true提及的情感内容",
                "0": "true中有但test遗漏情感内容",
                "skip": "true中未提及情感，该项不计分"
            },
            "accuracy_definition": {
                "1": "情感描述与true一致",
                "0": "情感描述与true不一致或错误",
                "skip": "true中未提及情感，该项不计分"
            }
        },
        {
            "id": 4,
            "element": "感知觉",
            "description": "幻觉、错觉等感知觉障碍",
            "coverage_definition": {
                "1": "test中包含true提及的感知觉内容",
                "0": "true中有但test遗漏感知觉内容",
                "skip": "true中未提及感知觉，该项不计分"
            },
            "accuracy_definition": {
                "1": "感知觉描述与true一致",
                "0": "感知觉描述与true不一致或错误",
                "skip": "true中未提及感知觉，该项不计分"
            }
        },
        {
            "id": 5,
            "element": "思维形式",
            "description": "思维联想、思维逻辑等",
            "coverage_definition": {
                "1": "test中包含true提及的思维形式内容",
                "0": "true中有但test遗漏思维形式内容",
                "skip": "true中未提及思维形式，该项不计分"
            },
            "accuracy_definition": {
                "1": "思维形式描述与true一致",
                "0": "思维形式描述与true不一致或错误",
                "skip": "true中未提及思维形式，该项不计分"
            }
        },
        {
            "id": 6,
            "element": "思维内容",
            "description": "妄想、强迫观念等思维内容障碍",
            "coverage_definition": {
                "1": "test中包含true提及的思维内容",
                "0": "true中有但test遗漏思维内容",
                "skip": "true中未提及思维内容，该项不计分"
            },
            "accuracy_definition": {
                "1": "思维内容描述与true一致",
                "0": "思维内容描述与true不一致或错误",
                "skip": "true中未提及思维内容，该项不计分"
            }
        },
        {
            "id": 7,
            "element": "认知功能",
            "description": "注意力、记忆力、定向力、智力等",
            "coverage_definition": {
                "1": "test中包含true提及的认知功能内容",
                "0": "true中有但test遗漏认知功能内容",
                "skip": "true中未提及认知功能，该项不计分"
            },
            "accuracy_definition": {
                "1": "认知功能描述与true一致",
                "0": "认知功能描述与true不一致或错误",
                "skip": "true中未提及认知功能，该项不计分"
            }
        },
        {
            "id": 8,
            "element": "自知力",
            "description": "患者对自身精神状态的认识和判断能力",
            "coverage_definition": {
                "1": "test中包含true提及的自知力内容",
                "0": "true中有但test遗漏自知力内容",
                "skip": "true中未提及自知力，该项不计分"
            },
            "accuracy_definition": {
                "1": "自知力描述与true一致",
                "0": "自知力描述与true不一致或错误",
                "skip": "true中未提及自知力，该项不计分"
            }
        }
    ]
}

RUBRICS["past_family_history"] = {
    "rubric_name": "既往史家族史评分标准",
    "weight": 0.25,
    "scoring_notes": "以true为基准进行对比评分。若true中未提及某要素，则该项不参与评分，满分相应减少。",
    "scoring_items": [
        {
            "id": 1,
            "element": "既往史",
            "description": "既往疾病史、手术史、外伤史等",
            "coverage_definition": {
                "1": "test中包含true提及的既往史内容",
                "0": "true中有但test遗漏既往史内容",
                "skip": "true中未提及既往史，该项不计分"
            },
            "accuracy_definition": {
                "1": "既往史描述与true一致",
                "0": "既往史描述与true不一致或错误",
                "skip": "true中未提及既往史，该项不计分"
            }
        },
        {
            "id": 2,
            "element": "个人史",
            "description": "出生发育、教育、职业、婚姻、性格、生活习惯等",
            "coverage_definition": {
                "1": "test中包含true提及的个人史内容",
                "0": "true中有但test遗漏个人史内容",
                "skip": "true中未提及个人史，该项不计分"
            },
            "accuracy_definition": {
                "1": "个人史描述与true一致",
                "0": "个人史描述与true不一致或错误",
                "skip": "true中未提及个人史，该项不计分"
            }
        },
        {
            "id": 3,
            "element": "家族史",
            "description": "家族精神疾病史、遗传病史等",
            "coverage_definition": {
                "1": "test中包含true提及的家族史内容",
                "0": "true中有但test遗漏家族史内容",
                "skip": "true中未提及家族史，该项不计分"
            },
            "accuracy_definition": {
                "1": "家族史描述与true一致",
                "0": "家族史描述与true不一致或错误",
                "skip": "true中未提及家族史，该项不计分"
            }
        },
        {
            "id": 4,
            "element": "物质接触史",
            "description": "精神活性物质接触史、吸烟饮酒史等",
            "coverage_definition": {
                "1": "test中包含true提及的物质接触史内容",
                "0": "true中有但test遗漏物质接触史内容",
                "skip": "true中未提及物质接触史，该项不计分"
            },
            "accuracy_definition": {
                "1": "物质接触史描述与true一致",
                "0": "物质接触史描述与true不一致或错误",
                "skip": "true中未提及物质接触史，该项不计分"
            }
        }
    ]
}
