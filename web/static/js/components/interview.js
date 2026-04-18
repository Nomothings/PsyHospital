/**
 * Interview 组件
 * Phase 1 — 病史采集 / 访谈界面
 *
 * 双栏布局:
 *   左侧 — 虚拟患者展示区（含 SVG 表情头像 + 患者信息 + 情绪状态）
 *   右侧 — 医患对话区（聊天记录 + 输入框）
 *
 * 页面语义: "医生" 与 "患者"
 *   医生发言 = 医学生输入
 *   患者发言 = LLM 输出
 */
const Interview = {
    template: `
        <div class="interview-page">
            <!-- 背景图 -->
            <div class="interview-page__bg"></div>

            <!-- 左侧: 虚拟患者 -->
            <aside class="interview-sidebar">
                <div class="interview-sidebar__back">
                    <el-button text @click="goBack" class="interview-sidebar__back-btn">
                        <el-icon><ArrowLeft /></el-icon>
                        返回
                    </el-button>
                </div>

                <virtual-patient
                    :patient-name="patientCaseId"
                    :basic-info="patientBasicInfo"
                    :physical-exam="patientPhysicalExam"
                    :emotion="avatarEmotion"
                />
            </aside>

            <!-- 右侧: 对话区 -->
            <main class="interview-main">
                <!-- 顶部栏 -->
                <header class="interview-header">
                    <div class="interview-header__left">
                        <h3 class="interview-header__title">病史采集</h3>
                        <span class="interview-header__subtitle">第一阶段访谈</span>
                        <div class="interview-header__turns">
                            第 {{ turnCount }} 轮
                        </div>
                    </div>
                    <div class="interview-header__right">
                        <div class="interview-header__status">
                            <span class="interview-header__status-dot"
                                  :class="{ 'typing': isTyping }"></span>
                            {{ isTyping ? '患者思考中' : '问诊中' }}
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
                            结束阶段
                        </el-button>
                    </div>
                </header>

                <!-- 对话区域 -->
                <div class="interview-chat" ref="chatRef">
                    <!-- 系统提示 -->
                    <div class="chat-bubble system">
                        <div class="chat-bubble__avatar">
                            <el-icon :size="18"><InfoFilled /></el-icon>
                        </div>
                        <div class="chat-bubble__content">
                            <div class="chat-bubble__text">
                                您正在与患者进行临床访谈，请由您（医生）发起第一次对话，注意问诊的全面性和沟通技巧。
                            </div>
                        </div>
                    </div>

                    <!-- 对话消息 -->
                    <div v-for="(msg, idx) in messages" :key="idx"
                         class="chat-bubble" :class="msg.role">
                        <div class="chat-bubble__avatar">
                            <el-icon :size="20" v-if="msg.role === 'patient'"><UserFilled /></el-icon>
                            <el-icon :size="20" v-else><User /></el-icon>
                        </div>
                        <div class="chat-bubble__content">
                            <div class="chat-bubble__name" :class="msg.role">
                                <template v-if="msg.role === 'patient'">
                                    患者 <span v-if="msg.presentation" class="chat-bubble__presentation">{{ msg.presentation }}</span>
                                </template>
                                <template v-else>医生</template>
                            </div>
                            <div class="chat-bubble__text">{{ msg.content }}</div>
                            <div class="chat-bubble__time">{{ msg.time }}</div>
                        </div>
                    </div>

                    <!-- 患者思考中 -->
                    <div class="chat-bubble patient" v-if="isTyping">
                        <div class="chat-bubble__avatar">
                            <el-icon :size="20"><UserFilled /></el-icon>
                        </div>
                        <div class="chat-bubble__content">
                            <div class="chat-bubble__name">患者</div>
                            <div class="typing-indicator">
                                <span></span><span></span><span></span>
                            </div>
                        </div>
                    </div>

                    <!-- 空状态 -->
                    <div v-if="messages.length === 0 && !isTyping"
                         class="chat-bubble system">
                        <div class="chat-bubble__content">
                            <div class="chat-bubble__text">请医生先发起第一次问诊对话…</div>
                        </div>
                    </div>
                </div>

                <!-- 底部输入栏 -->
                <div class="interview-input">
                    <div class="interview-input__box">
                        <el-input
                            v-model="inputText"
                            placeholder="以医生身份向患者提问…"
                            @keyup.enter.native.prevent="handleKeydown"
                            :disabled="isTyping || saving"
                            resize="none"
                            type="textarea"
                            :rows="1"
                            class="interview-input__field"
                        />
                        <el-button
                            type="primary"
                            round
                            @click="sendMessage"
                            :disabled="!inputText.trim() || isTyping || saving"
                            class="interview-input__btn"
                        >
                            <el-icon><Position /></el-icon>
                            发送
                        </el-button>
                    </div>
                    <div class="interview-input__hint">
                        Enter 发送 · Shift + Enter 换行
                    </div>
                </div>
            </main>

            <!-- 评价加载提示 -->
            <transition name="eval-fade">
                <div v-if="saving" class="eval-overlay">
                    <div class="eval-overlay__content">
                        <img src="/static/bg/eval.png" alt="" class="eval-overlay__icon" />
                        <div class="eval-overlay__text">正在保存数据…</div>
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
            patientIntro: null,
            patientIntroPresentation: '',
            patientCaseId: '',
            patientBasicInfo: '',
            patientPhysicalExam: [],
            sessionId: null,
            patientName: '',
            avatarEmotion: 'neutral',
            lastPatientMessage: '',
            prevEmotion: 'neutral',
            // 保存状态
            saving: false,
            // 第一次发送标记
            _firstMessage: false,
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
        // 医学生输入 → 显示为"医生" → 调用 LLM 患者 → 显示为"患者"
        async sendMessage() {
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
                let patientText;
                let presentation = '';
                // 第一次发送：使用后端返回的开场白作为患者回复
                if (this._firstMessage && this.patientIntro) {
                    patientText = this.patientIntro;
                    presentation = this.patientIntroPresentation;
                    this._firstMessage = false;
                } else {
                    const res = await API.sendMessage(this.sessionId, doctorMessage);
                    patientText = res.response || '';
                    presentation = res.presentation || '';
                }

                console.log('[Interview] 患者原始回复:', patientText.substring(0, 50));

                // 提取情绪状态并移除标记
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
                    content: '（患者暂时无法回应，请稍后重试）',
                    time: this.getCurrentTime(),
                });
                console.error('[Interview] 患者回复失败:', err);
            } finally {
                this.isTyping = false;
                this.$nextTick(() => this.scrollToBottom());
            }
        },

        handleKeydown(e) {
            if (!e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
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

        goBack() {
            if (this.sessionId) API.endChat(this.sessionId);
            this.$router.push('/patients');
        },

        async handleEndPhase() {
            if (this.saving) return;
            if (this.messages.length === 0) {
                this.$message.warning('尚未开始对话，无法结束阶段');
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
                    console.error('[Interview] 保存记录失败:', err);
                }
            }

            if (this.sessionId) API.endChat(this.sessionId);
            this.$router.push({ path: '/phase2', query: { id: caseId } });
        },

        async initSession() {
            const caseId = this.$route.query.id;
            if (!caseId) {
                this.patientIntro = '';
                return;
            }

            this.patientCaseId = caseId;

            try {
                const caseInfo = await API.getCaseInfo(caseId);
                this.patientBasicInfo = caseInfo.basicInfomation || '';
                this.patientPhysicalExam = caseInfo.physicalExamination || '';
                this.patientName = caseInfo.basicInfomation
                    ? caseInfo.basicInfomation.replace(/^患者/, '')
                    : caseId;

                const chatRes = await API.startChat(caseId);
                this.sessionId = chatRes.session_id;
                this.patientIntro = chatRes.opening || '';
                this.patientIntroPresentation = chatRes.opening_presentation || '';

                // 医生先发起对话，patientIntro 作为第一次发送时的患者回复
                if (this.patientIntro) {
                    this._firstMessage = true;
                }

                // 保存 record_id，后续所有阶段统一使用
                if (chatRes.record_id) {
                    sessionStorage.setItem('record_id', chatRes.record_id);
                }

                // 不再提前显示 patientIntro，等医生发送第一条消息后才由 sendMessage 更新表情
                this.prevEmotion = this.avatarEmotion;
            } catch (err) {
                console.error('[Interview] 初始化会话失败:', err);
                this.patientIntro = '医生您好，我最近身体不太舒服，想请您帮我看看。';
                this._firstMessage = true;
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
