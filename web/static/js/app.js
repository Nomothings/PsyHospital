/**
 * Vue 3 应用入口 + 路由配置
 */

// ---- 路由定义 ----
const routes = [
    { path: "/", component: SplashPage },
    { path: "/login", component: LoginPage },
    { path: "/register", component: LoginPage },
    { path: "/patients", component: PatientList },
    { path: "/phase1", component: Interview },
    { path: "/phase2", component: Phase2Check },
    { path: "/phase3", component: Phase3Diagnosis },
    { path: "/phase4", component: Phase4Treatment },
    { path: "/record", component: CaseRecord },
    { path: "/history", component: HistoryList },
    { path: "/history-detail", component: HistoryDetail },
];

const router = VueRouter.createRouter({
    history: VueRouter.createWebHashHistory(),
    routes,
});

// ---- Vue 应用创建 ----
const { createApp } = Vue;

const app = createApp({
    template: `
        <div>
            <router-view></router-view>
        </div>
    `,
});

// ---- 注册 Element Plus ----
app.use(ElementPlus);

// ---- 注册路由 ----
app.use(router);

// ---- 注册所有 Element Plus Icons ----
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
    app.component(key, component);
}

// ---- 注册全局组件 ----
app.component('phase-transition-pipeline', PhaseTransitionPipeline);

// ---- 挂载 ----
app.mount("#app");
