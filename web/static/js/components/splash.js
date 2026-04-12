/**
 * Splash 组件
 * 启动页 — 展示医院背景图，点击后进入登录界面
 * 包含像素风标题 + 粒子背景效果
 */
const SplashPage = {
    template: `
        <div class="splash-page" @click="enterLogin">
            <!-- 背景层 -->
            <div class="splash-page__bg"></div>
            <div class="splash-page__overlay"></div>

            <!-- 粒子画布 -->
            <canvas ref="particleCanvas" class="splash-page__particles"></canvas>

            <!-- 内容层 -->
            <div class="splash-page__content">
                <div class="splash-page__title-wrap">
                    <h1 class="splash-page__title">MentalHospital</h1>
                    <div class="splash-page__title-glow"></div>
                </div>
                <div class="splash-page__hint">
                    <el-icon :size="20"><ArrowDown /></el-icon>
                    <span>点击进入</span>
                </div>
            </div>
        </div>
    `,

    data() {
        return {
            particles: [],
            animFrameId: null,
        };
    },

    computed: {
        ArrowDown() { return ElementPlusIconsVue.ArrowDown; },
    },

    methods: {
        enterLogin() {
            this.$router.push('/login');
        },

        /**
         * 初始化粒子系统
         * 粒子类型：小圆点(主) + 方块(像素点缀)
         * 运动：缓慢漂移 + 闪烁
         */
        initParticles() {
            const canvas = this.$refs.particleCanvas;
            if (!canvas) return;

            const dpr = window.devicePixelRatio || 1;
            const w = window.innerWidth;
            const h = window.innerHeight;
            canvas.width = w * dpr;
            canvas.height = h * dpr;
            canvas.style.width = w + 'px';
            canvas.style.height = h + 'px';

            const ctx = canvas.getContext('2d');
            ctx.scale(dpr, dpr);

            // 粒子颜色：绿色系 / 青绿色 / 白色
            const colors = [
                { r: 94, g: 214, b: 200 },  // 主题绿 #5ED6C8
                { r: 106, g: 232, b: 216 },  // 亮绿 #6AE8D8
                { r: 70, g: 180, b: 170 },   // 深绿 #46B4AA
                { r: 180, g: 240, b: 230 },  // 浅青绿
                { r: 220, g: 255, b: 245 },  // 近白绿
                { r: 255, g: 255, b: 255 },  // 白色
            ];

            // 生成粒子
            const count = Math.min(60, Math.floor(w * h / 25000));
            this.particles = [];
            for (let i = 0; i < count; i++) {
                const col = colors[Math.floor(Math.random() * colors.length)];
                // 粒子集中在标题周围区域（垂直 30%-70%，水平全范围）
                const cx = Math.random() * w;
                const cy = h * 0.25 + Math.random() * h * 0.45;

                this.particles.push({
                    x: cx,
                    y: cy,
                    // 漂移速度（非常缓慢）
                    vx: (Math.random() - 0.5) * 0.3,
                    vy: (Math.random() - 0.5) * 0.2,
                    // 大小 1-4px，模拟像素感
                    size: 1 + Math.random() * 3,
                    // 颜色
                    color: col,
                    // 透明度
                    alpha: 0.2 + Math.random() * 0.6,
                    // 闪烁参数
                    flickerSpeed: 0.005 + Math.random() * 0.015,
                    flickerOffset: Math.random() * Math.PI * 2,
                    // 类型：'dot' 圆点 / 'square' 方块(像素风)
                    type: Math.random() > 0.6 ? 'square' : 'dot',
                    // 边界
                    bounds: { w, h },
                });
            }

            // 渲染循环
            let time = 0;
            const render = () => {
                ctx.clearRect(0, 0, w, h);
                time += 1;

                for (let i = 0; i < this.particles.length; i++) {
                    const p = this.particles[i];

                    // 更新位置
                    p.x += p.vx;
                    p.y += p.vy;

                    // 缓慢正弦波扰动
                    p.x += Math.sin(time * 0.008 + p.flickerOffset) * 0.15;
                    p.y += Math.cos(time * 0.006 + p.flickerOffset) * 0.1;

                    // 闪烁透明度
                    p.alpha = 0.25 + 0.45 *
                        (0.5 + 0.5 * Math.sin(time * p.flickerSpeed + p.flickerOffset));

                    // 边界环绕
                    if (p.x < -10) p.x = p.bounds.w + 10;
                    if (p.x > p.bounds.w + 10) p.x = -10;
                    if (p.y < -10) p.y = p.bounds.h + 10;
                    if (p.y > p.bounds.h + 10) p.y = -10;

                    // 绘制
                    const { r, g, b } = p.color;
                    ctx.globalAlpha = p.alpha;

                    if (p.type === 'square') {
                        // 像素方块
                        const half = Math.floor(p.size / 2);
                        ctx.fillStyle = `rgb(${r},${g},${b})`;
                        ctx.fillRect(
                            Math.floor(p.x) - half,
                            Math.floor(p.y) - half,
                            Math.ceil(p.size),
                            Math.ceil(p.size)
                        );
                    } else {
                        // 小圆点
                        ctx.fillStyle = `rgb(${r},${g},${b})`;
                        ctx.beginPath();
                        ctx.arc(p.x, p.y, p.size * 0.5, 0, Math.PI * 2);
                        ctx.fill();
                    }
                }

                ctx.globalAlpha = 1;
                this.animFrameId = requestAnimationFrame(render);
            };

            render();
        },

        /**
         * 窗口尺寸变化时重建画布
         */
        handleResize() {
            if (this.animFrameId) {
                cancelAnimationFrame(this.animFrameId);
            }
            this.initParticles();
        },
    },

    mounted() {
        this.$nextTick(() => {
            this.initParticles();
        });
        window.addEventListener('resize', this.handleResize);
    },

    beforeUnmount() {
        if (this.animFrameId) {
            cancelAnimationFrame(this.animFrameId);
        }
        window.removeEventListener('resize', this.handleResize);
    },
};
