/**
 * Interview Component
 * Phase 1 -- History Taking / Interview Interface
 *
 * Two-column layout:
 *   Left -- Virtual patient display area (SVG emotion avatar + patient info + emotion state)
 *   Right -- Doctor-patient dialogue area (chat history + input box)
 *
 * Page semantics: "Doctor" and "Patient"
 *   Doctor speaks = medical student input
 *   Patient speaks = LLM output
 */
const Interview = {
    template: `
        <div class="interview-page">
            <!-- Background Image -->
            <div class="interview-page__bg"></div>

            <!-- Left: Virtual Patient -->
            <aside class="interview-sidebar">
                <div class="interview-sidebar__back">
                    <el-button text @click="goBack" class="interview-sidebar__back-btn">
                        <el-icon><ArrowLeft /></el-icon>
                        Back
                    </el-button>
                </div>

                <virtual-patient
                    :patient-name="patientCaseId"
                    :basic-info="patientBasicInfo"
                    :physical-exam="patientPhysicalExam"
                    :emotion="avatarEmotion"
                />
            </aside>

            <!-- Right: Dialogue Area -->
            <main class="interview-main">
                <!-- Top Bar -->
                <header class="interview-header">
                    <div class="interview-header__left">
                        <h3 class="interview-header__title">History Taking</h3>
                        <span class="interview-header__subtitle">Phase 1 Interview</span>
                        <div class="interview-header__turns">
                            Turn {{ turnCount }}
                        </div>
                    </div>
                    <div class="interview-header__right">
                        <div class="interview-header__status">
                            <span class="interview-header__status-dot"
                                  :class="{ 'typing': isTyping }"></span>
                            {{ isTyping ? 'Patient thinking...' : 'Interviewing' }}
                        </div>
                        <el-button
                            type="danger"
                            size="small"
                            round
                            @click="handleEndPhase"
                            :disabled="saving"
                            class="interview-header__end-btn"
                        >
                            <el-icon><SwitchButton /></el-icon>
                            End Phase
                        </el-button>
                    </div>
                </header>

                <!-- Dialogue Area -->
                <div class="interview-chat" ref="chatRef">
                    <!-- System Prompt -->
                    <div class="chat-bubble system">
                        <div class="chat-bubble__avatar">
                            <el-icon :size="18"><InfoFilled /></el-icon>
                        </div>
                        <div class="chat-bubble__content">
                            <div class="chat-bubble__text">
                                You are conducting a clinical interview with the patient. Please initiate the first conversation as the doctor, paying attention to comprehensiveness and communication skills.
                            </div>
                        </div>
                    </div>

                    <!-- Dialogue Messages -->
                    <div v-for="(msg, idx) in messages" :key="idx"
                         class="chat-bubble" :class="msg.role">
                        <div class="chat-bubble__avatar">
                            <el-icon :size="20" v-if="msg.role === 'patient'"><UserFilled /></el-icon>
                            <el-icon :size="20" v-else><User /></el-icon>
                        </div>
                        <div class="chat-bubble__content">
                            <div class="chat-bubble__name" :class="msg.role">
                                <template v-if="msg.role === 'patient'">
                                    Patient <span v-if="msg.presentation" class="chat-bubble__presentation">{{ msg.presentation }}</span>
                                </template>
                                <template v-else>Doctor</template>
                            </div>
                            <div class="chat-bubble__text">{{ msg.content }}</div>
                            <div class="chat-bubble__time">{{ msg.time }}</div>
                        </div>
                    </div>

                    <!-- Patient Thinking -->
                    <div class="chat-bubble patient" v-if="isTyping">
                        <div class="chat-bubble__avatar">
                            <el-icon :size="20"><UserFilled /></el-icon>
                        </div>
                        <div class="chat-bubble__content">
                            <div class="chat-bubble__name">Patient</div>
                            <div class="typing-indicator">
                                <span></span><span></span><span></span>
                            </div>
                        </div>
                    </div>

                    <!-- Empty State -->
                    <div v-if="messages.length === 0 && !isTyping"
                         class="chat-bubble system">
                        <div class="chat-bubble__content">
                            <div class="chat-bubble__text">Doctor, please initiate the first interview conversation...</div>
                        </div>
                    </div>
                </div>

                <!-- Bottom Input Bar -->
                <div class="interview-input">
                    <div class="interview-input__box">
                        <el-input
                            v-model="inputText"
                            placeholder="Ask the patient as a doctor..."
                            @keyup.enter.native.prevent="handleKeydown"
                            :disabled="patientLoading || !patientReady || isTyping || saving"
                            resize="none"
                            type="textarea"
                            :rows="1"
                            ref="inputRef"
                            class="interview-input__field"
                        />
                        <el-button
                            type="primary"
                            round
                            @click="sendMessage"
                            :disabled="patientLoading || !patientReady || !inputText.trim() || isTyping || saving"
                            class="interview-input__btn"
                        >
                            <el-icon><Position /></el-icon>
                            Send
                        </el-button>
                    </div>
                    <div class="interview-input__hint">
                        Enter to send · Shift + Enter for new line
                    </div>
                </div>
            </main>

            <!-- Evaluation Loading Indicator -->
            <transition name="eval-fade">
                <div v-if="saving" class="eval-overlay">
                    <div class="eval-overlay__content">
                        <img src="/static/bg/eval.png" alt="" class="eval-overlay__icon" />
                        <div class="eval-overlay__text">Saving data...</div>
                    </div>
                </div>
            </transition>
        </div>
    `,

    components: {
        'virtual-patient': VirtualPatient,
    },

    data() {
        return {
            inputText: '',
            isTyping: false,
            messages: [],
            patientCaseId: '',
            patientBasicInfo: '',
            patientPhysicalExam: '',
            sessionId: null,
            patientName: '',
            avatarEmotion: 'neutral',
            lastPatientMessage: '',
            prevEmotion: 'neutral',
            patientLoading: true,
            patientReady: false,
            // Save state
            saving: false,
            // First send flag
        };
    },

    computed: {
        User() { return ElementPlusIconsVue.User; },
        UserFilled() { return ElementPlusIconsVue.UserFilled; },
        Position() { return ElementPlusIconsVue.Position; },
        InfoFilled() { return ElementPlusIconsVue.InfoFilled; },
        ArrowLeft() { return ElementPlusIconsVue.ArrowLeft; },
        SwitchButton() { return ElementPlusIconsVue.SwitchButton; },
        CircleCheckFilled() { return ElementPlusIconsVue.CircleCheckFilled; },

        turnCount() {
            return this.messages.filter(m => m.role === 'doctor').length;
        },
    },

    methods: {
        // Medical student input -> displayed as "Doctor" -> call LLM patient -> displayed as "Patient"
        async sendMessage() {
            if (!this.patientReady || this.patientLoading || !this.sessionId) return;
            if (!this.inputText.trim() || this.isTyping) return;

            const doctorMessage = this.inputText.trim();
            this.inputText = '';

            this.messages.push({
                role: 'doctor',
                content: doctorMessage,
                time: this.getCurrentTime(),
            });
            this.$nextTick(() => this.scrollToBottom());

            this.isTyping = true;
            try {
                const res = await API.sendMessage(this.sessionId, doctorMessage);
                const patientText = res.response || '';
                const presentation = res.presentation || '';
                const searchDebug = res.search_debug || null;
                // First send: use the opening statement returned by the backend as the patient reply

                if (searchDebug) {
                    this.logSearchDebug(searchDebug);
                }

                // Extract emotion state and remove tags
                this.avatarEmotion = EmotionDetector.detect(patientText, this.prevEmotion);
                const displayText = EmotionDetector.clean(patientText);
                this.prevEmotion = this.avatarEmotion;

                this.messages.push({
                    role: 'patient',
                    content: displayText,
                    presentation: presentation,
                    time: this.getCurrentTime(),
                });
            } catch (err) {
                this.messages.push({
                    role: 'patient',
                    content: '(Patient is temporarily unable to respond, please try again later)',
                    time: this.getCurrentTime(),
                });
                console.error('[Interview] Patient response failed:', err);
            } finally {
                this.isTyping = false;
                this.$nextTick(() => {
                    this.scrollToBottom();
                    this.focusInput();
                });
            }
        },

        handleKeydown(e) {
            if (!e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        },

        logSearchDebug(searchDebug) {
            const code = searchDebug.code || '[SEARCH]';
            const event = searchDebug.event || 'Unknown event';
            const statusMap = {
                resolved: 'Query completed and response generated',
                triggered: 'Query triggered',
                empty: 'Query triggered but no content returned',
                error: 'Query processing failed',
            };
            const status = statusMap[searchDebug.status] || searchDebug.status || 'Unknown status';
            const payload = {
                code,
                event,
                status: searchDebug.status || 'unknown',
                statusText: status,
                message: searchDebug.message || '',
            };

            if (searchDebug.status === 'error') {
                console.error('[Interview][SEARCH] Patient query processing failed:', payload);
            } else if (searchDebug.status === 'empty') {
                console.warn('[Interview][SEARCH] Patient query returned no content:', payload);
            } else {
                console.log('[Interview][SEARCH] Patient query triggered:', payload);
            }
        },

        getCurrentTime() {
            const now = new Date();
            return now.toLocaleTimeString('zh-CN', {
                hour: '2-digit',
                minute: '2-digit',
            });
        },

        scrollToBottom() {
            const el = this.$refs.chatRef;
            if (el) el.scrollTop = el.scrollHeight;
        },

        focusInput() {
            this.$nextTick(() => {
                const input = this.$refs.inputRef;
                if (input) {
                    const textarea = input.$el.querySelector('textarea');
                    if (textarea) textarea.focus();
                }
            });
        },

        goBack() {
            if (this.sessionId) API.endChat(this.sessionId);
            this.$router.push('/patients');
        },

        async handleEndPhase() {
            if (this.saving) return;
            if (this.messages.length === 0) {
                this.$message.warning('No conversation yet, cannot end phase');
                return;
            }

            this.saving = true;
            const caseId = this.$route.query.id;
            const recordId = sessionStorage.getItem('record_id') || caseId;
            if (caseId) {
                sessionStorage.setItem('phase2_caseId', caseId);
                sessionStorage.setItem('phase2_messages', JSON.stringify(this.messages));

                try {
                    await API.saveCaseRecord(recordId, {
                        caseInfo: {
                            basicInfomation: this.patientBasicInfo,
                            physicalExamination: this.patientPhysicalExam,
                        },
                        conversation: this.messages,
                    });
                } catch (err) {
                    console.error('[Interview] Failed to save record:', err);
                }
            }

            if (this.sessionId) API.endChat(this.sessionId);
            this.$router.push({ path: '/phase2', query: { id: caseId } });
        },

        async initSession() {
            const caseId = this.$route.query.id;
            if (!caseId) {
                this.patientLoading = false;
                this.patientReady = false;
                return;
            }

            this.patientCaseId = caseId;
            this.patientLoading = true;
            this.patientReady = false;

            try {
                const caseInfo = await API.getCaseInfo(caseId);
                this.patientBasicInfo = caseInfo.basicInfomation || '';
                this.patientPhysicalExam = caseInfo.physicalExamination || '';
                this.patientName = caseInfo.basicInfomation
                    ? caseInfo.basicInfomation.replace(/^Patient\s*/, '')
                    : caseId;

                const chatRes = await API.startChat(caseId);
                this.sessionId = chatRes.session_id;

                // Doctor initiates the conversation first, patientIntro is used as patient reply on first send

                // Save record_id for unified use across all phases
                if (chatRes.record_id) {
                    sessionStorage.setItem('record_id', chatRes.record_id);
                }

                // No longer display patientIntro upfront; wait until doctor sends first message before updating expression via sendMessage
                this.prevEmotion = this.avatarEmotion;
                this.patientReady = Boolean(this.sessionId);
                this.patientLoading = false;

                // Auto-focus input box
                this.focusInput();
            } catch (err) {
                console.error('[Interview] Failed to initialize session:', err);
                this.patientReady = false;
                this.patientLoading = false;
            }
        },
    },

    mounted() {
        this.initSession();
    },

    beforeUnmount() {
        if (this.sessionId) API.endChat(this.sessionId);
    },
};
