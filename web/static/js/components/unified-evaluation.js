/**
 * UnifiedEvaluation 组件
 * 统一评价页面 — 在第四阶段（治疗阶段）结束后展示
 *
 * 两阶段展示：
 *   状态 1：正在统一评价（加载态）— 流水线动画 + 串行调用后端接口
 *   状态 2：评价完成（结果态）— 逐步展示四个阶段评价结果
 *
 * 数据全部来自后端评价接口，不自创分数
 */
const UnifiedEvaluation = {
    template: `
        <div class="unified-eval-page">
            <!-- 背景图 -->
            <div class="unified-eval-page__bg"></div>

            <!-- 顶部品牌标题区 -->
            <div class="unified-eval-brand-center">
                <div class="unified-eval-brand-center__title">MentalEval</div>
                <div class="unified-eval-brand-center__divider"></div>
                <div class="unified-eval-brand-center__subtitle">COMPREHENSIVE CLINICAL EVALUATION</div>
            </div>

            <!-- 加载状态 -->
            <div v-if="loading" class="unified-eval-loading">
                <el-skeleton :rows="10" animated />
            </div>

            <!-- 状态 1：正在生成综合评估（流水线加载态） -->
            <div v-else-if="!allDone" class="eval-pipeline-page">
                <!-- 左侧：四阶段流程线（动态显示完成/正在评价） -->
                <div class="eval-pipeline__steps">
                    <div class="eval-pipeline-step"
                         v-for="(phase, idx) in phases" :key="phase.key"
                         :class="'eval-pipeline-step--' + phase.status">
                        <div class="eval-pipeline-step__circle">
                            <span class="eval-pipeline-step__num">{{ idx + 1 }}</span>
                        </div>
                        <span class="eval-pipeline-step__label">{{ phase.label }}</span>
                    </div>
                    <!-- 连接线 -->
                    <div class="eval-pipeline-connector"
                         v-for="(phase, idx) in phases.slice(0, 3)" :key="'c' + idx"
                         :class="{ 'eval-pipeline-connector--done': phase.status === 'done' }"></div>
                </div>

                <!-- 右侧核心：综合评价卡片 -->
                <div class="eval-pipeline__core">
                    <!-- 发光背景 -->
                    <div class="eval-pipeline__core-glow"></div>

                    <!-- eval.png 图标 + 呼吸光晕 -->
                    <div class="eval-pipeline__core-icon-wrap">
                        <div class="eval-pipeline__core-halo"></div>
                        <img src="/static/bg/eval.png" alt="" class="eval-pipeline__core-img eval-pipeline__core-img--breathing" />
                    </div>

                    <!-- 主标题 -->
                    <div class="eval-pipeline__core-title">MentalEval</div>
                    <div class="eval-pipeline__core-subtitle">GENERATING COMPREHENSIVE EVALUATION...</div>

                    <!-- 中文核心状态 -->
                    <div class="eval-pipeline__core-status">正在评价【{{ currentPhaseLabel }}】阶段...</div>
                    <div class="eval-pipeline__core-detail">{{ currentPhaseDetail }}</div>

                    <!-- 进度条 -->
                    <div class="eval-pipeline__progress">
                        <div class="eval-pipeline__progress-bar eval-pipeline__progress-bar--flowing"></div>
                    </div>
                </div>
            </div>

            <!-- 状态 2：评价结果展示 -->
            <div v-else class="unified-eval-content">
                <!-- 全部失败回退提示 -->
                <div v-if="allPhasesFailed" class="eval-error-banner">
                    <el-alert type="error" :closable="false" show-icon>
                        <template #title>评价流程失败</template>
                        所有评价阶段均未能完成，请刷新页面后重试。
                    </el-alert>
                </div>

                <!-- 结果头部 — 只保留品牌图标，去掉重复文字 -->
                <div v-else class="eval-result-header">
                    <div class="eval-result-header__brand">
                        <img src="/static/bg/eval.png" alt="" class="eval-result-header__icon" />
                    </div>
                </div>

                <!-- 阶段结果卡片 -->
                <div class="eval-result-cards">
                    <!-- Phase 1 -->
                    <transition name="eval-card-fade" appear>
                        <div class="eval-result-card" v-if="report.phase1 && !report.phase1._fallback">
                            <div class="eval-result-card__header">
                                <div class="eval-result-card__phase-num">1</div>
                                <h3 class="eval-result-card__title">访谈评价</h3>
                                <el-tag size="small" type="success" effect="plain">已完成</el-tag>
                            </div>
                            <div class="eval-result-card__body">
                                <!-- 对话统计 -->
                                <div class="eval-section" v-if="report.phase1.conversation_stats">
                                    <div class="eval-section__label">对话统计</div>
                                    <div class="eval-stats">
                                        <div class="eval-stat">
                                            <span class="eval-stat__label">总轮数</span>
                                            <span class="eval-stat__value">{{ report.phase1.conversation_stats.total_turns }}</span>
                                        </div>
                                        <div class="eval-stat">
                                            <span class="eval-stat__label">医生发言</span>
                                            <span class="eval-stat__value">{{ report.phase1.conversation_stats.doctor_turns }}</span>
                                        </div>
                                        <div class="eval-stat">
                                            <span class="eval-stat__label">患者发言</span>
                                            <span class="eval-stat__value">{{ report.phase1.conversation_stats.patient_turns }}</span>
                                        </div>
                                    </div>
                                </div>
                                <!-- 共情度评估 -->
                                <div class="eval-section" v-if="report.phase1.empathy_evaluation">
                                    <div class="eval-section__label">共情度评估</div>
                                    <div class="eval-empathy">
                                        <div class="eval-hp-bar">
                                            <div class="eval-hp-bar__track">
                                                <div class="eval-hp-bar__fill"
                                                     :style="hpBarStyle(report.phase1.empathy_evaluation.empathy_level || 0)"
                                                ></div>
                                            </div>
                                            <span class="eval-hp-bar__text">{{ empathyLevelDisplay(report.phase1.empathy_evaluation.empathy_level || 0) }}</span>
                                        </div>
                                        <div class="eval-empathy__reason" v-if="report.phase1.empathy_evaluation.why_this_level">
                                            {{ report.phase1.empathy_evaluation.why_this_level }}
                                        </div>
                                        <div class="eval-empathy__evidence" v-if="report.phase1.empathy_evaluation.evidence">
                                            <span class="eval-empathy__evidence-label">证据：</span>
                                            {{ report.phase1.empathy_evaluation.evidence }}
                                        </div>
                                    </div>
                                </div>
                                <!-- 专业度评估 -->
                                <div class="eval-section" v-if="report.phase1.profession_evaluation">
                                    <div class="eval-section__label">专业度评估</div>
                                    <div class="eval-profession">
                                        <div class="eval-profession__value">{{ report.phase1.profession_evaluation.total_score }}</div>
                                        <div class="eval-profession__max">/ {{ report.phase1.profession_evaluation.question_count * 2 }}</div>
                                        <div class="eval-profession__avg">
                                            平均分 {{ report.phase1.profession_evaluation.average_score.toFixed(2) }}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </transition>

                    <!-- Phase 2 -->
                    <transition name="eval-card-fade" appear :style="{ animationDelay: '0.15s' }">
                        <div class="eval-result-card" v-if="report.phase2 && !report.phase2._fallback">
                            <div class="eval-result-card__header">
                                <div class="eval-result-card__phase-num">2</div>
                                <h3 class="eval-result-card__title">检查评价</h3>
                                <el-tag size="small" type="success" effect="plain">已完成</el-tag>
                            </div>
                            <div class="eval-result-card__body">
                                <div class="eval-section">
                                    <div class="eval-section__label">检查正确率</div>
                                    <div class="eval-accuracy-display">
                                        <span class="eval-accuracy-value">{{ formatAccuracy(report.phase2.accuracy) }}</span>
                                        <span class="eval-accuracy-subtitle">基于金标准计算</span>
                                    </div>
                                </div>
                                <div class="eval-section" v-if="report.phase2.exam_details">
                                    <div class="eval-section__label">详细结果</div>
                                    <div class="eval-exam-details">
                                        <div v-for="(detail, key) in report.phase2.exam_details" :key="key"
                                             class="eval-exam-item">
                                            <span class="eval-exam-item__name">{{ key }}</span>
                                            <span class="eval-exam-item__result"
                                                  :class="detail?.correct ? 'eval-exam--correct' : 'eval-exam--wrong'">
                                                {{ detail?.correct ? '正确' : '错误' }}
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </transition>

                    <!-- Phase 3 -->
                    <transition name="eval-card-fade" appear :style="{ animationDelay: '0.3s' }">
                        <div class="eval-result-card eval-result-card--dual" v-if="report.phase3_full && !report.phase3_full._fallback">
                            <div class="eval-result-card__header">
                                <div class="eval-result-card__phase-num">3</div>
                                <h3 class="eval-result-card__title">病历书写与诊断评价</h3>
                                <el-tag size="small" type="success" effect="plain">已完成</el-tag>
                            </div>
                            <div class="eval-result-card__body dual-columns">
                                <!-- 左侧：病历书写 -->
                                <div class="dual-column">
                                    <div class="dual-column__header">
                                        <el-icon :size="14" color="#5ed6c8"><Document /></el-icon>
                                        <span>病历书写评价</span>
                                    </div>
                                    <div class="dual-column__body">
                                        <template v-if="caseWritingEval">
                                            <div class="eval-overall-score">
                                                <span class="eval-overall-score__value">{{ formatScore(caseWritingEval.total_score) }}</span>
                                                <span class="eval-overall-score__label">病历书写总分</span>
                                            </div>
                                            <div class="eval-writing-sections">
                                                <div v-for="(section, key) in caseWritingEval.dimensions" :key="key"
                                                     class="eval-writing-item">
                                                    <div class="eval-writing-item__header">
                                                        <span class="eval-writing-item__name">{{ section.section_name }}</span>
                                                        <span class="eval-writing-item__score" :class="scoreClass(section.score)">
                                                            {{ formatPercentage(section) }}
                                                        </span>
                                                    </div>
                                                    <div class="eval-writing-item__detail">{{ section.detail }}</div>
                                                    <div v-if="section.coverage_percentage !== undefined" class="eval-writing-item__sub">
                                                        <span>覆盖度 {{ section.coverage_percentage.toFixed(0) }}%</span>
                                                        <span class="eval-writing-item__sub-sep">|</span>
                                                        <span>准确度 {{ section.accuracy_percentage.toFixed(0) }}%</span>
                                                    </div>
                                                </div>
                                            </div>
                                        </template>
                                        <div v-else class="eval-note">
                                            <span>病历书写评价数据不可用</span>
                                        </div>
                                    </div>
                                </div>
                                <!-- 右侧：诊断 -->
                                <div class="dual-column">
                                    <div class="dual-column__header">
                                        <el-icon :size="14" color="#409eff"><Notebook /></el-icon>
                                        <span>诊断评价</span>
                                    </div>
                                    <div class="dual-column__body">
                                        <template v-if="diagnosisEval">
                                            <div class="eval-overall-score">
                                                <span class="eval-overall-score__value">{{ formatScore(diagnosisEval.total_score) }}</span>
                                                <span class="eval-overall-score__label">诊断总分</span>
                                            </div>
                                            <div class="eval-diagnosis-dimensions">
                                                <div class="eval-diag-item">
                                                    <span class="eval-diag-item__label">疾病类型</span>
                                                    <span class="eval-diag-item__score" :class="scoreClass(diagnosisEval.disease_type?.score)">
                                                        {{ formatScore(diagnosisEval.disease_type?.score) }}
                                                    </span>
                                                </div>
                                                <div class="eval-diag-item__detail">{{ diagnosisEval.disease_type?.detail }}</div>
                                                <div v-if="diagnosisEval.disease_type?.metrics" class="eval-diag-metrics">
                                                    <span class="eval-diag-metrics__label">P:</span><span :class="evalDiagMetricClass(diagnosisEval.disease_type.metrics.precision)">{{ (diagnosisEval.disease_type.metrics.precision * 100).toFixed(0) }}%</span>
                                                    <span class="eval-diag-metrics__label">R:</span><span :class="evalDiagMetricClass(diagnosisEval.disease_type.metrics.recall)">{{ (diagnosisEval.disease_type.metrics.recall * 100).toFixed(0) }}%</span>
                                                    <span class="eval-diag-metrics__label">F1:</span><span :class="evalDiagMetricClass(diagnosisEval.disease_type.metrics.f1)">{{ (diagnosisEval.disease_type.metrics.f1 * 100).toFixed(0) }}%</span>
                                                    <span class="eval-diag-metrics__label">J:</span><span :class="evalDiagMetricClass(diagnosisEval.disease_type.metrics.jaccard)">{{ (diagnosisEval.disease_type.metrics.jaccard * 100).toFixed(0) }}%</span>
                                                </div>
                                                <div class="eval-diag-item">
                                                    <span class="eval-diag-item__label">诊断正确性</span>
                                                    <span class="eval-diag-item__score" :class="scoreClass(diagnosisEval.diagnostic_correctness?.score)">
                                                        {{ formatScore(diagnosisEval.diagnostic_correctness?.score) }}
                                                    </span>
                                                </div>
                                                <div class="eval-diag-item__detail">{{ diagnosisEval.diagnostic_correctness?.detail }}</div>
                                                <div class="eval-diag-item">
                                                    <span class="eval-diag-item__label">诊断理由</span>
                                                    <span class="eval-diag-item__score" :class="scoreClass(diagnosisEval.diagnostic_reasoning?.score)">
                                                        {{ formatScore(diagnosisEval.diagnostic_reasoning?.score) }}
                                                    </span>
                                                </div>
                                                <div class="eval-diag-item__detail">{{ diagnosisEval.diagnostic_reasoning?.detail }}</div>
                                            </div>
                                        </template>
                                        <div v-else class="eval-note">
                                            <span>诊断评价数据不可用</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </transition>

                    <!-- Phase 4 -->
                    <transition name="eval-card-fade" appear :style="{ animationDelay: '0.45s' }">
                        <div class="eval-result-card" v-if="report.phase4 && !report.phase4._fallback">
                            <div class="eval-result-card__header">
                                <div class="eval-result-card__phase-num">4</div>
                                <h3 class="eval-result-card__title">治疗评价</h3>
                                <el-tag size="small" type="success" effect="plain">已完成</el-tag>
                            </div>
                            <div class="eval-result-card__body">
                                <div class="eval-section" v-if="report.phase4.treatment_stats">
                                    <div class="eval-section__label">治疗方案统计</div>
                                    <div class="eval-stats">
                                        <div class="eval-stat">
                                            <span class="eval-stat__label">已填方案</span>
                                            <span class="eval-stat__value">{{ report.phase4.treatment_stats.filled_categories }}</span>
                                        </div>
                                        <div class="eval-stat">
                                            <span class="eval-stat__label">未填方案</span>
                                            <span class="eval-stat__value">{{ report.phase4.treatment_stats.empty_categories }}</span>
                                        </div>
                                        <div class="eval-stat">
                                            <span class="eval-stat__label">方案总数</span>
                                            <span class="eval-stat__value">{{ report.phase4.treatment_stats.total_categories }}</span>
                                        </div>
                                    </div>
                                </div>
                                <div v-if="report.phase4.treatment_stats?.details" class="eval-section">
                                    <div class="eval-section__label">治疗详情评价</div>
                                    <div class="eval-treatment-details">
                                        <div v-for="(detail, key) in report.phase4.treatment_stats.details" :key="key"
                                             class="eval-treatment-item">
                                            <span class="eval-treatment-item__label">{{ key }}</span>
                                            <span class="eval-treatment-item__value">{{ detail }}</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </transition>
                </div>

                <!-- 底部操作按钮 -->
                <div class="eval-result-footer">
                    <el-button
                        type="primary"
                        size="large"
                        round
                        @click="goToPatients"
                        class="eval-result-footer__btn"
                    >
                        <el-icon :size="16"><HomeFilled /></el-icon>
                        返回患者列表
                    </el-button>
                    <el-button
                        size="large"
                        round
                        @click="goToHistory"
                        class="eval-result-footer__btn"
                    >
                        查看历史记录
                    </el-button>
                </div>
            </div>
        </div>
    `,

    data() {
        return {
            caseId: '',
            report: {
                phase1: null,
                phase2: null,
                phase3_full: null,
                phase4: null,
            },
            loading: true,
            allDone: false,

            // 流水线阶段状态
            phases: [
                { key: 'phase1', label: '访谈', status: 'pending' },   // pending / loading / done / error
                { key: 'phase2', label: '检查', status: 'pending' },
                { key: 'phase3', label: '诊断', status: 'pending' },
                { key: 'phase4', label: '治疗', status: 'pending' },
            ],

            // 各阶段说明文字
            phaseDetails: {
                phase1: '正在分析访谈质量与临床技巧',
                phase2: '正在分析检查项目选择与合理性',
                phase3: '正在分析诊断与病例书写质量',
                phase4: '正在分析治疗方案完整性与合理性',
            },

            retrying: false,
        };
    },

    computed: {
        Document() { return ElementPlusIconsVue.Document; },
        Notebook() { return ElementPlusIconsVue.Notebook; },
        HomeFilled() { return ElementPlusIconsVue.HomeFilled; },

        /** 从 phase3_full 中提取病历书写评价 */
        caseWritingEval() {
            if (this.report.phase3_full && this.report.phase3_full.case_writing) {
                return this.report.phase3_full.case_writing;
            }
            return null;
        },

        /** 从 phase3_full 中提取诊断评价 */
        diagnosisEval() {
            if (this.report.phase3_full && this.report.phase3_full.diagnosis) {
                return this.report.phase3_full.diagnosis;
            }
            return null;
        },

        /** 是否所有评价阶段都失败了 */
        allPhasesFailed() {
            return this.phases.every(p => p.status === 'error');
        },

        /** 当前正在评价的阶段名称 */
        currentPhaseLabel() {
            const loading = this.phases.find(p => p.status === 'loading');
            if (loading) return loading.label;
            const pending = this.phases.find(p => p.status === 'pending');
            if (pending) return pending.label;
            return '综合';
        },

        /** 当前评价阶段说明文字 */
        currentPhaseDetail() {
            const loading = this.phases.find(p => p.status === 'loading');
            if (loading) return this.phaseDetails[loading.key] || '';
            return '正在生成综合评估报告...';
        },
    },

    methods: {
        /**
         * 统一评价入口：串行调用四个阶段评价接口
         */
        async startUnifiedEvaluation() {
            // Phase 1
            await this.evaluatePhase1();

            // Phase 2
            await this.evaluatePhase2();

            // Phase 3
            await this.evaluatePhase3();

            // Phase 4
            await this.evaluatePhase4();

            // 评价流程结束（无论是否有阶段失败，都保存已获取的数据）
            this.allDone = true;
            await this.saveFinalRecord();
        },

        /**
         * Phase 1: 访谈评价
         */
        async evaluatePhase1() {
            this.phases[0].status = 'loading';
            try {
                const messagesStr = sessionStorage.getItem('phase2_messages');
                if (messagesStr) {
                    const messages = JSON.parse(messagesStr);
                    this.report.phase1 = await API.evaluatePhase(1, this.caseId, { messages });
                } else {
                    this.report.phase1 = { _fallback: true, error: '无访谈数据' };
                }
                this.phases[0].status = 'done';
            } catch (err) {
                console.error('[UnifiedEval] Phase 1 评价失败:', err);
                this.report.phase1 = { _fallback: true, error: err.message };
                this.phases[0].status = 'error';
            }
        },

        /**
         * Phase 2: 检查评价
         */
        async evaluatePhase2() {
            this.phases[1].status = 'loading';
            try {
                const phase2Results = JSON.parse(sessionStorage.getItem('phase2_checkedResults') || '{}');
                this.report.phase2 = await API.getPhase2Accuracy(this.caseId, phase2Results);
                this.phases[1].status = 'done';
            } catch (err) {
                console.error('[UnifiedEval] Phase 2 评价失败:', err);
                this.report.phase2 = { _fallback: true, error: err.message };
                this.phases[1].status = 'error';
            }
        },

        /**
         * Phase 3: 病历书写 + 诊断评价
         */
        async evaluatePhase3() {
            this.phases[2].status = 'loading';
            try {
                const phase3Result = JSON.parse(sessionStorage.getItem('phase3_result') || '{}');
                if (phase3Result && phase3Result.caseForm) {
                    this.report.phase3_full = await API.evaluatePhase(3, this.caseId, {
                        case_form: phase3Result.caseForm,
                        diagnosis: {
                            category: phase3Result.category,
                            disease: phase3Result.disease,
                            reason: phase3Result.reason,
                            diagnoses: phase3Result.diagnoses,
                        },
                    });
                } else {
                    this.report.phase3_full = { _fallback: true, error: '无诊断数据' };
                }
                this.phases[2].status = 'done';
            } catch (err) {
                console.error('[UnifiedEval] Phase 3 评价失败:', err);
                this.report.phase3_full = { _fallback: true, error: err.message };
                this.phases[2].status = 'error';
            }
        },

        /**
         * Phase 4: 治疗评价
         */
        async evaluatePhase4() {
            this.phases[3].status = 'loading';
            try {
                const phase4Str = sessionStorage.getItem('phase4_result');
                let treatmentRecord = {};
                if (phase4Str) {
                    const parsed = JSON.parse(phase4Str);
                    treatmentRecord = parsed.treatment || {};
                }
                this.report.phase4 = await API.evaluatePhase(4, this.caseId, { treatment: treatmentRecord });
                this.phases[3].status = 'done';
            } catch (err) {
                console.error('[UnifiedEval] Phase 4 评价失败:', err);
                this.report.phase4 = { _fallback: true, error: err.message };
                this.phases[3].status = 'error';
            }
        },

        /**
         * 保存最终记录到后端 — 包含全流程数据 + 评价报告
         */
        async saveFinalRecord() {
            const recordId = sessionStorage.getItem('record_id') || this.caseId;
            console.log('[UnifiedEval] 开始保存，recordId:', recordId);
            try {
                // 从 sessionStorage 收集全流程数据
                let conversation = null;
                try {
                    const msgsStr = sessionStorage.getItem('phase2_messages');
                    if (msgsStr) conversation = JSON.parse(msgsStr);
                } catch (e) { /* ignore */ }

                let exams = null;
                try {
                    const examsStr = sessionStorage.getItem('phase2_checkedResults');
                    if (examsStr) {
                        const parsed = JSON.parse(examsStr);
                        exams = Object.entries(parsed).map(([name, result]) => ({ name, result }));
                    }
                } catch (e) { /* ignore */ }

                let caseForm = null, diagnosis = null;
                try {
                    const phase3Str = sessionStorage.getItem('phase3_result');
                    if (phase3Str) {
                        const p3 = JSON.parse(phase3Str);
                        if (p3.caseForm) caseForm = p3.caseForm;
                        diagnosis = {
                            category: p3.category,
                            disease: p3.disease,
                            reason: p3.reason,
                            diagnoses: p3.diagnoses,
                        };
                    }
                } catch (e) { /* ignore */ }

                let treatment = null;
                try {
                    const phase4Str = sessionStorage.getItem('phase4_result');
                    if (phase4Str) {
                        const p4 = JSON.parse(phase4Str);
                        treatment = p4.treatment || {};
                    }
                } catch (e) { /* ignore */ }

                // 一次性提交全流程数据 + 评价报告
                const payload = { evaluation_report: this.report };
                if (conversation) payload.conversation = conversation;
                if (exams) payload.exams = exams;
                if (caseForm) { payload.caseForm = caseForm; }
                if (diagnosis) payload.diagnosis = diagnosis;
                if (treatment) payload.treatment = treatment;

                console.log('[UnifiedEval] 提交 payload keys:', Object.keys(payload));
                console.log('[UnifiedEval] evaluation_report keys:', this.report ? Object.keys(this.report) : 'null');

                const result = await API.saveCaseRecord(recordId, payload);
                console.log('[UnifiedEval] 全流程记录已保存:', recordId, result);
                this.$message.success('评价报告已保存');
            } catch (err) {
                console.error('[UnifiedEval] 保存评价报告失败:', err);
                this.$message.warning('评价报告保存失败: ' + err.message);
            }
            // 同时保存到 sessionStorage 供后续查看
            sessionStorage.setItem('unified_eval_report', JSON.stringify(this.report));
        },

        /** 根据分数返回 CSS 类 */
        scoreClass(score) {
            if (score === null || score === undefined) return 'score--none';
            if (score >= 0.8) return 'score--excellent';
            if (score >= 0.5) return 'score--good';
            if (score >= 0.3) return 'score--fair';
            return 'score--poor';
        },

        /** 诊断指标 CSS 类 */
        evalDiagMetricClass(value) {
            if (value === null || value === undefined) return 'diag-metric--none';
            if (value >= 0.8) return 'diag-metric--good';
            if (value >= 0.5) return 'diag-metric--mid';
            return 'diag-metric--low';
        },

        /** 格式化分数 */
        formatScore(score) {
            if (score === null || score === undefined) return '--';
            return (score * 100).toFixed(0) + '%';
        },

        /** 格式化百分比 */
        formatPercentage(section) {
            if (section.percentage !== undefined) return section.percentage.toFixed(0) + '%';
            if (section.score !== undefined) return (section.score * 100).toFixed(0) + '%';
            return '--';
        },

        /** 格式化正确率 */
        formatAccuracy(acc) {
            if (acc === null || acc === undefined) return '--';
            return (acc * 100).toFixed(1) + '%';
        },

        /** 5分制血条样式 — 每1分=20%，颜色从红到绿 */
        hpBarStyle(score) {
            const pct = Math.min(100, Math.max(0, (score / 5) * 100));
            // 颜色渐变：红(0%) -> 橙(25%) -> 黄(50%) -> 绿(100%)
            let color;
            if (pct <= 20) color = 'linear-gradient(90deg, #f56c6c, #f78989)';
            else if (pct <= 40) color = 'linear-gradient(90deg, #e6a23c, #f0c78a)';
            else if (pct <= 60) color = 'linear-gradient(90deg, #e6c13c, #f0d48a)';
            else if (pct <= 80) color = 'linear-gradient(90deg, #67c23a, #95d479)';
            else color = 'linear-gradient(90deg, #3ec4b0, #5ed6c8)';
            return { width: pct + '%', background: color };
        },

        /** 血条分数显示文字 */
        empathyLevelDisplay(score) {
            const rounded = Math.round(score);
            return `${rounded} / 5`;
        },

        /** 返回患者列表 — 清理本次问诊的临时数据 */
        goToPatients() {
            const keys = ['phase2_messages', 'phase2_checkedResults', 'phase3_result', 'phase4_result', 'unified_eval_report'];
            keys.forEach(k => sessionStorage.removeItem(k));
            this.$router.push('/patients');
        },

        /** 查看历史记录 */
        goToHistory() {
            this.$router.push('/history');
        },

        /** 加载页面 */
        init() {
            this.caseId = this.$route.query.id || '';
            if (!this.caseId) {
                this.$message.warning('未找到病例信息');
                this.loading = false;
                return;
            }

            this.loading = false;
            // 进入评价流程
            this.startUnifiedEvaluation();
        },
    },

    mounted() {
        this.init();
    },
};
