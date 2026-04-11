/**
 * PatientList 组件
 * 医学生训练系统 — 患者选择页面
 *
 * 展示所有可训练的模拟患者（病例），点击后进入该患者的访谈页面。
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
                    <div class="patient-list-hero__badge">
                        <span class="pulse-dot"></span>
                    </div>
                    <h1 class="patient-list-hero__title">选择患者</h1>
                    <div class="hero-divider"></div>
                </div>

                <!-- 搜索 -->
                <div class="patient-list-search">
                    <el-input
                        v-model="searchText"
                        placeholder="搜索患者信息…"
                        clearable
                        :prefix-icon="Search"
                        size="large"
                        class="patient-list-search__input"
                    />
                   
                   
                </div>

                <!-- 患者卡片列表 -->
                <div class="patient-list-grid" v-loading="loading">
                    <div v-for="(patient, index) in filteredPatients" :key="patient.id"
                         class="patient-card"
                         :style="{ animationDelay: (index * 0.06) + 's' }">
                        <div class="patient-card__info">
                            <div class="patient-card__name">患者 {{ patient.id }}</div>
                            <div class="patient-card__basic">{{ patient.basicInfomation || '暂无信息' }}</div>
                        </div>
                        <div class="patient-card__actions">
                            <el-button
                                type="primary"
                                round
                                size="default"
                                @click.stop="selectPatient(patient)"
                                class="patient-card__action-btn"
                            >
                                <el-icon :size="16"><ChatDotRound /></el-icon>
                                开始问诊
                            </el-button>
                            <el-button
                                type="primary"
                                round
                                size="default"
                                @click.stop="viewRecord(patient)"
                                class="patient-card__record-btn"
                            >
                                <el-icon :size="16"><Document /></el-icon>
                                查看记录
                            </el-button>
                        </div>
                    </div>
                </div>

                <el-empty v-if="!loading && filteredPatients.length === 0"
                          description="暂无匹配的患者" />
            </div>
        </div>
    `,

    data() {
        return {
            searchText: '',
            patients: [],
            loading: true,
        };
    },

    computed: {
        Search() { return ElementPlusIconsVue.Search; },
        User() { return ElementPlusIconsVue.User; },
        ChatDotRound() { return ElementPlusIconsVue.ChatDotRound; },
        FirstAidKit() { return ElementPlusIconsVue.FirstAidKit; },
        SwitchButton() { return ElementPlusIconsVue.SwitchButton; },
        Document() { return ElementPlusIconsVue.Document; },

        filteredPatients() {
            if (!this.searchText) return this.patients;
            const q = this.searchText.toLowerCase();
            return this.patients.filter(p => {
                const id = (p.id || '').toLowerCase();
                const info = (p.basicInfomation || '').toLowerCase();
                const complaints = (p.chiefComplaint || []).join(' ').toLowerCase();
                return id.includes(q) || info.includes(q) || complaints.includes(q);
            });
        },
    },

    methods: {
        async loadData() {
            this.loading = true;
            try {
                const res = await API.getCases();
                this.patients = res.cases || [];
            } catch (e) {
                this.$message.error('加载患者列表失败');
                console.error(e);
            } finally {
                this.loading = false;
            }
        },

        selectPatient(patient) {
            this.$router.push({
                path: '/phase1',
                query: { id: patient.id },
            });
        },

        viewRecord(patient) {
            this.$router.push({
                path: '/record',
                query: { id: patient.id },
            });
        },

        handleLogout() {
            this.$router.push('/login');
        },
    },

    mounted() {
        this.loadData();
    },
};
