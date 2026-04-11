---
name: 项目概述
description: 精神科多阶段AI问诊评估系统的架构、阶段流程、数据流和运行模式
type: project
---

## 项目概述：MentalHospital AI 问诊评估系统

一个模拟精神科临床问诊流程的多阶段AI系统，通过医患对话逐步推进诊断，并对各阶段输出进行自动化评估。

### 6个阶段

| 阶段 | 名称 | 输入 | 输出 |
|------|------|------|------|
| Phase 1 | Clinical History Collection | 病例基本信息、主诉、精神状态 | 医患对话记录 + grounding |
| Phase 2 | Examination Recommendation | Phase 1对话上下文 + 病例auxiliaryExamination | 推荐检查项目 + Instrument返回结果 |
| Phase 3 | Clinical Formulation | Phase 1-2对话上下文 + 检查结果 | 临床病历正文 |
| Phase 4 | Diagnostic Category Identification | Phase 1-3上下文 | 诊断类别(ICD-11大类) |
| Phase 5 | Diagnostic Hypotheses | Phase 1-4上下文 | 诊断假设(ICD-11具体编码) |
| Phase 6 | Differential Diagnosis | Phase 1-5上下文 | 最终鉴别诊断 |

每个阶段后有对应的评估模块 (interview_phase1-6_eval.py)。

### 核心Agent

- **Doctor**: LLM扮演精神科医生，维护对话上下文
- **Patient**: LLM扮演患者，基于病例skill.md和experience文档回答
- **Instrument**: LLM扮演虚拟检查仪器，根据auxiliaryExamination返回结果
- **Evaluator**: LLM评估各阶段质量（共情度、专业度、病历质量等）

### 数据流

```
cases.jsonl -> Phase 1 (医患对话) -> Phase 1 Eval (覆盖率+共情+专业)
  -> Phase 2 (检查推荐) -> Phase 2 Eval (Precision/Recall/F1)
  -> Phase 3 (临床病历) -> Phase 3 Eval (4维度rubric评分)
  -> Phase 4 (诊断类别) -> Phase 4 Eval (集合匹配)
  -> Phase 5 (诊断假设) -> Phase 5 Eval (集合匹配)
  -> Phase 6 (鉴别诊断) -> Phase 6 Eval (集合+排序指标)
```

### 当前数据状态

- 仅1个病例: 1009904 (19岁男性，精神分裂症)
- 仅1个模型的运行结果: qwen-flash
- ground_truth.jsonl 包含真实诊断和真实病历

### 运行方式

```
python run_interview.py  # 运行完整6阶段流程
```

### 关键设计约束

- 医生Agent不接收任何病例信息作为system prompt（仅Doctor Profile）
- 病例信息通过患者Agent间接传递
- Phase 1-6的医生实例是同一个LLMService对象（保持对话上下文传递）
