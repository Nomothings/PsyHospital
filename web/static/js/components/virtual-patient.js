/**
 * VirtualPatient Component
 * Left-side virtual patient display area - expression changes with dialogue
 */
const VirtualPatient = {
    props: {
        patientName: { type: String, default: '' },
        basicInfo: { type: String, default: '' },
        physicalExam: { type: [String, Array], default: '' },
        emotion: { type: String, default: 'neutral' },
    },

    template: `
        <div class="virtual-patient">
            <div class="virtual-patient__avatar-area">
                <div class="virtual-patient__face">
                    <img :src="characterSrc" alt="Patient" class="virtual-patient__image" />
                </div>

                <div class="virtual-patient__emotion-tag">
                    <span class="virtual-patient__emotion-dot"
                          :class="'emotion-' + emotion"></span>
                    {{ emotionLabel }}
                </div>
            </div>

            <div class="virtual-patient__info">
                <div class="virtual-patient__name">Patient {{ patientName }}</div>
                <div class="virtual-patient__basic">{{ basicInfo }}</div>
                <div class="virtual-patient__divider"></div>
                <div class="virtual-patient__complaint-title">Physical Examination</div>
                <div class="virtual-patient__physical-exam-text">
                    <template v-if="Array.isArray(physicalExam)">
                        <div v-for="(item, idx) in physicalExam" :key="idx" class="physical-exam-item">
                            {{ item }}
                        </div>
                    </template>
                    <template v-else>
                        {{ physicalExam }}
                    </template>
                </div>
            </div>
        </div>
    `,

    computed: {
        emotionLabel() {
            const labels = {
                neutral: 'Calm',
                sad: 'Sad',
                anxious: 'Anxious',
                angry: 'Angry',
                excited: 'Excited',
                flat: 'Flat',
            };
            return labels[this.emotion] || 'Calm';
        },

        avatarGender() {
            const rawInfo = String(this.basicInfo || '');
            const info = rawInfo.toLowerCase();

            if (
                info.includes('female') ||
                info.includes('woman') ||
                info.includes('girl') ||
                rawInfo.includes('女')
            ) {
                return 'f';
            }

            if (
                info.includes('male') ||
                info.includes('man') ||
                info.includes('boy') ||
                rawInfo.includes('男')
            ) {
                return 'm';
            }

            return 'm';
        },

        characterSrc() {
            const prefix = this.avatarGender;
            const map = {
                neutral: `/static/bg/${prefix}-neutral.png`,
                sad: `/static/bg/${prefix}-sad.png`,
                anxious: `/static/bg/${prefix}-anxious.png`,
                angry: `/static/bg/${prefix}-angry.png`,
                excited: `/static/bg/${prefix}-excited.png`,
                flat: `/static/bg/${prefix}-flat.png`,
            };
            return map[this.emotion] || `/static/bg/${prefix}-neutral.png`;
        },
    },
};
