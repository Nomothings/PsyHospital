/**
 * PatientList 组件
 * 医学生训练系统 — 模式选择页面
 *
 * 双模式入口：常规模式 vs 罕见病模式
 * 选择后随机抽取对应库中的患者，直接进入问诊
 */
const PatientList = {
    template: `
        <div class="patient-list-page">
            <!-- 背景 -->
            <div class="patient-list-page__bg"></div>
            <div class="patient-list-page__overlay"></div>

            <!-- 顶部导航 -->
            <header class="patient-list-header">
                <div class="patient-list-header__left">
                    <div class="patient-list-header__logo-mark">
                        <el-icon :size="20" color="#fff"><FirstAidKit /></el-icon>
                    </div>
                    <h2 class="patient-list-header__title">MentalHospital</h2>
                </div>
                <div class="patient-list-header__right">
                    <el-button text @click="handleLogout" class="patient-list-header__logout">
                        <el-icon><SwitchButton /></el-icon>
                        退出
                    </el-button>
                </div>
            </header>

            <!-- 主内容 -->
            <div class="patient-list-content">
                <!-- 标题区 -->
                <div class="patient-list-hero">
                    <h1 class="patient-list-hero__title">选择问诊模式</h1>
                    <p class="patient-list-hero__subtitle">Choose Your Training Mode</p>
                </div>

                <!-- 模式选择卡片 -->
                <div class="mode-cards" v-loading="loading">
                    <!-- 常规模式 -->
                    <div class="mode-card mode-card--common" @click="selectMode('common')">
                        <div class="mode-card__icon">
                            <el-icon :size="40"><User /></el-icon>
                        </div>
                        <h3 class="mode-card__title">常规模式</h3>
                        <p class="mode-card__subtitle">常见精神科病例</p>
                        <div class="mode-card__desc">
                            涵盖抑郁症、焦虑症、精神分裂症等精神科高频病例，
                            适合夯实基础问诊技能。
                        </div>
                        <div class="mode-card__meta">
                            <span class="mode-card__count">
                                <el-icon :size="14"><Files /></el-icon>
                                {{ commonCount }} 例
                            </span>
                        </div>
                        <el-button
                            type="primary"
                            round
                            size="large"
                            class="mode-card__btn"
                        >
                            <el-icon :size="18"><ChatDotRound /></el-icon>
                            开始问诊
                        </el-button>
                        <div class="mode-card__history-link" @click.stop="viewHistory('common')">
                            <el-icon :size="14"><Document /></el-icon>
                            查看历史记录
                        </div>
                    </div>

                    <!-- 罕见病模式 -->
                    <div class="mode-card mode-card--rare" @click="selectMode('rare')">
                        <div class="mode-card__icon">
                            <el-icon :size="40"><WarningFilled /></el-icon>
                        </div>
                        <h3 class="mode-card__title">罕见病模式</h3>
                        <p class="mode-card__subtitle">复杂 / 低概率 / 训练难度高</p>
                        <div class="mode-card__desc">
                            收录罕见及复杂精神科病例，挑战性高，
                            适合进阶训练与鉴别诊断能力培养。
                        </div>
                        <div class="mode-card__meta">
                            <span class="mode-card__count">
                                <el-icon :size="14"><Files /></el-icon>
                                {{ rareCount }} 例
                            </span>
                        </div>
                        <el-button
                            type="warning"
                            round
                            size="large"
                            class="mode-card__btn mode-card__btn--rare"
                        >
                            <el-icon :size="18"><ChatDotRound /></el-icon>
                            开始问诊
                        </el-button>
                        <div class="mode-card__history-link" @click.stop="viewHistory('rare')">
                            <el-icon :size="14"><Document /></el-icon>
                            查看历史记录
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `,

    data() {
        return {
            loading: true,
            commonCount: 0,
            rareCount: 0,
        };
    },

    computed: {
        User() { return ElementPlusIconsVue.User; },
        FirstAidKit() { return ElementPlusIconsVue.FirstAidKit; },
        SwitchButton() { return ElementPlusIconsVue.SwitchButton; },
        ChatDotRound() { return ElementPlusIconsVue.ChatDotRound; },
        WarningFilled() { return ElementPlusIconsVue.WarningFilled; },
        Files() { return ElementPlusIconsVue.Files; },
        Document() { return ElementPlusIconsVue.Document; },
    },

    methods: {
        async selectMode(mode) {
            try {
                this.loading = true;
                const res = await API.getRandomCase(mode);
                const caseId = res.case.id;
                this.$router.push({
                    path: '/phase1',
                    query: { id: caseId },
                });
            } catch (e) {
                this.$message.error('随机抽取患者失败，请重试');
                console.error(e);
            } finally {
                this.loading = false;
            }
        },

        async loadCounts() {
            try {
                const res = await API.getCaseCounts();
                const counts = res.counts || {};
                this.commonCount = counts.common || 0;
                this.rareCount = counts.rare || 0;
            } catch (e) {
                console.error('加载病例数量失败:', e);
            }
        },

        handleLogout() {
            this.$router.push('/login');
        },

        viewHistory(mode) {
            this.$router.push({
                path: '/history',
                query: { mode },
            });
        },
    },

    mounted() {
        this.loadCounts();
        this.loading = false;
    },
};
