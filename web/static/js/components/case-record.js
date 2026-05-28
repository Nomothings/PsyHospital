/**
 * CaseRecord Component
 * Interview Process Complete Record Page
 *
 * Displayed content:
 *   - Patient basic information
 *   - Phase 1: Doctor-patient dialogue record
 *   - Phase 2: Examinations ordered by doctor and results
 *   - Phase 3: Case writing + diagnosis results
 */
const CaseRecord = {
    template: `
        <div class="case-record-page">
            <!-- Background -->
            <div class="case-record-page__bg"></div>

            <!-- Top Bar -->
            <header class="case-record-header">
                <div class="case-record-header__left">
                    <el-button text @click="goBack" class="case-record-header__back-btn">
                        <el-icon><ArrowLeft /></el-icon>
                        Back
                    </el-button>
                    <h3 class="case-record-header__title">Interview Process Record</h3>
                </div>
                <div class="case-record-header__right">
                    <span class="case-record-header__patient">Patient {{ caseId }}</span>
                </div>
            </header>

            <!-- Main Content -->
            <div class="case-record-content">
                <div class="case-record-card">
                    <!-- Patient Basic Info -->
                    <div class="case-record-section" v-if="caseInfo">
                        <div class="case-record-section__header">
                            <el-icon :size="20" color="#5ed6c8"><UserFilled /></el-icon>
                            <h4 class="case-record-section__title">Patient Basic Info</h4>
                        </div>
                        <div class="case-record-section__body">
                            <div class="case-record-info-row">
                                <span class="case-record-info-row__label">Basic Info</span>
                                <span class="case-record-info-row__value">{{ caseInfo.basicInfomation || 'N/A' }}</span>
                            </div>
                            <div class="case-record-info-row" v-if="caseInfo.physicalExamination">
                                <span class="case-record-info-row__label">Physical Examination</span>
                                <span class="case-record-info-row__value">{{ caseInfo.physicalExamination }}</span>
                            </div>
                        </div>
                    </div>

                    <!-- Phase 1: Dialogue Record -->
                    <div class="case-record-section" v-if="conversationMessages.length">
                        <div class="case-record-section__header">
                            <el-icon :size="20" color="#5ed6c8"><ChatDotRound /></el-icon>
                            <h4 class="case-record-section__title">Phase 1: Doctor-Patient Dialogue</h4>
                            <el-tag type="info" size="small" effect="plain">{{ conversationMessages.length }} messages</el-tag>
                        </div>
                        <div class="case-record-section__body">
                            <div class="case-record-conversation">
                                <div v-for="(msg, idx) in conversationMessages" :key="idx"
                                     class="case-record-msg"
                                     :class="msg.role">
                                    <div class="case-record-msg__avatar">
                                        <el-icon :size="16" v-if="msg.role === 'patient'"><UserFilled /></el-icon>
                                        <el-icon :size="16" v-else><User /></el-icon>
                                    </div>
                                    <div class="case-record-msg__content">
                                        <div class="case-record-msg__role">
                                            {{ msg.role === 'patient' ? 'Patient' : 'Doctor' }}
                                        </div>
                                        <div class="case-record-msg__text">{{ msg.content }}</div>
                                        <div class="case-record-msg__time" v-if="msg.time">{{ msg.time }}</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Phase 2: Examination Record -->
                    <div class="case-record-section" v-if="examRecords.length">
                        <div class="case-record-section__header">
                            <el-icon :size="20" color="#5ed6c8"><DocumentChecked /></el-icon>
                            <h4 class="case-record-section__title">Phase 2: Auxiliary Examinations</h4>
                            <el-tag type="warning" size="small" effect="plain">{{ examRecords.length }} exams</el-tag>
                        </div>
                        <div class="case-record-section__body">
                            <div class="case-record-exam-list">
                                <div v-for="(exam, idx) in examRecords" :key="idx"
                                     class="case-record-exam-item"
                                     :class="(exam.result === '无' || exam.result === 'None') ? 'case-record-exam-item--none' : 'case-record-exam-item--has'">
                                    <div class="case-record-exam-item__name">{{ exam.name }}</div>
                                    <div class="case-record-exam-item__result">
                                        {{ (exam.result === '无' || exam.result === 'None') ? 'Not examined' : exam.result }}
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Phase 3: Case Writing -->
                    <div class="case-record-section" v-if="caseForm">
                        <div class="case-record-section__header">
                            <el-icon :size="20" color="#5ed6c8"><EditPen /></el-icon>
                            <h4 class="case-record-section__title">Phase 3: Case Writing</h4>
                        </div>
                        <div class="case-record-section__body">
                            <div class="case-record-case-form">
                                <div class="case-record-cf-row" v-if="caseForm.name">
                                    <span class="case-record-cf-label">Name</span>
                                    <span class="case-record-cf-value">{{ caseForm.name }}</span>
                                </div>
                                <div class="case-record-cf-row" v-if="caseForm.age">
                                    <span class="case-record-cf-label">Age</span>
                                    <span class="case-record-cf-value">{{ caseForm.age }}</span>
                                </div>
                                <div class="case-record-cf-row" v-if="caseForm.gender">
                                    <span class="case-record-cf-label">Gender</span>
                                    <span class="case-record-cf-value">{{ caseForm.gender }}</span>
                                </div>
                                <div class="case-record-cf-row" v-if="caseForm.chiefComplaint">
                                    <span class="case-record-cf-label">Chief Complaint</span>
                                    <span class="case-record-cf-value">{{ caseForm.chiefComplaint }}</span>
                                </div>
                                <div class="case-record-cf-row" v-if="caseForm.familyHistory">
                                    <span class="case-record-cf-label">Family History</span>
                                    <span class="case-record-cf-value">{{ caseForm.familyHistory }}</span>
                                </div>
                                <div class="case-record-cf-row" v-if="caseForm.pastHistory">
                                    <span class="case-record-cf-label">Past History</span>
                                    <span class="case-record-cf-value">{{ caseForm.pastHistory }}</span>
                                </div>
                                <div class="case-record-cf-row" v-if="caseForm.physicalExam">
                                    <span class="case-record-cf-label">Physical Examination</span>
                                    <span class="case-record-cf-value">{{ caseForm.physicalExam }}</span>
                                </div>
                                <div class="case-record-cf-row" v-if="caseForm.mentalExam">
                                    <span class="case-record-cf-label">Mental Status Exam</span>
                                    <span class="case-record-cf-value">{{ caseForm.mentalExam }}</span>
                                </div>
                                <div class="case-record-cf-row" v-if="caseForm.auxiliaryExam">
                                    <span class="case-record-cf-label">Auxiliary Examinations</span>
                                    <span class="case-record-cf-value">{{ caseForm.auxiliaryExam }}</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Phase 3: Diagnosis Results -->
                    <div class="case-record-section" v-if="diagnosis">
                        <div class="case-record-section__header">
                            <el-icon :size="20" color="#5ed6c8"><CircleCheckFilled /></el-icon>
                            <h4 class="case-record-section__title">Phase 3: Diagnosis Results</h4>
                        </div>
                        <div class="case-record-section__body">
                            <div class="case-record-diagnosis">
                                <!-- New format: multiple diagnoses -->
                                <template v-if="diagnosis.diagnoses && diagnosis.diagnoses.length">
                                    <div v-for="(dx, idx) in diagnosis.diagnoses" :key="idx" class="case-record-diagnosis-group">
                                        <div class="case-record-diagnosis-group__header">
                                            <el-tag type="success" size="small" effect="plain" round>{{ localizedCategory(dx.category) }}</el-tag>
                                        </div>
                                        <div class="case-record-diagnosis-group__items" v-if="dx.diseases && dx.diseases.length">
                                            <el-tag v-for="(dis, di) in dx.diseases" :key="di" size="small" round style="margin: 2px 4px 2px 0;">{{ localizedDisease(dis) }}</el-tag>
                                        </div>
                                        <div v-else class="case-record-diagnosis-group__none">No specific disease selected</div>
                                    </div>
                                </template>
                                <!-- Old format: single diagnosis -->
                                <template v-else>
                                    <div class="case-record-diagnosis__item">
                                        <span class="case-record-diagnosis__label">Diagnostic Category</span>
                                        <span class="case-record-diagnosis__value">{{ localizedCategory(diagnosis.category) }}</span>
                                    </div>
                                    <div class="case-record-diagnosis__item">
                                        <span class="case-record-diagnosis__label">Specific Diagnosis</span>
                                        <span class="case-record-diagnosis__value">{{ localizedDiseaseText(diagnosis.disease) }}</span>
                                    </div>
                                </template>
                                <div class="case-record-diagnosis__item">
                                    <span class="case-record-diagnosis__label">Diagnostic Reasoning</span>
                                    <span class="case-record-diagnosis__value">{{ diagnosis.reason }}</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Phase 4: Treatment Plan -->
                    <div class="case-record-section" v-if="treatment">
                        <div class="case-record-section__header">
                            <el-icon :size="20" color="#5ed6c8"><FirstAidKit /></el-icon>
                            <h4 class="case-record-section__title">Phase 4: Treatment Plan</h4>
                        </div>
                        <div class="case-record-section__body">
                            <div class="case-record-treatment">
                                <div v-for="(value, key) in treatment" :key="key" class="case-record-tx-item">
                                    <span class="case-record-tx-item__label">{{ key }}</span>
                                    <span class="case-record-tx-item__value">{{ value }}</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Unified Evaluation Report -->
                    <div class="case-record-section" v-if="evaluationReport">
                        <div class="case-record-section__header">
                            <el-icon :size="20" color="#3ec4b0"><CircleCheckFilled /></el-icon>
                            <h4 class="case-record-section__title">Comprehensive Evaluation Report</h4>
                            <el-tag type="success" size="small" effect="plain">Full Process Evaluation Complete</el-tag>
                        </div>
                        <div class="case-record-section__body">
                            <!-- Interview Evaluation -->
                            <div class="case-record-eval-block" v-if="evaluationReport.phase1 && !evaluationReport.phase1._fallback">
                                <h5 class="case-record-eval-block__title">1. Interview Evaluation</h5>
                                <div class="case-record-eval-block__body">
                                    <div v-if="evaluationReport.phase1.conversation_stats" class="case-record-eval-sub">
                                        <span>Dialogue Turns: {{ evaluationReport.phase1.conversation_stats.total_turns }}</span>
                                        <span class="case-record-eval-sub__sep">|</span>
                                        <span>Doctor Turns: {{ evaluationReport.phase1.conversation_stats.doctor_turns }}</span>
                                        <span class="case-record-eval-sub__sep">|</span>
                                        <span>Patient Turns: {{ evaluationReport.phase1.conversation_stats.patient_turns }}</span>
                                    </div>
                                    <div v-if="evaluationReport.phase1.empathy_evaluation" class="case-record-eval-sub">
                                        <span>Empathy Level: <strong>{{ evaluationReport.phase1.empathy_evaluation.empathy_level }}</strong></span>
                                    </div>
                                    <div v-if="evaluationReport.phase1.empathy_evaluation?.why_this_level" class="case-record-eval-detail eval-markdown eval-markdown--compact" v-html="renderMarkdown(evaluationReport.phase1.empathy_evaluation.why_this_level)">
                                    </div>
                                    <div v-if="evaluationReport.phase1.profession_evaluation" class="case-record-eval-sub">
                                        <span>Professionalism Level: <strong>{{ formatScore(evaluationReport.phase1.profession_evaluation.profession_level || evaluationReport.phase1.profession_evaluation.score) }}</strong> / 5</span>
                                    </div>
                                    <div v-if="subjectiveReasonText(evaluationReport.phase1.profession_evaluation)" class="case-record-eval-detail eval-markdown eval-markdown--compact" v-html="renderMarkdown(subjectiveReasonText(evaluationReport.phase1.profession_evaluation))">
                                    </div>
                                </div>
                            </div>

                            <!-- Examination Evaluation -->
                            <div class="case-record-eval-block" v-if="evaluationReport.phase2 && !evaluationReport.phase2._fallback">
                                <h5 class="case-record-eval-block__title">2. Examination Evaluation</h5>
                                <div class="case-record-eval-block__body">
                                    <div v-if="evaluationReport.phase2.accuracy !== undefined" class="case-record-eval-sub">
                                        <span>Examination Accuracy: <strong>{{ formatAccuracy(evaluationReport.phase2.accuracy) }}</strong></span>
                                    </div>
                                    <div v-if="evaluationReport.phase2.exam_details" class="case-record-eval-exam-list">
                                        <div v-for="(detail, key) in evaluationReport.phase2.exam_details" :key="key"
                                             class="case-record-eval-exam-item"
                                             :class="detail?.correct ? 'case-record-eval-exam-item--correct' : 'case-record-eval-exam-item--wrong'">
                                            <span>{{ key }}</span>
                                            <span>{{ detail?.correct ? 'Correct' : 'Incorrect' }}</span>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <!-- Case Writing & Diagnosis Evaluation -->
                            <div class="case-record-eval-block" v-if="evaluationReport.phase3_full && !evaluationReport.phase3_full._fallback">
                                <h5 class="case-record-eval-block__title">3. Case Writing & Diagnosis Evaluation</h5>
                                <div class="case-record-eval-block__body">
                                    <!-- Case Writing -->
                                    <div v-if="evaluationReport.phase3_full.case_writing" class="case-record-eval-sub-block">
                                        <div class="case-record-eval-sub">
                                            <span>Case Writing Total Score: <strong>{{ formatScore(evaluationReport.phase3_full.case_writing.total_score) }}</strong></span>
                                        </div>
                                        <div v-for="(section, key) in evaluationReport.phase3_full.case_writing.dimensions" :key="key" class="case-record-eval-sub">
                                            <span>{{ section.section_name }}: {{ formatPercentage(section) }}</span>
                                            <span v-if="section.detail" class="case-record-eval-sub__detail">— {{ section.detail }}</span>
                                        </div>
                                    </div>
                                    <!-- Diagnosis -->
                                    <div v-if="evaluationReport.phase3_full.diagnosis" class="case-record-eval-sub-block">
                                        <div class="case-record-eval-sub">
                                            <span>Disease Type Score: <strong>{{ formatScore(evaluationReport.phase3_full.diagnosis.disease_type?.score) }}</strong></span>
                                            <span v-if="evaluationReport.phase3_full.diagnosis.disease_type?.detail" class="case-record-eval-sub__detail">— {{ evaluationReport.phase3_full.diagnosis.disease_type.detail }}</span>
                                        </div>
                                        <div v-if="evaluationReport.phase3_full.diagnosis.disease_type?.metrics" class="case-record-eval-sub">
                                            <span>P: {{ (evaluationReport.phase3_full.diagnosis.disease_type.metrics.precision * 100).toFixed(0) }}%</span>
                                            <span>R: {{ (evaluationReport.phase3_full.diagnosis.disease_type.metrics.recall * 100).toFixed(0) }}%</span>
                                            <span>F1: {{ (evaluationReport.phase3_full.diagnosis.disease_type.metrics.f1 * 100).toFixed(0) }}%</span>
                                            <span>J: {{ (evaluationReport.phase3_full.diagnosis.disease_type.metrics.jaccard * 100).toFixed(0) }}%</span>
                                        </div>
                                        <div class="case-record-eval-sub">
                                            <span>Diagnostic Correctness: <strong>{{ formatScore(evaluationReport.phase3_full.diagnosis.diagnostic_correctness?.score) }}</strong></span>
                                        </div>
                                        <div v-if="evaluationReport.phase3_full.diagnosis.diagnostic_correctness?.detail" class="case-record-eval-detail eval-markdown eval-markdown--compact" v-html="renderMarkdown(evaluationReport.phase3_full.diagnosis.diagnostic_correctness.detail)">
                                        </div>
                                        <div class="case-record-eval-sub">
                                            <span>Diagnostic Reasoning: <strong>{{ formatScore(evaluationReport.phase3_full.diagnosis.diagnostic_reasoning?.score) }}</strong></span>
                                        </div>
                                        <div v-if="evaluationReport.phase3_full.diagnosis.diagnostic_reasoning?.detail" class="case-record-eval-detail eval-markdown eval-markdown--compact" v-html="renderMarkdown(evaluationReport.phase3_full.diagnosis.diagnostic_reasoning.detail)">
                                        </div>
                                    </div>
                                    <div v-if="evaluationReport.phase3_full.clinical_note_subjective" class="case-record-eval-sub-block">
                                        <div class="case-record-eval-sub">
                                            <span>Clinical Note Subjective: <strong>{{ formatScore(evaluationReport.phase3_full.clinical_note_subjective.score) }}</strong> / 5</span>
                                        </div>
                                        <div v-if="subjectiveReasonText(evaluationReport.phase3_full.clinical_note_subjective)" class="case-record-eval-detail eval-markdown eval-markdown--compact" v-html="renderMarkdown(subjectiveReasonText(evaluationReport.phase3_full.clinical_note_subjective))">
                                        </div>
                                    </div>
                                    <div v-if="evaluationReport.phase3_full.diagnostic_rigor_subjective" class="case-record-eval-sub-block">
                                        <div class="case-record-eval-sub">
                                            <span>Diagnostic Reasoning Subjective: <strong>{{ formatScore(evaluationReport.phase3_full.diagnostic_rigor_subjective.score) }}</strong> / 5</span>
                                        </div>
                                        <div v-if="subjectiveReasonText(evaluationReport.phase3_full.diagnostic_rigor_subjective)" class="case-record-eval-detail eval-markdown eval-markdown--compact" v-html="renderMarkdown(subjectiveReasonText(evaluationReport.phase3_full.diagnostic_rigor_subjective))">
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <!-- Treatment Evaluation -->
                            <div class="case-record-eval-block" v-if="evaluationReport.phase4 && !evaluationReport.phase4._fallback">
                                <h5 class="case-record-eval-block__title">4. Treatment Evaluation</h5>
                                <div class="case-record-eval-block__body">
                                    <div v-if="evaluationReport.phase4.treatment_stats" class="case-record-eval-sub">

                                        <span>Filled Categories: {{ evaluationReport.phase4.treatment_stats.filled_categories }}</span>
                                        <span class="case-record-eval-sub__sep">|</span>
                                        <span>Empty Categories: {{ evaluationReport.phase4.treatment_stats.empty_categories }}</span>
                                        <span class="case-record-eval-sub__sep">|</span>
                                        <span>Total Categories: {{ evaluationReport.phase4.treatment_stats.total_categories }}</span>
                                    </div>
                                    <div v-if="evaluationReport.phase4.treatment_stats?.details" class="case-record-eval-tx-list">
                                        <div v-for="(detail, key) in evaluationReport.phase4.treatment_stats.details" :key="key" class="case-record-eval-tx-item">
                                            <span class="case-record-eval-tx-item__label">{{ key }}</span>
                                            <span class="case-record-eval-tx-item__value">{{ detail }}</span>
                                        </div>
                                    </div>
                                    <div v-if="evaluationReport.phase4.treatment_subjective" class="case-record-eval-sub-block">
                                        <div class="case-record-eval-sub">
                                            <span>Treatment Subjective: <strong>{{ formatScore(evaluationReport.phase4.treatment_subjective.score) }}</strong> / 5</span>
                                        </div>
                                        <div v-if="subjectiveReasonText(evaluationReport.phase4.treatment_subjective)" class="case-record-eval-detail eval-markdown eval-markdown--compact" v-html="renderMarkdown(subjectiveReasonText(evaluationReport.phase4.treatment_subjective))">
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Empty State -->
                    <div v-if="!caseInfo && !conversationMessages.length && !examRecords.length && !caseForm && !diagnosis && !treatment && !evaluationReport"
                         class="case-record-empty">
                        <el-icon :size="48" color="#c0c4cc"><DocumentDelete /></el-icon>
                        <p>No interview records</p>
                    </div>
                </div>
            </div>
        </div>
    `,

    data() {
        return {
            caseId: '',
            caseInfo: null,
            conversationMessages: [],
            examRecords: [],
            caseText: '',
            caseForm: null,
            diagnosis: null,
            treatment: null,
            evaluationReport: null,
        };
    },

    computed: {
        ArrowLeft() { return ElementPlusIconsVue.ArrowLeft; },
        UserFilled() { return ElementPlusIconsVue.UserFilled; },
        User() { return ElementPlusIconsVue.User; },
        ChatDotRound() { return ElementPlusIconsVue.ChatDotRound; },
        DocumentChecked() { return ElementPlusIconsVue.DocumentChecked; },
        EditPen() { return ElementPlusIconsVue.EditPen; },
        CircleCheckFilled() { return ElementPlusIconsVue.CircleCheckFilled; },
        DocumentDelete() { return ElementPlusIconsVue.DocumentDelete; },
        FirstAidKit() { return ElementPlusIconsVue.FirstAidKit; },
    },

    methods: {
        goBack() {
            this.$router.push('/patients');
        },

        /** Format score: keep two decimal places */
        formatScore(value) {
            if (value == null) return '—';
            const n = Number(value);
            return isNaN(n) ? value : n.toFixed(2);
        },

        /** Format percentage: convert score to percentage string */
        formatPercentage(section) {
            if (!section) return '—';
            if (section.percentage !== undefined) return section.percentage.toFixed(0) + '%';
            if (section.score !== undefined) return (Number(section.score) * 100).toFixed(0) + '%';
            return '—';
        },

        /** Format accuracy: convert 0-1 decimal to percentage */
        formatAccuracy(value) {
            if (value == null) return '—';
            const n = Number(value);
            return isNaN(n) ? '—' : (n * 100).toFixed(0) + '%';
        },

        localizedCategory(category) {
            const localization = window.ICD11Localization;
            return localization ? localization.localizeCategory(category) : (category || '');
        },

        localizedDisease(disease) {
            const localization = window.ICD11Localization;
            return localization ? localization.localizeDisease(disease) : (disease || '');
        },

        localizedDiseaseText(value) {
            const localization = window.ICD11Localization;
            return localization ? localization.localizeDiseaseText(value) : (value || '');
        },

        escapeHtml(value) {
            return String(value)
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;')
                .replace(/"/g, '&quot;')
                .replace(/'/g, '&#39;');
        },

        renderMarkdown(value) {
            if (!value) return '';
            const text = String(value);
            if (window.marked?.parse) {
                return window.marked.parse(text, { breaks: false, gfm: true });
            }
            return this.escapeHtml(text).replace(/\n/g, '<br>');
        },

        subjectiveReasonText(subjective) {
            if (!subjective) return '';
            if (subjective.why_this_level) return subjective.why_this_level;
            if (subjective.raw_response) return subjective.raw_response;
            if (Array.isArray(subjective.analyses) && subjective.analyses.length) return subjective.analyses.filter(Boolean).join('\n\n');
            if (Array.isArray(subjective.raw_responses) && subjective.raw_responses.length) return subjective.raw_responses.filter(Boolean).join('\n\n');
            if (Array.isArray(subjective.individual_results) && subjective.individual_results.length) {
                return subjective.individual_results
                    .map((item, index) => item?.raw_response ? `Reviewer ${index + 1}: ${item.raw_response}` : '')
                    .filter(Boolean)
                    .join('\n\n');
            }
            return '';
        },

        async loadRecord() {
            this.caseId = this.$route.query.id || this.$route.query.record_id || '';
            if (!this.caseId) {
                this.$message.warning('Case information not found');
                return;
            }

            try {
                const record = await API.getCaseRecord(this.caseId);
                if (record) {
                    this.caseInfo = record.caseInfo || null;
                    this.conversationMessages = record.conversation || [];
                    this.examRecords = record.exams || [];
                    this.caseText = record.caseText || '';
                    this.caseForm = record.caseForm || null;
                    this.diagnosis = record.diagnosis || null;
                    this.treatment = record.treatment || null;
                    this.evaluationReport = record.evaluation_report || null;
                    // Extract original case_id from record_id for display
                    if (record.original_case_id) {
                        this.caseId = record.original_case_id;
                    }
                }
            } catch (err) {
                console.error('[CaseRecord] Failed to load record:', err);
                this.$message.error('Failed to load record');
            }
        },
    },

    mounted() {
        this.loadRecord();
    },
};
