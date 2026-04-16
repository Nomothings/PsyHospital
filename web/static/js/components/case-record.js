/**
 * CaseRecord 组件
 * 问诊过程完整记录页面
 *
 * 展示内容：
 *   - 患者基本信息
 *   - Phase 1: 医患对话记录
 *   - Phase 2: 医生开具的检查及结果
 *   - Phase 3: 病历书写 + 诊断结果
 */
const CaseRecord = {
    template: `
        <div class="case-record-page">
            <!-- 背景图 -->
            <div class="case-record-page__bg"></div>

            <!-- 顶部栏 -->
            <header class="case-record-header">
                <div class="case-record-header__left">
                    <el-button text @click="goBack" class="case-record-header__back-btn">
                        <el-icon><ArrowLeft /></el-icon>
                        返回
                    </el-button>
                    <h3 class="case-record-header__title">问诊过程记录</h3>
                </div>
                <div class="case-record-header__right">
                    <span class="case-record-header__patient">患者 {{ caseId }}</span>
                </div>
            </header>

            <!-- 主内容 -->
            <div class="case-record-content">
                <div class="case-record-card">
                    <!-- 患者基本信息 -->
                    <div class="case-record-section" v-if="caseInfo">
                        <div class="case-record-section__header">
                            <el-icon :size="20" color="#5ed6c8"><UserFilled /></el-icon>
                            <h4 class="case-record-section__title">患者基本信息</h4>
                        </div>
                        <div class="case-record-section__body">
                            <div class="case-record-info-row">
                                <span class="case-record-info-row__label">基本信息</span>
                                <span class="case-record-info-row__value">{{ caseInfo.basicInfomation || '暂无' }}</span>
                            </div>
                            <div class="case-record-info-row" v-if="caseInfo.physicalExamination">
                                <span class="case-record-info-row__label">体格检查</span>
                                <span class="case-record-info-row__value">{{ caseInfo.physicalExamination }}</span>
                            </div>
                        </div>
                    </div>

                    <!-- Phase 1: 对话记录 -->
                    <div class="case-record-section" v-if="conversationMessages.length">
                        <div class="case-record-section__header">
                            <el-icon :size="20" color="#5ed6c8"><ChatDotRound /></el-icon>
                            <h4 class="case-record-section__title">第一阶段：医患对话</h4>
                            <el-tag type="info" size="small" effect="plain">共 {{ conversationMessages.length }} 条消息</el-tag>
                        </div>
                        <div class="case-record-section__body">
                            <div class="case-record-conversation">
                                <div v-for="(msg, idx) in conversationMessages" :key="idx"
                                     class="case-record-msg"
                                     :class="msg.role">
                                    <div class="case-record-msg__avatar">
                                        <el-icon :size="16" v-if="msg.role === 'patient'"><UserFilled /></el-icon>
                                        <el-icon :size="16" v-else><User /></el-icon>
                                    </div>
                                    <div class="case-record-msg__content">
                                        <div class="case-record-msg__role">
                                            {{ msg.role === 'patient' ? '患者' : '医生' }}
                                        </div>
                                        <div class="case-record-msg__text">{{ msg.content }}</div>
                                        <div class="case-record-msg__time" v-if="msg.time">{{ msg.time }}</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Phase 2: 检查记录 -->
                    <div class="case-record-section" v-if="examRecords.length">
                        <div class="case-record-section__header">
                            <el-icon :size="20" color="#5ed6c8"><DocumentChecked /></el-icon>
                            <h4 class="case-record-section__title">第二阶段：辅助检查</h4>
                            <el-tag type="warning" size="small" effect="plain">共 {{ examRecords.length }} 项检查</el-tag>
                        </div>
                        <div class="case-record-section__body">
                            <div class="case-record-exam-list">
                                <div v-for="(exam, idx) in examRecords" :key="idx"
                                     class="case-record-exam-item"
                                     :class="exam.result === '无' ? 'case-record-exam-item--none' : 'case-record-exam-item--has'">
                                    <div class="case-record-exam-item__name">{{ exam.name }}</div>
                                    <div class="case-record-exam-item__result">
                                        {{ exam.result === '无' ? '无此项检查' : exam.result }}
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Phase 3: 病历书写 -->
                    <div class="case-record-section" v-if="caseForm">
                        <div class="case-record-section__header">
                            <el-icon :size="20" color="#5ed6c8"><EditPen /></el-icon>
                            <h4 class="case-record-section__title">第三阶段：病历书写</h4>
                        </div>
                        <div class="case-record-section__body">
                            <div class="case-record-case-form">
                                <div class="case-record-cf-row" v-if="caseForm.name">
                                    <span class="case-record-cf-label">姓名</span>
                                    <span class="case-record-cf-value">{{ caseForm.name }}</span>
                                </div>
                                <div class="case-record-cf-row" v-if="caseForm.age">
                                    <span class="case-record-cf-label">年龄</span>
                                    <span class="case-record-cf-value">{{ caseForm.age }}</span>
                                </div>
                                <div class="case-record-cf-row" v-if="caseForm.gender">
                                    <span class="case-record-cf-label">性别</span>
                                    <span class="case-record-cf-value">{{ caseForm.gender }}</span>
                                </div>
                                <div class="case-record-cf-row" v-if="caseForm.chiefComplaint">
                                    <span class="case-record-cf-label">主诉</span>
                                    <span class="case-record-cf-value">{{ caseForm.chiefComplaint }}</span>
                                </div>
                                <div class="case-record-cf-row" v-if="caseForm.familyHistory">
                                    <span class="case-record-cf-label">家族史</span>
                                    <span class="case-record-cf-value">{{ caseForm.familyHistory }}</span>
                                </div>
                                <div class="case-record-cf-row" v-if="caseForm.pastHistory">
                                    <span class="case-record-cf-label">既往史</span>
                                    <span class="case-record-cf-value">{{ caseForm.pastHistory }}</span>
                                </div>
                                <div class="case-record-cf-row" v-if="caseForm.physicalExam">
                                    <span class="case-record-cf-label">体格检查</span>
                                    <span class="case-record-cf-value">{{ caseForm.physicalExam }}</span>
                                </div>
                                <div class="case-record-cf-row" v-if="caseForm.mentalExam">
                                    <span class="case-record-cf-label">精神检查</span>
                                    <span class="case-record-cf-value">{{ caseForm.mentalExam }}</span>
                                </div>
                                <div class="case-record-cf-row" v-if="caseForm.auxiliaryExam">
                                    <span class="case-record-cf-label">辅助检查</span>
                                    <span class="case-record-cf-value">{{ caseForm.auxiliaryExam }}</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Phase 3: 诊断结果 -->
                    <div class="case-record-section" v-if="diagnosis">
                        <div class="case-record-section__header">
                            <el-icon :size="20" color="#5ed6c8"><CircleCheckFilled /></el-icon>
                            <h4 class="case-record-section__title">第三阶段：诊断结果</h4>
                        </div>
                        <div class="case-record-section__body">
                            <div class="case-record-diagnosis">
                                <!-- 新格式：多个诊断 -->
                                <template v-if="diagnosis.diagnoses && diagnosis.diagnoses.length">
                                    <div v-for="(dx, idx) in diagnosis.diagnoses" :key="idx" class="case-record-diagnosis-group">
                                        <div class="case-record-diagnosis-group__header">
                                            <el-tag type="success" size="small" effect="plain" round>{{ dx.category }}</el-tag>
                                        </div>
                                        <div class="case-record-diagnosis-group__items" v-if="dx.diseases && dx.diseases.length">
                                            <el-tag v-for="(dis, di) in dx.diseases" :key="di" size="small" round style="margin: 2px 4px 2px 0;">{{ dis }}</el-tag>
                                        </div>
                                        <div v-else class="case-record-diagnosis-group__none">未选择具体疾病</div>
                                    </div>
                                </template>
                                <!-- 旧格式：单个诊断 -->
                                <template v-else>
                                    <div class="case-record-diagnosis__item">
                                        <span class="case-record-diagnosis__label">诊断类别</span>
                                        <span class="case-record-diagnosis__value">{{ diagnosis.category }}</span>
                                    </div>
                                    <div class="case-record-diagnosis__item">
                                        <span class="case-record-diagnosis__label">具体病症</span>
                                        <span class="case-record-diagnosis__value">{{ diagnosis.disease }}</span>
                                    </div>
                                </template>
                                <div class="case-record-diagnosis__item">
                                    <span class="case-record-diagnosis__label">诊断理由</span>
                                    <span class="case-record-diagnosis__value">{{ diagnosis.reason }}</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Phase 4: 治疗方案 -->
                    <div class="case-record-section" v-if="treatment">
                        <div class="case-record-section__header">
                            <el-icon :size="20" color="#5ed6c8"><FirstAidKit /></el-icon>
                            <h4 class="case-record-section__title">第四阶段：治疗方案</h4>
                        </div>
                        <div class="case-record-section__body">
                            <div class="case-record-treatment">
                                <div v-for="(value, key) in treatment" :key="key" class="case-record-tx-item">
                                    <span class="case-record-tx-item__label">{{ key }}</span>
                                    <span class="case-record-tx-item__value">{{ value }}</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- 统一评价报告 -->
                    <div class="case-record-section" v-if="evaluationReport">
                        <div class="case-record-section__header">
                            <el-icon :size="20" color="#3ec4b0"><CircleCheckFilled /></el-icon>
                            <h4 class="case-record-section__title">综合评估报告</h4>
                            <el-tag type="success" size="small" effect="plain">全流程评价完成</el-tag>
                        </div>
                        <div class="case-record-section__body">
                            <!-- 访谈评价 -->
                            <div class="case-record-eval-block" v-if="evaluationReport.phase1 && !evaluationReport.phase1._fallback">
                                <h5 class="case-record-eval-block__title">一、访谈评价</h5>
                                <div class="case-record-eval-block__body">
                                    <div v-if="evaluationReport.phase1.conversation_stats" class="case-record-eval-sub">
                                        <span>对话轮数: {{ evaluationReport.phase1.conversation_stats.total_turns }}</span>
                                        <span class="case-record-eval-sub__sep">|</span>
                                        <span>医生发言: {{ evaluationReport.phase1.conversation_stats.doctor_turns }}</span>
                                        <span class="case-record-eval-sub__sep">|</span>
                                        <span>患者发言: {{ evaluationReport.phase1.conversation_stats.patient_turns }}</span>
                                    </div>
                                    <div v-if="evaluationReport.phase1.empathy_evaluation" class="case-record-eval-sub">
                                        <span>共情等级: <strong>{{ evaluationReport.phase1.empathy_evaluation.empathy_level }}</strong></span>
                                    </div>
                                    <div v-if="evaluationReport.phase1.empathy_evaluation?.why_this_level" class="case-record-eval-detail">
                                        {{ evaluationReport.phase1.empathy_evaluation.why_this_level }}
                                    </div>
                                    <div v-if="evaluationReport.phase1.profession_evaluation" class="case-record-eval-sub">
                                        <span>专业度得分: <strong>{{ evaluationReport.phase1.profession_evaluation.total_score }}</strong> / {{ evaluationReport.phase1.profession_evaluation.question_count * 2 }}</span>
                                    </div>
                                </div>
                            </div>

                            <!-- 检查评价 -->
                            <div class="case-record-eval-block" v-if="evaluationReport.phase2 && !evaluationReport.phase2._fallback">
                                <h5 class="case-record-eval-block__title">二、检查评价</h5>
                                <div class="case-record-eval-block__body">
                                    <div v-if="evaluationReport.phase2.accuracy !== undefined" class="case-record-eval-sub">
                                        <span>检查正确率: <strong>{{ formatAccuracy(evaluationReport.phase2.accuracy) }}</strong></span>
                                    </div>
                                    <div v-if="evaluationReport.phase2.exam_details" class="case-record-eval-exam-list">
                                        <div v-for="(detail, key) in evaluationReport.phase2.exam_details" :key="key"
                                             class="case-record-eval-exam-item"
                                             :class="detail?.correct ? 'case-record-eval-exam-item--correct' : 'case-record-eval-exam-item--wrong'">
                                            <span>{{ key }}</span>
                                            <span>{{ detail?.correct ? '正确' : '错误' }}</span>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <!-- 病历书写与诊断评价 -->
                            <div class="case-record-eval-block" v-if="evaluationReport.phase3_full && !evaluationReport.phase3_full._fallback">
                                <h5 class="case-record-eval-block__title">三、病历书写与诊断评价</h5>
                                <div class="case-record-eval-block__body">
                                    <!-- 病历书写 -->
                                    <div v-if="evaluationReport.phase3_full.case_writing" class="case-record-eval-sub-block">
                                        <div class="case-record-eval-sub">
                                            <span>病历书写总分: <strong>{{ formatScore(evaluationReport.phase3_full.case_writing.total_score) }}</strong></span>
                                        </div>
                                        <div v-for="(section, key) in evaluationReport.phase3_full.case_writing.dimensions" :key="key" class="case-record-eval-sub">
                                            <span>{{ section.section_name }}: {{ formatPercentage(section) }}</span>
                                            <span v-if="section.detail" class="case-record-eval-sub__detail">— {{ section.detail }}</span>
                                        </div>
                                    </div>
                                    <!-- 诊断 -->
                                    <div v-if="evaluationReport.phase3_full.diagnosis" class="case-record-eval-sub-block">
                                        <div class="case-record-eval-sub">
                                            <span>疾病类型得分: <strong>{{ formatScore(evaluationReport.phase3_full.diagnosis.disease_type?.score) }}</strong></span>
                                            <span v-if="evaluationReport.phase3_full.diagnosis.disease_type?.detail" class="case-record-eval-sub__detail">— {{ evaluationReport.phase3_full.diagnosis.disease_type.detail }}</span>
                                        </div>
                                        <div v-if="evaluationReport.phase3_full.diagnosis.disease_type?.metrics" class="case-record-eval-sub">
                                            <span>P: {{ (evaluationReport.phase3_full.diagnosis.disease_type.metrics.precision * 100).toFixed(0) }}%</span>
                                            <span>R: {{ (evaluationReport.phase3_full.diagnosis.disease_type.metrics.recall * 100).toFixed(0) }}%</span>
                                            <span>F1: {{ (evaluationReport.phase3_full.diagnosis.disease_type.metrics.f1 * 100).toFixed(0) }}%</span>
                                            <span>J: {{ (evaluationReport.phase3_full.diagnosis.disease_type.metrics.jaccard * 100).toFixed(0) }}%</span>
                                        </div>
                                        <div class="case-record-eval-sub">
                                            <span>诊断正确性: <strong>{{ formatScore(evaluationReport.phase3_full.diagnosis.diagnostic_correctness?.score) }}</strong></span>
                                        </div>
                                        <div v-if="evaluationReport.phase3_full.diagnosis.diagnostic_correctness?.detail" class="case-record-eval-detail">
                                            {{ evaluationReport.phase3_full.diagnosis.diagnostic_correctness.detail }}
                                        </div>
                                        <div class="case-record-eval-sub">
                                            <span>诊断理由: <strong>{{ formatScore(evaluationReport.phase3_full.diagnosis.diagnostic_reasoning?.score) }}</strong></span>
                                        </div>
                                        <div v-if="evaluationReport.phase3_full.diagnosis.diagnostic_reasoning?.detail" class="case-record-eval-detail">
                                            {{ evaluationReport.phase3_full.diagnosis.diagnostic_reasoning.detail }}
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <!-- 治疗评价 -->
                            <div class="case-record-eval-block" v-if="evaluationReport.phase4 && !evaluationReport.phase4._fallback">
                                <h5 class="case-record-eval-block__title">四、治疗评价</h5>
                                <div class="case-record-eval-block__body">
                                    <div v-if="evaluationReport.phase4.treatment_stats" class="case-record-eval-sub">
                                        <span>已填方案: {{ evaluationReport.phase4.treatment_stats.filled_categories }}</span>
                                        <span class="case-record-eval-sub__sep">|</span>
                                        <span>未填方案: {{ evaluationReport.phase4.treatment_stats.empty_categories }}</span>
                                        <span class="case-record-eval-sub__sep">|</span>
                                        <span>方案总数: {{ evaluationReport.phase4.treatment_stats.total_categories }}</span>
                                    </div>
                                    <div v-if="evaluationReport.phase4.treatment_stats?.details" class="case-record-eval-tx-list">
                                        <div v-for="(detail, key) in evaluationReport.phase4.treatment_stats.details" :key="key" class="case-record-eval-tx-item">
                                            <span class="case-record-eval-tx-item__label">{{ key }}</span>
                                            <span class="case-record-eval-tx-item__value">{{ detail }}</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- 空状态 -->
                    <div v-if="!caseInfo && !conversationMessages.length && !examRecords.length && !caseForm && !diagnosis && !treatment && !evaluationReport"
                         class="case-record-empty">
                        <el-icon :size="48" color="#c0c4cc"><DocumentDelete /></el-icon>
                        <p>暂无问诊记录</p>
                    </div>
                </div>
            </div>
        </div>
    `,

    data() {
        return {
            caseId: '',
            caseInfo: null,
            conversationMessages: [],
            examRecords: [],
            caseText: '',
            caseForm: null,
            diagnosis: null,
            treatment: null,
            evaluationReport: null,
        };
    },

    computed: {
        ArrowLeft() { return ElementPlusIconsVue.ArrowLeft; },
        UserFilled() { return ElementPlusIconsVue.UserFilled; },
        User() { return ElementPlusIconsVue.User; },
        ChatDotRound() { return ElementPlusIconsVue.ChatDotRound; },
        DocumentChecked() { return ElementPlusIconsVue.DocumentChecked; },
        EditPen() { return ElementPlusIconsVue.EditPen; },
        CircleCheckFilled() { return ElementPlusIconsVue.CircleCheckFilled; },
        DocumentDelete() { return ElementPlusIconsVue.DocumentDelete; },
        FirstAidKit() { return ElementPlusIconsVue.FirstAidKit; },
    },

    methods: {
        goBack() {
            this.$router.push('/patients');
        },

        /** 格式化分数：保留两位小数 */
        formatScore(value) {
            if (value == null) return '—';
            const n = Number(value);
            return isNaN(n) ? value : n.toFixed(2);
        },

        /** 格式化百分比：将分数转为百分比字符串 */
        formatPercentage(section) {
            if (!section) return '—';
            if (section.percentage !== undefined) return section.percentage.toFixed(0) + '%';
            if (section.score !== undefined) return (Number(section.score) * 100).toFixed(0) + '%';
            return '—';
        },

        /** 格式化准确率：0-1 小数转为百分比 */
        formatAccuracy(value) {
            if (value == null) return '—';
            const n = Number(value);
            return isNaN(n) ? '—' : (n * 100).toFixed(0) + '%';
        },

        async loadRecord() {
            this.caseId = this.$route.query.id || this.$route.query.record_id || '';
            if (!this.caseId) {
                this.$message.warning('未找到病例信息');
                return;
            }

            try {
                const record = await API.getCaseRecord(this.caseId);
                if (record) {
                    this.caseInfo = record.caseInfo || null;
                    this.conversationMessages = record.conversation || [];
                    this.examRecords = record.exams || [];
                    this.caseText = record.caseText || '';
                    this.caseForm = record.caseForm || null;
                    this.diagnosis = record.diagnosis || null;
                    this.treatment = record.treatment || null;
                    this.evaluationReport = record.evaluation_report || null;
                    // 从 record_id 中提取原始 case_id 用于显示
                    if (record.original_case_id) {
                        this.caseId = record.original_case_id;
                    }
                }
            } catch (err) {
                console.error('[CaseRecord] 加载记录失败:', err);
                this.$message.error('加载记录失败');
            }
        },
    },

    mounted() {
        this.loadRecord();
    },
};
