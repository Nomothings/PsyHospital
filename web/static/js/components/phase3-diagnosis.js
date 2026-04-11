/**
 * Phase3Diagnosis 组件
 * Phase 3 — 病历书写 + 诊断
 *
 * 左右分栏布局：
 *   左侧 — 患者基本信息、体格检查、辅助检查结果、对话记录（可滚动）
 *   右侧 — 医生病历书写文本框
 */
const Phase3Diagnosis = {
    template: `
        <div class="phase3-page">
            <!-- 背景图 -->
            <div class="phase3-page__bg"></div>

            <!-- 顶部栏 -->
            <header class="phase3-header">
                <div class="phase3-header__left">
                    <el-button text @click="goBack" class="phase3-header__back-btn">
                        <el-icon><ArrowLeft /></el-icon>
                        返回
                    </el-button>
                    <h3 class="phase3-header__title">
                        {{ subStep === 'caseWriting' ? '病历书写' : '诊断' }}
                    </h3>
                    <span class="phase3-header__subtitle">第三阶段</span>
                </div>
                <div class="phase3-header__right">
                    <span class="phase3-header__patient">
                        患者 {{ caseId }}
                    </span>
                    <el-button
                        v-if="subStep === 'caseWriting'"
                        type="primary"
                        size="small"
                        round
                        @click="goToDiagnosis"
                        :disabled="!caseText.trim()"
                        class="phase3-header__next-btn"
                    >
                        完成病历书写，进入诊断
                    </el-button>
                </div>
            </header>

            <!-- 主内容 -->
            <div class="phase3-content phase3-content--split">
                <!-- ======================== 步骤1: 病历书写 ======================== -->
                <template v-if="subStep === 'caseWriting'">
                    <!-- 左侧：患者信息面板 -->
                    <aside class="phase3-left-panel">
                        <!-- 患者基本信息 -->
                        <div class="phase3-panel-section" v-if="caseInfo">
                            <div class="phase3-panel-section__title">患者基本信息</div>
                            <div class="phase3-panel-section__content">
                                <div class="phase3-info-row">
                                    <span class="phase3-info-row__label">基本信息</span>
                                    <span class="phase3-info-row__value">{{ caseInfo.basicInfomation || '暂无' }}</span>
                                </div>
                            </div>
                        </div>

                        <!-- 体格检查报告 -->
                        <div class="phase3-panel-section" v-if="caseInfo && caseInfo.physicalExamination">
                            <div class="phase3-panel-section__title">体格检查报告</div>
                            <div class="phase3-panel-section__content phase3-panel-section__scroll">
                                <div class="phase3-physical-exam-text">{{ caseInfo.physicalExamination }}</div>
                            </div>
                        </div>

                        <!-- 辅助检查结果 -->
                        <div class="phase3-panel-section" v-if="Object.keys(phase2Results).length">
                            <div class="phase3-panel-section__title">辅助检查结果</div>
                            <div class="phase3-panel-section__content">
                                <div v-for="(result, exam) in phase2Results" :key="exam"
                                     class="phase3-exam-result-row"
                                     :class="result === '无' ? 'phase3-exam-result-row--none' : 'phase3-exam-result-row--has'">
                                    <span class="phase3-exam-result-row__name">{{ exam }}</span>
                                    <span class="phase3-exam-result-row__value">
                                        {{ result === '无' ? '无此项检查' : result }}
                                    </span>
                                </div>
                            </div>
                        </div>

                        <!-- 对话记录 -->
                        <div class="phase3-panel-section phase3-panel-section--chat" v-if="phase1Messages.length">
                            <div class="phase3-panel-section__title">
                                对话记录
                                <span class="phase3-panel-section__hint">（最近 {{ phase1Messages.length }} 条）</span>
                            </div>
                            <div class="phase3-panel-section__scroll phase3-chat-scroll">
                                <div v-for="(msg, idx) in phase1Messages" :key="idx"
                                     class="phase3-chat-msg"
                                     :class="msg.role">
                                    <span class="phase3-chat-msg__role">
                                        {{ msg.role === 'doctor' ? '医生' : '患者' }}
                                    </span>
                                    <span class="phase3-chat-msg__content">{{ msg.content }}</span>
                                </div>
                            </div>
                        </div>
                    </aside>

                    <!-- 右侧：病历书写 -->
                    <main class="phase3-right-panel">
                        <div class="phase3-case-writing-card">
                            <div class="phase3-case-writing-card__header">
                                <h2 class="phase3-case-writing-card__title">病历书写</h2>
                                <p class="phase3-case-writing-card__subtitle">
                                    请根据左侧信息书写完整病历
                                </p>
                            </div>
                            <el-input
                                v-model="caseText"
                                type="textarea"
                                :rows="24"
                                placeholder="请根据访谈与检查结果书写病例（包括主诉、现病史、精神症状、功能受损情况等）"
                                resize="none"
                                class="phase3-case-textarea"
                            />
                        </div>
                    </main>
                </template>

                <!-- ======================== 步骤2: 诊断 ======================== -->
                <template v-else>
                    <div class="phase3-form-card">
                        <div class="phase3-form-card__header">
                            <h2 class="phase3-form-card__title">填写诊断</h2>
                            <p class="phase3-form-card__subtitle">
                                请根据已完成的病历，填写最终诊断信息
                            </p>
                            <el-tag type="success" effect="plain" size="small" style="margin-top: 8px;">
                                病历已书写
                            </el-tag>
                        </div>

                        <el-form
                            :model="form"
                            :rules="rules"
                            ref="formRef"
                            label-position="top"
                            class="phase3-form"
                        >
                            <el-form-item label="诊断类别" prop="category">
                                <el-select
                                    v-model="form.category"
                                    placeholder="请选择 ICD-11 疾病分类"
                                    filterable
                                    size="large"
                                    class="phase3-form__select"
                                >
                                    <el-option
                                        v-for="(cat, idx) in categories"
                                        :key="idx"
                                        :label="cat"
                                        :value="cat"
                                    />
                                </el-select>
                            </el-form-item>

                            <el-form-item label="具体病症" prop="disease">
                                <el-select
                                    v-model="form.disease"
                                    placeholder="请先选择诊断类别"
                                    filterable
                                    size="large"
                                    class="phase3-form__select"
                                    :disabled="!form.category"
                                >
                                    <el-option
                                        v-for="(dis, idx) in availableDiseases"
                                        :key="idx"
                                        :label="dis"
                                        :value="dis"
                                    />
                                </el-select>
                            </el-form-item>

                            <el-form-item label="诊断理由" prop="reason">
                                <el-input
                                    v-model="form.reason"
                                    type="textarea"
                                    :rows="6"
                                    placeholder="请说明诊断依据和推理过程…"
                                    resize="none"
                                    class="phase3-form__textarea"
                                />
                            </el-form-item>

                            <div class="phase3-form__actions">
                                <el-button
                                    type="primary"
                                    size="large"
                                    round
                                    @click="handleSubmit"
                                    :loading="submitting"
                                    class="phase3-form__submit-btn"
                                >
                                    完成诊断
                                </el-button>
                            </div>
                        </el-form>
                    </div>
                </template>
            </div>
        </div>
    `,

    data() {
        return {
            caseId: '',
            subStep: 'caseWriting',
            caseText: '',
            caseInfo: null,
            phase1Messages: [],
            phase2Results: {},
            form: {
                category: '',
                disease: '',
                reason: '',
            },
            submitting: false,
            categories: [
                "Neurodevelopmental disorders",
                "Schizophrenia or other primary psychotic disorders",
                "Catatonia",
                "Mood disorders",
                "Anxiety or fear-related disorders",
                "Obsessive-compulsive or related disorders",
                "Disorders specifically associated with stress",
                "Dissociative disorders",
                "Feeding or eating disorders",
                "Elimination disorders",
                "Disorders of bodily distress or bodily experience",
                "Disorders due to substance use or addictive behaviours",
                "Impulse control disorders",
                "Disruptive behaviour or dissocial disorders",
                "Personality disorders and related traits",
                "Paraphilic disorders",
                "Neurocognitive disorders",
                "Mental or behavioural disorders associated with pregnancy, childbirth or the puerperium",
                "Factitious disorders",
            ],
            diseaseMapping: {
                "Neurodevelopmental disorders": [
                    "6A00 Disorders of intellectual development",
                    "6A01 Developmental speech or language disorders",
                    "6A02 Autism spectrum disorder",
                    "6A03 Developmental learning disorder",
                    "6A04 Developmental motor coordination disorder",
                    "6A05 Attention deficit hyperactivity disorder",
                    "6A06 Stereotyped movement disorder",
                ],
                "Schizophrenia or other primary psychotic disorders": [
                    "6A20 Schizophrenia",
                    "6A21 Schizoaffective disorder",
                    "6A22 Schizotypal disorder",
                    "6A23 Acute and transient psychotic disorder",
                    "6A24 Delusional disorder",
                ],
                "Catatonia": [
                    "6A40 Catatonia associated with another mental disorder",
                    "6A41 Catatonia induced by substances or medications",
                ],
                "Mood disorders": [
                    "6A60 Bipolar type I disorder",
                    "6A61 Bipolar type II disorder",
                    "6A62 Cyclothymic disorder",
                    "6A70 Single episode depressive disorder",
                    "6A71 Recurrent depressive disorder",
                    "6A72 Dysthymic disorder",
                    "6A73 Mixed depressive and anxiety disorder",
                ],
                "Anxiety or fear-related disorders": [
                    "6B00 Generalised anxiety disorder",
                    "6B01 Panic disorder",
                    "6B02 Agoraphobia",
                    "6B03 Specific phobia",
                    "6B04 Social anxiety disorder",
                    "6B05 Separation anxiety disorder",
                    "6B06 Selective mutism",
                ],
                "Obsessive-compulsive or related disorders": [
                    "6B20 Obsessive-compulsive disorder",
                    "6B21 Body dysmorphic disorder",
                    "6B22 Olfactory reference disorder",
                    "6B23 Hypochondriasis",
                    "6B24 Hoarding disorder",
                    "6B25 Body-focused repetitive behaviour disorders",
                ],
                "Disorders specifically associated with stress": [
                    "6B40 Post traumatic stress disorder",
                    "6B41 Complex post traumatic stress disorder",
                    "6B42 Prolonged grief disorder",
                    "6B43 Adjustment disorder",
                    "6B44 Reactive attachment disorder",
                    "6B45 Disinhibited social engagement disorder",
                ],
                "Dissociative disorders": [
                    "6B60 Dissociative neurological symptom disorder",
                    "6B61 Dissociative amnesia",
                    "6B62 Trance disorder",
                    "6B63 Possession trance disorder",
                    "6B64 Dissociative identity disorder",
                    "6B65 Partial dissociative identity disorder",
                    "6B66 Depersonalization-derealization disorder",
                ],
                "Feeding or eating disorders": [
                    "6B80 Anorexia Nervosa",
                    "6B81 Bulimia Nervosa",
                    "6B82 Binge eating disorder",
                    "6B83 Avoidant-restrictive food intake disorder",
                    "6B84 Pica",
                    "6B85 Rumination-regurgitation disorder",
                ],
                "Elimination disorders": [
                    "6C00 Enuresis",
                    "6C01 Encopresis",
                ],
                "Disorders of bodily distress or bodily experience": [
                    "6C20 Bodily distress disorder",
                    "6C21 Body integrity dysphoria",
                ],
                "Disorders due to substance use or addictive behaviours": [
                    "6C40 Disorders due to use of alcohol",
                    "6C41 Disorders due to use of cannabis",
                    "6C42 Disorders due to use of synthetic cannabinoids",
                    "6C43 Disorders due to use of opioids",
                    "6C44 Disorders due to use of sedatives, hypnotics or anxiolytics",
                    "6C45 Disorders due to use of cocaine",
                    "6C46 Disorders due to use of stimulants including amphetamines, methamphetamine or methcathinone",
                    "6C47 Disorders due to use of synthetic cathinones",
                    "6C48 Disorders due to use of caffeine",
                    "6C49 Disorders due to use of hallucinogens",
                    "6C4A Disorders due to use of nicotine",
                    "6C4C Disorders due to use of MDMA or related drugs, including MDA",
                    "6C4D Disorders due to use of dissociative drugs including ketamine and phencyclidine [PCP]",
                    "6C4E Disorders due to use of other specified psychoactive substances, including medications",
                    "6C4F Disorders due to use of multiple specified psychoactive substances, including medications",
                    "6C4G Disorders due to use of unknown or unspecified psychoactive substances",
                    "6C4H Disorders due to use of non-psychoactive substances",
                    "6C50 Gambling disorder",
                    "6C51 Gaming disorder",
                ],
                "Impulse control disorders": [
                    "6C70 Pyromania",
                    "6C71 Kleptomania",
                    "6C72 Compulsive sexual behaviour disorder",
                ],
                "Disruptive behaviour or dissocial disorders": [
                    "6C90 Oppositional defiant disorder",
                    "6C91 Conduct-dissocial disorder",
                ],
                "Personality disorders and related traits": [
                    "6D10 Personality disorder",
                ],
                "Paraphilic disorders": [
                    "6D30 Exhibitionistic disorder",
                    "6D31 Voyeuristic disorder",
                    "6D32 Pedophilic disorder",
                    "6D33 Coercive sexual sadism disorder",
                    "6D34 Frotteuristic disorder",
                    "6D35 Other paraphilic disorder involving non-consenting individuals",
                    "6D36 Paraphilic disorder involving solitary behaviour or consenting individuals",
                ],
                "Neurocognitive disorders": [
                    "6D70 Delirium",
                    "6D71 Mild neurocognitive disorder",
                    "6D72 Amnestic disorder",
                    "6D80 Dementia due to Alzheimer disease",
                    "6D81 Dementia due to cerebrovascular disease",
                    "6D82 Dementia due to Lewy body disease",
                    "6D83 Frontotemporal dementia",
                    "6D84 Dementia due to psychoactive substances including medications",
                    "6D85 Dementia due to diseases classified elsewhere",
                    "6D86 Behavioural or psychological disturbances in dementia",
                ],
                "Mental or behavioural disorders associated with pregnancy, childbirth or the puerperium": [
                    "6E20 Mental or behavioural disorders associated with pregnancy, childbirth or the puerperium, without psychotic symptoms",
                    "6E21 Mental or behavioural disorders associated with pregnancy, childbirth or the puerperium, with psychotic symptoms",
                ],
                "Factitious disorders": [
                    "6D50 Factitious disorder imposed on self",
                    "6D51 Factitious disorder imposed on another",
                ],
            },
            rules: {
                category: [
                    { required: true, message: '请选择诊断类别', trigger: 'change' },
                ],
                disease: [
                    { required: true, message: '请输入具体病症', trigger: 'blur' },
                ],
                reason: [
                    { required: true, message: '请填写诊断理由', trigger: 'blur' },
                ],
            },
        };
    },

    computed: {
        ArrowLeft() { return ElementPlusIconsVue.ArrowLeft; },
        availableDiseases() {
            return this.diseaseMapping[this.form.category] || [];
        },
    },

    watch: {
        'form.category'() {
            this.form.disease = '';
        },
    },

    methods: {
        goToDiagnosis() {
            if (!this.caseText.trim()) {
                this.$message.warning('请先书写病历');
                return;
            }
            sessionStorage.setItem('phase3_caseText', this.caseText.trim());
            this.subStep = 'diagnosis';
            this.$message.success('病历已保存，请填写诊断信息');
        },

        async handleSubmit() {
            this.$refs.formRef.validate(async (valid) => {
                if (!valid) return;

                this.submitting = true;
                try {
                    await API.submitCaseWriting(this.caseId, this.caseText.trim());

                    const result = await API.submitDiagnosis(this.caseId, {
                        category: this.form.category,
                        disease: this.form.disease,
                        reason: this.form.reason,
                    });

                    this.$message.success('第三阶段已完成');
                    console.log('[Phase3Diagnosis] 提交成功:', result);

                    sessionStorage.setItem('phase3_result', JSON.stringify({
                        caseId: this.caseId,
                        caseText: this.caseText.trim(),
                        category: this.form.category,
                        disease: this.form.disease,
                        reason: this.form.reason,
                    }));

                    this.$router.push('/patients');
                } catch (err) {
                    this.$message.error('提交失败: ' + (err.message || '未知错误'));
                    console.error('[Phase3Diagnosis] 提交失败:', err);
                } finally {
                    this.submitting = false;
                }
            });
        },

        goBack() {
            if (this.subStep === 'diagnosis') {
                this.subStep = 'caseWriting';
            } else {
                this.$router.push({ path: '/phase2', query: { id: this.caseId } });
            }
        },

        async loadPhaseData() {
            if (this.caseId) {
                try {
                    const info = await API.getCaseInfo(this.caseId);
                    this.caseInfo = info;
                } catch (err) {
                    console.error('[Phase3Diagnosis] 加载患者信息失败:', err);
                }
            }

            const messagesStr = sessionStorage.getItem('phase2_messages');
            console.log('[Phase3Diagnosis] phase2_messages raw:', messagesStr);
            if (messagesStr) {
                try {
                    const messages = JSON.parse(messagesStr);
                    console.log('[Phase3Diagnosis] parsed messages:', messages);
                    this.phase1Messages = messages.slice(-12);
                    console.log('[Phase3Diagnosis] phase1Messages:', this.phase1Messages);
                } catch (err) {
                    console.error('[Phase3Diagnosis] 解析 Phase 1 消息失败:', err);
                }
            } else {
                console.warn('[Phase3Diagnosis] 未找到 phase2_messages');
            }

            const resultsStr = sessionStorage.getItem('phase2_checkedResults');
            if (resultsStr) {
                try {
                    this.phase2Results = JSON.parse(resultsStr);
                } catch (err) {
                    console.error('[Phase3Diagnosis] 解析 Phase 2 结果失败:', err);
                }
            }

            const savedCaseText = sessionStorage.getItem('phase3_caseText');
            if (savedCaseText) {
                this.caseText = savedCaseText;
            }
        },
    },

    mounted() {
        this.caseId = this.$route.query.id || sessionStorage.getItem('phase2_caseId') || '';
        if (!this.caseId) {
            this.$message.warning('未找到病例信息，请从患者列表进入');
        }
        this.loadPhaseData();
    },
};
