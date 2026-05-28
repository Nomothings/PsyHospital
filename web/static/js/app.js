/**
 * Vue 3 Application Entry + Router Configuration
 */

// ---- Route Definitions ----
const routes = [
    { path: "/", component: SplashPage },
    { path: "/login", component: LoginPage },
    { path: "/register", component: LoginPage },
    { path: "/patients", component: PatientList },
    { path: "/phase1", component: Interview },
    { path: "/phase2", component: Phase2Check },
    { path: "/phase3", component: Phase3Diagnosis },
    { path: "/phase4", component: Phase4Treatment },
    { path: "/evaluation", component: UnifiedEvaluation },
    { path: "/record", component: CaseRecord },
    { path: "/history", component: HistoryList },
    { path: "/history-detail", component: HistoryDetail },
];

const router = VueRouter.createRouter({
    history: VueRouter.createWebHashHistory(),
    routes,
});

// ---- Vue Application Creation ----
const { createApp } = Vue;

const app = createApp({
    template: `
        <div>
            <router-view></router-view>
        </div>
    `,
});

// ---- Register Element Plus ----
app.use(ElementPlus);

// ---- Register Router ----
app.use(router);

// ---- Register All Element Plus Icons ----
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
    app.component(key, component);
}

// ---- Register Global Components ----
app.component('phase-transition-pipeline', PhaseTransitionPipeline);

// ---- Mount ----
app.mount("#app");
