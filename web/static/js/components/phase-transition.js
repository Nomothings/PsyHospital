/**
 * PhaseTransitionPipeline - Phase transition pipeline animation component
 *
 * Used for transitions between phases, displaying a pipeline-style progression animation,
 * while calling the backend evaluation API and auto-navigating after results return.
 *
 * Usage:
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
                <!-- Glass overlay -->
                <div class="pipeline-overlay__glass"></div>

                <!-- Particle background -->
                <div class="pipeline-particles">
                    <div v-for="(p, i) in particles" :key="i"
                         class="pipeline-particle"
                         :style="p.style">
                    </div>
                </div>

                <!-- Top brand logo -->
                <div class="pipeline-brand">
                    <span class="pipeline-brand__title">MentalEval</span>
                    <div class="pipeline-brand__divider"></div>
                </div>

                <!-- Phase name (below brand) -->
                <div class="pipeline-phase-name">
                    <span class="pipeline-phase-name__label">Current Phase</span>
                    <span class="pipeline-phase-name__current">{{ currentPhaseName }}</span>
                    <span class="pipeline-phase-name__progress">{{ progressText }}</span>
                </div>

                <!-- Main content -->
                <div class="pipeline-content">
                    <!-- Left: Phase pipeline -->
                    <div class="pipeline-steps">
                        <template v-for="(step, idx) in steps" :key="idx">
                            <!-- Phase node -->
                            <div class="pipeline-node" :class="getNodeClass(idx)">
                                <div class="pipeline-node__circle">
                                    <span class="node-text">{{ step.label }}</span>
                                </div>
                                <div class="pipeline-node__label">{{ step.name }}</div>
                            </div>

                            <!-- Connector line -->
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

                    <!-- Right: MentalEval core (glass card) -->
                    <div class="pipeline-core">
                        <div class="pipeline-core__glow"></div>

                        <!-- eval.png + halo -->
                        <div class="pipeline-core__icon-wrap">
                            <div class="pipeline-core__halo"></div>
                            <img
                                src="/static/bg/eval.png"
                                alt="MentalEval"
                                class="pipeline-core__icon"
                                :class="{ 'pipeline-core__icon--breathing': isEvaluating }"
                            />
                        </div>

                        <!-- Center MentalEval text -->
                        <div class="pipeline-core__mental-eval">MentalEval</div>
                        <div class="pipeline-core__subtitle">Evaluating Clinical Interaction...</div>

                        <!-- Status text -->
                        <div class="pipeline-core__text">{{ statusText }}</div>
                        <div class="pipeline-core__subtext">{{ subStatusText }}</div>

                        <!-- Progress bar -->
                        <div class="pipeline-progress">
                            <div class="pipeline-progress__bar" :style="{ width: progressPercent + '%' }"></div>
                        </div>
                    </div>
                </div>
            </div>
        </transition>
    `,

    props: {
        // Whether to show
        visible: { type: Boolean, default: false },
        // Current phase number 1-4
        phaseNumber: { type: Number, required: true },
        // Case ID
        caseId: { type: String, default: '' },
        // Extra evaluation parameters
        evalPayload: { type: Object, default: () => ({}) },
        // Whether to auto-call evaluation API
        autoEvaluate: { type: Boolean, default: true },
        // Next phase route path
        nextPath: { type: String, default: '' },
    },

    emits: ['eval-complete', 'close'],

    data() {
        return {
            // Step definitions
            steps: [
                { label: '1', name: 'Interview' },
                { label: '2', name: 'Examination' },
                { label: '3', name: 'Diagnosis' },
                { label: '4', name: 'Treatment' },
            ],
            // Pre-generated particle data
            particles: [],
            // Evaluation status: 'idle' | 'evaluating' | 'done' | 'error'
            evalStatus: 'idle',
            evalResult: null,
            evalError: null,
            // Exit animation flag
            exiting: false,
            // Progress simulation
            simulatedProgress: 0,
            progressTimer: null,
            // Sound effects
            audioCtx: null,
            soundEnabled: true,
        };
    },

    computed: {
        /** Current phase name */
        currentPhaseName() {
            const names = {
                1: 'History Taking',
                2: 'Examination Recommendation',
                3: 'Clinical Case',
                4: 'Treatment Plan',
            };
            return names[this.phaseNumber] || 'Phase ' + this.phaseNumber;
        },

        /** Whether evaluation is in progress */
        isEvaluating() {
            return this.evalStatus === 'evaluating';
        },

        /** Status text */
        statusText() {
            const texts = {
                idle: 'Preparing Evaluation',
                evaluating: 'Evaluating...',
                done: 'Evaluation Complete',
                error: 'Evaluation Error',
            };
            return texts[this.evalStatus] || '';
        },

        /** Sub-status text */
        subStatusText() {
            if (this.evalStatus === 'evaluating') {
                return 'Analyzing dialogue quality and clinical skills';
            }
            if (this.evalStatus === 'done') {
                return 'Proceeding to next phase';
            }
            if (this.evalStatus === 'error') {
                return this.evalError || 'Please try again later';
            }
            return 'MentalEval Intelligent Assessment System';
        },

        /** Progress percentage */
        progressPercent() {
            if (this.evalStatus === 'done') return 100;
            if (this.evalStatus === 'evaluating') {
                return Math.min(this.simulatedProgress, 90);
            }
            // Initial progress based on phase number
            return (this.phaseNumber / 4) * 25;
        },

        /** Progress text */
        progressText() {
            var pct = Math.round(this.progressPercent);
            return 'Phase ' + this.phaseNumber + ' → ' + pct + '%';
        },
    },

    methods: {
        /** Get node style class */
        getNodeClass(idx) {
            var phaseNum = idx + 1;
            if (phaseNum < this.phaseNumber) return 'pipeline-node--done';
            if (phaseNum === this.phaseNumber) {
                if (this.evalStatus === 'done') return 'pipeline-node--done';
                return 'pipeline-node--active';
            }
            return 'pipeline-node--pending';
        },

        /** Get connector style class */
        getConnectorClass(idx) {
            var isFast = this.evalStatus === 'evaluating';
            return {
                'pipeline-connector--fast': isFast,
            };
        },

        /** Check if node is completed */
        isDone(idx) {
            return this.phaseNumber > idx + 1 || this.evalStatus === 'done';
        },

        /** Play tick sound effect */
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
                // Silently fail when audio is unavailable
            }
        },

        /** Play completion sound effect */
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
                // Silently fail when audio is unavailable
            }
        },

        /** Start evaluation process */
        async startEvaluation() {
            if (this.evalStatus !== 'idle') return;

            this.evalStatus = 'evaluating';
            this.evalResult = null;
            this.evalError = null;

            // Simulate progress growth
            this.simulatedProgress = 10;
            var self = this;
            this.progressTimer = setInterval(function() {
                if (self.simulatedProgress < 85) {
                    self.simulatedProgress += Math.random() * 8 + 2;
                }
            }, 300);

            // Play tick sound
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

                // Auto-close and navigate
                var self2 = this;
                setTimeout(function() {
                    self2.close();
                }, 1500);
            } catch (err) {
                console.error('[PhaseTransitionPipeline] Evaluation failed:', err);
                this.evalError = err.message || 'Unknown error';
                this.evalStatus = 'done'; // Still enter done state to allow user to continue
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

        /** Get fallback data */
        getFallbackData() {
            return {
                phase: this.phaseNumber,
                case_id: this.caseId,
                _fallback: true,
            };
        },

        /** Close animation */
        close() {
            this.exiting = true;
            var self = this;
            setTimeout(function() {
                self.$emit('close');
            }, 500);
        },

        /** Reset state */
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

        /** Toggle sound effects */
        toggleSound() {
            this.soundEnabled = !this.soundEnabled;
        },

        /** Generate particle data */
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
        /** Auto-start evaluation when visible becomes true */
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
        // Keyboard ESC to close
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
