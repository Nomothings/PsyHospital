/**
 * Splash 组件
 * 启动页 — 展示医院背景图，点击后进入登录界面
 */
const SplashPage = {
    template: `
        <div class="splash-page" @click="enterLogin">
            <div class="splash-page__bg"></div>
            <div class="splash-page__overlay"></div>
            <div class="splash-page__content">
                <h1 class="splash-page__title">Mental Hospital</h1>
                <div class="splash-page__hint">
                    <el-icon :size="20"><ArrowDown /></el-icon>
                    <span>点击进入</span>
                </div>
            </div>
        </div>
    `,

    computed: {
        FirstAidKit() { return ElementPlusIconsVue.FirstAidKit; },
        ArrowDown() { return ElementPlusIconsVue.ArrowDown; },
    },

    methods: {
        enterLogin() {
            this.$router.push('/login');
        },
    },
};
