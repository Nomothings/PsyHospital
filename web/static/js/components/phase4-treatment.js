/**
 * Phase4Treatment Component
 * Phase 4 — Treatment
 *
 * Layout follows Phase 3 case writing:
 *   Left — Patient basic info, auxiliary examination results, diagnosis results (scrollable)
 *   Right — Five treatment category input areas
 */
const Phase4Treatment = {
    template: `
        <div class="phase4-page">
            <!-- Background -->
            <div class="phase4-page__bg"></div>

            <!-- Top Bar -->
            <header class="phase4-header">
                <div class="phase4-header__left">
                    <el-button text @click="goBack" class="phase4-header__back-btn">
                        <el-icon><ArrowLeft /></el-icon>
                        Back
                    </el-button>
                    <h3 class="phase4-header__title">Treatment</h3>
                    <span class="phase4-header__subtitle">Phase 4</span>
                </div>
                <div class="phase4-header__right">
                    <span class="phase4-header__patient">
                        Patient {{ caseId }}
                    </span>
                    <el-button
                        type="primary"
                        size="small"
                        round
                        @click="handleComplete"
                        :loading="submitting"
                        class="phase4-header__complete-btn"
                    >
                        Complete Treatment
                    </el-button>
                </div>
            </header>

            <!-- Main Content -->
            <div class="phase4-content phase4-content--split">
                <!-- Left: Reference Info Panel -->
                <aside class="phase4-left-panel">
                    <!-- Patient Basic Info -->
                    <div class="phase4-panel-section" v-if="caseInfo">
                        <div class="phase4-panel-section__title">Patient Basic Info</div>
                        <div class="phase4-panel-section__content">
                            <div class="phase4-info-row">
                                <span class="phase4-info-row__label">Basic Info</span>
                                <span class="phase4-info-row__value">{{ caseInfo.basicInfomation || 'N/A' }}</span>
                            </div>
                        </div>
                    </div>

                    <!-- Auxiliary Examination Results -->
                    <div class="phase4-panel-section" v-if="Object.keys(phase2Results).length">
                        <div class="phase4-panel-section__title">Auxiliary Examination Results</div>
                        <div class="phase4-panel-section__content">
                            <div v-for="(result, exam) in phase2Results" :key="exam"
                                 class="phase4-exam-result-row"
                                 :class="(result === '无' || result === 'None') ? 'phase4-exam-result-row--none' : 'phase4-exam-result-row--has'">
                                <span class="phase4-exam-result-row__name">{{ exam }}</span>
                                <span class="phase4-exam-result-row__value">
                                    {{ (result === '无' || result === 'None') ? 'No organic lesions found' : result }}
                                </span>
                            </div>
                        </div>
                    </div>

                    <!-- Diagnosis Results -->
                    <div class="phase4-panel-section" v-if="diagnosis">
                        <div class="phase4-panel-section__title">Diagnosis Results</div>
                        <div class="phase4-panel-section__content">
                            <div class="phase4-info-row">
                                <span class="phase4-info-row__label">Diagnostic Category</span>
                                <span class="phase4-info-row__value">{{ localizedCategory(diagnosis.category) }}</span>
                            </div>
                            <div class="phase4-info-row">
                                <span class="phase4-info-row__label">Specific Diagnosis</span>
                                <span class="phase4-info-row__value">{{ localizedDiseaseText(diagnosis.disease) }}</span>
                            </div>
                        </div>
                    </div>

                    <!-- Case Summary -->
                    <div class="phase4-panel-section" v-if="caseForm">
                        <div class="phase4-panel-section__title">Case Summary</div>
                        <div class="phase4-panel-section__content phase4-panel-section__scroll">
                            <div class="phase4-info-row">
                                <span class="phase4-info-row__label">Chief Complaint</span>
                                <span class="phase4-info-row__value">{{ caseForm.chiefComplaint || 'N/A' }}</span>
                            </div>
                            <div class="phase4-info-row">
                                <span class="phase4-info-row__label">Family History</span>
                                <span class="phase4-info-row__value">{{ caseForm.familyHistory || 'N/A' }}</span>
                            </div>
                            <div class="phase4-info-row">
                                <span class="phase4-info-row__label">Past History</span>
                                <span class="phase4-info-row__value">{{ caseForm.pastHistory || 'N/A' }}</span>
                            </div>
                            <div class="phase4-info-row">
                                <span class="phase4-info-row__label">Physical Examination</span>
                                <span class="phase4-info-row__value">{{ caseForm.physicalExam || 'N/A' }}</span>
                            </div>
                            <div class="phase4-info-row">
                                <span class="phase4-info-row__label">Mental Status Exam</span>
                                <span class="phase4-info-row__value">{{ caseForm.mentalExam || 'N/A' }}</span>
                            </div>
                            <div class="phase4-info-row">
                                <span class="phase4-info-row__label">Auxiliary Examinations</span>
                                <span class="phase4-info-row__value">{{ caseForm.auxiliaryExam || 'N/A' }}</span>
                            </div>
                        </div>
                    </div>
                </aside>

                <!-- Right: Treatment Form -->
                <main class="phase4-right-panel">
                    <div class="phase4-treatment-card">
                        <div class="phase4-treatment-card__header">
                            <h2 class="phase4-treatment-card__title">Treatment Plan</h2>
                            <p class="phase4-treatment-card__subtitle">
                                Fill in the treatment plan based on diagnosis (empty fields will be recorded as "None")
                            </p>
                        </div>

                        <!-- Five Treatment Category Input Areas -->
                        <div class="phase4-treatment-grid">
                            <div class="phase4-treatment-card-item">
                                <div class="phase4-treatment-card-item__header">
                                    <span class="phase4-treatment-card-item__title">Pharmacotherapy</span>
                                </div>
                                <textarea v-model="treatment.medication" class="phase4-treatment-card-item__input" rows="3" placeholder="Enter medication treatment plan"></textarea>
                            </div>
                            <div class="phase4-treatment-card-item">
                                <div class="phase4-treatment-card-item__header">
                                    <span class="phase4-treatment-card-item__title">Psychotherapy</span>
                                </div>
                                <textarea v-model="treatment.psychotherapy" class="phase4-treatment-card-item__input" rows="3" placeholder="Enter psychotherapy plan"></textarea>
                            </div>
                            <div class="phase4-treatment-card-item">
                                <div class="phase4-treatment-card-item__header">
                                    <span class="phase4-treatment-card-item__title">Neuromodulation & Somatic Therapy</span>
                                </div>
                                <textarea v-model="treatment.neuromodulation" class="phase4-treatment-card-item__input" rows="3" placeholder="Enter neuromodulation and somatic therapy plan"></textarea>
                            </div>
                            <div class="phase4-treatment-card-item">
                                <div class="phase4-treatment-card-item__header">
                                    <span class="phase4-treatment-card-item__title">Psychosocial Intervention & Rehabilitation</span>
                                </div>
                                <textarea v-model="treatment.psychosocial" class="phase4-treatment-card-item__input" rows="3" placeholder="Enter psychosocial intervention and rehabilitation plan"></textarea>
                            </div>
                            <div class="phase4-treatment-card-item">
                                <div class="phase4-treatment-card-item__header">
                                    <span class="phase4-treatment-card-item__title">Adjuvant Therapy</span>
                                </div>
                                <textarea v-model="treatment.adjuvant" class="phase4-treatment-card-item__input" rows="3" placeholder="Enter adjuvant therapy plan"></textarea>
                            </div>
                        </div>
                    </div>
                </main>
            </div>
        </div>
    `,

    data() {
        return {
            caseId: '',
            caseInfo: null,
            phase2Results: {},
            diagnosis: null,
            caseForm: null,
            treatment: {
                medication: '',
                psychotherapy: '',
                neuromodulation: '',
                psychosocial: '',
                adjuvant: '',
            },
            submitting: false,
        };
    },

    computed: {
        ArrowLeft() { return ElementPlusIconsVue.ArrowLeft; },
    },

    methods: {
        localizedCategory(category) {
            const localization = window.ICD11Localization;
            return localization ? localization.localizeCategory(category) : (category || '');
        },

        localizedDiseaseText(value) {
            const localization = window.ICD11Localization;
            return localization ? localization.localizeDiseaseText(value) : (value || '');
        },

        async handleComplete() {
            if (this.submitting) return;
            this.submitting = true;
            try {
                const effectiveCaseId = this.caseId || sessionStorage.getItem('phase2_caseId') || '';
                if (!effectiveCaseId) {
                    this.$message.error('Case ID not found, cannot proceed to evaluation');
                    return;
                }

                // Keep empty fields as null so the evaluation flow can still finish cleanly
                const treatmentRecord = {};
                const labels = {
                    medication: 'Pharmacotherapy',
                    psychotherapy: 'Psychotherapy',
                    neuromodulation: 'Neuromodulation & Somatic Therapy',
                    psychosocial: 'Psychosocial Intervention & Rehabilitation',
                    adjuvant: 'Adjuvant Therapy',
                };
                for (const [key, label] of Object.entries(labels)) {
                    const value = this.treatment[key] ? this.treatment[key].trim() : '';
                    treatmentRecord[label] = value || null;
                }

                // Use record_id to ensure all data is integrated into the same interview record
                const recordId = sessionStorage.getItem('record_id') || effectiveCaseId;

                await API.submitTreatment(recordId, treatmentRecord);

                await API.saveCaseRecord(recordId, {
                    treatment: treatmentRecord,
                });

                this.$message.success('Phase 4 treatment completed');

                sessionStorage.setItem('phase4_result', JSON.stringify({
                    caseId: effectiveCaseId,
                    treatment: treatmentRecord,
                }));
                sessionStorage.setItem('final_case_id', effectiveCaseId);

                // Navigate directly to unified evaluation page, which will call backend APIs on its own
                this.$router.push({ path: '/evaluation', query: { id: effectiveCaseId } });
            } catch (err) {
                this.$message.error('Submission failed: ' + (err.message || 'Unknown error'));
                console.error('[Phase4Treatment] Submission failed:', err);
            } finally {
                this.submitting = false;
            }
        },

        goBack() {
            this.$router.push('/phase3');
        },

        async loadPhaseData() {
            // Load case basic info
            if (this.caseId) {
                try {
                    const info = await API.getCaseInfo(this.caseId);
                    this.caseInfo = info;
                } catch (err) {
                    console.error('[Phase4Treatment] Failed to load patient info:', err);
                }
            }

            // Load Phase 2 examination results
            const resultsStr = sessionStorage.getItem('phase2_checkedResults');
            if (resultsStr) {
                try {
                    this.phase2Results = JSON.parse(resultsStr);
                } catch (err) {
                    console.error('[Phase4Treatment] Failed to parse Phase 2 results:', err);
                }
            }

            // Load Phase 3 diagnosis results
            const diagnosisStr = sessionStorage.getItem('phase3_result');
            if (diagnosisStr) {
                try {
                    const phase3Result = JSON.parse(diagnosisStr);
                    this.diagnosis = {
                        category: phase3Result.category,
                        disease: phase3Result.disease,
                    };
                    this.caseForm = phase3Result.caseForm || null;
                } catch (err) {
                    console.error('[Phase4Treatment] Failed to parse Phase 3 diagnosis results:', err);
                }
            }

            // Load saved treatment data (preserved when returning from Phase 3)
            const savedTreatment = sessionStorage.getItem('phase4_treatment');
            if (savedTreatment) {
                try {
                    const parsed = JSON.parse(savedTreatment);
                    this.treatment = {
                        medication: parsed.medication || '',
                        psychotherapy: parsed.psychotherapy || '',
                        neuromodulation: parsed.neuromodulation || '',
                        psychosocial: parsed.psychosocial || '',
                        adjuvant: parsed.adjuvant || '',
                    };
                } catch (err) {
                    console.error('[Phase4Treatment] Failed to parse saved treatment plan:', err);
                }
            }
        },
    },

    mounted() {
        this.caseId = this.$route.query.id || sessionStorage.getItem('phase2_caseId') || '';
        if (!this.caseId) {
            this.$message.warning('Case not found, please enter from patient list');
        }
        this.loadPhaseData();
    },

    beforeUnmount() {
        // Save current form data to sessionStorage before leaving to prevent accidental loss
        sessionStorage.setItem('phase4_treatment', JSON.stringify(this.treatment));
    },
};
