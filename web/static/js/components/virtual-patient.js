/**
 * VirtualPatient 组件
 * 左侧虚拟患者展示区 — 表情随对话变化
 */
const VirtualPatient = {
    props: {
        patientName: { type: String, default: '' },
        basicInfo: { type: String, default: '' },
        physicalExam: { type: String, default: '' },
        emotion: { type: String, default: 'neutral' },
    },

    template: `
        <div class="virtual-patient">
            <!-- 患者虚拟形象 -->
            <div class="virtual-patient__avatar-area">
                <div class="virtual-patient__face">
                    <img src="/static/character/patient.png" alt="患者" class="virtual-patient__image" />
                </div>

                <!-- 情绪标签 -->
                <div class="virtual-patient__emotion-tag">
                    <span class="virtual-patient__emotion-dot"
                          :class="'emotion-' + emotion"></span>
                    {{ emotionLabel }}
                </div>
            </div>

            <!-- 患者信息 -->
            <div class="virtual-patient__info">
                <div class="virtual-patient__name">患者 {{ patientName }}</div>
                <div class="virtual-patient__basic">{{ basicInfo }}</div>
                <div class="virtual-patient__divider"></div>
                <div class="virtual-patient__complaint-title">体格检查</div>
                <div class="virtual-patient__physical-exam-text">
                    {{ physicalExam }}
                </div>
            </div>
        </div>
    `,

    computed: {
        emotionLabel() {
            const labels = {
                neutral: '平静',
                nervous: '紧张',
                suspicious: '怀疑',
                sad: '悲伤',
                angry: '愤怒',
                defensive: '防御',
                confused: '困惑',
                relaxed: '放松',
                hesitant: '犹豫',
                distressed: '痛苦',
            };
            return labels[this.emotion] || '平静';
        },
    },
};
