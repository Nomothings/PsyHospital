/**
 * Phase2Check Component
 * Phase 2 - Auxiliary Examination (Selection + Submission)
 */
const Phase2Check = {
    template: `
        <div class="phase2-page">
            <div class="phase2-page__bg"></div>

            <header class="phase2-header">
                <div class="phase2-header__left">
                    <el-button text @click="goBack" class="phase2-header__back-btn">
                        <el-icon><ArrowLeft /></el-icon>
                        Back
                    </el-button>
                    <h3 class="phase2-header__title">Auxiliary Examination</h3>
                    <span class="phase2-header__subtitle">Phase 2</span>
                </div>
                <div class="phase2-header__right">
                    <span class="phase2-header__patient">Patient {{ caseId }}</span>
                    <el-button
                        v-if="step === 'results'"
                        type="primary"
                        size="small"
                        round
                        @click="goToNextPhase"
                        class="phase2-header__next-btn"
                    >
                        Proceed to Case Writing
                    </el-button>
                </div>
            </header>

            <div class="phase2-content">
                <div v-if="step === 'selecting'" class="phase2-form-card">
                    <div class="phase2-form-card__header">
                        <h2 class="phase2-form-card__title">Select Auxiliary Examinations</h2>
                        <p class="phase2-form-card__subtitle">
                            Select the auxiliary examinations based on the interview findings
                        </p>
                    </div>

                    <div class="phase2-selector" ref="selectorRef">
                        <label class="phase2-selector__label">Examinations</label>

                        <div class="phase2-selector__input" @click.self="openDropdown">
                            <transition-group name="phase2-tag" tag="div" class="phase2-selector__tags">
                                <div
                                    v-for="exam in selectedExams"
                                    :key="exam"
                                    class="phase2-tag"
                                >
                                    <span class="phase2-tag__text">{{ exam }}</span>
                                    <span class="phase2-tag__delete" @click.stop="removeExam(exam)" title="Remove">
                                        <el-icon :size="12"><Close /></el-icon>
                                    </span>
                                </div>
                            </transition-group>

                            <div class="phase2-tag phase2-tag--add" @click.stop="openDropdown">
                                <el-icon :size="14" class="phase2-tag__add-icon"><Plus /></el-icon>
                                <span>Add Exam</span>
                            </div>

                            <div v-if="selectedExams.length === 0" class="phase2-selector__placeholder">
                                Click "Add Exam" to select auxiliary examinations
                            </div>

                            <div v-show="dropdownVisible" class="phase2-dropdown" @click.stop>
                                <div class="phase2-dropdown__body">
                                    <div class="phase2-dropdown__categories">
                                        <div class="phase2-dropdown__section-title">Exam Categories</div>
                                        <div
                                            v-for="cat in examCategories"
                                            :key="cat"
                                            class="phase2-dropdown__cat-item"
                                            :class="{
                                                'phase2-dropdown__cat-item--active': activeCategory === cat,
                                            }"
                                            @click="selectCategory(cat)"
                                        >
                                            <span class="phase2-dropdown__cat-item__text">{{ cat }}</span>
                                        </div>
                                    </div>

                                    <div class="phase2-dropdown__exams">
                                        <div v-if="!activeCategory" class="phase2-dropdown__empty">
                                            Please select an exam category on the left first
                                        </div>

                                        <template v-else>
                                            <template v-if="activeCategory === 'Other'">
                                                <div class="phase2-dropdown__custom-input">
                                                    <el-input
                                                        v-model="customExamInput"
                                                        placeholder="Enter custom examination name"
                                                        size="small"
                                                        clearable
                                                        @keyup.enter="addCustomExam"
                                                    />
                                                    <el-button
                                                        size="small"
                                                        round
                                                        class="phase2-custom-input__btn"
                                                        @click="addCustomExam"
                                                        :disabled="!customExamInput.trim()"
                                                        style="margin-top: 8px;"
                                                    >
                                                        Add
                                                    </el-button>
                                                </div>
                                            </template>

                                            <template v-else>
                                                <div class="phase2-dropdown__section-title">
                                                    {{ activeCategory }} - Examinations
                                                </div>
                                                <div
                                                    v-for="exam in getExamsForCategory(activeCategory)"
                                                    :key="exam"
                                                    class="phase2-dropdown__exam-item"
                                                    :class="{
                                                        'phase2-dropdown__exam-item--selected': selectedExams.includes(normalizeExamName(exam)),
                                                    }"
                                                    @click="toggleExam(exam)"
                                                >
                                                    <span class="phase2-dropdown__exam-item__text">{{ exam }}</span>
                                                    <el-icon
                                                        v-if="selectedExams.includes(normalizeExamName(exam))"
                                                        :size="14"
                                                        color="#5ed6c8"
                                                    >
                                                        <Check />
                                                    </el-icon>
                                                </div>
                                            </template>
                                        </template>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="phase2-form__actions">
                        <el-button
                            type="primary"
                            size="large"
                            round
                            @click="handleSubmit"
                            :loading="submitting"
                            class="phase2-form__submit-btn"
                        >
                            Submit Examinations
                        </el-button>
                    </div>
                </div>

                <div v-if="step === 'loading'" class="phase2-form-card phase2-form-card--center-text">
                    <div class="phase2-loading-animation">
                            <img src="/static/bg/eval.png" alt="" class="phase2-loading-animation__icon" />
                        <div class="phase2-loading-animation__title">Loading results...</div>
                        <div class="phase2-loading-animation__dots">
                            <span class="phase2-loading-animation__dot" :style="{ animationDelay: '0s' }"></span>
                            <span class="phase2-loading-animation__dot" :style="{ animationDelay: '0.2s' }"></span>
                            <span class="phase2-loading-animation__dot" :style="{ animationDelay: '0.4s' }"></span>
                        </div>
                    </div>
                </div>

                <div v-if="step === 'results'" class="phase2-form-card phase2-form-card--results">
                    <div class="phase2-form-card__header">
                        <h2 class="phase2-form-card__title">Examination Results</h2>
                        <p class="phase2-form-card__subtitle">
                            Below are the results of your selected auxiliary examinations
                        </p>
                    </div>

                    <div class="phase2-results-list">
                        <div v-if="Object.keys(checkedResults).length === 0" class="phase2-result-item phase2-result-item--none">
                            <div class="phase2-result-item__header">
                                <span class="phase2-result-item__name">No auxiliary examinations selected</span>
                            </div>
                            <div class="phase2-result-item__content">
                                No auxiliary examinations were selected in this phase. You can proceed to the next phase directly.
                            </div>
                        </div>
                        <div
                            v-for="(result, exam) in checkedResults"
                            :key="exam"
                            class="phase2-result-item"
                            :class="(result === '无' || result === 'None') ? 'phase2-result-item--none' : 'phase2-result-item--has'"
                        >
                            <div class="phase2-result-item__header">
                                <span class="phase2-result-item__name">{{ exam }}</span>
                            </div>
                            <div class="phase2-result-item__content">
                                {{ (result === '无' || result === 'None') ? 'No organic lesions found' : result }}
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <transition name="eval-fade">
                <div v-if="saving" class="eval-overlay">
                    <div class="eval-overlay__content">
                        <img src="/static/bg/loading2.png" alt="" class="eval-overlay__icon" />
                        <div class="eval-overlay__text">Submitting examination requests...</div>
                    </div>
                </div>
            </transition>
        </div>
    `,

    data() {
        return {
            caseId: '',
            step: 'selecting',
            selectedExams: [],
            checkedResults: {},
            dropdownVisible: false,
            activeCategory: '',
            submitting: false,
            saving: false,
            examCategories: [
                'Laboratory Tests',
                'Imaging',
                'Endoscopy',
                'Pathology & Cytology',
                'Functional / Physiological Tests',
                'Genetic & Molecular Tests',
                'Other',
            ],
            customExamInput: '',
            examAliasMap: {
                'Electrolytes': ['Blood Electrolytes', 'Serum Electrolytes'],
                'Urine Test': ['Urinalysis', 'Urine Laboratory Test'],
                'Stool Routine': ['Stool Routine Test', 'Fecal Routine'],
                'Cardiac Enzyme Panel': ['Cardiac Enzymes'],
                'Ambulatory Blood Pressure Monitoring': ['Ambulatory BP'],
                'Exercise Stress ECG': ['Exercise Treadmill Test'],
                'Thyroid Ultrasound': ['Thyroid Sonography'],
                'Echocardiography': ['Cardiac Ultrasound'],
                'CSF Routine': ['Cerebrospinal Fluid Test'],
                'Brain ET': ['Brain ET', 'ET Test'],
                'SCL-90 Symptom Checklist': ['SCL-90', 'SCL-90 Assessment', 'scl-90', 'SL-90', 'SCR-90', '90-Symptom Checklist'],
                'MMSE Assessment': ['MMSE Score', 'Neuropsychological Assessment (MMSE)'],
                'Hepatic and Renal Function with Electrolytes': ['Liver and Renal Function', 'Hepatic and Renal Function', 'Liver Renal Function Electrolytes'],
                'Head CT': ['Head CT', 'Brain CT'],
                'Head MRI': ['Brain MRI', 'Head MRI', 'Cranial MRI'],
                'Chest X-Ray': ['Chest PA View', 'X-Ray'],
                'Abdominal Ultrasound': ['Abdominal B-Ultrasound'],
                'Video EEG': ['Ambulatory EEG', 'Brain Electrical Monitoring'],
                'Biochemistry Tests': ['Biochemistry'],
            },
            examMapping: {
                'Laboratory Tests': [
                    'Complete Blood Count (CBC)', 'Electrolytes', 'Urinalysis', 'Liver Function Tests', 'Renal Function Tests', 'Blood Glucose',
                    'Thyroid Function Tests', 'Cardiac Enzyme Panel', 'Coagulation Time', 'Stool and Urine Routine', 'Urine Test', 'Urine Screening',
                    'Urine Cannabis Metabolite Test', 'Toxicology Screen - Ketamine', 'Stool Routine', 'CSF Routine', 'Drug Level Monitoring',
                    'Pre-transfusion Tests', 'Hepatitis B Panel', 'Hepatic and Renal Function with Electrolytes', 'Infection Screening', 'Tuberculosis Test',
                    'Rheumatoid Factor', 'Anti-Streptolysin O', 'Tumor Markers', 'Carbamazepine Blood Level',
                    'Valproate Blood Level', 'Biochemistry Tests', 'Urine Methamphetamine Test', 'Serum Amylase',
                    'Secretion Specimen Test', 'CSF Biochemistry',
                    'Urine Protein Quantitation', 'Urine Sediment', 'Urine Culture', 'Pleural Fluid Analysis', 'Ascitic Fluid Analysis', 'Joint Fluid Analysis',
                    'Bacterial Culture', 'Fungal Culture', 'Antimicrobial Susceptibility Test', 'Viral Antibody Test', 'Nucleic Acid Test',
                    'Autoantibodies', 'Immunoglobulins', 'Complement', 'Allergy Testing', 'Parasite Examination', 'Pathogen Detection',
                ],
                'Imaging': [
                    'Head MRI', 'Head CT', 'Chest CT Plain', 'Echocardiography', 'Chest X-Ray', 'Thyroid Ultrasound',
                    'Abdominal Ultrasound', 'Transcranial Doppler', 'Brain ET', 'Lumbar CT', 'Head MRI Plain', 'Head MRI Enhanced',
                    'Head Imaging', 'Head-Chest-Abdomen CT', 'Mandible X-Ray', 'Brain Imaging', 'Lung Imaging', 'Abdominal Ultrasound',
                    'Bone and Joint X-Ray', 'GI Contrast Study', 'Urinary Ultrasound', 'Breast Ultrasound', 'Vascular Ultrasound',
                    'Chest CT', 'Abdominal CT', 'Contrast-Enhanced CT', 'CTA', 'Spine MRI', 'Joint MRI',
                    'Contrast-Enhanced MRI', 'MRA', 'PET-CT', 'Bone Scan', 'Thyroid Scintigraphy',
                    'Myocardial Perfusion Imaging', 'Coronary CTA', 'DSA', 'Other Contrast Studies',
                ],
                'Endoscopy': [
                    'Gastroscopy', 'Colonoscopy', 'Duodenoscopy', 'Capsule Endoscopy', 'Bronchoscopy', 'Cystoscopy',
                    'Ureteroscopy', 'Hysteroscopy', 'Knee Arthroscopy', 'Shoulder Arthroscopy', 'Laparoscopy', 'Thoracoscopy',
                ],
                'Pathology & Cytology': [
                    'Gastric Mucosal Biopsy', 'Liver Biopsy', 'Lung Biopsy', 'Lymph Node Biopsy',
                    'Intraoperative Frozen Section', 'Cervical Smear', 'Sputum Cytology', 'Pleural/Ascitic Fluid Cytology',
                    'Fine Needle Aspiration Cytology', 'Tumor Gene Mutation', 'Fusion Gene', 'Immunohistochemistry',
                ],
                'Functional / Physiological Tests': [
                    'EEG', 'ECG', 'Holter Monitoring', 'Ambulatory Blood Pressure Monitoring', 'Exercise Stress ECG',
                    'Video EEG', 'Eye Movement Test', 'Language Development Assessment', 'Brief Intelligence Test', 'Standardized Motor Function Assessment',
                    'Brain Electrical Activity Mapping', 'Brain Mapping', 'Fetal Heart Monitoring (NST)',
                    'Pulmonary Function Test', 'Bronchial Provocation Test', 'Diffusion Capacity Test', 'Evoked Potentials', 'EMG',
                    'Nerve Conduction Study', 'Gastric Motility Test', '24h pH Monitoring', 'Hearing Test', 'Vestibular Function Test',
                ],
                'Genetic & Molecular Tests': [
                    'Karyotype Analysis', 'Chromosomal Microarray', 'Genetic Disease Gene Testing', 'Tumor Driver Gene Testing',
                    'Pharmacogenomic Testing', 'DNA Testing', 'RNA Testing', 'Pathogen Nucleic Acid Testing',
                    'Liquid Biopsy', 'Non-invasive Prenatal Screening', 'Preimplantation Genetic Testing',
                ],
                'Other': [
                    'SCL-90 Symptom Checklist', 'MMPI', 'Self-Rating Anxiety Scale', 'Self-Rating Depression Scale',
                    'MMSE Assessment', 'ADL Scale', 'EPDS Scale', 'MoCA Assessment',
                ],
            },
        };
    },

    computed: {
        ArrowLeft() { return ElementPlusIconsVue.ArrowLeft; },
        Close() { return ElementPlusIconsVue.Close; },
        Check() { return ElementPlusIconsVue.Check; },
        Plus() { return ElementPlusIconsVue.Plus; },
    },

    methods: {
        normalizeExamName(exam) {
            const raw = (exam || '').trim();
            if (!raw) return raw;

            for (const [canonical, aliases] of Object.entries(this.examAliasMap)) {
                if (raw === canonical || aliases.includes(raw)) {
                    return canonical;
                }
            }

            return raw;
        },

        openDropdown() {
            this.dropdownVisible = true;
            if (!this.activeCategory && this.examCategories.length > 0) {
                this.activeCategory = this.examCategories[0];
            }
        },

        closeDropdown() {
            this.dropdownVisible = false;
        },

        selectCategory(cat) {
            this.activeCategory = cat;
            this.customExamInput = '';
        },

        addCustomExam() {
            const exam = this.normalizeExamName(this.customExamInput);
            if (!exam) return;
            if (this.selectedExams.includes(exam)) {
                this.$message.warning('This examination has already been added');
                return;
            }
            this.selectedExams.push(exam);
            this.customExamInput = '';
        },

        getExamsForCategory(cat) {
            return this.examMapping[cat] || [];
        },

        toggleExam(exam) {
            const normalizedExam = this.normalizeExamName(exam);
            if (this.selectedExams.includes(normalizedExam)) {
                this.selectedExams = this.selectedExams.filter(e => e !== normalizedExam);
            } else {
                this.selectedExams.push(normalizedExam);
            }
        },

        removeExam(exam) {
            this.selectedExams = this.selectedExams.filter(e => e !== exam);
        },

        handleClickOutside(e) {
            const el = this.$refs.selectorRef;
            if (el && !el.contains(e.target)) {
                this.closeDropdown();
            }
        },

        async handleSubmit() {
            this.submitting = true;
            this.saving = true;
            this.step = 'loading';

            const checkedResults = {};
            for (const exam of this.selectedExams) {
                try {
                    const normalizedExam = this.normalizeExamName(exam);
                    const result = await API.checkExam(this.caseId, normalizedExam);
                    checkedResults[exam] = result;
                } catch (err) {
                    console.error('[Phase2Check] Examination query failed:', exam, err);
                    checkedResults[exam] = 'None';
                }
            }

            sessionStorage.setItem('phase2_checkedResults', JSON.stringify(checkedResults));
            const recordId = sessionStorage.getItem('record_id') || this.caseId;
            const examRecords = Object.entries(checkedResults).map(([name, result]) => ({
                name,
                result,
            }));

            try {
                await API.saveCaseRecord(recordId, {
                    exams: examRecords,
                });
            } catch (err) {
                console.error('[Phase2Check] Failed to save record:', err);
            }

            setTimeout(() => {
                this.checkedResults = checkedResults;
                this.saving = false;
                this.submitting = false;
                this.step = 'results';
            }, 1000);
        },

        goToNextPhase() {
            this.$router.push({ path: '/phase3', query: { id: this.caseId } });
        },

        goBack() {
            this.$router.push({ path: '/phase1', query: { id: this.caseId } });
        },
    },

    mounted() {
        this.caseId = this.$route.query.id || sessionStorage.getItem('phase2_caseId') || '';
        document.addEventListener('mousedown', this.handleClickOutside);
    },

    beforeUnmount() {
        document.removeEventListener('mousedown', this.handleClickOutside);
    },
};
