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
                                <div class="history-detail-diagnosis__item">
                                    <span class="history-detail-diagnosis__label">诊断类别</span>
                                    <span class="history-detail-diagnosis__value">{{ diagnosis.category }}</span>
                                </div>
                                <div class="history-detail-diagnosis__item">
                                    <span class="history-detail-diagnosis__label">具体病症</span>
                                    <span class="history-detail-diagnosis__value">{{ diagnosis.disease }}</span>
                                </div>
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
    },

    methods: {
        goBack() {
            this.$router.push('/history');
        },

        async loadDetail() {
            this.caseId = this.$route.query.case_id || '';
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
