/**
 * PatientList Component
 * Medical student training system - Mode selection page
 *
 * Dual-mode entry: Standard mode vs Rare disease mode
 * After selection, randomly draw a patient from the corresponding pool and enter the interview directly
 */
const PatientList = {
    template: `
        <div class="patient-list-page">
            <!-- Background -->
            <div class="patient-list-page__bg"></div>
            <div class="patient-list-page__overlay"></div>

            <!-- Top Navigation -->
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
                        Logout
                    </el-button>
                </div>
            </header>

            <!-- Main Content -->
            <div class="patient-list-content">
                <!-- Title Area -->
                <div class="patient-list-hero">
                    <h1 class="patient-list-hero__title">Choose Interview Mode</h1>
                    <p class="patient-list-hero__subtitle">Choose Your Training Mode</p>
                </div>

                <!-- Mode Selection Cards -->
                <div class="mode-cards" v-loading="loading">
                    <!-- Standard Mode -->
                    <div class="mode-card mode-card--common" @click="selectMode('common')">
                        <div class="mode-card__icon">
                            <el-icon :size="40"><User /></el-icon>
                        </div>
                        <h3 class="mode-card__title">Standard Mode</h3>
                        <p class="mode-card__subtitle">Common Psychiatric Cases</p>
                        <div class="mode-card__desc">
                            Covers high-frequency psychiatric cases including depression, anxiety, schizophrenia, etc. Suitable for building foundational interview skills.
                        </div>
                        <div class="mode-card__meta">
                            <span class="mode-card__count">
                                <el-icon :size="14"><Files /></el-icon>
                                {{ commonCount }} cases
                            </span>
                        </div>
                        <el-button
                            type="primary"
                            round
                            size="large"
                            class="mode-card__btn"
                        >
                            <el-icon :size="18"><ChatDotRound /></el-icon>
                            Start Interview
                        </el-button>
                        <div class="mode-card__history-link" @click.stop="viewHistory('common')">
                            <el-icon :size="14"><Document /></el-icon>
                            View History
                        </div>
                    </div>

                    <!-- Rare Disease Mode -->
                    <div class="mode-card mode-card--rare" @click="selectMode('rare')">
                        <div class="mode-card__icon">
                            <el-icon :size="40"><WarningFilled /></el-icon>
                        </div>
                        <h3 class="mode-card__title">Rare Disease Mode</h3>
                        <p class="mode-card__subtitle">Complex / Low Probability / High Difficulty</p>
                        <div class="mode-card__desc">
                            Contains rare and complex psychiatric cases with high challenge. Suitable for advanced training and differential diagnosis skill development.
                        </div>
                        <div class="mode-card__meta">
                            <span class="mode-card__count">
                                <el-icon :size="14"><Files /></el-icon>
                                {{ rareCount }} cases
                            </span>
                        </div>
                        <el-button
                            type="warning"
                            round
                            size="large"
                            class="mode-card__btn mode-card__btn--rare"
                        >
                            <el-icon :size="18"><ChatDotRound /></el-icon>
                            Start Interview
                        </el-button>
                        <div class="mode-card__history-link" @click.stop="viewHistory('rare')">
                            <el-icon :size="14"><Document /></el-icon>
                            View History
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
                this.$message.error('Failed to select random patient, please try again');
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
                console.error('Failed to load case counts:', e);
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
