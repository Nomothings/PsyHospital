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
                        :disabled="saving"
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

            <!-- 保存状态提示 -->
            <transition name="eval-fade">
                <div v-if="saving" class="eval-overlay">
                    <div class="eval-overlay__content">
                        <img src="/static/bg/eval.png" alt="" class="eval-overlay__icon" />
                        <div class="eval-overlay__text">正在保存数据…</div>
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
            // 保存状态
            saving: false,
            // 检查正确率（来自后端接口，暂存用于后续统一评价）
            accuracyValue: null,
        };
    },

    computed: {
        ArrowLeft() { return ElementPlusIconsVue.ArrowLeft; },
        Select() { return ElementPlusIconsVue.Select; },

        currentResult() {
            if (!this.selectedExam) return null;
            return this.checkedResults[this.selectedExam] || null;
        },

        accuracyText() {
            if (this.accuracyValue === null || this.accuracyValue === undefined) return '--';
            return (this.accuracyValue * 100).toFixed(1) + '%';
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
         * 拦截"结束阶段"按钮，保存数据并进入下一阶段
         */
        async handleEndPhase() {
            if (this.saving) return;

            this.saving = true;

            // 调用后端接口获取检查正确率（暂存，统一评价时使用）
            try {
                console.log('[Phase2Check] 提交正确率计算, caseId:', this.caseId, 'examResults:', this.checkedResults);
                const res = await API.getPhase2Accuracy(this.caseId, this.checkedResults);
                console.log('[Phase2Check] 后端返回响应:', res);
                this.accuracyValue = res.accuracy;
                console.log('[Phase2Check] 设置 accuracyValue:', this.accuracyValue, '显示文本:', this.accuracyText);
            } catch (err) {
                console.error('[Phase2Check] 获取正确率失败:', err);
                this.accuracyValue = null;
            }

            // 保存检查数据到 sessionStorage
            sessionStorage.setItem('phase2_checkedResults', JSON.stringify(this.checkedResults));
            const recordId = sessionStorage.getItem('record_id') || this.caseId;
            const examRecords = Object.entries(this.checkedResults).map(([name, result]) => ({
                name,
                result,
            }));
            API.saveCaseRecord(recordId, {
                exams: examRecords,
            }).catch(err => console.error('[Phase2Check] 保存记录失败:', err));

            this.$router.push({ path: '/phase3', query: { id: this.caseId } });
        },
    },

    mounted() {
        this.caseId = this.$route.query.id || sessionStorage.getItem('phase2_caseId') || '';
    },
};
