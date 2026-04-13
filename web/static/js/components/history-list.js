/**
 * HistoryList 组件
 * 问诊历史记录列表页面
 */
const HistoryList = {
    template: `
        <div class="history-list-page">
            <!-- 背景 -->
            <div class="history-list-page__bg"></div>

            <!-- 顶部导航 -->
            <header class="history-list-header">
                <div class="history-list-header__left">
                    <el-button text @click="goBack" class="history-list-header__back-btn">
                        <el-icon><ArrowLeft /></el-icon>
                        返回
                    </el-button>
                    <h3 class="history-list-header__title">问诊历史记录</h3>
                </div>
            </header>

            <!-- 主内容 -->
            <div class="history-list-content" v-loading="loading">
                <!-- 记录列表 -->
                <div class="history-list-card" v-if="filteredHistories.length">
                    <div
                        v-for="item in filteredHistories"
                        :key="item.record_id"
                        class="history-item"
                        @click="viewDetail(item)"
                    >
                        <div class="history-item__left">
                            <div class="history-item__patient">
                                <el-icon :size="18" color="#5ed6c8"><UserFilled /></el-icon>
                                <span class="history-item__id">患者 {{ item.case_id }}</span>
                            </div>
                            <div class="history-item__info">
                                <span class="history-item__time">{{ formatTime(item.saved_at) }}</span>
                                <span class="history-item__turns">{{ item.turns }} 轮对话</span>
                                <el-tag v-if="item.has_diagnosis" type="success" size="small" effect="plain">已完成诊断</el-tag>
                            </div>
                        </div>
                        <div class="history-item__right">
                            <el-button text type="primary" size="small">
                                查看详情 <el-icon><ArrowRight /></el-icon>
                            </el-button>
                        </div>
                    </div>
                </div>

                <!-- 空状态 -->
                <div v-if="!loading && !filteredHistories.length" class="history-list-empty">
                    <el-icon :size="48" color="#c0c4cc"><DocumentDelete /></el-icon>
                    <p>暂无问诊历史</p>
                </div>
            </div>
        </div>
    `,

    data() {
        return {
            loading: true,
            histories: [],
            mode: '',
        };
    },

    computed: {
        ArrowLeft() { return ElementPlusIconsVue.ArrowLeft; },
        ArrowRight() { return ElementPlusIconsVue.ArrowRight; },
        UserFilled() { return ElementPlusIconsVue.UserFilled; },
        DocumentDelete() { return ElementPlusIconsVue.DocumentDelete; },

        filteredHistories() {
            if (!this.mode) return this.histories;
            // mode 参数暂不用于过滤，直接返回全部
            return this.histories;
        },
    },

    methods: {
        goBack() {
            this.$router.push('/patients');
        },

        formatTime(isoString) {
            if (!isoString) return '未知';
            const d = new Date(isoString);
            const pad = n => String(n).padStart(2, '0');
            return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
        },

        async loadHistory() {
            try {
                this.loading = true;
                const data = await API.getHistoryList();
                this.histories = data.histories || [];
            } catch (err) {
                console.error('[HistoryList] 加载历史记录失败:', err);
                this.$message.error('加载历史记录失败');
            } finally {
                this.loading = false;
            }
        },

        viewDetail(item) {
            this.$router.push({
                path: '/history-detail',
                query: { record_id: item.record_id },
            });
        },
    },

    mounted() {
        this.mode = this.$route.query.mode || '';
        this.loadHistory();
    },
};
