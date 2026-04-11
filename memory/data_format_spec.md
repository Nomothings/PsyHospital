---
name: 数据格式规范
description: cases.jsonl和ground_truth.jsonl的字段定义和示例
type: reference
---

## 数据格式规范

### cases.jsonl (病例数据)

每条记录包含:
- `id`: 病例ID (如 "1009904")
- `basicInfomation`: 患者基本信息字符串 (如 "患者男，19 岁")
- `chiefComplaint`: 主诉条目列表 (注意: 条目可能含前导/尾随空格!)
- `mentalStatus`: 精神状态条目列表
- `physicalExamination`: 体格检查字符串
- `auxiliaryExamination`: 辅助检查结果的JSON对象, 键为检查名称, 值为结果描述

**注意**: 字段名 `basicInfomation` 是拼写错误 (应为 Information)，但代码已按此名称使用。

### ground_truth.jsonl (真实标签)

每条记录包含:
- `id`: 病例ID
- `realFormulation`: 真实病历全文 (字符串)
- `realCategory`: 真实诊断类别 (ICD-11大类列表)
- `realDisorder`: 真实诊断 (ICD-11具体编码列表)

示例 (病例1009904):
```json
{
  "id": "1009904",
  "realFormulation": "患者男，19岁。主诉：3个多月前起病，表现为敏感多疑...",
  "realCategory": ["Schizophrenia or other primary psychotic disorders"],
  "realDisorder": ["6A20 Schizophrenia", "6A24 Delusional disorder"]
}
```

### 输出文件结构

```
data/output/interview/{model_name}/{case_id}/
  interview_phase{1-6}_output.json
  interview_summary.json

data/output/evaluation/{model_name}/{case_id}/
  evaluation_phase{1-6}_output.json
```

### 关键路径

- 病例数据: `data/cases.jsonl`
- Ground Truth: `data/ground_truth.jsonl`
- 患者Skill: `data/patient_{case_id}/skill.md`
- 患者Experience: `data/patient_{case_id}/experience/{event_name}.md`
