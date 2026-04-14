/**
 * PhaseTransitionPipeline — 阶段转场流水线动画组件
 *
 * 用于各阶段之间的过渡，展示流水线式推进动画，
 * 同时调用后端评价接口，等待结果后自动跳转。
 *
 * 用法:
 *   <phase-transition-pipeline
 *       :visible="showTransition"
 *       :phase-number="currentPhase"
 *       :case-id="caseId"
 *       :eval-payload="{ messages }"
 *       @eval-complete="onEvalComplete"
 *       @close="showTransition = false"
 *   />
 */
const PhaseTransitionPipeline = {
    template: `
        <transition name="pipeline-fade">
            <div v-if="visible" class="pipeline-overlay" :class="{ 'pipeline-overlay--exiting': exiting }">
                <!-- 玻璃叠加层 -->
                <div class="pipeline-overlay__glass"></div>

                <!-- 粒子背景 -->
                <div class="pipeline-particles">
                    <div v-for="(p, i) in particles" :key="i"
                         class="pipeline-particle"
                         :style="p.style">
                    </div>
                </div>

                <!-- 顶部品牌标识 -->
                <div class="pipeline-brand">
                    <span class="pipeline-brand__title">MentalEval</span>
                    <div class="pipeline-brand__divider"></div>
                </div>

                <!-- 阶段名称（品牌下方） -->
                <div class="pipeline-phase-name">
                    <span class="pipeline-phase-name__label">当前阶段</span>
                    <span class="pipeline-phase-name__current">{{ currentPhaseName }}</span>
                    <span class="pipeline-phase-name__progress">{{ progressText }}</span>
                </div>

                <!-- 主内容 -->
                <div class="pipeline-content">
                    <!-- 左侧: 阶段管道 -->
                    <div class="pipeline-steps">
                        <template v-for="(step, idx) in steps" :key="idx">
                            <!-- 阶段节点 -->
                            <div class="pipeline-node" :class="getNodeClass(idx)">
                                <div class="pipeline-node__circle">
                                    <span class="node-text">{{ step.label }}</span>
                                </div>
                                <div class="pipeline-node__label">{{ step.name }}</div>
                            </div>

                            <!-- 连接线 -->
                            <div v-if="idx < steps.length - 1"
                                 class="pipeline-connector"
                                 :class="getConnectorClass(idx)">
                                <div class="pipeline-connector__track"
                                     :class="{ 'pipeline-connector__track--done': isDone(idx) }">
                                    <div class="pipeline-connector__flow"></div>
                                </div>
                            </div>
                        </template>
                    </div>

                    <!-- 右侧: MentalEval 核心（玻璃卡片） -->
                    <div class="pipeline-core">
                        <div class="pipeline-core__glow"></div>

                        <!-- eval.png + 光环 -->
                        <div class="pipeline-core__icon-wrap">
                            <div class="pipeline-core__halo"></div>
                            <img
                                src="/static/bg/eval.png"
                                alt="MentalEval"
                                class="pipeline-core__icon"
                                :class="{ 'pipeline-core__icon--breathing': isEvaluating }"
                            />
                        </div>

                        <!-- 中央 MentalEval 文字 -->
                        <div class="pipeline-core__mental-eval">MentalEval</div>
                        <div class="pipeline-core__subtitle">Evaluating Clinical Interaction...</div>

                        <!-- 状态文字 -->
                        <div class="pipeline-core__text">{{ statusText }}</div>
                        <div class="pipeline-core__subtext">{{ subStatusText }}</div>

                        <!-- 进度条 -->
                        <div class="pipeline-progress">
                            <div class="pipeline-progress__bar" :style="{ width: progressPercent + '%' }"></div>
                        </div>
                    </div>
                </div>
            </div>
        </transition>
    `,

    props: {
        // 是否显示
        visible: { type: Boolean, default: false },
        // 当前阶段编号 1-4
        phaseNumber: { type: Number, required: true },
        // 病例 ID
        caseId: { type: String, default: '' },
        // 评价额外参数
        evalPayload: { type: Object, default: () => ({}) },
        // 是否自动调用评价 API
        autoEvaluate: { type: Boolean, default: true },
        // 下一阶段路由路径
        nextPath: { type: String, default: '' },
    },

    emits: ['eval-complete', 'close'],

    data() {
        return {
            // 步骤定义
            steps: [
                { label: '1', name: '访谈' },
                { label: '2', name: '检查' },
                { label: '3', name: '诊断' },
                { label: '4', name: '治疗' },
            ],
            // 预生成的粒子数据
            particles: [],
            // 评价状态: 'idle' | 'evaluating' | 'done' | 'error'
            evalStatus: 'idle',
            evalResult: null,
            evalError: null,
            // 退出动画标志
            exiting: false,
            // 进度模拟
            simulatedProgress: 0,
            progressTimer: null,
            // 音效
            audioCtx: null,
            soundEnabled: true,
        };
    },

    computed: {
        /** 当前阶段名称 */
        currentPhaseName() {
            const names = {
                1: '病史采集',
                2: '检查推荐',
                3: '临床病历',
                4: '治疗方案',
            };
            return names[this.phaseNumber] || '阶段 ' + this.phaseNumber;
        },

        /** 是否正在评价 */
        isEvaluating() {
            return this.evalStatus === 'evaluating';
        },

        /** 状态文字 */
        statusText() {
            const texts = {
                idle: '准备评估',
                evaluating: '正在进行评估…',
                done: '评估完成',
                error: '评估异常',
            };
            return texts[this.evalStatus] || '';
        },

        /** 副状态文字 */
        subStatusText() {
            if (this.evalStatus === 'evaluating') {
                return '分析对话质量与临床技巧';
            }
            if (this.evalStatus === 'done') {
                return '即将进入下一阶段';
            }
            if (this.evalStatus === 'error') {
                return this.evalError || '请稍后重试';
            }
            return 'MentalEval 智能评估系统';
        },

        /** 进度百分比 */
        progressPercent() {
            if (this.evalStatus === 'done') return 100;
            if (this.evalStatus === 'evaluating') {
                return Math.min(this.simulatedProgress, 90);
            }
            // 基于阶段编号的初始进度
            return (this.phaseNumber / 4) * 25;
        },

        /** 进度文字 */
        progressText() {
            var pct = Math.round(this.progressPercent);
            return 'Phase ' + this.phaseNumber + ' → ' + pct + '%';
        },
    },

    methods: {
        /** 获取节点样式类 */
        getNodeClass(idx) {
            var phaseNum = idx + 1;
            if (phaseNum < this.phaseNumber) return 'pipeline-node--done';
            if (phaseNum === this.phaseNumber) {
                if (this.evalStatus === 'done') return 'pipeline-node--done';
                return 'pipeline-node--active';
            }
            return 'pipeline-node--pending';
        },

        /** 获取连接线样式类 */
        getConnectorClass(idx) {
            var isFast = this.evalStatus === 'evaluating';
            return {
                'pipeline-connector--fast': isFast,
            };
        },

        /** 判断节点是否已完成 */
        isDone(idx) {
            return this.phaseNumber > idx + 1 || this.evalStatus === 'done';
        },

        /** 播放滴答音效 */
        playTick() {
            if (!this.soundEnabled) return;
            try {
                if (!this.audioCtx) {
                    this.audioCtx = new (window.AudioContext || window.webkitAudioContext)();
                }
                var osc = this.audioCtx.createOscillator();
                var gain = this.audioCtx.createGain();
                osc.connect(gain);
                gain.connect(this.audioCtx.destination);
                osc.frequency.value = 800 + Math.random() * 400;
                osc.type = 'sine';
                gain.gain.setValueAtTime(0.08, this.audioCtx.currentTime);
                gain.gain.exponentialRampToValueAtTime(0.001, this.audioCtx.currentTime + 0.15);
                osc.start();
                osc.stop(this.audioCtx.currentTime + 0.15);
            } catch (e) {
                // 音频不可用时静默失败
            }
        },

        /** 播放完成音效 */
        playComplete() {
            if (!this.soundEnabled) return;
            try {
                if (!this.audioCtx) {
                    this.audioCtx = new (window.AudioContext || window.webkitAudioContext)();
                }
                var notes = [523, 659, 784]; // C5, E5, G5
                var ctx = this.audioCtx;
                notes.forEach(function(freq, i) {
                    var o = ctx.createOscillator();
                    var g = ctx.createGain();
                    o.connect(g);
                    g.connect(ctx.destination);
                    o.frequency.value = freq;
                    o.type = 'sine';
                    var startTime = ctx.currentTime + i * 0.12;
                    g.gain.setValueAtTime(0.1, startTime);
                    g.gain.exponentialRampToValueAtTime(0.001, startTime + 0.3);
                    o.start(startTime);
                    o.stop(startTime + 0.3);
                });
            } catch (e) {
                // 音频不可用时静默失败
            }
        },

        /** 启动评价流程 */
        async startEvaluation() {
            if (this.evalStatus !== 'idle') return;

            this.evalStatus = 'evaluating';
            this.evalResult = null;
            this.evalError = null;

            // 模拟进度增长
            this.simulatedProgress = 10;
            var self = this;
            this.progressTimer = setInterval(function() {
                if (self.simulatedProgress < 85) {
                    self.simulatedProgress += Math.random() * 8 + 2;
                }
            }, 300);

            // 播放滴答声
            this.playTick();

            try {
                this.evalResult = await API.evaluatePhase(
                    this.phaseNumber,
                    this.caseId,
                    this.evalPayload
                );

                this.simulatedProgress = 100;
                this.evalStatus = 'done';
                this.playComplete();

                this.$emit('eval-complete', this.evalResult);

                // 自动关闭并跳转
                var self2 = this;
                setTimeout(function() {
                    self2.close();
                }, 1500);
            } catch (err) {
                console.error('[PhaseTransitionPipeline] 评价失败:', err);
                this.evalError = err.message || '未知错误';
                this.evalStatus = 'done'; // 仍然进入完成状态，允许用户继续
                this.simulatedProgress = 100;
                this.playComplete();
                this.$emit('eval-complete', this.getFallbackData());
                var self3 = this;
                setTimeout(function() {
                    self3.close();
                }, 2000);
            } finally {
                if (this.progressTimer) {
                    clearInterval(this.progressTimer);
                    this.progressTimer = null;
                }
            }
        },

        /** 获取兜底数据 */
        getFallbackData() {
            return {
                phase: this.phaseNumber,
                case_id: this.caseId,
                _fallback: true,
            };
        },

        /** 关闭动画 */
        close() {
            this.exiting = true;
            var self = this;
            setTimeout(function() {
                self.$emit('close');
            }, 500);
        },

        /** 重置状态 */
        reset() {
            this.evalStatus = 'idle';
            this.evalResult = null;
            this.evalError = null;
            this.exiting = false;
            this.simulatedProgress = 0;
            if (this.progressTimer) {
                clearInterval(this.progressTimer);
                this.progressTimer = null;
            }
        },

        /** 切换音效 */
        toggleSound() {
            this.soundEnabled = !this.soundEnabled;
        },

        /** 生成粒子数据 */
        generateParticles() {
            var particles = [];
            for (var i = 0; i < 30; i++) {
                particles.push({
                    style: {
                        left: (Math.random() * 100) + '%',
                        animationDuration: (4 + Math.random() * 6) + 's',
                        animationDelay: (Math.random() * 5) + 's',
                        width: (2 + Math.random() * 3) + 'px',
                        height: (2 + Math.random() * 3) + 'px',
                    }
                });
            }
            this.particles = particles;
        },
    },

    watch: {
        /** 当 visible 变为 true 时自动启动评价 */
        visible(newVal) {
            if (newVal && this.autoEvaluate) {
                this.reset();
                this.generateParticles();
                var self = this;
                this.$nextTick(function() {
                    self.startEvaluation();
                });
            }
        },
    },

    mounted() {
        // 键盘 ESC 关闭
        var self = this;
        this._onKeydown = function(e) {
            if (e.key === 'Escape' && self.visible && self.evalStatus === 'done') {
                self.close();
            }
        };
        document.addEventListener('keydown', this._onKeydown);
    },

    beforeUnmount() {
        document.removeEventListener('keydown', this._onKeydown);
        if (this.progressTimer) {
            clearInterval(this.progressTimer);
        }
        if (this.audioCtx) {
            this.audioCtx.close();
        }
    },
};
