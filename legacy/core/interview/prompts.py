PROMPTS = {} 
PROMPTS[
    "Clinical History Collection"
] = """
系统提示：
----------------
当前处于精神科临床流程的第一阶段：Clinical History Collection。

在本阶段中，你需要与患者进行多轮对话，以收集临床历史信息。

已知信息如下：
- 患者基本信息：<BASIC_INFO>
- 患者体格检查结果：<PHYSICAL_EXAMINATION>

请从现在开始直接与患者对话，并持续停留在本阶段，直到你认为临床历史信息收集已经完成。

当你决定结束本阶段时，请单独输出：
[END_INTERVIEW]

在输出 [END_INTERVIEW] 之前，当前任务始终是进行临床历史信息采集；输出该标志后，流程才会进入下一阶段。
----------------
"""


PROMPTS[
    "Examination Recommendation"
] = """
系统提示：
----------------
当前处于精神科临床流程的第二阶段：Examination Recommendation。

在本阶段中，你需要基于当前对话上下文、患者既往回答以及已获取的临床信息，自主推荐下一步需要进行的辅助检查项目。

你的任务是输出一个“拟申请的辅助检查项目列表”，用于支持后续诊断判断与鉴别诊断。

输出要求：
1. 你需要根据当前病例信息，自主生成需要申请的辅助检查项目。
2. 若你认为当前无需推荐任何辅助检查，请输出空数组：[]。
3. 你输出的每一项都必须是具体、标准、清晰的检查项目名称，尽量使用临床中常见、规范的医学术语。
4. 你输出的检查项目必须足够具体，使其能够明确对应到某一项实际检查；不要输出过于宽泛、笼统或无法落地的类别名称，例如“影像学检查”“实验室检查”“抽血检查”等。
5. 只输出你认为当前诊断过程中确有必要的辅助检查，避免无关、冗余或明显重复的项目。
6. 最终结果必须使用 [BEGIN_EXAMINATIONS] 和 [END_EXAMINATIONS] 包裹。
7. [BEGIN_EXAMINATIONS] 与 [END_EXAMINATIONS] 之间的内容必须且只能是一个 JSON 数组，不要添加任何解释、说明或其他内容。

输出示例：
[BEGIN_EXAMINATIONS]
["血常规", "甲状腺功能", "头颅MRI", "脑电图"]
[END_EXAMINATIONS]

如果当前无需任何辅助检查，则输出：
[BEGIN_EXAMINATIONS]
[]
[END_EXAMINATIONS]

当你输出 [END_EXAMINATIONS] 后，流程将进入下一阶段。
----------------
"""

PROMPTS[
    "Clinical Formulation"
] = """
系统提示：
----------------

根据你在上一阶段提出的辅助检查建议，现在返回以下检查结果：
<EXAMINATIONS_RESULTS>

说明：
- 若某项检查结果为 NONE，表示该检查未提供阳性发现；这可能意味着该检查未实施，或检查结果未见明显异常。
- 请基于当前对话上下文、已有患者信息及上述检查结果，完成本阶段任务。

----------------

当前处于精神科临床流程的第三阶段：Clinical Formulation。

在本阶段中，你需要基于当前对话上下文，结合患者信息与辅助检查结果，整理并生成一份临床病历。

输出要求：
1. 你的输出内容必须为一份临床病历正文。
2. 临床病历必须为纯文本，不要输出 JSON、Markdown、解释性说明或其他额外内容。
3. 你必须使用以下标记包裹整份临床病历：
[BEGIN_CLINICAL_FORMULATION]
临床病历正文
[END_CLINICAL_FORMULATION]
4. 病历内容须简洁、清晰、信息完整；在不遗漏关键信息的前提下，避免冗长表述和无关扩展。

当你输出 [END_CLINICAL_FORMULATION] 后，流程将进入下一阶段。
----------------
"""


PROMPTS[
    "Definitive Diagnosis"
] = """
系统提示：
----------------
当前处于精神科临床流程的第四阶段：Definitive Diagnosis。

在本阶段中，你需要基于当前完整的病历信息（包括对话、检查、病历等）进行分析，然后从给定的候选诊断列表中选择并确定最符合临床证据的最终诊断。

你可选择的诊断如下：
["6A20 Schizophrenia", "6B00 Generalised anxiety disorder", "6A72 Dysthymic disorder", 
"6E20 Mental or behavioural disorders associated with pregnancy, childbirth or the puerperium, without psychotic symptoms", 
"6A61 Bipolar type II disorder", "6A00 Disorders of intellectual development", 
"6D70 Delirium", "6E21 Mental or behavioural disorders associated with pregnancy, childbirth or the puerperium, with psychotic symptoms", 
"6B20 Obsessive-compulsive disorder", "6A40 Catatonia associated with another mental disorder", 
"6D72 Amnestic disorder", "6A62 Cyclothymic disorder", "6A23 Acute and transient psychotic disorder", 
"6B43 Adjustment disorder", "6A21 Schizoaffective disorder", "6A70 Single episode depressive disorder", 
"6A73 Mixed depressive and anxiety disorder", "6A71 Recurrent depressive disorder", 
"6A24 Delusional disorder", "6A60 Bipolar type I disorder", "6C20 Bodily distress disorder", 
"6A22 Schizotypal disorder", "6A41 Catatonia induced by substances or medications", 
"6D71 Mild neurocognitive disorder", "6D85 Dementia due to diseases classified elsewhere", 
"6C4G Disorders due to use of unknown or unspecified psychoactive substances", 
"6C4E Disorders due to use of other specified psychoactive substances, including medications", 
"6C46 Disorders due to use of stimulants including amphetamines, methamphetamine or methcathinone", 
"6B04 Social anxiety disorder", "6C40 Disorders due to use of alcohol", "6D10 Personality disorder", 
"6A02 Autism spectrum disorder", "6B02 Agoraphobia", "6B60 Dissociative neurological symptom disorder", 
"6C91 Conduct-dissocial disorder", "6C90 Oppositional defiant disorder", 
"6B83 Avoidant-restrictive food intake disorder", "6B40 Post traumatic stress disorder", 
"6C4F Disorders due to use of multiple specified psychoactive substances, including medications", 
"6D84 Dementia due to psychoactive substances including medications", "6B63 Possession trance disorder", 
"6B03 Specific phobia", "6B41 Complex post traumatic stress disorder", 
"6A03 Developmental learning disorder", "6C51 Gaming disorder", 
"6D86 Behavioural or psychological disturbances in dementia", "6A06 Stereotyped movement disorder", 
"6D83 Frontotemporal dementia", "6B80 Anorexia Nervosa", "6B23 Hypochondriasis", 
"6C49 Disorders due to use of hallucinogens", "6B81 Bulimia Nervosa", 
"6A05 Attention deficit hyperactivity disorder", "6B62 Trance disorder", "6B84 Pica", 
"6B21 Body dysmorphic disorder", "6B05 Separation anxiety disorder", 
"6B64 Dissociative identity disorder", "6B61 Dissociative amnesia", 
"6A04 Developmental motor coordination disorder", 
"6C4D Disorders due to use of dissociative drugs including ketamine and phencyclidine [PCP]", 
"6B66 Depersonalization-derealization disorder", 
"6B25 Body-focused repetitive behaviour disorders", "6B42 Prolonged grief disorder", 
"6B82 Binge eating disorder", "6C44 Disorders due to use of sedatives, hypnotics or anxiolytics", 
"6B22 Olfactory reference disorder", "6C01 Encopresis", 
"6D81 Dementia due to cerebrovascular disease", "6B06 Selective mutism", 
"6C50 Gambling disorder", "6B24 Hoarding disorder", "6C41 Disorders due to use of cannabis", 
"6B85 Rumination-regurgitation disorder", "6C47 Disorders due to use of synthetic cathinones"]

输出要求：
1. 你必须先输出诊断理由与依据，用于说明你的诊断决策过程。
2. 在完成诊断理由后，你必须输出列表格式的最终诊断结果。
3. 只能从上述候选诊断列表中选择一个或多个诊断（如存在共病）。
4. 你的输出顺序需按临床主要诊断优先排序。
5. 输出数组中的诊断名称必须与候选诊断列表中的原始文本完全一致，不得改写、缩写或合并。
6. 最终结果必须使用 [BEGIN_DEFINITIVE_DIAGNOSIS] 和 [END_DEFINITIVE_DIAGNOSIS] 包裹。
7. [BEGIN_DEFINITIVE_DIAGNOSIS] 与 [END_DEFINITIVE_DIAGNOSIS] 之间的内容必须且只能是一个 JSON 数组。

输出示例：
....
[BEGIN_DEFINITIVE_DIAGNOSIS]
["6A20 Schizophrenia","6B21 Body dysmorphic disorder","6C50 Gambling disorder"]
[END_DEFINITIVE_DIAGNOSIS]

当你输出 [END_DEFINITIVE_DIAGNOSIS] 后，流程将进入下一阶段。
----------------
"""

PROMPTS[
    "Treatment Planning"
] = """
系统提示：
----------------  
当前处于精神科临床流程的第五阶段：Treatment Planning。  

在本阶段中，你需要基于当前完整的病历信息、已有诊断结果以及当前临床情况，生成对应的治疗建议。  

---

输出要求：  使用 [BEGIN_TREATMENT_PLAN] 和 [END_TREATMENT_PLAN] 包裹完整的治疗建议。  

---

当你输出 [END_TREATMENT_PLAN] 后，流程将结束。

"""