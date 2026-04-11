---
name: 评估指标口径
description: 各阶段评估指标的计算方法和已知偏差
type: project
---

## 评估指标口径

### Phase 1 评估

- **覆盖率**: chief_complaint和mental_status的used/total百分比
- **对话统计**: 总轮数、患者轮数、医生轮数
- **共情度**: LLM评估, 6级量表 (1.0-5.0)
- **专业度**: LLM评估, 12题量表, 每题0-2分

### Phase 2 评估

- **Precision**: TP/(TP+FP) — ⚠️ TP定义有误, 非标准集合匹配
- **Recall**: TP/(TP+FN) — ⚠️ 同上
- **F1**: 2*P*R/(P+R)
- **Jaccard**: TP/(TP+FP+FN)

**已知偏差**: TP = predicted_count - none_count, 不是 predicted ∩ gold

### Phase 3 评估

- 4个维度 (主诉/体格检查/精神检查/既往史家族史) 各占25%权重
- 每项覆盖度(0/1) + 准确度(0/1)
- 总分 = 加权平均百分比

### Phase 4 评估

- **Precision/Recall/F1/Jaccard**: 基于集合匹配
- 诊断类别为ICD-11大类列表

### Phase 5 评估

- **Precision/Recall/F1/Jaccard**: 基于集合匹配
- 诊断假设为ICD-11具体编码列表
- 有序列表但评估忽略顺序(用set)

### Phase 6 评估

- **集合匹配**: Precision/Recall/F1/Jaccard
- **主诊断排序**: Primary Exact Match, Hit@3, Reciprocal Rank
- **排序一致性**: POA (Pairwise Order Accuracy), nDCG
- ⚠️ POA在共同命中<2时返回null
