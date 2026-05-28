/**
 * Splash Component
 * Startup page -- displays hospital background image, click to enter login screen
 * Includes pixel-style title + particle background effect
 */
const SplashPage = {
    template: `
        <div class="splash-page" @click="enterLogin">
            <!-- Background Layer -->
            <div class="splash-page__bg"></div>
            <div class="splash-page__overlay"></div>

            <!-- Particle Canvas -->
            <canvas ref="particleCanvas" class="splash-page__particles"></canvas>

            <!-- Content Layer -->
            <div class="splash-page__content">
                <div class="splash-page__title-wrap">
                    <h1 class="splash-page__title">MentalHospital</h1>
                    <div class="splash-page__title-glow"></div>
                </div>
                <div class="splash-page__hint">
                    <el-icon :size="20"><ArrowDown /></el-icon>
                    <span>Click to Enter</span>
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
         * Initialize particle system
         * Particle types: small dots (main) + squares (pixel accents)
         * Motion: slow drift + flickering
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

            // Particle colors: green shades / teal / white
            const colors = [
                { r: 94, g: 214, b: 200 },  // Theme green #5ED6C8
                { r: 106, g: 232, b: 216 },  // Bright green #6AE8D8
                { r: 70, g: 180, b: 170 },   // Dark green #46B4AA
                { r: 180, g: 240, b: 230 },  // Light teal
                { r: 220, g: 255, b: 245 },  // Near-white green
                { r: 255, g: 255, b: 255 },  // White
            ];

            // Generate particles
            const count = Math.min(60, Math.floor(w * h / 25000));
            this.particles = [];
            for (let i = 0; i < count; i++) {
                const col = colors[Math.floor(Math.random() * colors.length)];
                // Particles concentrated around the title area (vertical 30%-70%, full horizontal range)
                const cx = Math.random() * w;
                const cy = h * 0.25 + Math.random() * h * 0.45;

                this.particles.push({
                    x: cx,
                    y: cy,
                    // Drift speed (very slow)
                    vx: (Math.random() - 0.5) * 0.3,
                    vy: (Math.random() - 0.5) * 0.2,
                    // Size 1-4px, simulating pixel feel
                    size: 1 + Math.random() * 3,
                    // Color
                    color: col,
                    // Opacity
                    alpha: 0.2 + Math.random() * 0.6,
                    // Flicker parameters
                    flickerSpeed: 0.005 + Math.random() * 0.015,
                    flickerOffset: Math.random() * Math.PI * 2,
                    // Type: 'dot' circle / 'square' block (pixel style)
                    type: Math.random() > 0.6 ? 'square' : 'dot',
                    // Bounds
                    bounds: { w, h },
                });
            }

            // Render loop
            let time = 0;
            const render = () => {
                ctx.clearRect(0, 0, w, h);
                time += 1;

                for (let i = 0; i < this.particles.length; i++) {
                    const p = this.particles[i];

                    // Update position
                    p.x += p.vx;
                    p.y += p.vy;

                    // Slow sine wave perturbation
                    p.x += Math.sin(time * 0.008 + p.flickerOffset) * 0.15;
                    p.y += Math.cos(time * 0.006 + p.flickerOffset) * 0.1;

                    // Flickering opacity
                    p.alpha = 0.25 + 0.45 *
                        (0.5 + 0.5 * Math.sin(time * p.flickerSpeed + p.flickerOffset));

                    // Boundary wrapping
                    if (p.x < -10) p.x = p.bounds.w + 10;
                    if (p.x > p.bounds.w + 10) p.x = -10;
                    if (p.y < -10) p.y = p.bounds.h + 10;
                    if (p.y > p.bounds.h + 10) p.y = -10;

                    // Draw
                    const { r, g, b } = p.color;
                    ctx.globalAlpha = p.alpha;

                    if (p.type === 'square') {
                        // Pixel square
                        const half = Math.floor(p.size / 2);
                        ctx.fillStyle = `rgb(${r},${g},${b})`;
                        ctx.fillRect(
                            Math.floor(p.x) - half,
                            Math.floor(p.y) - half,
                            Math.ceil(p.size),
                            Math.ceil(p.size)
                        );
                    } else {
                        // Small dot
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
         * Rebuild canvas when window size changes
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
