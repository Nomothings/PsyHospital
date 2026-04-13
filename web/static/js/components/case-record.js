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
                                <div class="case-record-diagnosis__item">
                                    <span class="case-record-diagnosis__label">诊断类别</span>
                                    <span class="case-record-diagnosis__value">{{ diagnosis.category }}</span>
                                </div>
                                <div class="case-record-diagnosis__item">
                                    <span class="case-record-diagnosis__label">具体病症</span>
                                    <span class="case-record-diagnosis__value">{{ diagnosis.disease }}</span>
                                </div>
                                <div class="case-record-diagnosis__item">
                                    <span class="case-record-diagnosis__label">诊断理由</span>
                                    <span class="case-record-diagnosis__value">{{ diagnosis.reason }}</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- 空状态 -->
                    <div v-if="!caseInfo && !conversationMessages.length && !examRecords.length && !caseText && !diagnosis"
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
    },

    methods: {
        goBack() {
            this.$router.push('/patients');
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
