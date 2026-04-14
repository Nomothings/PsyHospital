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
                    :last-patient-message="lastPatientMessage"
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
                            :disabled="evalState !== 'idle'"
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
                                您正在与患者进行临床访谈，注意问诊的全面性和沟通技巧。
                            </div>
                        </div>
                    </div>

                    <!-- 患者开场白 -->
                    <div class="chat-bubble patient" v-if="patientIntro">
                        <div class="chat-bubble__avatar">
                            <el-icon :size="20"><UserFilled /></el-icon>
                        </div>
                        <div class="chat-bubble__content">
                            <div class="chat-bubble__name">患者</div>
                            <div class="chat-bubble__text">{{ patientIntro }}</div>
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
                                {{ msg.role === 'patient' ? '患者' : '医生' }}
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
                    <div v-if="messages.length === 0 && !isTyping && patientIntro === null"
                         class="chat-bubble system">
                        <div class="chat-bubble__content">
                            <div class="chat-bubble__text">正在加载患者信息…</div>
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
                            :disabled="isTyping || evalState !== 'idle'"
                            resize="none"
                            type="textarea"
                            :rows="1"
                            class="interview-input__field"
                        />
                        <el-button
                            type="primary"
                            round
                            @click="sendMessage"
                            :disabled="!inputText.trim() || isTyping || evalState !== 'idle'"
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

            <!-- 流水线转场动画 -->
            <phase-transition-pipeline
                :visible="showPipeline"
                :phase-number="1"
                :case-id="$route.query.id"
                :eval-payload="{ messages: messages }"
                @eval-complete="onPipelineEvalComplete"
                @close="showPipeline = false"
            />

            <!-- 评价加载遮罩（保留作为兜底） -->
            <transition name="eval-fade">
                <div v-if="evalState === 'loading' && !showPipeline" class="eval-overlay">
                    <div class="eval-overlay__content">
                        <img src="/static/bg/eval.png" alt="" class="eval-overlay__icon" />
                        <div class="eval-overlay__text">正在进行阶段评价…</div>
                        <div class="eval-overlay__subtext">分析对话质量与临床技巧</div>
                    </div>
                </div>
            </transition>

            <!-- 评价结果面板 -->
            <transition name="eval-slide">
                <div v-if="evalState === 'showing' || evalState === 'done'" class="eval-panel">
                    <div class="eval-panel__inner">
                        <div class="eval-panel__header">
                            <el-icon :size="22" color="#5ed6c8"><CircleCheckFilled /></el-icon>
                            <h3 class="eval-panel__title">阶段评价完成</h3>
                            <el-tag type="success" size="small" effect="plain">Phase 1</el-tag>
                        </div>

                        <div class="eval-panel__body">
                            <!-- 对话统计 -->
                            <div class="eval-section" v-if="evalData.conversation_stats">
                                <div class="eval-section__title">
                                    <el-icon :size="14" color="#5ed6c8"><ChatDotRound /></el-icon>
                                    对话统计
                                </div>
                                <div class="eval-stats">
                                    <div class="eval-stat">
                                        <span class="eval-stat__label">总轮数</span>
                                        <span class="eval-stat__value">{{ evalData.conversation_stats.total_turns }}</span>
                                    </div>
                                    <div class="eval-stat">
                                        <span class="eval-stat__label">医生发言</span>
                                        <span class="eval-stat__value">{{ evalData.conversation_stats.doctor_turns }}</span>
                                    </div>
                                    <div class="eval-stat">
                                        <span class="eval-stat__label">患者发言</span>
                                        <span class="eval-stat__value">{{ evalData.conversation_stats.patient_turns }}</span>
                                    </div>
                                </div>
                            </div>

                            <!-- 共情度评估 -->
                            <div class="eval-section" v-if="evalData.empathy_evaluation">
                                <div class="eval-section__title">
                                    <el-icon :size="14" color="#e6a23c"><StarFilled /></el-icon>
                                    共情度评估
                                </div>
                                <div class="eval-empathy">
                                    <div class="eval-empathy__level">
                                        <el-tag type="warning" size="large" effect="dark" round>
                                            {{ evalData.empathy_evaluation.empathy_level }}
                                        </el-tag>
                                    </div>
                                    <div class="eval-empathy__reason" v-if="evalData.empathy_evaluation.why_this_level">
                                        {{ evalData.empathy_evaluation.why_this_level }}
                                    </div>
                                    <div class="eval-empathy__evidence" v-if="evalData.empathy_evaluation.evidence">
                                        <span class="eval-empathy__evidence-label">证据：</span>
                                        {{ evalData.empathy_evaluation.evidence }}
                                    </div>
                                </div>
                            </div>

                            <!-- 专业度评估 -->
                            <div class="eval-section" v-if="evalData.profession_evaluation">
                                <div class="eval-section__title">
                                    <el-icon :size="14" color="#409eff"><TrophyBase /></el-icon>
                                    专业度评估
                                </div>
                                <div class="eval-profession">
                                    <div class="eval-profession__score">
                                        <span class="eval-profession__value">{{ evalData.profession_evaluation.total_score }}</span>
                                        <span class="eval-profession__max">/ {{ evalData.profession_evaluation.question_count * 2 }}</span>
                                    </div>
                                    <div class="eval-profession__avg">
                                        平均分 {{ evalData.profession_evaluation.average_score.toFixed(2) }}
                                    </div>
                                </div>
                            </div>

                            <!-- 无评估数据提示 -->
                            <div v-if="!evalData.empathy_evaluation && !evalData.profession_evaluation" class="eval-section eval-section--note">
                                <el-icon :size="16" color="#c0c4cc"><InfoFilled /></el-icon>
                                <span>LLM 评估服务暂时不可用，已跳过共情度与专业度评估</span>
                            </div>
                        </div>

                        <div class="eval-panel__footer">
                            <el-button
                                type="primary"
                                size="large"
                                round
                                @click="confirmAndProceed"
                            >
                                好的，进入下一阶段
                            </el-button>
                        </div>
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
            patientCaseId: '',
            patientBasicInfo: '',
            patientPhysicalExam: [],
            sessionId: null,
            patientName: '',
            avatarEmotion: 'neutral',
            lastPatientMessage: '',
            prevEmotion: 'neutral',
            // 评价状态: 'idle' | 'loading' | 'showing' | 'done'
            evalState: 'idle',
            evalData: {},
            // 流水线动画
            showPipeline: false,
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
        ChatDotRound() { return ElementPlusIconsVue.ChatDotRound; },
        StarFilled() { return ElementPlusIconsVue.StarFilled; },
        TrophyBase() { return ElementPlusIconsVue.TrophyBase; },

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
                const res = await API.sendMessage(this.sessionId, doctorMessage);
                const patientText = res.response || '';

                this.messages.push({
                    role: 'patient',
                    content: patientText,
                    time: this.getCurrentTime(),
                });

                // 更新患者表情
                this.lastPatientMessage = patientText;
                this.avatarEmotion = EmotionDetector.detect(patientText, this.prevEmotion);
                this.prevEmotion = this.avatarEmotion;
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
            if (this.evalState !== 'idle') return;
            if (this.messages.length === 0) {
                this.$message.warning('尚未开始对话，无法评价');
                return;
            }

            // 先保存当前阶段记录
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

            // 保存记录后显示流水线动画
            this.showPipeline = true;
        },

        /** 流水线评价完成回调 */
        onPipelineEvalComplete(result) {
            // 先保存评价结果
            this.evalData = result;
            // 显示评价结果面板
            this.evalState = 'showing';
        },

        async confirmAndProceed() {
            this.evalState = 'done';
            const caseId = this.$route.query.id;
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

                // 保存 record_id，后续所有阶段统一使用
                if (chatRes.record_id) {
                    sessionStorage.setItem('record_id', chatRes.record_id);
                }

                // 从开场白推断初始情绪
                if (this.patientIntro) {
                    this.lastPatientMessage = this.patientIntro;
                    this.avatarEmotion = EmotionDetector.detect(this.patientIntro, 'neutral');
                    this.prevEmotion = this.avatarEmotion;
                }
            } catch (err) {
                console.error('[Interview] 初始化会话失败:', err);
                this.patientIntro = '医生您好，我最近身体不太舒服，想请您帮我看看。';
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
