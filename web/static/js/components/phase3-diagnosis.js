/**
 * Phase3Diagnosis 组件
 * Phase 3 — 病历书写 + 诊断
 *
 * 左右分栏布局：
 *   左侧 — 患者基本信息、体格检查、辅助检查结果、对话记录（可滚动）
 *   右侧 — 医生病历书写文本框
 */
const Phase3Diagnosis = {
    template: `
        <div class="phase3-page">
            <!-- 背景图 -->
            <div class="phase3-page__bg"></div>

            <!-- 顶部栏 -->
            <header class="phase3-header">
                <div class="phase3-header__left">
                    <el-button text @click="goBack" class="phase3-header__back-btn">
                        <el-icon><ArrowLeft /></el-icon>
                        返回
                    </el-button>
                    <h3 class="phase3-header__title">
                        {{ subStep === 'caseWriting' ? '病历书写' : '诊断' }}
                    </h3>
                    <span class="phase3-header__subtitle">第三阶段</span>
                </div>
                <div class="phase3-header__right">
                    <span class="phase3-header__patient">
                        患者 {{ caseId }}
                    </span>
                    <el-button
                        v-if="subStep === 'caseWriting'"
                        type="primary"
                        size="small"
                        round
                        @click="goToDiagnosis"
                        :disabled="!isCaseFormFilled"
                        class="phase3-header__next-btn"
                    >
                        完成病历书写，进入诊断
                    </el-button>
                </div>
            </header>

            <!-- 主内容 -->
            <div class="phase3-content phase3-content--split">
                <!-- ======================== 步骤1: 病历书写 ======================== -->
                <template v-if="subStep === 'caseWriting'">
                    <!-- 左侧：患者信息面板 -->
                    <aside class="phase3-left-panel">
                        <!-- 患者基本信息 -->
                        <div class="phase3-panel-section" v-if="caseInfo">
                            <div class="phase3-panel-section__title">患者基本信息</div>
                            <div class="phase3-panel-section__content">
                                <div class="phase3-info-row">
                                    <span class="phase3-info-row__label">基本信息</span>
                                    <span class="phase3-info-row__value">{{ caseInfo.basicInfomation || '暂无' }}</span>
                                </div>
                            </div>
                        </div>

                        <!-- 体格检查报告 -->
                        <div class="phase3-panel-section" v-if="caseInfo && caseInfo.physicalExamination">
                            <div class="phase3-panel-section__title">体格检查报告</div>
                            <div class="phase3-panel-section__content phase3-panel-section__scroll">
                                <div class="phase3-physical-exam-text">{{ caseInfo.physicalExamination }}</div>
                            </div>
                        </div>

                        <!-- 辅助检查结果 -->
                        <div class="phase3-panel-section" v-if="Object.keys(phase2Results).length">
                            <div class="phase3-panel-section__title">辅助检查结果</div>
                            <div class="phase3-panel-section__content">
                                <div v-for="(result, exam) in phase2Results" :key="exam"
                                     class="phase3-exam-result-row"
                                     :class="result === '无' ? 'phase3-exam-result-row--none' : 'phase3-exam-result-row--has'">
                                    <span class="phase3-exam-result-row__name">{{ exam }}</span>
                                    <span class="phase3-exam-result-row__value">
                                        {{ result === '无' ? '无此项检查' : result }}
                                    </span>
                                </div>
                            </div>
                        </div>

                        <!-- 对话记录 -->
                        <div class="phase3-panel-section phase3-panel-section--chat" v-if="phase1Messages.length">
                            <div class="phase3-panel-section__title">
                                对话记录
                                <span class="phase3-panel-section__hint">（最近 {{ phase1Messages.length }} 条）</span>
                            </div>
                            <div class="phase3-panel-section__scroll phase3-chat-scroll">
                                <div v-for="(msg, idx) in phase1Messages" :key="idx"
                                     class="phase3-chat-msg"
                                     :class="msg.role">
                                    <span class="phase3-chat-msg__role">
                                        {{ msg.role === 'doctor' ? '医生' : '患者' }}
                                    </span>
                                    <span class="phase3-chat-msg__content">{{ msg.content }}</span>
                                </div>
                            </div>
                        </div>
                    </aside>

                    <!-- 右侧：病历书写 -->
                    <main class="phase3-right-panel">
                        <div class="phase3-case-writing-card">
                            <div class="phase3-case-writing-card__header">
                                <h2 class="phase3-case-writing-card__title">病历书写</h2>
                                <p class="phase3-case-writing-card__subtitle">
                                    请根据左侧信息填写病历表单
                                </p>
                            </div>

                            <!-- 患者信息填写区 -->
                            <div class="case-info-readonly" v-if="caseInfo">
                                <div class="case-info-readonly__grid">
                                    <div class="case-info-row">
                                        <span class="case-info-row__label">姓名</span>
                                        <input v-model="caseForm.name" class="case-info-row__input case-info-row__input--auto" placeholder="请输入" />
                                    </div>
                                    <div class="case-info-row">
                                        <span class="case-info-row__label">年龄</span>
                                        <input v-model="caseForm.age" class="case-info-row__input case-info-row__input--auto" placeholder="请输入" />
                                    </div>
                                    <div class="case-info-row">
                                        <span class="case-info-row__label">性别</span>
                                        <input v-model="caseForm.gender" class="case-info-row__input case-info-row__input--auto" placeholder="请输入" />
                                    </div>
                                </div>
                                <div class="case-info-divider"></div>
                                <div class="case-info-section">
                                    <span class="case-info-section__label">主诉</span>
                                    <textarea v-model="caseForm.chiefComplaint" class="case-info-section__input" rows="2" placeholder="请输入主诉"></textarea>
                                </div>
                                <div class="case-info-divider"></div>
                                <div class="case-info-section">
                                    <span class="case-info-section__label">家族史</span>
                                    <textarea v-model="caseForm.familyHistory" class="case-info-section__input" rows="2" placeholder="请输入家族史"></textarea>
                                </div>
                                <div class="case-info-divider"></div>
                                <div class="case-info-section">
                                    <span class="case-info-section__label">既往史</span>
                                    <textarea v-model="caseForm.pastHistory" class="case-info-section__input" rows="2" placeholder="请输入既往史"></textarea>
                                </div>
                                <div class="case-info-divider"></div>
                                <div class="case-info-section">
                                    <span class="case-info-section__label">体格检查</span>
                                    <textarea v-model="caseForm.physicalExam" class="case-info-section__input" rows="4" placeholder="请输入体格检查"></textarea>
                                </div>
                                <div class="case-info-divider"></div>
                                <div class="case-info-section">
                                    <span class="case-info-section__label">精神检查</span>
                                    <textarea v-model="caseForm.mentalExam" class="case-info-section__input" rows="3" placeholder="请输入精神检查"></textarea>
                                </div>
                                <div class="case-info-divider"></div>
                                <div class="case-info-section">
                                    <span class="case-info-section__label">辅助检查</span>
                                    <textarea v-model="caseForm.auxiliaryExam" class="case-info-section__input" rows="3" placeholder="请输入辅助检查"></textarea>
                                </div>
                            </div>
                        </div>
                    </main>
                </template>

                <!-- ======================== 步骤2: 诊断 ======================== -->
                <template v-else>
                    <div class="phase3-form-card">
                        <div class="phase3-form-card__header">
                            <h2 class="phase3-form-card__title">填写诊断</h2>
                            <p class="phase3-form-card__subtitle">
                                请根据已完成的病历，填写最终诊断信息
                            </p>
                            <el-tag type="success" effect="plain" size="small" style="margin-top: 8px;">
                                病历已书写
                            </el-tag>
                        </div>

                        <el-form
                            :model="form"
                            :rules="rules"
                            ref="formRef"
                            label-position="top"
                            class="phase3-form"
                        >
                            <el-form-item label="诊断类别" prop="category">
                                <el-select
                                    v-model="form.category"
                                    placeholder="请选择 ICD-11 疾病分类"
                                    filterable
                                    size="large"
                                    class="phase3-form__select"
                                >
                                    <el-option
                                        v-for="(cat, idx) in categories"
                                        :key="idx"
                                        :label="cat"
                                        :value="cat"
                                    />
                                </el-select>
                            </el-form-item>

                            <el-form-item label="具体病症" prop="disease">
                                <el-select
                                    v-model="form.disease"
                                    placeholder="请先选择诊断类别"
                                    filterable
                                    size="large"
                                    class="phase3-form__select"
                                    :disabled="!form.category"
                                >
                                    <el-option
                                        v-for="(dis, idx) in availableDiseases"
                                        :key="idx"
                                        :label="dis"
                                        :value="dis"
                                    />
                                </el-select>
                            </el-form-item>

                            <el-form-item label="诊断理由" prop="reason">
                                <el-input
                                    v-model="form.reason"
                                    type="textarea"
                                    :rows="6"
                                    placeholder="请说明诊断依据和推理过程…"
                                    resize="none"
                                    class="phase3-form__textarea"
                                />
                            </el-form-item>

                            <div class="phase3-form__actions">
                                <el-button
                                    type="primary"
                                    size="large"
                                    round
                                    @click="handleSubmit"
                                    :loading="submitting"
                                    class="phase3-form__submit-btn"
                                >
                                    完成诊断
                                </el-button>
                            </div>
                        </el-form>
                    </div>
                </template>
            </div>
        </div>
    `,

    data() {
        return {
            caseId: '',
            subStep: 'caseWriting',
            caseInfo: null,
            phase1Messages: [],
            phase2Results: {},
            caseForm: {
                name: '',
                age: '',
                gender: '',
                chiefComplaint: '',
                familyHistory: '',
                pastHistory: '',
                physicalExam: '',
                mentalExam: '',
                auxiliaryExam: '',
            },
            form: {
                category: '',
                disease: '',
                reason: '',
            },
            submitting: false,
            categories: [
                "神经发育障碍",
                "精神分裂症或其他原发性精神病性障碍",
                "紧张症",
                "心境障碍",
                "焦虑或恐惧相关障碍",
                "强迫症或相关障碍",
                "应激相关障碍",
                "分离障碍",
                "喂养或进食障碍",
                "排泄障碍",
                "躯体痛苦或躯体体验障碍",
                "物质使用或成瘾行为所致障碍",
                "冲动控制障碍",
                "破坏性行为或解社会行为障碍",
                "人格障碍及相关特质",
                "性欲倒错障碍",
                "神经认知障碍",
                "妊娠、分娩或产褥期相关精神或行为障碍",
                "做作性障碍",
            ],
            diseaseMapping: {
                "神经发育障碍": [
                    "6A00 智力发育障碍",
                    "6A01 发育性言语或语言障碍",
                    "6A02 孤独症谱系障碍",
                    "6A03 发育性学习障碍",
                    "6A04 发育性运动协调障碍",
                    "6A05 注意缺陷多动障碍",
                    "6A06 刻板运动障碍",
                ],
                "精神分裂症或其他原发性精神病性障碍": [
                    "6A20 精神分裂症",
                    "6A21 分裂情感性障碍",
                    "6A22 分裂型障碍",
                    "6A23 急性短暂性精神病性障碍",
                    "6A24 妄想性障碍",
                ],
                "紧张症": [
                    "6A40 伴发于其他精神障碍的紧张症",
                    "6A41 物质或药物所致紧张症",
                ],
                "心境障碍": [
                    "6A60 双相情感障碍 I 型",
                    "6A61 双相情感障碍 II 型",
                    "6A62 环性心境障碍",
                    "6A70 单次发作抑郁障碍",
                    "6A71 复发性抑郁障碍",
                    "6A72 恶劣心境障碍",
                    "6A73 混合性抑郁和焦虑障碍",
                ],
                "焦虑或恐惧相关障碍": [
                    "6B00 广泛性焦虑障碍",
                    "6B01 惊恐障碍",
                    "6B02 广场恐惧症",
                    "6B03 特定恐惧症",
                    "6B04 社交焦虑障碍",
                    "6B05 分离焦虑障碍",
                    "6B06 选择性缄默症",
                ],
                "强迫症或相关障碍": [
                    "6B20 强迫症",
                    "6B21 躯体变形障碍",
                    "6B22 嗅觉参考障碍",
                    "6B23 疑病症",
                    "6B24 囤积障碍",
                    "6B25 以身体为中心的重复行为障碍",
                ],
                "应激相关障碍": [
                    "6B40 创伤后应激障碍",
                    "6B41 复杂性创伤后应激障碍",
                    "6B42 延长哀伤障碍",
                    "6B43 适应障碍",
                    "6B44 反应性依恋障碍",
                    "6B45 脱抑制性社会参与障碍",
                ],
                "分离障碍": [
                    "6B60 分离性神经症状障碍",
                    "6B61 分离性遗忘症",
                    "6B62 恍惚障碍",
                    "6B63 附体恍惚障碍",
                    "6B64 分离性身份障碍",
                    "6B65 部分分离性身份障碍",
                    "6B66 人格解体-现实解体障碍",
                ],
                "喂养或进食障碍": [
                    "6B80 神经性厌食",
                    "6B81 神经性贪食",
                    "6B82 暴食障碍",
                    "6B83 回避性/限制性摄食障碍",
                    "6B84 异食癖",
                    "6B85 反刍-反流障碍",
                ],
                "排泄障碍": [
                    "6C00 遗尿症",
                    "6C01 遗粪症",
                ],
                "躯体痛苦或躯体体验障碍": [
                    "6C20 躯体痛苦障碍",
                    "6C21 身体完整性烦躁障碍",
                ],
                "物质使用或成瘾行为所致障碍": [
                    "6C40 酒精使用所致障碍",
                    "6C41 大麻使用所致障碍",
                    "6C42 合成大麻素使用所致障碍",
                    "6C43 阿片类物质使用所致障碍",
                    "6C44 镇静催眠药或抗焦虑药使用所致障碍",
                    "6C45 可卡因使用所致障碍",
                    "6C46 苯丙胺类兴奋剂使用所致障碍",
                    "6C47 合成卡西酮使用所致障碍",
                    "6C48 咖啡因使用所致障碍",
                    "6C49 致幻剂使用所致障碍",
                    "6C4A 尼古丁使用所致障碍",
                    "6C4C MDMA 或相关药物使用所致障碍",
                    "6C4D 解离性药物使用所致障碍",
                    "6C4E 其他特定精神活性物质使用所致障碍",
                    "6C4F 多种特定精神活性物质使用所致障碍",
                    "6C4G 未知或未特定精神活性物质使用所致障碍",
                    "6C4H 非精神活性物质使用所致障碍",
                    "6C50 赌博障碍",
                    "6C51 游戏障碍",
                ],
                "冲动控制障碍": [
                    "6C70 纵火癖",
                    "6C71 偷窃癖",
                    "6C72 强迫性性行为障碍",
                ],
                "破坏性行为或解社会行为障碍": [
                    "6C90 对立违抗障碍",
                    "6C91 品行-解社会障碍",
                ],
                "人格障碍及相关特质": [
                    "6D10 人格障碍",
                ],
                "性欲倒错障碍": [
                    "6D30 露阴障碍",
                    "6D31 窥阴障碍",
                    "6D32 恋童障碍",
                    "6D33 强制性施虐障碍",
                    "6D34 摩擦障碍",
                    "6D35 涉及非同意个体的其他性欲倒错障碍",
                    "6D36 涉及独处行为或同意个体的性欲倒错障碍",
                ],
                "神经认知障碍": [
                    "6D70 谵妄",
                    "6D71 轻度神经认知障碍",
                    "6D72 遗忘障碍",
                    "6D80 阿尔茨海默病所致痴呆",
                    "6D81 脑血管病所致痴呆",
                    "6D82 路易体病所致痴呆",
                    "6D83 额颞叶痴呆",
                    "6D84 精神活性物质所致痴呆",
                    "6D85 其他疾病所致痴呆",
                    "6D86 痴呆的行为或心理障碍",
                ],
                "妊娠、分娩或产褥期相关精神或行为障碍": [
                    "6E20 妊娠、分娩或产褥期相关精神或行为障碍，不伴精神病性症状",
                    "6E21 妊娠、分娩或产褥期相关精神或行为障碍，伴精神病性症状",
                ],
                "做作性障碍": [
                    "6D50 施加于自身的做作性障碍",
                    "6D51 施加于他人的做作性障碍",
                ],
            },
            rules: {
                category: [
                    { required: true, message: '请选择诊断类别', trigger: 'change' },
                ],
                disease: [
                    { required: true, message: '请输入具体病症', trigger: 'blur' },
                ],
                reason: [
                    { required: true, message: '请填写诊断理由', trigger: 'blur' },
                ],
            },
        };
    },

    computed: {
        ArrowLeft() { return ElementPlusIconsVue.ArrowLeft; },
        availableDiseases() {
            return this.diseaseMapping[this.form.category] || [];
        },
        isCaseFormFilled() {
            const f = this.caseForm;
            return f.name && f.age && f.gender && f.chiefComplaint
                && f.familyHistory && f.pastHistory && f.physicalExam
                && f.mentalExam && f.auxiliaryExam;
        },
    },

    watch: {
        'form.category'() {
            this.form.disease = '';
        },
    },

    methods: {
        goToDiagnosis() {
            if (!this.isCaseFormFilled) {
                this.$message.warning('请先填写完整病历表单');
                return;
            }
            sessionStorage.setItem('phase3_caseForm', JSON.stringify(this.caseForm));
            this.subStep = 'diagnosis';
            this.$message.success('病历已保存，请填写诊断信息');
        },

        async handleSubmit() {
            this.$refs.formRef.validate(async (valid) => {
                if (!valid) return;

                this.submitting = true;
                try {
                    // 使用 record_id 确保所有数据整合到同一次问诊记录
                    const recordId = sessionStorage.getItem('record_id') || this.caseId;

                    await API.submitCaseWriting(recordId, JSON.stringify(this.caseForm));

                    const result = await API.submitDiagnosis(recordId, {
                        category: this.form.category,
                        disease: this.form.disease,
                        reason: this.form.reason,
                    });

                    await API.saveCaseRecord(recordId, {
                        caseForm: { ...this.caseForm },
                        diagnosis: {
                            category: this.form.category,
                            disease: this.form.disease,
                            reason: this.form.reason,
                        },
                    });

                    this.$message.success('第三阶段已完成');
                    console.log('[Phase3Diagnosis] 提交成功:', result);

                    sessionStorage.setItem('phase3_result', JSON.stringify({
                        caseId: this.caseId,
                        caseForm: { ...this.caseForm },
                        category: this.form.category,
                        disease: this.form.disease,
                        reason: this.form.reason,
                    }));

                    this.$router.push('/phase4');
                } catch (err) {
                    this.$message.error('提交失败: ' + (err.message || '未知错误'));
                    console.error('[Phase3Diagnosis] 提交失败:', err);
                } finally {
                    this.submitting = false;
                }
            });
        },

        goBack() {
            if (this.subStep === 'diagnosis') {
                this.subStep = 'caseWriting';
            } else {
                this.$router.push({ path: '/phase2', query: { id: this.caseId } });
            }
        },

        async loadPhaseData() {
            if (this.caseId) {
                try {
                    const info = await API.getCaseInfo(this.caseId);
                    this.caseInfo = info;

                    // 从 basicInfomation 中解析性别和年龄，自动填入表单
                    if (info && info.basicInfomation) {
                        const basicInfo = info.basicInfomation;

                        // 解析性别：匹配"男"或"女"
                        const genderMatch = basicInfo.match(/患者([男女])/);
                        if (genderMatch) {
                            this.caseForm.gender = genderMatch[1];
                        }

                        // 解析年龄：匹配"XX 岁"或"XX岁"
                        const ageMatch = basicInfo.match(/(\d+)\s*岁/);
                        if (ageMatch) {
                            this.caseForm.age = ageMatch[1];
                        }

                        // 姓名默认为"患者"
                        this.caseForm.name = '患者';
                    }
                } catch (err) {
                    console.error('[Phase3Diagnosis] 加载患者信息失败:', err);
                }
            }

            const messagesStr = sessionStorage.getItem('phase2_messages');
            console.log('[Phase3Diagnosis] phase2_messages raw:', messagesStr);
            if (messagesStr) {
                try {
                    const messages = JSON.parse(messagesStr);
                    console.log('[Phase3Diagnosis] parsed messages:', messages);
                    this.phase1Messages = messages.slice(-12);
                    console.log('[Phase3Diagnosis] phase1Messages:', this.phase1Messages);
                } catch (err) {
                    console.error('[Phase3Diagnosis] 解析 Phase 1 消息失败:', err);
                }
            } else {
                console.warn('[Phase3Diagnosis] 未找到 phase2_messages');
            }

            const resultsStr = sessionStorage.getItem('phase2_checkedResults');
            if (resultsStr) {
                try {
                    this.phase2Results = JSON.parse(resultsStr);
                } catch (err) {
                    console.error('[Phase3Diagnosis] 解析 Phase 2 结果失败:', err);
                }
            }

            const savedCaseForm = sessionStorage.getItem('phase3_caseForm');
            if (savedCaseForm) {
                try {
                    this.caseForm = JSON.parse(savedCaseForm);
                } catch (err) {
                    console.error('[Phase3Diagnosis] 解析已保存病历表单失败:', err);
                }
            }
        },
    },

    mounted() {
        this.caseId = this.$route.query.id || sessionStorage.getItem('phase2_caseId') || '';
        if (!this.caseId) {
            this.$message.warning('未找到病例信息，请从患者列表进入');
        }
        this.loadPhaseData();
    },
};
