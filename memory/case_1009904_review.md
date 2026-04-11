---
name: 病例1009904数据审查
description: 对病例1009904完整运行结果的8项数据层异常审查报告
type: project
---

## 病例1009904 数据审查报告

审查日期: 2026-04-11
模型: qwen-flash
真实诊断: 6A20 Schizophrenia + 6A24 Delusional disorder

### Bug #1: Phase 2 TP/FP 评估口径根本性错误

**文件**: core/evaluate/interview_phase2_eval.py:105-107

```python
tp = predicted_count - none_count  # 非NONE的数量
fp = none_count                     # NONE的数量
fn = max(gold_count - tp, 0)
```

**问题**: TP被定义为"医生请求了且Instrument返回非NONE"，而不是"医生请求的项目在gold中存在"。

**实际数据**:
- 医生请求6项: 血常规, 电解质及肝肾功能, 甲状腺功能, 维生素B12, 头颅MRI, 脑电图
- Gold 4项: 心电图, 脑电图, 头颅CT, 头颅MRI
- 真正的交集只有2项 (头颅MRI, 脑电图)
- 但TP计算为 6-4=2，碰巧数值相同但语义完全错误
- 如果医生请求的项目全部在gold中，TP=6, FP=0, 但实际上gold只有4项，这是不可能的

**后果**: 评估指标在边缘情况下会给出荒谬结果（Precision可能>1的含义）。

---

### Bug #2: Phase 3 医生幻觉化验结果

医生生成的临床病历中包含:
> "实验室检查（血常规、电解质、肝肾功能、甲状腺功能、维生素B12及叶酸水平）均未见明确异常"

但Phase 2的Instrument返回中，这4项结果全是 `NONE`（无数据）。

**医生将"无数据"错误理解为"结果正常"**，这在临床安全上是严重问题。

**根因**: interview_phase3.py 中格式化检查结果时，NONE值直接传给了医生，prompt对NONE的解释"该检查未提供阳性发现"被误解为"正常"。

---

### Bug #3: chief_complaint 数据含前导/尾随空格

cases.jsonl 中 chiefComplaint 字段大量含空格:
```
"3 + 月前起病 "
" 敏感多疑 "
"1 + 月前曾至门诊就诊但拒绝检查未予治疗 "
```

虽然代码中有strip修复，但数据源未清理。如果患者模型在grounding中返回的条目没有完全strip，匹配会失败，覆盖率统计可能不准确。

---

### Bug #4: Phase 1 患者grounding覆盖严重不足

- chief_complaint: 16项中使用11项 (68.75%)
- mental_status: 12项中**仅使用4项** (33.33%)

**未使用的精神状态**: 面无表情, 精神检查不合作, 有时独自傻笑, 社会功能受损, 自知力缺乏 等8项全部遗漏。

根因: grounding依赖模型主动在JSON response中报告，但患者实际表现可能已包含这些信息，只是没有被捕获。

---

### Bug #5: Phase 3 LLM Parser 区域划分错误

生成病历被Parser划分为:
- past_family_history: "无躁狂或抑郁发作史。"

真实应该是:
- past_family_history: "1个多月前曾至门诊就诊，但拒绝检查，未予治疗，基本生活尚能自理。"

导致 past_family_history 维度评分为0%。

---

### Bug #6: Phase 6 输出诊断数 vs Ground Truth

- 真实诊断: 2项 (Schizophrenia + Delusional disorder)
- 医生Phase 6输出: 仅1项 (Schizophrenia)
- 医生Phase 5曾识别到2项，但Phase 6排除了Delusional disorder

---

### Bug #7: Ground Truth 一致性风险

cases.jsonl 的 auxiliaryExamination 字段需要与 ground_truth.jsonl 的 realFormulation 中提到的检查结果核对是否一致。

---

### Bug #8: 仅1个病例，统计无意义

所有评估指标基于单次运行，无方差、无置信区间。Phase 6的POA在共同命中<2时为null。
