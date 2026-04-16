/**
 * HistoryDetail 组件
 * 问诊历史详情页面
 */
const HistoryDetail = {
    template: `
        <div class="history-detail-page">
            <!-- 背景 -->
            <div class="history-detail-page__bg"></div>

            <!-- 顶部栏 -->
            <header class="history-detail-header">
                <div class="history-detail-header__left">
                    <el-button text @click="goBack" class="history-detail-header__back-btn">
                        <el-icon><ArrowLeft /></el-icon>
                        返回
                    </el-button>
                    <h3 class="history-detail-header__title">问诊历史记录</h3>
                </div>
                <div class="history-detail-header__right">
                    <span class="history-detail-header__patient">患者 {{ caseId }}</span>
                    <el-tag v-if="hasDiagnosis" type="success" size="small" effect="plain" style="margin-left: 8px;">已完成诊断</el-tag>
                </div>
            </header>

            <!-- 主内容 -->
            <div class="history-detail-content" v-loading="loading">
                <div class="history-detail-card">
                    <!-- 患者基本信息 -->
                    <div class="history-detail-section" v-if="recordData.caseInfo">
                        <div class="history-detail-section__header">
                            <el-icon :size="20" color="#5ed6c8"><UserFilled /></el-icon>
                            <h4 class="history-detail-section__title">患者基本信息</h4>
                        </div>
                        <div class="history-detail-section__body">
                            <div class="history-detail-info-row">
                                <span class="history-detail-info-row__label">基本信息</span>
                                <span class="history-detail-info-row__value">{{ recordData.caseInfo.basicInfomation || '暂无' }}</span>
                            </div>
                            <div class="history-detail-info-row" v-if="recordData.caseInfo.physicalExamination">
                                <span class="history-detail-info-row__label">体格检查</span>
                                <span class="history-detail-info-row__value">{{ recordData.caseInfo.physicalExamination }}</span>
                            </div>
                        </div>
                    </div>

                    <!-- 对话记录 -->
                    <div class="history-detail-section" v-if="messages.length">
                        <div class="history-detail-section__header">
                            <el-icon :size="20" color="#5ed6c8"><ChatDotRound /></el-icon>
                            <h4 class="history-detail-section__title">医患对话</h4>
                            <el-tag type="info" size="small" effect="plain">共 {{ messages.length }} 条消息</el-tag>
                        </div>
                        <div class="history-detail-section__body">
                            <div class="history-detail-conversation">
                                <div v-for="(msg, idx) in messages" :key="idx"
                                     class="history-detail-msg"
                                     :class="msg.role">
                                    <div class="history-detail-msg__avatar">
                                        <el-icon :size="16" v-if="msg.role === 'patient'"><UserFilled /></el-icon>
                                        <el-icon :size="16" v-else><User /></el-icon>
                                    </div>
                                    <div class="history-detail-msg__content">
                                        <div class="history-detail-msg__role">
                                            {{ msg.role === 'patient' ? '患者' : '医生' }}
                                        </div>
                                        <div class="history-detail-msg__text">{{ msg.content }}</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- 检查记录 -->
                    <div class="history-detail-section" v-if="exams.length">
                        <div class="history-detail-section__header">
                            <el-icon :size="20" color="#5ed6c8"><DocumentChecked /></el-icon>
                            <h4 class="history-detail-section__title">辅助检查</h4>
                            <el-tag type="warning" size="small" effect="plain">共 {{ exams.length }} 项检查</el-tag>
                        </div>
                        <div class="history-detail-section__body">
                            <div class="history-detail-exam-list">
                                <div v-for="(exam, idx) in exams" :key="idx"
                                     class="history-detail-exam-item"
                                     :class="exam.result === '无' ? 'history-detail-exam-item--none' : 'history-detail-exam-item--has'">
                                    <div class="history-detail-exam-item__name">{{ exam.name }}</div>
                                    <div class="history-detail-exam-item__result">
                                        {{ exam.result === '无' ? '无此项检查' : exam.result }}
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- 病历书写 -->
                    <div class="history-detail-section" v-if="caseForm">
                        <div class="history-detail-section__header">
                            <el-icon :size="20" color="#5ed6c8"><EditPen /></el-icon>
                            <h4 class="history-detail-section__title">病历书写</h4>
                        </div>
                        <div class="history-detail-section__body">
                            <div class="history-detail-case-form">
                                <div class="history-detail-cf-row" v-if="caseForm.name">
                                    <span class="history-detail-cf-label">姓名</span>
                                    <span class="history-detail-cf-value">{{ caseForm.name }}</span>
                                </div>
                                <div class="history-detail-cf-row" v-if="caseForm.age">
                                    <span class="history-detail-cf-label">年龄</span>
                                    <span class="history-detail-cf-value">{{ caseForm.age }}</span>
                                </div>
                                <div class="history-detail-cf-row" v-if="caseForm.gender">
                                    <span class="history-detail-cf-label">性别</span>
                                    <span class="history-detail-cf-value">{{ caseForm.gender }}</span>
                                </div>
                                <div class="history-detail-cf-row" v-if="caseForm.chiefComplaint">
                                    <span class="history-detail-cf-label">主诉</span>
                                    <span class="history-detail-cf-value">{{ caseForm.chiefComplaint }}</span>
                                </div>
                                <div class="history-detail-cf-row" v-if="caseForm.familyHistory">
                                    <span class="history-detail-cf-label">家族史</span>
                                    <span class="history-detail-cf-value">{{ caseForm.familyHistory }}</span>
                                </div>
                                <div class="history-detail-cf-row" v-if="caseForm.pastHistory">
                                    <span class="history-detail-cf-label">既往史</span>
                                    <span class="history-detail-cf-value">{{ caseForm.pastHistory }}</span>
                                </div>
                                <div class="history-detail-cf-row" v-if="caseForm.physicalExam">
                                    <span class="history-detail-cf-label">体格检查</span>
                                    <span class="history-detail-cf-value">{{ caseForm.physicalExam }}</span>
                                </div>
                                <div class="history-detail-cf-row" v-if="caseForm.mentalExam">
                                    <span class="history-detail-cf-label">精神检查</span>
                                    <span class="history-detail-cf-value">{{ caseForm.mentalExam }}</span>
                                </div>
                                <div class="history-detail-cf-row" v-if="caseForm.auxiliaryExam">
                                    <span class="history-detail-cf-label">辅助检查</span>
                                    <span class="history-detail-cf-value">{{ caseForm.auxiliaryExam }}</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- 诊断结果 -->
                    <div class="history-detail-section" v-if="diagnosis">
                        <div class="history-detail-section__header">
                            <el-icon :size="20" color="#5ed6c8"><CircleCheckFilled /></el-icon>
                            <h4 class="history-detail-section__title">诊断结果</h4>
                        </div>
                        <div class="history-detail-section__body">
                            <div class="history-detail-diagnosis">
                                <!-- 新格式：多个诊断 -->
                                <template v-if="diagnosis.diagnoses && diagnosis.diagnoses.length">
                                    <div v-for="(dx, idx) in diagnosis.diagnoses" :key="idx" class="history-detail-diagnosis-group">
                                        <div class="history-detail-diagnosis-group__header">
                                            <el-tag type="success" size="small" effect="plain" round>{{ dx.category }}</el-tag>
                                        </div>
                                        <div class="history-detail-diagnosis-group__items" v-if="dx.diseases && dx.diseases.length">
                                            <el-tag v-for="(dis, di) in dx.diseases" :key="di" size="small" round style="margin: 2px 4px 2px 0;">{{ dis }}</el-tag>
                                        </div>
                                        <div v-else class="history-detail-diagnosis-group__none">未选择具体疾病</div>
                                    </div>
                                </template>
                                <!-- 旧格式：单个诊断 -->
                                <template v-else>
                                    <div class="history-detail-diagnosis__item">
                                        <span class="history-detail-diagnosis__label">诊断类别</span>
                                        <span class="history-detail-diagnosis__value">{{ diagnosis.category }}</span>
                                    </div>
                                    <div class="history-detail-diagnosis__item">
                                        <span class="history-detail-diagnosis__label">具体病症</span>
                                        <span class="history-detail-diagnosis__value">{{ diagnosis.disease }}</span>
                                    </div>
                                </template>
                                <div class="history-detail-diagnosis__item">
                                    <span class="history-detail-diagnosis__label">诊断理由</span>
                                    <span class="history-detail-diagnosis__value">{{ diagnosis.reason }}</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- 治疗方案 -->
                    <div class="history-detail-section" v-if="treatment">
                        <div class="history-detail-section__header">
                            <el-icon :size="20" color="#5ed6c8"><FirstAidKit /></el-icon>
                            <h4 class="history-detail-section__title">治疗方案</h4>
                        </div>
                        <div class="history-detail-section__body">
                            <div class="history-detail-treatment">
                                <div class="history-detail-treatment__item">
                                    <span class="history-detail-treatment__label">药物治疗</span>
                                    <span class="history-detail-treatment__value">{{ treatment['药物治疗'] || '无' }}</span>
                                </div>
                                <div class="history-detail-treatment__item">
                                    <span class="history-detail-treatment__label">心理治疗</span>
                                    <span class="history-detail-treatment__value">{{ treatment['心理治疗'] || '无' }}</span>
                                </div>
                                <div class="history-detail-treatment__item">
                                    <span class="history-detail-treatment__label">神经调控与其他躯体治疗</span>
                                    <span class="history-detail-treatment__value">{{ treatment['神经调控与其他躯体治疗'] || '无' }}</span>
                                </div>
                                <div class="history-detail-treatment__item">
                                    <span class="history-detail-treatment__label">社会心理干预与康复治疗</span>
                                    <span class="history-detail-treatment__value">{{ treatment['社会心理干预与康复治疗'] || '无' }}</span>
                                </div>
                                <div class="history-detail-treatment__item">
                                    <span class="history-detail-treatment__label">辅助治疗</span>
                                    <span class="history-detail-treatment__value">{{ treatment['辅助治疗'] || '无' }}</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- 综合评估报告 -->
                    <div class="history-detail-section" v-if="evaluationReport">
                        <div class="history-detail-section__header">
                            <el-icon :size="20" color="#3ec4b0"><CircleCheckFilled /></el-icon>
                            <h4 class="history-detail-section__title">综合评估报告</h4>
                            <el-tag type="success" size="small" effect="plain">全流程评价完成</el-tag>
                        </div>
                        <div class="history-detail-section__body">
                            <!-- 访谈评价 -->
                            <div class="history-detail-eval-block" v-if="evaluationReport.phase1 && !evaluationReport.phase1._fallback">
                                <h5 class="history-detail-eval-block__title">一、访谈评价</h5>
                                <div class="history-detail-eval-block__body">
                                    <div v-if="evaluationReport.phase1.conversation_stats" class="history-detail-eval-sub">
                                        <span>对话轮数: {{ evaluationReport.phase1.conversation_stats.total_turns }}</span>
                                        <span class="history-detail-eval-sub__sep">|</span>
                                        <span>医生发言: {{ evaluationReport.phase1.conversation_stats.doctor_turns }}</span>
                                        <span class="history-detail-eval-sub__sep">|</span>
                                        <span>患者发言: {{ evaluationReport.phase1.conversation_stats.patient_turns }}</span>
                                    </div>
                                    <div v-if="evaluationReport.phase1.empathy_evaluation" class="history-detail-eval-sub">
                                        <span>共情等级: <strong>{{ evaluationReport.phase1.empathy_evaluation.empathy_level }}</strong></span>
                                    </div>
                                    <div v-if="evaluationReport.phase1.empathy_evaluation?.why_this_level" class="history-detail-eval-detail">
                                        {{ evaluationReport.phase1.empathy_evaluation.why_this_level }}
                                    </div>
                                    <div v-if="evaluationReport.phase1.profession_evaluation" class="history-detail-eval-sub">
                                        <span>专业度得分: <strong>{{ formatScore(evaluationReport.phase1.profession_evaluation.total_score) }}</strong> / {{ evaluationReport.phase1.profession_evaluation.question_count * 2 }}</span>
                                    </div>
                                </div>
                            </div>

                            <!-- 检查评价 -->
                            <div class="history-detail-eval-block" v-if="evaluationReport.phase2 && !evaluationReport.phase2._fallback">
                                <h5 class="history-detail-eval-block__title">二、检查评价</h5>
                                <div class="history-detail-eval-block__body">
                                    <div v-if="evaluationReport.phase2.accuracy !== undefined" class="history-detail-eval-sub">
                                        <span>检查正确率: <strong>{{ formatAccuracy(evaluationReport.phase2.accuracy) }}</strong></span>
                                    </div>
                                    <div v-if="evaluationReport.phase2.exam_details" class="history-detail-eval-exam-list">
                                        <div v-for="(detail, key) in evaluationReport.phase2.exam_details" :key="key"
                                             class="history-detail-eval-exam-item"
                                             :class="detail?.correct ? 'history-detail-eval-exam-item--correct' : 'history-detail-eval-exam-item--wrong'">
                                            <span>{{ key }}</span>
                                            <span>{{ detail?.correct ? '正确' : '错误' }}</span>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <!-- 病历书写与诊断评价 -->
                            <div class="history-detail-eval-block" v-if="evaluationReport.phase3_full && !evaluationReport.phase3_full._fallback">
                                <h5 class="history-detail-eval-block__title">三、病历书写与诊断评价</h5>
                                <div class="history-detail-eval-block__body">
                                    <div v-if="evaluationReport.phase3_full.case_writing" class="history-detail-eval-sub-block">
                                        <div class="history-detail-eval-sub">
                                            <span>病历书写总分: <strong>{{ formatScore(evaluationReport.phase3_full.case_writing.total_score) }}</strong></span>
                                        </div>
                                        <div v-for="(section, key) in evaluationReport.phase3_full.case_writing.dimensions" :key="key" class="history-detail-eval-sub">
                                            <span>{{ section.section_name }}: {{ formatPercentage(section) }}</span>
                                            <span v-if="section.detail" class="history-detail-eval-sub__detail">— {{ section.detail }}</span>
                                        </div>
                                    </div>
                                    <div v-if="evaluationReport.phase3_full.diagnosis" class="history-detail-eval-sub-block">
                                        <div class="history-detail-eval-sub">
                                            <span>疾病类型得分: <strong>{{ formatScore(evaluationReport.phase3_full.diagnosis.disease_type?.score) }}</strong></span>
                                            <span v-if="evaluationReport.phase3_full.diagnosis.disease_type?.detail" class="history-detail-eval-sub__detail">— {{ evaluationReport.phase3_full.diagnosis.disease_type.detail }}</span>
                                        </div>
                                        <div v-if="evaluationReport.phase3_full.diagnosis.disease_type?.metrics" class="history-detail-eval-sub">
                                            <span>P: {{ (evaluationReport.phase3_full.diagnosis.disease_type.metrics.precision * 100).toFixed(0) }}%</span>
                                            <span>R: {{ (evaluationReport.phase3_full.diagnosis.disease_type.metrics.recall * 100).toFixed(0) }}%</span>
                                            <span>F1: {{ (evaluationReport.phase3_full.diagnosis.disease_type.metrics.f1 * 100).toFixed(0) }}%</span>
                                            <span>J: {{ (evaluationReport.phase3_full.diagnosis.disease_type.metrics.jaccard * 100).toFixed(0) }}%</span>
                                        </div>
                                        <div class="history-detail-eval-sub">
                                            <span>诊断正确性: <strong>{{ formatScore(evaluationReport.phase3_full.diagnosis.diagnostic_correctness?.score) }}</strong></span>
                                        </div>
                                        <div v-if="evaluationReport.phase3_full.diagnosis.diagnostic_correctness?.detail" class="history-detail-eval-detail">
                                            {{ evaluationReport.phase3_full.diagnosis.diagnostic_correctness.detail }}
                                        </div>
                                        <div class="history-detail-eval-sub">
                                            <span>诊断理由: <strong>{{ formatScore(evaluationReport.phase3_full.diagnosis.diagnostic_reasoning?.score) }}</strong></span>
                                        </div>
                                        <div v-if="evaluationReport.phase3_full.diagnosis.diagnostic_reasoning?.detail" class="history-detail-eval-detail">
                                            {{ evaluationReport.phase3_full.diagnosis.diagnostic_reasoning.detail }}
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <!-- 治疗评价 -->
                            <div class="history-detail-eval-block" v-if="evaluationReport.phase4 && !evaluationReport.phase4._fallback">
                                <h5 class="history-detail-eval-block__title">四、治疗评价</h5>
                                <div class="history-detail-eval-block__body">
                                    <div v-if="evaluationReport.phase4.treatment_stats" class="history-detail-eval-sub">
                                        <span>已填方案: {{ evaluationReport.phase4.treatment_stats.filled_categories }}</span>
                                        <span class="history-detail-eval-sub__sep">|</span>
                                        <span>未填方案: {{ evaluationReport.phase4.treatment_stats.empty_categories }}</span>
                                        <span class="history-detail-eval-sub__sep">|</span>
                                        <span>方案总数: {{ evaluationReport.phase4.treatment_stats.total_categories }}</span>
                                    </div>
                                    <div v-if="evaluationReport.phase4.treatment_stats?.details" class="history-detail-eval-tx-list">
                                        <div v-for="(detail, key) in evaluationReport.phase4.treatment_stats.details" :key="key" class="history-detail-eval-tx-item">
                                            <span class="history-detail-eval-tx-item__label">{{ key }}</span>
                                            <span class="history-detail-eval-tx-item__value">{{ detail }}</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- 空状态 -->
                    <div v-if="!loading && !recordData.caseInfo && !messages.length && !exams.length && !caseForm && !diagnosis"
                         class="history-detail-empty">
                        <el-icon :size="48" color="#c0c4cc"><DocumentDelete /></el-icon>
                        <p>暂无问诊记录</p>
                    </div>
                </div>
            </div>
        </div>
    `,

    data() {
        return {
            loading: true,
            caseId: '',
            recordData: {},
            hasDiagnosis: false,
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
        FirstAidKit() { return ElementPlusIconsVue.FirstAidKit; },
        DocumentDelete() { return ElementPlusIconsVue.DocumentDelete; },

        messages() {
            return this.recordData.messages || this.recordData.conversation || [];
        },

        exams() {
            return this.recordData.exams || [];
        },

        caseForm() {
            return this.recordData.caseForm || this.recordData.case_form || null;
        },

        diagnosis() {
            return this.recordData.diagnosis || null;
        },

        treatment() {
            return this.recordData.treatment || null;
        },

        evaluationReport() {
            return this.recordData.evaluation_report || null;
        },
    },

    methods: {
        goBack() {
            this.$router.push('/history');
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

        async loadDetail() {
            this.caseId = this.$route.query.record_id || this.$route.query.case_id || '';
            if (!this.caseId) {
                this.$message.warning('未找到历史记录');
                return;
            }

            try {
                this.loading = true;
                const data = await API.getHistoryDetail(this.caseId);
                this.recordData = data;
                this.hasDiagnosis = !!data.diagnosis;
            } catch (err) {
                console.error('[HistoryDetail] 加载历史详情失败:', err);
                this.$message.error('加载历史详情失败');
            } finally {
                this.loading = false;
            }
        },
    },

    mounted() {
        this.loadDetail();
    },
};
