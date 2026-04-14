/**
 * Phase4Treatment 组件
 * Phase 4 — 诊疗
 *
 * 布局仿照 Phase 3 病历书写：
 *   左侧 — 患者基本信息、辅助检查结果、诊断结果（可滚动）
 *   右侧 — 五大治疗类别填写区域
 */
const Phase4Treatment = {
    template: `
        <div class="phase4-page">
            <!-- 背景图 -->
            <div class="phase4-page__bg"></div>

            <!-- 顶部栏 -->
            <header class="phase4-header">
                <div class="phase4-header__left">
                    <el-button text @click="goBack" class="phase4-header__back-btn">
                        <el-icon><ArrowLeft /></el-icon>
                        返回
                    </el-button>
                    <h3 class="phase4-header__title">诊疗</h3>
                    <span class="phase4-header__subtitle">第四阶段</span>
                </div>
                <div class="phase4-header__right">
                    <span class="phase4-header__patient">
                        患者 {{ caseId }}
                    </span>
                    <el-button
                        type="primary"
                        size="small"
                        round
                        @click="handleComplete"
                        :loading="submitting"
                        class="phase4-header__complete-btn"
                    >
                        完成诊疗
                    </el-button>
                </div>
            </header>

            <!-- 主内容 -->
            <div class="phase4-content phase4-content--split">
                <!-- 左侧：参考信息面板 -->
                <aside class="phase4-left-panel">
                    <!-- 患者基本信息 -->
                    <div class="phase4-panel-section" v-if="caseInfo">
                        <div class="phase4-panel-section__title">患者基本信息</div>
                        <div class="phase4-panel-section__content">
                            <div class="phase4-info-row">
                                <span class="phase4-info-row__label">基本信息</span>
                                <span class="phase4-info-row__value">{{ caseInfo.basicInfomation || '暂无' }}</span>
                            </div>
                        </div>
                    </div>

                    <!-- 辅助检查结果 -->
                    <div class="phase4-panel-section" v-if="Object.keys(phase2Results).length">
                        <div class="phase4-panel-section__title">辅助检查结果</div>
                        <div class="phase4-panel-section__content">
                            <div v-for="(result, exam) in phase2Results" :key="exam"
                                 class="phase4-exam-result-row"
                                 :class="result === '无' ? 'phase4-exam-result-row--none' : 'phase4-exam-result-row--has'">
                                <span class="phase4-exam-result-row__name">{{ exam }}</span>
                                <span class="phase4-exam-result-row__value">
                                    {{ result === '无' ? '无此项检查' : result }}
                                </span>
                            </div>
                        </div>
                    </div>

                    <!-- 诊断结果 -->
                    <div class="phase4-panel-section" v-if="diagnosis">
                        <div class="phase4-panel-section__title">诊断结果</div>
                        <div class="phase4-panel-section__content">
                            <div class="phase4-info-row">
                                <span class="phase4-info-row__label">诊断类别</span>
                                <span class="phase4-info-row__value">{{ diagnosis.category }}</span>
                            </div>
                            <div class="phase4-info-row">
                                <span class="phase4-info-row__label">具体病症</span>
                                <span class="phase4-info-row__value">{{ diagnosis.disease }}</span>
                            </div>
                        </div>
                    </div>
                </aside>

                <!-- 右侧：治疗填写 -->
                <main class="phase4-right-panel">
                    <div class="phase4-treatment-card">
                        <div class="phase4-treatment-card__header">
                            <h2 class="phase4-treatment-card__title">治疗方案</h2>
                            <p class="phase4-treatment-card__subtitle">
                                请根据诊断结果，填写治疗方案（未填写的项将自动记为"无"）
                            </p>
                        </div>

                        <!-- 五大治疗类别填写区 -->
                        <div class="case-info-readonly">
                            <div class="case-info-section">
                                <span class="case-info-section__label">药物治疗</span>
                                <textarea v-model="treatment.medication" class="case-info-section__input" rows="3" placeholder="请输入药物治疗方案"></textarea>
                            </div>
                            <div class="case-info-divider"></div>
                            <div class="case-info-section">
                                <span class="case-info-section__label">心理治疗</span>
                                <textarea v-model="treatment.psychotherapy" class="case-info-section__input" rows="3" placeholder="请输入心理治疗方案"></textarea>
                            </div>
                            <div class="case-info-divider"></div>
                            <div class="case-info-section">
                                <span class="case-info-section__label">神经调控与其他躯体治疗</span>
                                <textarea v-model="treatment.neuromodulation" class="case-info-section__input" rows="3" placeholder="请输入神经调控与其他躯体治疗方案"></textarea>
                            </div>
                            <div class="case-info-divider"></div>
                            <div class="case-info-section">
                                <span class="case-info-section__label">社会心理干预与康复治疗</span>
                                <textarea v-model="treatment.psychosocial" class="case-info-section__input" rows="3" placeholder="请输入社会心理干预与康复治疗方案"></textarea>
                            </div>
                            <div class="case-info-divider"></div>
                            <div class="case-info-section">
                                <span class="case-info-section__label">辅助治疗</span>
                                <textarea v-model="treatment.adjuvant" class="case-info-section__input" rows="3" placeholder="请输入辅助治疗方案"></textarea>
                            </div>
                        </div>

                        <!-- 提交按钮 -->
                        <div class="phase4-form__actions">
                            <el-button
                                type="primary"
                                size="large"
                                round
                                @click="handleComplete"
                                :loading="submitting"
                                :disabled="evalState !== 'idle'"
                                class="phase4-form__submit-btn"
                            >
                                完成诊疗
                            </el-button>
                        </div>
                    </div>
                </main>
            </div>

            <!-- 评价加载遮罩 -->
            <transition name="eval-fade">
                <div v-if="evalState === 'loading'" class="eval-overlay">
                    <div class="eval-overlay__content">
                        <img src="/static/bg/eval.png" alt="" class="eval-overlay__icon" />
                        <div class="eval-overlay__text">正在进行阶段评价…</div>
                        <div class="eval-overlay__subtext">分析诊疗方案合理性</div>
                    </div>
                </div>
            </transition>

            <!-- 评价结果面板 -->
            <transition name="eval-slide">
                <div v-if="evalState === 'showing' || evalState === 'done'" class="eval-panel">
                    <div class="eval-panel__inner">
                        <div class="eval-panel__header">
                            <el-icon :size="22" color="#5ed6c8"><CircleCheckFilled /></el-icon>
                            <h3 class="eval-panel__title">阶段评价完成</h3>
                            <el-tag type="success" size="small" effect="plain">Phase 4</el-tag>
                        </div>

                        <div class="eval-panel__body">
                            <!-- 治疗方案统计 -->
                            <div class="eval-section" v-if="evalData.treatment_stats">
                                <div class="eval-section__title">
                                    <el-icon :size="14" color="#5ed6c8"><MedicineBox /></el-icon>
                                    治疗方案
                                </div>
                                <div class="eval-stats">
                                    <div class="eval-stat">
                                        <span class="eval-stat__label">已填方案</span>
                                        <span class="eval-stat__value">{{ evalData.treatment_stats.filled_categories }}</span>
                                    </div>
                                    <div class="eval-stat">
                                        <span class="eval-stat__label">未填方案</span>
                                        <span class="eval-stat__value">{{ evalData.treatment_stats.empty_categories }}</span>
                                    </div>
                                    <div class="eval-stat">
                                        <span class="eval-stat__label">方案总数</span>
                                        <span class="eval-stat__value">{{ evalData.treatment_stats.total_categories }}</span>
                                    </div>
                                </div>
                            </div>

                            <!-- 无评估数据提示 -->
                            <div v-if="!evalData.treatment_stats" class="eval-section eval-section--note">
                                <el-icon :size="16" color="#c0c4cc"><InfoFilled /></el-icon>
                                <span>评价服务暂时不可用，已跳过详细评估</span>
                            </div>
                        </div>

                        <div class="eval-panel__footer">
                            <el-button
                                type="primary"
                                size="large"
                                round
                                @click="confirmAndProceed"
                            >
                                好的，返回患者列表
                            </el-button>
                        </div>
                    </div>
                </div>
            </transition>
        </div>
    `,

    data() {
        return {
            caseId: '',
            caseInfo: null,
            phase2Results: {},
            diagnosis: null,
            treatment: {
                medication: '',
                psychotherapy: '',
                neuromodulation: '',
                psychosocial: '',
                adjuvant: '',
            },
            submitting: false,
            // 评价状态: 'idle' | 'loading' | 'showing' | 'done'
            evalState: 'idle',
            evalData: {},
            evalError: null,
        };
    },

    computed: {
        ArrowLeft() { return ElementPlusIconsVue.ArrowLeft; },
        CircleCheckFilled() { return ElementPlusIconsVue.CircleCheckFilled; },
        MedicineBox() { return ElementPlusIconsVue.MedicineBox; },
        InfoFilled() { return ElementPlusIconsVue.InfoFilled; },
    },

    methods: {
        async handleComplete() {
            if (this.evalState !== 'idle') return;
            this.submitting = true;
            try {
                // 空项自动补为"无"
                const treatmentRecord = {};
                const labels = {
                    medication: '药物治疗',
                    psychotherapy: '心理治疗',
                    neuromodulation: '神经调控与其他躯体治疗',
                    psychosocial: '社会心理干预与康复治疗',
                    adjuvant: '辅助治疗',
                };
                for (const [key, label] of Object.entries(labels)) {
                    treatmentRecord[label] = this.treatment[key] ? this.treatment[key].trim() : '无';
                }

                // 使用 record_id 确保所有数据整合到同一次问诊记录
                const recordId = sessionStorage.getItem('record_id') || this.caseId;

                await API.submitTreatment(recordId, treatmentRecord);

                await API.saveCaseRecord(recordId, {
                    treatment: treatmentRecord,
                });

                this.$message.success('第四阶段诊疗已完成');

                sessionStorage.setItem('phase4_result', JSON.stringify({
                    caseId: this.caseId,
                    treatment: treatmentRecord,
                }));

                // 进入评价流程
                await this.startEvaluation(treatmentRecord);
            } catch (err) {
                this.$message.error('提交失败: ' + (err.message || '未知错误'));
                console.error('[Phase4Treatment] 提交失败:', err);
            } finally {
                this.submitting = false;
            }
        },

        goBack() {
            this.$router.push('/phase3');
        },

        /**
         * 统一评价入口
         */
        async startEvaluation(treatmentRecord) {
            if (this.evalState !== 'idle') return;

            this.evalState = 'loading';
            this.evalError = null;
            this.evalData = {};

            try {
                console.log(`[Phase4Treatment] 开始评价 Phase 4, caseId=${this.caseId}`);
                this.evalData = await API.evaluatePhase(4, this.caseId, {
                    treatment: treatmentRecord,
                });
                console.log('[Phase4Treatment] 评价结果:', this.evalData);
                this.evalState = 'showing';
            } catch (err) {
                console.error('[Phase4Treatment] 阶段评价失败:', err);
                this.evalError = err.message || '未知错误';
                // 即使失败也展示面板
                const categories = ['药物治疗', '心理治疗', '神经调控与其他躯体治疗', '社会心理干预与康复治疗', '辅助治疗'];
                const filled = Object.values(treatmentRecord).filter(v => v && v !== '无' && v.trim()).length;
                this.evalData = {
                    phase: 4,
                    phase_name: '诊疗',
                    case_id: this.caseId,
                    treatment_stats: {
                        filled_categories: filled,
                        empty_categories: categories.length - filled,
                        total_categories: categories.length,
                        details: treatmentRecord,
                    },
                    _fallback: true,
                };
                this.evalState = 'showing';
            }
        },

        /**
         * 用户确认评价后返回患者列表
         */
        confirmAndProceed() {
            if (this.evalState !== 'showing' && this.evalState !== 'done') return;
            this.evalState = 'done';
            this.$router.push('/patients');
        },

        async loadPhaseData() {
            // 加载病例基本信息
            if (this.caseId) {
                try {
                    const info = await API.getCaseInfo(this.caseId);
                    this.caseInfo = info;
                } catch (err) {
                    console.error('[Phase4Treatment] 加载患者信息失败:', err);
                }
            }

            // 加载 Phase 2 检查结果
            const resultsStr = sessionStorage.getItem('phase2_checkedResults');
            if (resultsStr) {
                try {
                    this.phase2Results = JSON.parse(resultsStr);
                } catch (err) {
                    console.error('[Phase4Treatment] 解析 Phase 2 结果失败:', err);
                }
            }

            // 加载 Phase 3 诊断结果
            const diagnosisStr = sessionStorage.getItem('phase3_result');
            if (diagnosisStr) {
                try {
                    const phase3Result = JSON.parse(diagnosisStr);
                    this.diagnosis = {
                        category: phase3Result.category,
                        disease: phase3Result.disease,
                    };
                } catch (err) {
                    console.error('[Phase4Treatment] 解析 Phase 3 诊断结果失败:', err);
                }
            }

            // 加载已保存的治疗数据（从 Phase 3 回退后再进入时保留）
            const savedTreatment = sessionStorage.getItem('phase4_treatment');
            if (savedTreatment) {
                try {
                    const parsed = JSON.parse(savedTreatment);
                    this.treatment = {
                        medication: parsed.medication || '',
                        psychotherapy: parsed.psychotherapy || '',
                        neuromodulation: parsed.neuromodulation || '',
                        psychosocial: parsed.psychosocial || '',
                        adjuvant: parsed.adjuvant || '',
                    };
                } catch (err) {
                    console.error('[Phase4Treatment] 解析已保存治疗方案失败:', err);
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

    beforeUnmount() {
        // 离开前保存当前填写内容到 sessionStorage，防止意外丢失
        sessionStorage.setItem('phase4_treatment', JSON.stringify(this.treatment));
    },
};
