const Phase3Diagnosis = {
    template: `
        <div class="phase3-page">
            <div class="phase3-page__bg"></div>

            <header class="phase3-header">
                <div class="phase3-header__left">
                    <el-button text @click="goBack" class="phase3-header__back-btn">
                        <el-icon><ArrowLeft /></el-icon>
                        Back
                    </el-button>
                    <h3 class="phase3-header__title">
                        {{ subStep === 'caseWriting' ? 'Case Writing' : 'Diagnosis' }}
                    </h3>
                    <span class="phase3-header__subtitle">Phase 3</span>
                </div>
                <div class="phase3-header__right">
                    <span class="phase3-header__patient">
                        Case {{ caseId }}
                    </span>
                    <el-button
                        v-if="subStep === 'caseWriting'"
                        type="primary"
                        size="small"
                        round
                        @click="goToDiagnosis"
                        :disabled="!isCaseFormFilled"
                        class="phase3-header__next-btn"
                    >
                        Next: Fill Diagnosis
                    </el-button>
                </div>
            </header>

            <div class="phase3-content phase3-content--split">
                <template v-if="subStep === 'caseWriting'">
                    <aside class="phase3-left-panel">
                        <div class="phase3-panel-section" v-if="caseInfo">
                            <div class="phase3-panel-section__title">Patient Basic Info</div>
                            <div class="phase3-panel-section__content">
                                <div class="phase3-info-row">
                                    <span class="phase3-info-row__label">Basic Info</span>
                                    <span class="phase3-info-row__value">{{ caseInfo.basicInfomation || 'N/A' }}</span>
                                </div>
                            </div>
                        </div>

                        <div class="phase3-panel-section" v-if="caseInfo && caseInfo.physicalExamination">
                            <div class="phase3-panel-section__title">Physical Examination Report</div>
                            <div class="phase3-panel-section__content phase3-panel-section__scroll">
                                <div class="phase3-physical-exam-text">{{ caseInfo.physicalExamination }}</div>
                            </div>
                        </div>

                        <div class="phase3-panel-section" v-if="Object.keys(phase2Results).length">
                            <div class="phase3-panel-section__title">Auxiliary Examination Results</div>
                            <div class="phase3-panel-section__content">
                                <div
                                    v-for="(result, exam) in phase2Results"
                                    :key="exam"
                                    class="phase3-exam-result-row"
                                    :class="result === '无' ? 'phase3-exam-result-row--none' : 'phase3-exam-result-row--has'"
                                >
                                    <span class="phase3-exam-result-row__name">{{ exam }}</span>
                                    <span class="phase3-exam-result-row__value">
                                        {{ result === '无' ? 'Not examined' : result }}
                                    </span>
                                </div>
                            </div>
                        </div>

                        <div class="phase3-panel-section phase3-panel-section--chat" v-if="phase1Messages.length">
                            <div class="phase3-panel-section__title">
                                Interview Records
                                <span class="phase3-panel-section__hint">Last {{ phase1Messages.length }} turns</span>
                            </div>
                            <div class="phase3-panel-section__scroll phase3-chat-scroll">
                                <div
                                    v-for="(msg, idx) in phase1Messages"
                                    :key="idx"
                                    class="phase3-chat-msg"
                                    :class="msg.role"
                                >
                                    <span class="phase3-chat-msg__role">
                                        {{ msg.role === 'doctor' ? 'Doctor' : 'Patient' }}
                                    </span>
                                    <span class="phase3-chat-msg__content">{{ msg.content }}</span>
                                </div>
                            </div>
                        </div>
                    </aside>

                    <main class="phase3-right-panel">
                        <div class="phase3-case-writing-card">
                            <div class="phase3-case-writing-card__header">
                                <h2 class="phase3-case-writing-card__title">Case Writing</h2>
                                <p class="phase3-case-writing-card__subtitle">
                                    Please fill in the case notes based on the interview and examination results.
                                </p>
                            </div>

                            <div class="case-info-readonly" v-if="caseInfo">
                                <div class="case-info-readonly__grid">
                                    <div class="case-info-row">
                                        <span class="case-info-row__label">Name</span>
                                        <input v-model="caseForm.name" class="case-info-row__input case-info-row__input--auto" placeholder="Enter name" />
                                    </div>
                                    <div class="case-info-row">
                                        <span class="case-info-row__label">Age</span>
                                        <input v-model="caseForm.age" class="case-info-row__input case-info-row__input--auto" placeholder="Enter age" />
                                    </div>
                                    <div class="case-info-row">
                                        <span class="case-info-row__label">Gender</span>
                                        <input v-model="caseForm.gender" class="case-info-row__input case-info-row__input--auto" placeholder="Enter gender" />
                                    </div>
                                </div>
                                <div class="case-info-divider"></div>
                                <div class="case-info-section">
                                    <span class="case-info-section__label">Chief Complaint</span>
                                    <textarea v-model="caseForm.chiefComplaint" class="case-info-section__input" rows="2" placeholder="Enter chief complaint"></textarea>
                                </div>
                                <div class="case-info-divider"></div>
                                <div class="case-info-section">
                                    <span class="case-info-section__label">Family History</span>
                                    <textarea v-model="caseForm.familyHistory" class="case-info-section__input" rows="2" placeholder="Enter family history"></textarea>
                                </div>
                                <div class="case-info-divider"></div>
                                <div class="case-info-section">
                                    <span class="case-info-section__label">Past History</span>
                                    <textarea v-model="caseForm.pastHistory" class="case-info-section__input" rows="2" placeholder="Enter past history"></textarea>
                                </div>
                                <div class="case-info-divider"></div>
                                <div class="case-info-section">
                                    <span class="case-info-section__label">Physical Examination</span>
                                    <textarea v-model="caseForm.physicalExam" class="case-info-section__input" rows="4" placeholder="Enter physical examination findings"></textarea>
                                </div>
                                <div class="case-info-divider"></div>
                                <div class="case-info-section">
                                    <span class="case-info-section__label">Mental Status Examination</span>
                                    <textarea v-model="caseForm.mentalExam" class="case-info-section__input" rows="3" placeholder="Enter mental status examination"></textarea>
                                </div>
                                <div class="case-info-divider"></div>
                                <div class="case-info-section">
                                    <span class="case-info-section__label">Auxiliary Examinations</span>
                                    <textarea v-model="caseForm.auxiliaryExam" class="case-info-section__input" rows="3" placeholder="Enter auxiliary examination results"></textarea>
                                </div>
                            </div>
                        </div>
                    </main>
                </template>

                <template v-else>
                    <div class="phase3-form-card">
                        <div class="phase3-form-card__header">
                            <h2 class="phase3-form-card__title">Fill in Diagnosis</h2>
                            <p class="phase3-form-card__subtitle">
                                Select diagnoses from ICD-11 diagnostic categories and fill in the diagnostic reasoning.
                            </p>
                            <el-tag type="success" effect="plain" size="small" style="margin-top: 8px;">
                                Case saved
                            </el-tag>
                        </div>

                        <div class="phase3-form">
                            <div class="diagnosis-selector" ref="diagnosisSelectorRef">
                                <label class="diagnosis-selector__label">Diagnostic Categories & Items</label>

                                <div class="diagnosis-selector__input" @click.self="openDropdown">
                                    <transition-group name="compound-tag" tag="div" class="diagnosis-selector__tags">
                                        <div
                                            v-for="tag in compoundTags"
                                            :key="tag.key"
                                            class="compound-tag"
                                            :class="{ 'compound-tag--removing': tag._removing }"
                                            :title="categoryLabel(tag.category) + ' - ' + (tag.disease || 'No specific diagnosis selected')"
                                        >
                                            <span class="compound-tag__category">
                                                <el-icon :size="10" class="compound-tag__cat-icon"><Folder /></el-icon>
                                                {{ categoryLabel(tag.category) }}
                                            </span>
                                            <span class="compound-tag__sep"></span>
                                            <span class="compound-tag__disease">
                                                <span class="compound-tag__dot"></span>
                                                {{ tag.disease || 'Not selected' }}
                                            </span>
                                            <span class="compound-tag__delete" @click.stop="removeCompoundTag(tag)" title="Remove">
                                                <el-icon :size="13"><Close /></el-icon>
                                            </span>
                                        </div>
                                    </transition-group>

                                    <div class="compound-tag compound-tag--add" @click.stop="openDropdown">
                                        <el-icon :size="14" class="compound-tag__add-icon"><Plus /></el-icon>
                                        <span>Add Diagnosis</span>
                                    </div>

                                    <div v-if="compoundTags.length === 0" class="diagnosis-selector__placeholder">
                                        Click to select ICD-11 diagnostic categories and specific diagnoses
                                    </div>

                                    <div v-show="dropdownVisible" class="diagnosis-dropdown" @click.stop>
                                        <div class="diagnosis-dropdown__body">
                                            <div class="diagnosis-dropdown__categories">
                                                <div class="diagnosis-dropdown__section-title">Diagnostic Categories</div>
                                                <div
                                                    v-for="cat in categories"
                                                    :key="cat"
                                                    class="diagnosis-dropdown__cat-item"
                                                    :class="{
                                                        'diagnosis-dropdown__cat-item--selected': isSelectedCategory(cat),
                                                        'diagnosis-dropdown__cat-item--active': activeCategory === cat,
                                                    }"
                                                    @click="selectCategory(cat)"
                                                >
                                                    <span class="diagnosis-dropdown__cat-item__text">{{ categoryLabel(cat) }}</span>
                                                    <el-icon v-if="isSelectedCategory(cat)" :size="14" color="#5ed6c8"><Check /></el-icon>
                                                </div>
                                            </div>
                                            <div class="diagnosis-dropdown__diseases">
                                                <div v-if="!activeCategory" class="diagnosis-dropdown__empty">
                                                    Please select a diagnostic category on the left first
                                                </div>
                                                <template v-else>
                                                    <div class="diagnosis-dropdown__section-title">
                                                        ICD-11 Diagnoses under {{ categoryLabel(activeCategory) }}
                                                    </div>
                                                    <div
                                                        v-for="dis in getDiseasesForCategory(activeCategory)"
                                                        :key="dis"
                                                        class="diagnosis-dropdown__dis-item"
                                                        :class="{ 'diagnosis-dropdown__dis-item--selected': isSelectedDisease(activeCategory, dis) }"
                                                        @click="selectDisease(activeCategory, dis)"
                                                    >
                                                        <span class="diagnosis-dropdown__dis-item__text">{{ dis }}</span>
                                                        <el-icon v-if="isSelectedDisease(activeCategory, dis)" :size="14" color="#5ed6c8"><Check /></el-icon>
                                                    </div>
                                                </template>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div class="diagnosis-selector__reason">
                                <label class="diagnosis-selector__label">Diagnostic Reasoning</label>
                                <textarea
                                    v-model="form.reason"
                                    class="diagnosis-selector__textarea"
                                    rows="5"
                                    placeholder="Please describe the diagnostic reasoning and evidence"
                                ></textarea>
                            </div>

                            <div class="phase3-form__actions">
                                <el-button
                                    type="primary"
                                    size="large"
                                    round
                                    @click="handleSubmit"
                                    :loading="submitting"
                                    class="phase3-form__submit-btn"
                                >
                                    Submit Diagnosis
                                </el-button>
                            </div>
                        </div>
                    </div>
                </template>
            </div>

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

    data() {
        return {
            caseId: '',
            subStep: 'caseWriting',
            caseInfo: null,
            phase1Messages: [],
            phase2Results: {},
            caseForm: {
                name: '',
                age: '',
                gender: '',
                chiefComplaint: '',
                familyHistory: '',
                pastHistory: '',
                physicalExam: '',
                mentalExam: '',
                auxiliaryExam: '',
            },
            form: {
                category: '',
                disease: '',
                reason: '',
            },
            submitting: false,
            dropdownVisible: false,
            activeCategory: '',
            selectedCategories: [],
            selectedDiseasesByCategory: {},
            categories: Object.keys(ICD11_CATEGORY_OPTIONS),
            diseaseMapping: ICD11_CATEGORY_OPTIONS,
            saving: false,
        };
    },

    computed: {
        ArrowLeft() { return ElementPlusIconsVue.ArrowLeft; },
        Close() { return ElementPlusIconsVue.Close; },
        Check() { return ElementPlusIconsVue.Check; },
        Plus() { return ElementPlusIconsVue.Plus; },
        Folder() { return ElementPlusIconsVue.Folder; },

        compoundTags() {
            const tags = [];
            for (const cat of this.selectedCategories) {
                const diseases = this.selectedDiseasesByCategory[cat] || [];
                if (diseases.length === 0) {
                    tags.push({
                        key: `cat:${cat}`,
                        category: cat,
                        disease: '',
                        type: 'category-only',
                        _removing: false,
                    });
                } else {
                    for (const dis of diseases) {
                        tags.push({
                            key: `dis:${cat}::${dis}`,
                            category: cat,
                            disease: dis,
                            type: 'compound',
                            _removing: false,
                        });
                    }
                }
            }
            return tags;
        },

        isCaseFormFilled() {
            const f = this.caseForm;
            return f.name && f.age && f.gender && f.chiefComplaint
                && f.familyHistory && f.pastHistory && f.physicalExam
                && f.mentalExam && f.auxiliaryExam;
        },
    },

    methods: {
        categoryLabel(category) {
            return ICD11Localization.localizeCategory(category);
        },

        diseaseLabel(disease) {
            return ICD11Localization.localizeDisease(disease);
        },

        getDiseasesForCategory(cat) {
            return this.diseaseMapping[cat] || [];
        },

        isSelectedCategory(cat) {
            return this.selectedCategories.includes(cat);
        },

        isSelectedDisease(cat, dis) {
            return (this.selectedDiseasesByCategory[cat] || []).includes(dis);
        },

        openDropdown() {
            this.dropdownVisible = true;
            if (!this.activeCategory) {
                this.activeCategory = this.selectedCategories[0] || this.categories[0] || '';
            }
        },

        closeDropdown() {
            this.dropdownVisible = false;
        },

        selectCategory(cat) {
            this.activeCategory = cat;
        },

        selectDisease(cat, dis) {
            if (!this.isSelectedCategory(cat)) {
                this.selectedCategories.push(cat);
            }
            if (!this.selectedDiseasesByCategory[cat]) {
                this.selectedDiseasesByCategory[cat] = [];
            }
            const diseases = this.selectedDiseasesByCategory[cat];
            if (!diseases.includes(dis)) {
                diseases.push(dis);
            } else {
                this.selectedDiseasesByCategory[cat] = diseases.filter((item) => item !== dis);
                if (this.selectedDiseasesByCategory[cat].length === 0) {
                    this.selectedCategories = this.selectedCategories.filter((item) => item !== cat);
                    delete this.selectedDiseasesByCategory[cat];
                    if (this.activeCategory === cat) {
                        this.activeCategory = this.selectedCategories[0] || this.categories[0] || '';
                    }
                }
            }
        },

        removeCompoundTag(tag) {
            if (tag.type === 'category-only') {
                this.selectedCategories = this.selectedCategories.filter((item) => item !== tag.category);
                delete this.selectedDiseasesByCategory[tag.category];
            } else if (this.selectedDiseasesByCategory[tag.category]) {
                this.selectedDiseasesByCategory[tag.category] =
                    this.selectedDiseasesByCategory[tag.category].filter((item) => item !== tag.disease);
                if (this.selectedDiseasesByCategory[tag.category].length === 0) {
                    this.selectedCategories = this.selectedCategories.filter((item) => item !== tag.category);
                    delete this.selectedDiseasesByCategory[tag.category];
                }
            }
            if (this.activeCategory === tag.category && !this.selectedCategories.includes(tag.category)) {
                this.activeCategory = this.selectedCategories[0] || this.categories[0] || '';
            }
        },

        handleClickOutside(e) {
            const el = this.$refs.diagnosisSelectorRef;
            if (el && !el.contains(e.target)) {
                this.closeDropdown();
            }
        },

        goToDiagnosis() {
            if (!this.isCaseFormFilled) {
                this.$message.warning('Please complete all case writing fields first');
                return;
            }
            sessionStorage.setItem('phase3_caseForm', JSON.stringify(this.caseForm));
            this.subStep = 'diagnosis';
            this.$message.success('Case saved, please continue to fill in diagnosis');
        },

        async handleSubmit() {
            if (this.selectedCategories.length === 0) {
                this.$message.warning('Please select at least one diagnostic category');
                return;
            }
            if (!this.form.reason.trim()) {
                this.$message.warning('Please fill in the diagnostic reasoning');
                return;
            }

            this.submitting = true;
            this.saving = true;
            try {
                const recordId = sessionStorage.getItem('record_id') || this.caseId;
                const allDiseases = [];
                const diagnoses = [];

                for (const cat of this.selectedCategories) {
                    const diseases = this.selectedDiseasesByCategory[cat] || [];
                    allDiseases.push(...diseases);
                    diagnoses.push({ category: cat, diseases });
                }

                const primaryCategory = this.selectedCategories[0] || '';
                const primaryDisease = allDiseases[0] || '';
                const diseaseText = allDiseases.join(' | ');

                const diagnosisPayload = {
                    category: primaryCategory,
                    disease: diseaseText || primaryDisease,
                    reason: this.form.reason,
                    diagnoses,
                };

                await API.submitCaseWriting(recordId, JSON.stringify(this.caseForm));

                const result = await API.submitDiagnosis(recordId, {
                    category: primaryCategory,
                    disease: diseaseText || primaryDisease,
                    reason: this.form.reason,
                });

                await API.saveCaseRecord(recordId, {
                    caseForm: { ...this.caseForm },
                    diagnosis: diagnosisPayload,
                });

                sessionStorage.setItem('phase3_result', JSON.stringify({
                    caseId: this.caseId,
                    caseForm: { ...this.caseForm },
                    category: primaryCategory,
                    disease: diseaseText || primaryDisease,
                    reason: this.form.reason,
                    diagnoses,
                }));

                this.$message.success('Phase 3 completed');
                console.log('[Phase3Diagnosis] diagnosis submit result:', result);
                this.$router.push({ path: '/phase4', query: { id: this.caseId } });
            } catch (err) {
                this.$message.error(`Submission failed: ${err.message || 'Unknown error'}`);
                console.error('[Phase3Diagnosis] submit failed:', err);
            } finally {
                this.submitting = false;
                this.saving = false;
            }
        },

        goBack() {
            if (this.subStep === 'diagnosis') {
                this.subStep = 'caseWriting';
            } else {
                this.$router.push({ path: '/phase2', query: { id: this.caseId } });
            }
        },

        fillBasicInfoFromSummary(basicInfo) {
            if (!basicInfo) return;

            const text = String(basicInfo);
            const lower = text.toLowerCase();

            if (lower.includes('female') || lower.includes('woman') || lower.includes('girl') || text.includes('女')) {
                this.caseForm.gender = 'Female';
            } else if (lower.includes('male') || lower.includes('man') || lower.includes('boy') || text.includes('男')) {
                this.caseForm.gender = 'Male';
            }

            const ageMatch = basicInfo.match(/(\d+)/);
            if (ageMatch) {
                this.caseForm.age = ageMatch[1];
            }

            if (!this.caseForm.name) {
                this.caseForm.name = 'Patient';
            }
        },

        async loadPhaseData() {
            if (this.caseId) {
                try {
                    const info = await API.getCaseInfo(this.caseId);
                    this.caseInfo = info;
                    if (info?.basicInfomation) {
                        this.fillBasicInfoFromSummary(info.basicInfomation);
                    }
                } catch (err) {
                    console.error('[Phase3Diagnosis] failed to load case info:', err);
                }
            }

            const messagesStr = sessionStorage.getItem('phase2_messages');
            if (messagesStr) {
                try {
                    const messages = JSON.parse(messagesStr);
                    this.phase1Messages = messages.slice(-12);
                } catch (err) {
                    console.error('[Phase3Diagnosis] failed to parse Phase 1 messages:', err);
                }
            } else {
                console.warn('[Phase3Diagnosis] phase2_messages not found');
            }

            const resultsStr = sessionStorage.getItem('phase2_checkedResults');
            if (resultsStr) {
                try {
                    this.phase2Results = JSON.parse(resultsStr);
                } catch (err) {
                    console.error('[Phase3Diagnosis] failed to parse Phase 2 results:', err);
                }
            }

            const savedCaseForm = sessionStorage.getItem('phase3_caseForm');
            if (savedCaseForm) {
                try {
                    this.caseForm = JSON.parse(savedCaseForm);
                } catch (err) {
                    console.error('[Phase3Diagnosis] failed to restore saved case form:', err);
                }
            }
        },
    },

    mounted() {
        this.caseId = this.$route.query.id || sessionStorage.getItem('phase2_caseId') || '';
        if (!this.caseId) {
            this.$message.warning('Case not found, please re-enter from patient list');
        }
        this.loadPhaseData();
        document.addEventListener('mousedown', this.handleClickOutside);
    },

    beforeUnmount() {
        document.removeEventListener('mousedown', this.handleClickOutside);
    },
};
