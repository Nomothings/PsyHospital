/**
 * Vue 3 应用入口 + 路由配置
 */

// ---- 路由定义 ----
const routes = [
    // 启动页
    { path: "/", component: SplashPage },
    // 登录 / 注册
    { path: "/login", component: LoginPage },
    { path: "/register", component: LoginPage },
    // 患者选择 → 访谈
    { path: "/patients", component: PatientList },
    { path: "/phase1", component: Interview },
    // Phase 2: 检查选择
    { path: "/phase2", component: Phase2Check },
    // Phase 3: 诊断
    { path: "/phase3", component: Phase3Diagnosis },
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

// ---- 挂载 ----
app.mount("#app");
