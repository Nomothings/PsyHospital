/**
 * HistoryDetail Component
 * Interview history detail page
 */
const HistoryDetail = {
    template: `
        <div class="history-detail-page">
            <!-- Background -->
            <div class="history-detail-page__bg"></div>

            <!-- Top Bar -->
            <header class="history-detail-header">
                <div class="history-detail-header__left">
                    <el-button text @click="goBack" class="history-detail-header__back-btn">
                        <el-icon><ArrowLeft /></el-icon>
                        Back
                    </el-button>
                    <h3 class="history-detail-header__title">Interview History</h3>
                </div>
                <div class="history-detail-header__right">
                    <span class="history-detail-header__patient">Patient {{ caseId }}</span>
                    <el-tag v-if="hasDiagnosis" type="success" size="small" effect="plain" style="margin-left: 8px;">Diagnosed</el-tag>
                </div>
            </header>

            <!-- Main Content -->
            <div class="history-detail-content" v-loading="loading">
                <div class="history-detail-card">
                    <!-- Patient Basic Info -->
                    <div class="history-detail-section" v-if="recordData.caseInfo">
                        <div class="history-detail-section__header">
                            <el-icon :size="20" color="#5ed6c8"><UserFilled /></el-icon>
                            <h4 class="history-detail-section__title">Patient Basic Info</h4>
                        </div>
                        <div class="history-detail-section__body">
                            <div class="history-detail-info-row">
                                <span class="history-detail-info-row__label">Basic Info</span>
                                <span class="history-detail-info-row__value">{{ recordData.caseInfo.basicInfomation || 'N/A' }}</span>
                            </div>
                            <div class="history-detail-info-row" v-if="recordData.caseInfo.physicalExamination">
                                <span class="history-detail-info-row__label">Physical Examination</span>
                                <span class="history-detail-info-row__value">{{ recordData.caseInfo.physicalExamination }}</span>
                            </div>
                        </div>
                    </div>

                    <!-- Dialogue Records -->
                    <div class="history-detail-section" v-if="messages.length">
                        <div class="history-detail-section__header">
                            <el-icon :size="20" color="#5ed6c8"><ChatDotRound /></el-icon>
                            <h4 class="history-detail-section__title">Doctor-Patient Dialogue</h4>
                            <el-tag type="info" size="small" effect="plain">{{ messages.length }} messages</el-tag>
                        </div>
                        <div class="history-detail-section__body">
                            <div class="history-detail-conversation">
                                <div v-for="(msg, idx) in messages" :key="idx"
                                     class="history-detail-msg"
                                     :class="msg.role">
                                    <div class="history-detail-msg__avatar">
                                        <el-icon :size="16" v-if="msg.role === 'patient'"><UserFilled /></el-icon>
                                        <el-icon :size="16" v-else><User /></el-icon>
                                    </div>
                                    <div class="history-detail-msg__content">
                                        <div class="history-detail-msg__role">
                                            {{ msg.role === 'patient' ? 'Patient' : 'Doctor' }}
                                        </div>
                                        <div class="history-detail-msg__text">{{ msg.content }}</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Examination Records -->
                    <div class="history-detail-section" v-if="exams.length">
                        <div class="history-detail-section__header">
                            <el-icon :size="20" color="#5ed6c8"><DocumentChecked /></el-icon>
                            <h4 class="history-detail-section__title">Auxiliary Examinations</h4>
                            <el-tag type="warning" size="small" effect="plain">{{ exams.length }} exams</el-tag>
                        </div>
                        <div class="history-detail-section__body">
                            <div class="history-detail-exam-list">
                                <div v-for="(exam, idx) in exams" :key="idx"
                                     class="history-detail-exam-item"
                                     :class="(exam.result === '无' || exam.result === 'None') ? 'history-detail-exam-item--none' : 'history-detail-exam-item--has'">
                                    <div class="history-detail-exam-item__name">{{ exam.name }}</div>
                                    <div class="history-detail-exam-item__result">
                                        {{ (exam.result === '无' || exam.result === 'None') ? 'Not examined' : exam.result }}
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Case Writing -->
                    <div class="history-detail-section" v-if="caseForm">
                        <div class="history-detail-section__header">
                            <el-icon :size="20" color="#5ed6c8"><EditPen /></el-icon>
                            <h4 class="history-detail-section__title">Case Writing</h4>
                        </div>
                        <div class="history-detail-section__body">
                            <div class="history-detail-case-form">
                                <div class="history-detail-cf-row" v-if="caseForm.name">
                                    <span class="history-detail-cf-label">Name</span>
                                    <span class="history-detail-cf-value">{{ caseForm.name }}</span>
                                </div>
                                <div class="history-detail-cf-row" v-if="caseForm.age">
                                    <span class="history-detail-cf-label">Age</span>
                                    <span class="history-detail-cf-value">{{ caseForm.age }}</span>
                                </div>
                                <div class="history-detail-cf-row" v-if="caseForm.gender">
                                    <span class="history-detail-cf-label">Gender</span>
                                    <span class="history-detail-cf-value">{{ caseForm.gender }}</span>
                                </div>
                                <div class="history-detail-cf-row" v-if="caseForm.chiefComplaint">
                                    <span class="history-detail-cf-label">Chief Complaint</span>
                                    <span class="history-detail-cf-value">{{ caseForm.chiefComplaint }}</span>
                                </div>
                                <div class="history-detail-cf-row" v-if="caseForm.familyHistory">
                                    <span class="history-detail-cf-label">Family History</span>
                                    <span class="history-detail-cf-value">{{ caseForm.familyHistory }}</span>
                                </div>
                                <div class="history-detail-cf-row" v-if="caseForm.pastHistory">
                                    <span class="history-detail-cf-label">Past History</span>
                                    <span class="history-detail-cf-value">{{ caseForm.pastHistory }}</span>
                                </div>
                                <div class="history-detail-cf-row" v-if="caseForm.physicalExam">
                                    <span class="history-detail-cf-label">Physical Examination</span>
                                    <span class="history-detail-cf-value">{{ caseForm.physicalExam }}</span>
                                </div>
                                <div class="history-detail-cf-row" v-if="caseForm.mentalExam">
                                    <span class="history-detail-cf-label">Mental Status Exam</span>
                                    <span class="history-detail-cf-value">{{ caseForm.mentalExam }}</span>
                                </div>
                                <div class="history-detail-cf-row" v-if="caseForm.auxiliaryExam">
                                    <span class="history-detail-cf-label">Auxiliary Examinations</span>
                                    <span class="history-detail-cf-value">{{ caseForm.auxiliaryExam }}</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Diagnosis Results -->
                    <div class="history-detail-section" v-if="diagnosis">
                        <div class="history-detail-section__header">
                            <el-icon :size="20" color="#5ed6c8"><CircleCheckFilled /></el-icon>
                            <h4 class="history-detail-section__title">Diagnosis Results</h4>
                        </div>
                        <div class="history-detail-section__body">
                            <div class="history-detail-diagnosis">
                                <!-- New format: multiple diagnoses -->
                                <template v-if="diagnosis.diagnoses && diagnosis.diagnoses.length">
                                    <div v-for="(dx, idx) in diagnosis.diagnoses" :key="idx" class="history-detail-diagnosis-group">
                                        <div class="history-detail-diagnosis-group__header">
                                            <el-tag type="success" size="small" effect="plain" round>{{ localizedCategory(dx.category) }}</el-tag>
                                        </div>
                                        <div class="history-detail-diagnosis-group__items" v-if="dx.diseases && dx.diseases.length">
                                            <el-tag v-for="(dis, di) in dx.diseases" :key="di" size="small" round style="margin: 2px 4px 2px 0;">{{ localizedDisease(dis) }}</el-tag>
                                        </div>
                                        <div v-else class="history-detail-diagnosis-group__none">No specific disease selected</div>
                                    </div>
                                </template>
                                <!-- Old format: single diagnosis -->
                                <template v-else>
                                    <div class="history-detail-diagnosis__item">
                                        <span class="history-detail-diagnosis__label">Diagnostic Category</span>
                                        <span class="history-detail-diagnosis__value">{{ localizedCategory(diagnosis.category) }}</span>
                                    </div>
                                    <div class="history-detail-diagnosis__item">
                                        <span class="history-detail-diagnosis__label">Specific Diagnosis</span>
                                        <span class="history-detail-diagnosis__value">{{ localizedDiseaseText(diagnosis.disease) }}</span>
                                    </div>
                                </template>
                                <div class="history-detail-diagnosis__item">
                                    <span class="history-detail-diagnosis__label">Diagnostic Reasoning</span>
                                    <span class="history-detail-diagnosis__value">{{ diagnosis.reason }}</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Treatment Plan -->
                    <div class="history-detail-section" v-if="treatment">
                        <div class="history-detail-section__header">
                            <el-icon :size="20" color="#5ed6c8"><FirstAidKit /></el-icon>
                            <h4 class="history-detail-section__title">Treatment Plan</h4>
                        </div>
                        <div class="history-detail-section__body">
                            <div class="history-detail-treatment">
                                <div class="history-detail-treatment__item">
                                    <span class="history-detail-treatment__label">Pharmacotherapy</span>
                                    <span class="history-detail-treatment__value">{{ treatment['Pharmacotherapy'] || 'None' }}</span>
                                </div>
                                <div class="history-detail-treatment__item">
                                    <span class="history-detail-treatment__label">Psychotherapy</span>
                                    <span class="history-detail-treatment__value">{{ treatment['Psychotherapy'] || 'None' }}</span>
                                </div>
                                <div class="history-detail-treatment__item">
                                    <span class="history-detail-treatment__label">Neuromodulation & Somatic Therapy</span>
                                    <span class="history-detail-treatment__value">{{ treatment['Neuromodulation & Somatic Therapy'] || 'None' }}</span>
                                </div>
                                <div class="history-detail-treatment__item">
                                    <span class="history-detail-treatment__label">Psychosocial Intervention & Rehabilitation</span>
                                    <span class="history-detail-treatment__value">{{ treatment['Psychosocial Intervention & Rehabilitation'] || 'None' }}</span>
                                </div>
                                <div class="history-detail-treatment__item">
                                    <span class="history-detail-treatment__label">Adjuvant Therapy</span>
                                    <span class="history-detail-treatment__value">{{ treatment['Adjuvant Therapy'] || 'None' }}</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Comprehensive Evaluation Report -->
                    <div class="history-detail-section" v-if="evaluationReport">
                        <div class="history-detail-section__header">
                            <el-icon :size="20" color="#3ec4b0"><CircleCheckFilled /></el-icon>
                            <h4 class="history-detail-section__title">Comprehensive Evaluation Report</h4>
                            <el-tag type="success" size="small" effect="plain">Full evaluation completed</el-tag>
                        </div>
                        <div class="history-detail-section__body">
                            <!-- Interview Evaluation -->
                            <div class="history-detail-eval-block" v-if="evaluationReport.phase1 && !evaluationReport.phase1._fallback">
                                <h5 class="history-detail-eval-block__title">1. Interview Evaluation</h5>
                                <div class="history-detail-eval-block__body">
                                    <div v-if="evaluationReport.phase1.conversation_stats" class="history-detail-eval-sub">
                                        <span>Turns: {{ evaluationReport.phase1.conversation_stats.total_turns }}</span>
                                        <span class="history-detail-eval-sub__sep">|</span>
                                        <span>Doctor: {{ evaluationReport.phase1.conversation_stats.doctor_turns }}</span>
                                        <span class="history-detail-eval-sub__sep">|</span>
                                        <span>Patient: {{ evaluationReport.phase1.conversation_stats.patient_turns }}</span>
                                    </div>
                                    <div v-if="evaluationReport.phase1.empathy_evaluation" class="history-detail-eval-sub">
                                        <span>Empathy Level: <strong>{{ evaluationReport.phase1.empathy_evaluation.empathy_level }}</strong></span>
                                    </div>
                                    <div v-if="evaluationReport.phase1.empathy_evaluation?.why_this_level" class="history-detail-eval-collapse">
                                        <button class="history-detail-eval-collapse__toggle" type="button" @click="toggleEvalQuote('phase1_empathy')">
                                            <span>Reviewer Reasoning</span>
                                            <span class="history-detail-eval-collapse__arrow" :class="{ 'is-collapsed': isEvalQuoteCollapsed('phase1_empathy') }"></span>
                                        </button>
                                        <div v-show="!isEvalQuoteCollapsed('phase1_empathy')" class="history-detail-eval-detail eval-markdown eval-markdown--compact" v-html="renderMarkdown(evaluationReport.phase1.empathy_evaluation.why_this_level)">
                                        </div>
                                    </div>
                                    <div class="history-detail-eval-sub-block">
                                        <div class="history-detail-eval-sub">
                                            <span>CC Coverage: <strong>{{ evaluationReport.phase1.coverage_stats?.chief_complaint_coverage ?? 100 }}%</strong></span>
                                            <span class="history-detail-eval-sub__sep">|</span>
                                            <span>MS Coverage: <strong>{{ evaluationReport.phase1.coverage_stats?.mental_status_coverage ?? 100 }}%</strong></span>
                                            <span class="history-detail-eval-sub__sep">|</span>
                                            <span>Overall: <strong>{{ evaluationReport.phase1.coverage_stats?.overall_coverage ?? 100 }}%</strong></span>
                                        </div>
                                    </div>
                                    <div v-if="evaluationReport.phase1.profession_evaluation" class="history-detail-eval-sub">
                                        <span>Professionalism Level: <strong>{{ formatScore(evaluationReport.phase1.profession_evaluation.profession_level || evaluationReport.phase1.profession_evaluation.score) }}</strong> / 5</span>
                                    </div>
                                    <div v-if="subjectiveReasonText(evaluationReport.phase1.profession_evaluation)" class="history-detail-eval-collapse">
                                        <button class="history-detail-eval-collapse__toggle" type="button" @click="toggleEvalQuote('phase1_profession')">
                                            <span>Reviewer Reasoning</span>
                                            <span class="history-detail-eval-collapse__arrow" :class="{ 'is-collapsed': isEvalQuoteCollapsed('phase1_profession') }"></span>
                                        </button>
                                        <div v-show="!isEvalQuoteCollapsed('phase1_profession')" class="history-detail-eval-detail eval-markdown eval-markdown--compact" v-html="renderMarkdown(subjectiveReasonText(evaluationReport.phase1.profession_evaluation))">
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <!-- Examination Evaluation -->
                            <div class="history-detail-eval-block" v-if="evaluationReport.phase2 && !evaluationReport.phase2._fallback">
                                <h5 class="history-detail-eval-block__title">2. Examination Evaluation</h5>
                                <div class="history-detail-eval-block__body">
                                    <div v-if="evaluationReport.phase2.accuracy !== undefined" class="history-detail-eval-sub">
                                        <span>Accuracy: <strong>{{ formatAccuracy(evaluationReport.phase2.accuracy) }}</strong></span>
                                    </div>
                                    <div class="history-detail-eval-sub">
                                        <span>Precision: <strong>{{ formatAccuracy(evaluationReport.phase2.metrics?.precision || 0) }}</strong></span>
                                        <span class="history-detail-eval-sub__sep">|</span>
                                        <span>Recall: <strong>{{ formatAccuracy(evaluationReport.phase2.metrics?.recall || 0) }}</strong></span>
                                        <span class="history-detail-eval-sub__sep">|</span>
                                        <span>F1: <strong>{{ formatAccuracy(evaluationReport.phase2.metrics?.f1 || 0) }}</strong></span>
                                    </div>
                                    <div v-if="evaluationReport.phase2.exam_details" class="history-detail-eval-exam-list">
                                        <div v-for="(detail, key) in evaluationReport.phase2.exam_details" :key="key"
                                             class="history-detail-eval-exam-item"
                                             :class="detail?.correct ? 'history-detail-eval-exam-item--correct' : 'history-detail-eval-exam-item--wrong'">
                                            <span>{{ key }}</span>
                                            <span>{{ detail?.correct ? 'Correct' : 'Wrong' }}</span>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <!-- Case Writing & Diagnosis Evaluation -->
                            <div class="history-detail-eval-block" v-if="evaluationReport.phase3_full && !evaluationReport.phase3_full._fallback">
                                <h5 class="history-detail-eval-block__title">3. Case Writing & Diagnosis Evaluation</h5>
                                <div class="history-detail-eval-block__body">
                                    <div v-if="evaluationReport.phase3_full.case_writing" class="history-detail-eval-sub-block">
                                        <div class="history-detail-eval-sub">
                                            <span>Case Writing Score: <strong>{{ formatScore(evaluationReport.phase3_full.case_writing.total_score) }}</strong></span>
                                        </div>
                                        <div v-for="(section, key) in evaluationReport.phase3_full.case_writing.dimensions" :key="key" class="history-detail-eval-sub">
                                            <span>{{ section.section_name }}: {{ formatPercentage(section) }}</span>
                                            <span v-if="section.detail" class="history-detail-eval-sub__detail">— {{ section.detail }}</span>
                                        </div>
                                    </div>
                                    <div v-if="evaluationReport.phase3_full.diagnosis" class="history-detail-eval-sub-block">
                                        <div class="history-detail-eval-sub">
                                            <span>Disease Type Score: <strong>{{ formatScore(evaluationReport.phase3_full.diagnosis.disease_type?.score) }}</strong></span>
                                            <span v-if="evaluationReport.phase3_full.diagnosis.disease_type?.detail" class="history-detail-eval-sub__detail">— {{ evaluationReport.phase3_full.diagnosis.disease_type.detail }}</span>
                                        </div>
                                        <div v-if="evaluationReport.phase3_full.diagnosis.disease_type?.metrics" class="history-detail-eval-sub">
                                            <span>P: {{ (evaluationReport.phase3_full.diagnosis.disease_type.metrics.precision * 100).toFixed(0) }}%</span>
                                            <span>R: {{ (evaluationReport.phase3_full.diagnosis.disease_type.metrics.recall * 100).toFixed(0) }}%</span>
                                            <span>F1: {{ (evaluationReport.phase3_full.diagnosis.disease_type.metrics.f1 * 100).toFixed(0) }}%</span>
                                            <span>J: {{ (evaluationReport.phase3_full.diagnosis.disease_type.metrics.jaccard * 100).toFixed(0) }}%</span>
                                        </div>
                                        <div class="history-detail-eval-sub">
                                            <span>Diagnostic Correctness: <strong>{{ formatScore(evaluationReport.phase3_full.diagnosis.diagnostic_correctness?.score) }}</strong></span>
                                        </div>
                                        <div v-if="evaluationReport.phase3_full.diagnosis.diagnostic_correctness?.detail" class="history-detail-eval-detail eval-markdown eval-markdown--compact" v-html="renderMarkdown(evaluationReport.phase3_full.diagnosis.diagnostic_correctness.detail)">
                                        </div>
                                        <div class="history-detail-eval-sub">
                                            <span>Diagnostic Reasoning: <strong>{{ formatScore(evaluationReport.phase3_full.diagnosis.diagnostic_reasoning?.score) }}</strong></span>
                                        </div>
                                        <div v-if="evaluationReport.phase3_full.diagnosis.diagnostic_reasoning?.detail" class="history-detail-eval-detail eval-markdown eval-markdown--compact" v-html="renderMarkdown(evaluationReport.phase3_full.diagnosis.diagnostic_reasoning.detail)">
                                        </div>
                                    </div>
                                    <div v-if="evaluationReport.phase3_full.clinical_note_subjective" class="history-detail-eval-sub-block">
                                        <div class="history-detail-eval-sub">
                                            <span>Case Writing Subjective: <strong>{{ formatScore(evaluationReport.phase3_full.clinical_note_subjective.score) }}</strong> / 5</span>
                                        </div>
                                        <div v-if="subjectiveReasonText(evaluationReport.phase3_full.clinical_note_subjective)" class="history-detail-eval-collapse">
                                            <button class="history-detail-eval-collapse__toggle" type="button" @click="toggleEvalQuote('phase3_clinical_note')">
                                                <span>Reviewer Reasoning</span>
                                                <span class="history-detail-eval-collapse__arrow" :class="{ 'is-collapsed': isEvalQuoteCollapsed('phase3_clinical_note') }"></span>
                                            </button>
                                            <div v-show="!isEvalQuoteCollapsed('phase3_clinical_note')" class="history-detail-eval-detail eval-markdown eval-markdown--compact" v-html="renderMarkdown(subjectiveReasonText(evaluationReport.phase3_full.clinical_note_subjective))">
                                            </div>
                                        </div>
                                    </div>
                                    <div v-if="evaluationReport.phase3_full.diagnostic_rigor_subjective" class="history-detail-eval-sub-block">
                                        <div class="history-detail-eval-sub">
                                            <span>Diagnostic Reasoning Subjective: <strong>{{ formatScore(evaluationReport.phase3_full.diagnostic_rigor_subjective.score) }}</strong> / 5</span>
                                        </div>
                                        <div v-if="subjectiveReasonText(evaluationReport.phase3_full.diagnostic_rigor_subjective)" class="history-detail-eval-collapse">
                                            <button class="history-detail-eval-collapse__toggle" type="button" @click="toggleEvalQuote('phase3_diagnostic_rigor')">
                                                <span>Reviewer Reasoning</span>
                                                <span class="history-detail-eval-collapse__arrow" :class="{ 'is-collapsed': isEvalQuoteCollapsed('phase3_diagnostic_rigor') }"></span>
                                            </button>
                                            <div v-show="!isEvalQuoteCollapsed('phase3_diagnostic_rigor')" class="history-detail-eval-detail eval-markdown eval-markdown--compact" v-html="renderMarkdown(subjectiveReasonText(evaluationReport.phase3_full.diagnostic_rigor_subjective))">
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <!-- Treatment Evaluation -->
                            <div class="history-detail-eval-block" v-if="evaluationReport.phase4 && !evaluationReport.phase4._fallback">
                                <h5 class="history-detail-eval-block__title">4. Treatment Evaluation</h5>
                                <div class="history-detail-eval-block__body">
                                    <div v-if="evaluationReport.phase4.treatment_stats" class="history-detail-eval-sub">
                                        <span>Filled: {{ evaluationReport.phase4.treatment_stats.filled_categories }}</span>
                                        <span class="history-detail-eval-sub__sep">|</span>
                                        <span>Empty: {{ evaluationReport.phase4.treatment_stats.empty_categories }}</span>
                                        <span class="history-detail-eval-sub__sep">|</span>
                                        <span>Total: {{ evaluationReport.phase4.treatment_stats.total_categories }}</span>
                                    </div>
                                    <div v-if="evaluationReport.phase4.treatment_stats?.details" class="history-detail-eval-tx-list">
                                        <div v-for="(detail, key) in evaluationReport.phase4.treatment_stats.details" :key="key" class="history-detail-eval-tx-item">
                                            <span class="history-detail-eval-tx-item__label">{{ key }}</span>
                                            <span class="history-detail-eval-tx-item__value">{{ detail }}</span>
                                        </div>
                                    </div>
                                    <div v-if="evaluationReport.phase4.treatment_subjective" class="history-detail-eval-sub-block">
                                        <div class="history-detail-eval-sub">
                                            <span>Treatment Subjective: <strong>{{ formatScore(evaluationReport.phase4.treatment_subjective.score) }}</strong> / 5</span>
                                        </div>
                                        <div v-if="subjectiveReasonText(evaluationReport.phase4.treatment_subjective)" class="history-detail-eval-collapse">
                                            <button class="history-detail-eval-collapse__toggle" type="button" @click="toggleEvalQuote('phase4_treatment')">
                                                <span>Reviewer Reasoning</span>
                                                <span class="history-detail-eval-collapse__arrow" :class="{ 'is-collapsed': isEvalQuoteCollapsed('phase4_treatment') }"></span>
                                            </button>
                                            <div v-show="!isEvalQuoteCollapsed('phase4_treatment')" class="history-detail-eval-detail eval-markdown eval-markdown--compact" v-html="renderMarkdown(subjectiveReasonText(evaluationReport.phase4.treatment_subjective))">
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Empty State -->
                    <div v-if="!loading && !recordData.caseInfo && !messages.length && !exams.length && !caseForm && !diagnosis"
                         class="history-detail-empty">
                        <el-icon :size="48" color="#c0c4cc"><DocumentDelete /></el-icon>
                        <p>No interview records</p>
                    </div>
                </div>
            </div>
        </div>
    `,

    data() {
        return {
            loading: true,
            caseId: '',
            recordData: {},
            hasDiagnosis: false,
            collapsedEvalQuotes: {
                phase1_empathy: true,
                phase1_profession: true,
                phase3_clinical_note: true,
                phase3_diagnostic_rigor: true,
                phase4_treatment: true,
            },
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
        FirstAidKit() { return ElementPlusIconsVue.FirstAidKit; },
        DocumentDelete() { return ElementPlusIconsVue.DocumentDelete; },

        messages() {
            return this.recordData.messages || this.recordData.conversation || [];
        },

        exams() {
            return this.recordData.exams || [];
        },

        caseForm() {
            return this.recordData.caseForm || this.recordData.case_form || null;
        },

        diagnosis() {
            return this.recordData.diagnosis || null;
        },

        treatment() {
            return this.recordData.treatment || null;
        },

        evaluationReport() {
            return this.recordData.evaluation_report || null;
        },
    },

    methods: {
        goBack() {
            this.$router.push('/history');
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

        toggleEvalQuote(key) {
            this.collapsedEvalQuotes[key] = !this.collapsedEvalQuotes[key];
        },

        isEvalQuoteCollapsed(key) {
            return this.collapsedEvalQuotes[key] !== false;
        },

        async loadDetail() {
            this.caseId = this.$route.query.record_id || this.$route.query.case_id || '';
            if (!this.caseId) {
                this.$message.warning('History record not found');
                return;
            }

            try {
                this.loading = true;
                const data = await API.getHistoryDetail(this.caseId);
                this.recordData = data;
                this.hasDiagnosis = !!data.diagnosis;
            } catch (err) {
                console.error('[HistoryDetail] Failed to load history details:', err);
                this.$message.error('Failed to load history details');
            } finally {
                this.loading = false;
            }
        },
    },

    mounted() {
        this.loadDetail();
    },
};
