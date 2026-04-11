---
name: 关键Bug清单
description: 需要优先修复的关键数据异常和评估口径问题
type: project
---

## 关键Bug清单

按严重程度排序，需要修复的8个问题:

### CRITICAL

1. **Phase 2 TP计算口径错误** - TP定义为"非NONE数量"而非"与gold交集"
   - 文件: core/evaluate/interview_phase2_eval.py:105-107
   - 影响: Precision/Recall/F1/Jaccard全部不可信
   - 修复方向: 改为真正的集合匹配 TP = |predicted ∩ gold|

2. **Phase 3 医生幻觉化验结果** - 将NONE理解为"正常"
   - 文件: core/interview/interview_phase3.py:137-138
   - 影响: 临床病历包含伪造的实验室检查描述
   - 修复方向: prompt明确NONE="未检查/无数据，不得假设结果"

### HIGH

3. **chief_complaint 数据源空格污染**
   - 文件: data/cases.jsonl
   - 影响: grounding匹配可能失败
   - 修复方向: 清理数据源 + 确保所有比较用strip

4. **Phase 1 mental_status grounding覆盖率仅33%**
   - 影响: 覆盖率评估偏低
   - 修复方向: 改进患者agent的grounding机制

### MEDIUM

5. **Phase 3 LLM Parser 区域划分错误**
   - 影响: past_family_history维度评分为0%
   - 修复方向: 改进Parser prompt或后处理逻辑

6. **Phase 6 输出诊断数不足**
   - 影响: Recall被低估
   - 修复方向: 检查鉴别诊断prompt是否过度收敛

7. **Ground Truth 一致性待验证**
   - 影响: 评估基准可能不一致
   - 修复方向: 核对cases.jsonl与ground_truth.jsonl

### LOW

8. **仅1个病例**
   - 影响: 无法计算统计显著性
   - 修复方向: 增加更多病例
