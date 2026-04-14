/**
 * Phase2Check 组件
 * Phase 2 — 检查选择场景
 *
 * 左侧 — 辅助检查项目列表
 * 右侧 — 选中检查项的结果展示（从患者病例中读取）
 */
const Phase2Check = {
    template: `
        <div class="phase2-page">
            <!-- 背景图 -->
            <div class="phase2-page__bg"></div>

            <!-- 顶部栏 -->
            <header class="phase2-header">
                <div class="phase2-header__left">
                    <el-button text @click="goBack" class="phase2-header__back-btn">
                        <el-icon><ArrowLeft /></el-icon>
                        返回
                    </el-button>
                    <h3 class="phase2-header__title">检查选择</h3>
                    <span class="phase2-header__subtitle">第二阶段</span>
                </div>
                <div class="phase2-header__right">
                    <span class="phase2-header__patient">
                        患者 {{ caseId }}
                    </span>
                    <el-button
                        type="primary"
                        size="small"
                        round
                        @click="handleEndPhase"
                        :disabled="evalState !== 'idle'"
                        class="phase2-header__next-btn"
                    >
                        结束阶段
                    </el-button>
                </div>
            </header>

            <!-- 主内容 -->
            <div class="phase2-content">
                <!-- 左侧: 检查项目列表 -->
                <aside class="phase2-sidebar">
                    <div class="phase2-sidebar__title">辅助检查项目</div>
                    <div class="phase2-sidebar__list">
                        <div
                            v-for="(exam, idx) in examItems"
                            :key="idx"
                            class="phase2-category-item"
                            :class="{
                                'phase2-category-item--active': selectedExam === exam,
                                'phase2-category-item--positive': checkedResults[exam] && checkedResults[exam] !== '无',
                                'phase2-category-item--negative': checkedResults[exam] === '无',
                            }"
                            @click="selectExam(exam)"
                        >
                            <span class="phase2-category-item__text">{{ exam }}</span>
                            <span class="phase2-category-item__status" v-if="checkedResults[exam] !== undefined">
                                <el-tag
                                    :type="checkedResults[exam] === '无' ? 'info' : 'success'"
                                    size="small"
                                >
                                    {{ checkedResults[exam] === '无' ? '无' : '有结果' }}
                                </el-tag>
                            </span>
                        </div>
                    </div>
                </aside>

                <!-- 右侧: 结果展示区 -->
                <main class="phase2-result">
                    <!-- 未选中任何检查 -->
                    <div v-if="!selectedExam" class="phase2-result__placeholder">
                        <el-icon :size="48" color="#c0c4cc"><Select /></el-icon>
                        <p>请从左侧选择一项辅助检查</p>
                    </div>

                    <!-- 加载中 -->
                    <div v-else-if="loading" class="phase2-result__loading">
                        <el-skeleton :rows="6" animated />
                    </div>

                    <!-- 检查结果 -->
                    <div v-else class="phase2-result__content">
                        <div class="phase2-result__header">
                            <h4 class="phase2-result__category">{{ selectedExam }}</h4>
                            <el-tag
                                :type="currentResult === '无' ? 'info' : 'success'"
                                size="large"
                            >
                                {{ currentResult === '无' ? '无此项检查' : '有结果' }}
                            </el-tag>
                        </div>

                        <el-divider />

                        <!-- 有结果 -->
                        <div v-if="currentResult !== '无'" class="phase2-result__evidence">
                            <div class="phase2-result__evidence-title">检查结果</div>
                            <div class="phase2-exam-result-text">
                                {{ currentResult }}
                            </div>
                        </div>

                        <!-- 无结果 -->
                        <div v-else class="phase2-result__none">
                            <el-empty description="该患者病例中无此项检查记录" />
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
                        <div class="eval-overlay__subtext">分析检查选择合理性</div>
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
                            <el-tag type="success" size="small" effect="plain">Phase 2</el-tag>
                        </div>

                        <div class="eval-panel__body">
                            <!-- 检查统计 -->
                            <div class="eval-section" v-if="evalData.exam_stats">
                                <div class="eval-section__title">
                                    <el-icon :size="14" color="#5ed6c8"><DocumentChecked /></el-icon>
                                    检查统计
                                </div>
                                <div class="eval-stats">
                                    <div class="eval-stat">
                                        <span class="eval-stat__label">已做检查</span>
                                        <span class="eval-stat__value">{{ evalData.exam_stats.total_examined }}</span>
                                    </div>
                                    <div class="eval-stat">
                                        <span class="eval-stat__label">阳性结果</span>
                                        <span class="eval-stat__value">{{ evalData.exam_stats.positive_results }}</span>
                                    </div>
                                    <div class="eval-stat">
                                        <span class="eval-stat__label">阴性结果</span>
                                        <span class="eval-stat__value">{{ evalData.exam_stats.negative_results }}</span>
                                    </div>
                                </div>
                            </div>

                            <!-- 评价指标 (如果有核心评价器结果) -->
                            <div class="eval-section" v-if="evalData.metrics">
                                <div class="eval-section__title">
                                    <el-icon :size="14" color="#409eff"><DataAnalysis /></el-icon>
                                    评价指标
                                </div>
                                <div class="eval-stats">
                                    <div class="eval-stat">
                                        <span class="eval-stat__label">Precision</span>
                                        <span class="eval-stat__value">{{ (evalData.metrics.precision * 100).toFixed(1) }}%</span>
                                    </div>
                                    <div class="eval-stat">
                                        <span class="eval-stat__label">Recall</span>
                                        <span class="eval-stat__value">{{ (evalData.metrics.recall * 100).toFixed(1) }}%</span>
                                    </div>
                                    <div class="eval-stat">
                                        <span class="eval-stat__label">F1</span>
                                        <span class="eval-stat__value">{{ (evalData.metrics.f1 * 100).toFixed(1) }}%</span>
                                    </div>
                                </div>
                            </div>

                            <!-- 无评估数据提示 -->
                            <div v-if="!evalData.exam_stats && !evalData.metrics" class="eval-section eval-section--note">
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
                                好的，进入下一阶段
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
            examItems: [
                "心电图",
                "脑电图",
                "头颅 CT",
                "头颅 MRI",
                "胸部 X 线",
                "腹部 B 超",
                "血常规",
                "生化检查",
                "甲状腺功能",
                "毒物筛查",
            ],
            selectedExam: null,
            loading: false,
            checkedResults: {},
            // 评价状态: 'idle' | 'loading' | 'showing' | 'done'
            evalState: 'idle',
            evalData: {},
            evalError: null,
        };
    },

    computed: {
        ArrowLeft() { return ElementPlusIconsVue.ArrowLeft; },
        Select() { return ElementPlusIconsVue.Select; },
        CircleCheckFilled() { return ElementPlusIconsVue.CircleCheckFilled; },
        DocumentChecked() { return ElementPlusIconsVue.DocumentChecked; },
        DataAnalysis() { return ElementPlusIconsVue.DataAnalysis; },
        InfoFilled() { return ElementPlusIconsVue.InfoFilled; },

        currentResult() {
            if (!this.selectedExam) return null;
            return this.checkedResults[this.selectedExam] || null;
        },
    },

    methods: {
        async selectExam(exam) {
            if (this.checkedResults[exam] !== undefined) {
                this.selectedExam = exam;
                return;
            }

            this.selectedExam = exam;
            this.loading = true;

            try {
                const result = await API.checkExam(this.caseId, exam);
                this.checkedResults[exam] = result;
            } catch (err) {
                console.error('[Phase2Check] 检查查询失败:', err);
                this.checkedResults[exam] = '无';
            } finally {
                this.loading = false;
            }
        },

        goBack() {
            this.$router.push({ path: '/phase1', query: { id: this.caseId } });
        },

        /**
         * 拦截"结束阶段"按钮，先进入评价流程
         */
        async handleEndPhase() {
            if (this.evalState !== 'idle') return;
            await this.startEvaluation();
        },

        /**
         * 统一评价入口（来自 EvalMixin 模式）
         */
        async startEvaluation() {
            if (this.evalState !== 'idle') return;

            // 先保存检查数据到 sessionStorage
            sessionStorage.setItem('phase2_checkedResults', JSON.stringify(this.checkedResults));
            const recordId = sessionStorage.getItem('record_id') || this.caseId;
            const examRecords = Object.entries(this.checkedResults).map(([name, result]) => ({
                name,
                result,
            }));
            API.saveCaseRecord(recordId, {
                exams: examRecords,
            }).catch(err => console.error('[Phase2Check] 保存记录失败:', err));

            // 进入评价流程
            this.evalState = 'loading';
            this.evalError = null;
            this.evalData = {};

            try {
                console.log(`[Phase2Check] 开始评价 Phase 2, caseId=${this.caseId}`);
                this.evalData = await API.evaluatePhase(2, this.caseId, {
                    exam_results: this.checkedResults,
                });
                console.log('[Phase2Check] 评价结果:', this.evalData);
                this.evalState = 'showing';
            } catch (err) {
                console.error('[Phase2Check] 阶段评价失败:', err);
                this.evalError = err.message || '未知错误';
                // 即使失败也展示面板，附带基础统计
                this.evalData = {
                    phase: 2,
                    phase_name: '检查选择',
                    case_id: this.caseId,
                    exam_stats: {
                        total_examined: Object.keys(this.checkedResults).length,
                        positive_results: Object.values(this.checkedResults).filter(v => v && v !== '无').length,
                        negative_results: Object.values(this.checkedResults).filter(v => !v || v === '无').length,
                    },
                    _fallback: true,
                };
                this.evalState = 'showing';
            }
        },

        /**
         * 用户确认评价后进入下一阶段
         */
        confirmAndProceed() {
            if (this.evalState !== 'showing' && this.evalState !== 'done') return;
            this.evalState = 'done';
            this.$router.push({ path: '/phase3', query: { id: this.caseId } });
        },
    },

    mounted() {
        this.caseId = this.$route.query.id || sessionStorage.getItem('phase2_caseId') || '';
    },
};
