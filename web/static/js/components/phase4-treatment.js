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
                                class="phase4-form__submit-btn"
                            >
                                完成诊疗
                            </el-button>
                        </div>
                    </div>
                </main>
            </div>
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
        };
    },

    computed: {
        ArrowLeft() { return ElementPlusIconsVue.ArrowLeft; },
    },

    methods: {
        async handleComplete() {
            if (this.submitting) return;
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

                // 直接跳转到统一评价页，由评价页自行调用后端接口
                this.$router.push({ path: '/evaluation', query: { id: this.caseId } });
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
