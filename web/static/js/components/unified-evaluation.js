const EVAL_MARKDOWN_OPTIONS = Object.freeze({
    breaks: false,
    gfm: true,
});

const EVAL_REQUEST_TIMEOUT_MS = 45000;
const PHASE3_EVAL_TIMEOUT_MS = 180000;
const PHASE4_EVAL_TIMEOUT_MS = 90000;

const UnifiedEvaluation = {
    template: `
        <div class="unified-eval-page">
            <div class="unified-eval-page__bg"></div>

            <div class="unified-eval-brand-center">
                <div class="unified-eval-brand-center__title">MentalEval</div>
                <div class="unified-eval-brand-center__divider"></div>
                <div class="unified-eval-brand-center__subtitle">Comprehensive Clinical Evaluation</div>
            </div>

            <div v-if="loading" class="unified-eval-loading">
                <el-skeleton :rows="10" animated />
            </div>

            <div v-else-if="!allDone" class="eval-pipeline-page">
                <div class="eval-pipeline__steps">
                    <template v-for="(phase, idx) in phases" :key="phase.key">
                        <div class="eval-pipeline-step"
                             :class="'eval-pipeline-step--' + phase.status">
                            <div class="eval-pipeline-step__circle">
                                <span class="eval-pipeline-step__num">{{ idx + 1 }}</span>
                            </div>
                            <span class="eval-pipeline-step__label">{{ phase.label }}</span>
                        </div>
                        <div v-if="idx < phases.length - 1"
                             class="eval-pipeline-connector"
                             :class="{ 'eval-pipeline-connector--done': phase.status === 'done' }"></div>
                    </template>
                </div>

                <div class="eval-pipeline__core">
                    <div class="eval-pipeline__core-glow"></div>

                    <div class="eval-pipeline__core-icon-wrap">
                        <div class="eval-pipeline__core-halo"></div>
                        <img src="/static/bg/eval.png" alt="" class="eval-pipeline__core-img eval-pipeline__core-img--breathing" />
                    </div>

                    <div class="eval-pipeline__core-title">MentalEval</div>
                    <div class="eval-pipeline__core-subtitle">Generating comprehensive evaluation...</div>

                    <div class="eval-pipeline__core-status">Currently processing: {{ currentPhaseLabel }}</div>
                    <div class="eval-pipeline__core-detail">{{ currentPhaseDetail }}</div>

                    <div class="eval-pipeline__progress">
                        <div class="eval-pipeline__progress-bar eval-pipeline__progress-bar--flowing"></div>
                    </div>
                </div>
            </div>

            <div v-else class="unified-eval-content">
                <div v-if="allPhasesFailed" class="eval-error-banner">
                    <el-alert type="error" :closable="false" show-icon>
                        <template #title>Evaluation data temporarily unavailable</template>
                        Some evaluation results could not be loaded. Please retry, or return to the previous phase to regenerate the report.
                    </el-alert>
                </div>

                <div v-else class="eval-result-header">
                    <div class="eval-result-header__brand">
                        <img src="/static/bg/eval.png" alt="" class="eval-result-header__icon" />
                    </div>
                </div>

                <div class="eval-result-cards">
                    <transition name="eval-card-fade" appear>
                        <div class="eval-result-card" v-if="report.phase1 && !report.phase1._fallback">
                            <div class="eval-result-card__header">
                                <div class="eval-result-card__phase-num">1</div>
                                <h3 class="eval-result-card__title">Interview Phase Evaluation</h3>
                                <el-tag size="small" type="success" effect="plain">Completed</el-tag>
                                <button class="eval-collapse-btn" type="button" @click="togglePhaseCollapse('phase1')" aria-label="Toggle Phase 1 section">
                                    <span class="eval-collapse-btn__arrow" :class="{ 'is-collapsed': isPhaseCollapsed('phase1') }"></span>
                                </button>
                            </div>
                            <div class="eval-result-card__body" :class="{ 'eval-result-card__body--collapsed': isPhaseCollapsed('phase1') }">
                                <div class="eval-section" v-if="report.phase1.conversation_stats">
                                    <div class="eval-section__label">Dialogue Overview</div>
                                    <div class="eval-stats">
                                        <div class="eval-stat">
                                            <span class="eval-stat__label">Total Turns</span>
                                            <span class="eval-stat__value">{{ report.phase1.conversation_stats.total_turns }}</span>
                                        </div>
                                        <div class="eval-stat">
                                            <span class="eval-stat__label">Doctor Turns</span>
                                            <span class="eval-stat__value">{{ report.phase1.conversation_stats.doctor_turns }}</span>
                                        </div>
                                        <div class="eval-stat">
                                            <span class="eval-stat__label">Patient Turns</span>
                                            <span class="eval-stat__value">{{ report.phase1.conversation_stats.patient_turns }}</span>
                                        </div>
                                    </div>
                                </div>
                                <div class="eval-section">
                                    <div class="eval-section__label">Interview Coverage</div>
                                    <div class="eval-stats">
                                        <div class="eval-stat">
                                            <span class="eval-stat__label">Chief Complaint Coverage</span>
                                            <span class="eval-stat__value">{{ report.phase1.coverage_stats?.chief_complaint_coverage ?? 100 }}%</span>
                                            <span class="eval-stat__sub">{{ report.phase1.coverage_stats?.chief_complaint_used_count ?? 0 }}/{{ report.phase1.coverage_stats?.chief_complaint_total_count ?? 0 }} items</span>
                                        </div>
                                        <div class="eval-stat">
                                            <span class="eval-stat__label">Mental Status Coverage</span>
                                            <span class="eval-stat__value">{{ report.phase1.coverage_stats?.mental_status_coverage ?? 100 }}%</span>
                                            <span class="eval-stat__sub">{{ report.phase1.coverage_stats?.mental_status_used_count ?? 0 }}/{{ report.phase1.coverage_stats?.mental_status_total_count ?? 0 }} items</span>
                                        </div>
                                        <div class="eval-stat">
                                            <span class="eval-stat__label">Overall Coverage</span>
                                            <span class="eval-stat__value">{{ report.phase1.coverage_stats?.overall_coverage ?? 100 }}%</span>
                                        </div>
                                    </div>
                                </div>
                                <div class="eval-section eval-section--compact" v-if="report.phase1.empathy_evaluation">
                                    <div class="eval-section__label">Communication & Empathy</div>
                                    <div class="eval-empathy">
                                        <div class="eval-hp-bar">
                                            <div class="eval-hp-bar__track">
                                                <div class="eval-hp-bar__fill"
                                                     :style="hpBarStyle(report.phase1.empathy_evaluation.empathy_level || 0)"
                                                ></div>
                                            </div>
                                            <span class="eval-hp-bar__text">{{ empathyLevelDisplay(report.phase1.empathy_evaluation.empathy_level || 0) }}</span>
                                        </div>
                                        <div class="eval-scroll-card" v-if="report.phase1.empathy_evaluation.why_this_level">
                                            <div class="eval-scroll-card__title">Scoring Basis</div>
                                            <div
                                                class="eval-scroll-card__body eval-empathy__reason eval-markdown"
                                                v-html="renderMarkdown(report.phase1.empathy_evaluation.why_this_level)"
                                            ></div>
                                        </div>
                                        <div class="eval-scroll-card" v-if="report.phase1.empathy_evaluation.evidence">
                                            <div class="eval-scroll-card__title">Supporting Evidence</div>
                                            <div
                                                class="eval-scroll-card__body eval-empathy__evidence eval-markdown"
                                                v-html="renderMarkdown(report.phase1.empathy_evaluation.evidence)"
                                            ></div>
                                        </div>
                                    </div>
                                </div>
                                <div class="eval-section eval-section--compact" v-if="report.phase1.profession_evaluation">
                                    <div class="eval-section__label">Interview Professionalism Evaluation</div>
                                    <div class="eval-empathy">
                                        <div class="eval-hp-bar">
                                            <div class="eval-hp-bar__track">
                                                <div class="eval-hp-bar__fill"
                                                     :style="hpBarStyle(report.phase1.profession_evaluation.profession_level || 0)"
                                                ></div>
                                            </div>
                                            <span class="eval-hp-bar__text">{{ empathyLevelDisplay(report.phase1.profession_evaluation.profession_level || 0) }}</span>
                                        </div>
                                        <div class="eval-scroll-card" v-if="professionEvaluationItems.length">
                                            <div class="eval-scroll-card__title">AI Item Analysis</div>
                                            <div class="eval-scroll-card__body eval-phase3-scroll">
                                                <div class="eval-writing-sections eval-writing-sections--compact">
                                                    <div v-for="item in professionEvaluationItems" :key="'profession-' + item.index" class="eval-writing-item">
                                                        <div class="eval-writing-item__header">
                                                            <span class="eval-writing-item__name">Item {{ item.index }}</span>
                                                            <span class="eval-writing-item__score" :class="scoreClass(item.score / 2)">{{ item.scoreLabel }}</span>
                                                        </div>
                                                        <div class="eval-writing-item__detail eval-markdown eval-markdown--compact" v-html="renderMarkdown(item.reason)"></div>
                                                        <div v-if="item.evidence" class="eval-writing-item__sub eval-writing-item__sub--stack">
                                                            <span class="eval-writing-item__sub-label">Evidence</span>
                                                            <div class="eval-markdown eval-markdown--compact" v-html="renderMarkdown(item.evidence)"></div>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                        <div class="eval-scroll-card" v-if="professionEvaluationSummary">
                                            <div class="eval-scroll-card__title">Overall Summary</div>
                                            <div
                                                class="eval-scroll-card__body eval-empathy__reason eval-markdown"
                                                v-html="renderMarkdown(professionEvaluationSummary)"
                                            ></div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </transition>

                    <transition name="eval-card-fade" appear :style="{ animationDelay: '0.15s' }">
                        <div class="eval-result-card" v-if="report.phase2 && !report.phase2._fallback">
                            <div class="eval-result-card__header">
                                <div class="eval-result-card__phase-num">2</div>
                                <h3 class="eval-result-card__title">Auxiliary Examination Evaluation</h3>
                                <el-tag size="small" type="success" effect="plain">Completed</el-tag>
                                <button class="eval-collapse-btn" type="button" @click="togglePhaseCollapse('phase2')" aria-label="Toggle Phase 2 section">
                                    <span class="eval-collapse-btn__arrow" :class="{ 'is-collapsed': isPhaseCollapsed('phase2') }"></span>
                                </button>
                            </div>
                            <div class="eval-result-card__body" :class="{ 'eval-result-card__body--collapsed': isPhaseCollapsed('phase2') }">
                                <div class="eval-section">
                                    <div class="eval-section__label">Accuracy Overview</div>
                                    <div class="eval-accuracy-display">
                                        <span class="eval-accuracy-value">{{ formatAccuracy(report.phase2.accuracy) }}</span>
                                        <span class="eval-accuracy-subtitle">Matching accuracy between selected examinations and standard examination plan.</span>
                                    </div>
                                </div>
                                <div class="eval-section">
                                    <div class="eval-section__label">Metrics</div>
                                    <div class="eval-stats">
                                        <div class="eval-stat">
                                            <span class="eval-stat__label">Precision</span>
                                            <span class="eval-stat__value">{{ formatAccuracy(report.phase2.metrics?.precision || 0) }}</span>
                                        </div>
                                        <div class="eval-stat">
                                            <span class="eval-stat__label">Recall</span>
                                            <span class="eval-stat__value">{{ formatAccuracy(report.phase2.metrics?.recall || 0) }}</span>
                                        </div>
                                        <div class="eval-stat">
                                            <span class="eval-stat__label">F1 Score</span>
                                            <span class="eval-stat__value">{{ formatAccuracy(report.phase2.metrics?.f1 || 0) }}</span>
                                        </div>
                                    </div>
                                </div>
                                <div class="eval-section" v-if="doctorExamList.length || goldExamList.length">
                                    <div class="eval-section__label">Examination Comparison</div>
                                    <div class="eval-exam-compare">
                                        <div class="eval-exam-compare__column" v-if="doctorExamList.length">
                                            <div class="eval-exam-compare__title">Doctor's Selected Examinations</div>
                                            <div class="eval-exam-compare__list">
                                                <div
                                                    v-for="exam in doctorExamList"
                                                    :key="'doctor-' + exam.name"
                                                    class="eval-exam-pill"
                                                    :class="exam.statusClass"
                                                >
                                                    <span class="eval-exam-pill__name">{{ exam.name }}</span>
                                                    <span class="eval-exam-pill__tag">{{ exam.statusText }}</span>
                                                </div>
                                            </div>
                                        </div>
                                        <div class="eval-exam-compare__column" v-if="goldExamList.length">
                                            <div class="eval-exam-compare__title">Standard Examination Plan</div>
                                            <div class="eval-exam-compare__list">
                                                <div
                                                    v-for="exam in goldExamList"
                                                    :key="'gold-' + exam.name"
                                                    class="eval-exam-pill"
                                                    :class="exam.statusClass"
                                                >
                                                    <span class="eval-exam-pill__name">{{ exam.name }}</span>
                                                    <span class="eval-exam-pill__tag">{{ exam.statusText }}</span>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                <div class="eval-section" v-if="report.phase2.exam_details">
                                    <div class="eval-section__label">Examination Detail Results</div>
                                    <div class="eval-exam-details">
                                        <div v-for="(detail, key) in report.phase2.exam_details" :key="key"
                                             class="eval-exam-item">
                                            <span class="eval-exam-item__name">{{ translateExamLabel(key) }}</span>
                                            <span class="eval-exam-item__result"
                                                  :class="detail?.correct ? 'eval-exam--correct' : 'eval-exam--wrong'">
                                                {{ detail?.correct ? 'Matched' : 'Unmatched' }}
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </transition>

                    <transition name="eval-card-fade" appear :style="{ animationDelay: '0.3s' }">
                        <div class="eval-result-card" v-if="report.phase3_full">
                            <div class="eval-result-card__header">
                                <div class="eval-result-card__phase-num">3</div>
                                <h3 class="eval-result-card__title">Case & Diagnosis Evaluation</h3>
                                <el-tag size="small" type="success" effect="plain">Completed</el-tag>
                                <button class="eval-collapse-btn" type="button" @click="togglePhaseCollapse('phase3')" aria-label="Toggle Phase 3 section">
                                    <span class="eval-collapse-btn__arrow" :class="{ 'is-collapsed': isPhaseCollapsed('phase3') }"></span>
                                </button>
                            </div>
                            <div class="eval-result-card__body" :class="{ 'eval-result-card__body--collapsed': isPhaseCollapsed('phase3') }">
                                <div v-if="report.phase3_full._fallback" class="eval-note">
                                    <span>{{ report.phase3_full.error || 'Phase 3 evaluation results are temporarily unavailable.' }}</span>
                                </div>
                                <div v-else class="eval-phase3-stack">
                                    <div class="eval-phase3-summary" v-if="phase3OverallScore !== null">
                                        <div class="eval-note eval-markdown eval-markdown--compact" v-html="renderMarkdown(phase3Narrative)"></div>
                                    </div>
                                    <div class="eval-phase3-panel">
                                        <div class="eval-phase3-panel__header">
                                            <el-icon :size="14" color="#409eff"><Notebook /></el-icon>
                                            <span>Diagnosis Evaluation</span>
                                        </div>
                                        <div class="eval-phase3-panel__body">
                                            <template v-if="diagnosisEval">
                                                <div class="eval-overall-score">
                                                    <span class="eval-overall-score__value">{{ formatPhase3FivePointScore(diagnosisEval.total_score) }}</span>
                                                    <span class="eval-overall-score__label">Diagnosis Total Score</span>
                                                </div>
                                                <div class="eval-phase3-diagnosis-grid">
                                                    <div class="eval-basis-card eval-basis-card--phase3-aligned" v-if="phase3DiagnosisCompare.length">
                                                        <div class="eval-basis-card__title">Diagnosis Comparison</div>
                                                        <div class="eval-basis-card__list eval-basis-card__list--themed">
                                                            <div v-for="item in phase3DiagnosisCompare" :key="item.label" class="eval-basis-item">
                                                                <div class="eval-basis-item__label">{{ item.label }}</div>
                                                                <div class="eval-basis-item__content eval-markdown eval-markdown--compact" v-html="renderMarkdown(item.content)"></div>
                                                            </div>
                                                        </div>
                                                    </div>
                                                    <div class="eval-phase3-diagnosis-scores">
                                                        <div class="eval-diagnosis-dimensions">
                                                            <div class="eval-diag-item">
                                                                <span class="eval-diag-item__label">Disease Category Judgment</span>
                                                                <span class="eval-diag-item__score" :class="scoreClass(diagnosisEval.disease_type?.score)">
                                                                    {{ formatPhase3FivePointScore(diagnosisEval.disease_type?.score) }}
                                                                </span>
                                                            </div>
                                                            <div class="eval-diag-item__detail eval-markdown eval-markdown--compact" v-html="renderMarkdown(diagnosisEval.disease_type?.detail)"></div>
                                                            <div class="eval-diag-item">
                                                                <span class="eval-diag-item__label">Diagnostic Reasoning</span>
                                                                <span class="eval-diag-item__score" :class="scoreClass(diagnosisEval.diagnostic_reasoning?.score)">
                                                                    {{ formatPhase3FivePointScore(diagnosisEval.diagnostic_reasoning?.score) }}
                                                                </span>
                                                            </div>
                                                            <div class="eval-diag-item__detail eval-markdown eval-markdown--compact" v-html="renderMarkdown(diagnosisEval.diagnostic_reasoning?.detail)"></div>
                                                            <div class="eval-diag-item">
                                                                <span class="eval-diag-item__label">Diagnostic Correctness</span>
                                                                <span class="eval-diag-item__score" :class="scoreClass(diagnosisEval.diagnostic_correctness?.score || 0)">
                                                                    {{ formatPhase3FivePointScore(diagnosisEval.diagnostic_correctness?.score || 0) }}
                                                                </span>
                                                            </div>
                                                            <div class="eval-diag-item__detail eval-markdown eval-markdown--compact" v-if="diagnosisEval.diagnostic_correctness?.detail" v-html="renderMarkdown(diagnosisEval.diagnostic_correctness.detail)"></div>
                                                        </div>
                                                    </div>
                                                </div>
                                            </template>
                                            <div v-else class="eval-note">
                                                <span>No diagnosis evaluation results available.</span>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="eval-phase3-panel">
                                        <div class="eval-phase3-panel__header">
                                            <el-icon :size="14" color="#5ed6c8"><Document /></el-icon>
                                            <span>Case Writing Evaluation</span>
                                        </div>
                                        <div class="eval-phase3-panel__body">
                                            <template v-if="caseWritingEval">
                                                <div class="eval-overall-score">
                                                    <span class="eval-overall-score__value">{{ formatPhase3FivePointScore(caseWritingEval.total_score) }}</span>
                                                    <span class="eval-overall-score__label">Case Writing Score</span>
                                                </div>
                                                <div class="eval-phase3-compare">
                                                    <div class="eval-phase3-compare__column">
                                                        <div class="eval-basis-card" v-if="phase3CaseBasis.length">
                                                            <div class="eval-basis-card__title">Standard Case</div>
                                                            <div class="eval-basis-card__list">
                                                                <div v-for="item in phase3CaseBasis" :key="item.label" class="eval-basis-item">
                                                                    <div class="eval-basis-item__label">{{ item.label }}</div>
                                                                    <div class="eval-basis-item__content eval-markdown eval-markdown--compact" v-html="renderMarkdown(item.content)"></div>
                                                                </div>
                                                            </div>
                                                        </div>
                                                    </div>
                                                    <div class="eval-phase3-compare__column eval-phase3-compare__column--full">
                                                        <div class="eval-basis-card eval-basis-card--phase3-aligned" v-if="phase3DoctorCaseBasis.length">
                                                            <div class="eval-basis-card__title">Doctor's Case</div>
                                                            <div class="eval-basis-card__list eval-basis-card__list--themed">
                                                                <div v-for="item in phase3DoctorCaseBasis" :key="item.label" class="eval-basis-item">
                                                                    <div class="eval-basis-item__label">{{ item.label }}</div>
                                                                    <div class="eval-basis-item__content eval-markdown eval-markdown--compact" v-html="renderMarkdown(item.content)"></div>
                                                                </div>
                                                            </div>
                                                        </div>
                                                        <div v-else class="eval-note">
                                                            <span>Doctor's case not yet correctly extracted</span>
                                                        </div>
                                                    </div>
                                                </div>
                                                <div class="eval-scroll-card" v-if="phase3CaseDimensionCards.length">
                                                    <div class="eval-scroll-card__title">Case Writing Dimension Evaluation</div>
                                                    <div class="eval-scroll-card__body eval-phase3-scroll">
                                                        <div class="eval-writing-sections">
                                                            <div v-for="section in phase3CaseDimensionCards" :key="section.label"
                                                                 class="eval-writing-item">
                                                                <div class="eval-writing-item__header">
                                                                    <span class="eval-writing-item__name">{{ section.label }}</span>
                                                                    <span class="eval-writing-item__score" :class="scoreClass(section.rawScore)">
                                                                        {{ section.score }}
                                                                    </span>
                                                                </div>
                                                                <div class="eval-writing-item__detail eval-markdown eval-markdown--compact" v-html="renderMarkdown(section.detail)"></div>
                                                                <div v-if="section.subDetail" class="eval-writing-item__sub">
                                                                    <div class="eval-markdown eval-markdown--compact" v-html="renderMarkdown(section.subDetail)"></div>
                                                                </div>
                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>
                                                <div class="eval-section eval-section--compact" v-if="phase3ClinicalNoteSubjective">
                                                    <div class="eval-section__label">Clinical Note Subjective Evaluation</div>
                                                    <div class="eval-empathy">
                                                        <div class="eval-hp-bar">
                                                            <div class="eval-hp-bar__track">
                                                                <div class="eval-hp-bar__fill" :style="hpBarStyle(phase3ClinicalNoteSubjective.score || 0)"></div>
                                                            </div>
                                                            <span class="eval-hp-bar__text">{{ empathyLevelDisplay(phase3ClinicalNoteSubjective.score || 0) }}</span>
                                                        </div>
                                                        <div class="eval-scroll-card" v-if="subjectiveReasonText(phase3ClinicalNoteSubjective)">
                                                            <div class="eval-scroll-card__title">Reviewer Reasoning</div>
                                                            <div class="eval-scroll-card__body eval-empathy__reason eval-markdown" v-html="renderMarkdown(subjectiveReasonText(phase3ClinicalNoteSubjective))"></div>
                                                        </div>
                                                </div>
                                            </div>
                                                <div class="eval-section eval-section--compact" v-if="phase3DiagnosticRigorSubjective">
                                                    <div class="eval-section__label">Diagnostic Reasoning Subjective Evaluation</div>
                                                    <div class="eval-empathy">
                                                        <div class="eval-hp-bar">
                                                            <div class="eval-hp-bar__track">
                                                                <div class="eval-hp-bar__fill" :style="hpBarStyle(phase3DiagnosticRigorSubjective.score || 0)"></div>
                                                            </div>
                                                            <span class="eval-hp-bar__text">{{ empathyLevelDisplay(phase3DiagnosticRigorSubjective.score || 0) }}</span>
                                                        </div>
                                                        <div class="eval-scroll-card" v-if="subjectiveReasonText(phase3DiagnosticRigorSubjective)">
                                                            <div class="eval-scroll-card__title">Reviewer Reasoning</div>
                                                            <div class="eval-scroll-card__body eval-empathy__reason eval-markdown" v-html="renderMarkdown(subjectiveReasonText(phase3DiagnosticRigorSubjective))"></div>
                                                        </div>
                                                </div>
                                            </div>
                                            </template>
                                            <div v-else class="eval-note">
                                                <span>No case writing evaluation results available.</span>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </transition>

                    <transition name="eval-card-fade" appear :style="{ animationDelay: '0.45s' }">
                        <div class="eval-result-card" v-if="report.phase4 && !report.phase4._fallback">
                            <div class="eval-result-card__header">
                                <div class="eval-result-card__phase-num">4</div>
                                <h3 class="eval-result-card__title">Treatment Phase Evaluation</h3>
                                <el-tag size="small" type="success" effect="plain">Completed</el-tag>
                                <button class="eval-collapse-btn" type="button" @click="togglePhaseCollapse('phase4')" aria-label="Toggle Phase 4 section">
                                    <span class="eval-collapse-btn__arrow" :class="{ 'is-collapsed': isPhaseCollapsed('phase4') }"></span>
                                </button>
                            </div>
                            <div class="eval-result-card__body" :class="{ 'eval-result-card__body--collapsed': isPhaseCollapsed('phase4') }">
                                <div class="eval-phase3-stack">
                                    <div class="eval-phase3-summary" v-if="phase4OverallScore !== null">
                                        <div class="eval-note">{{ phase4Narrative }}</div>
                                    </div>
                                    <div class="eval-phase3-panel">
                                        <div class="eval-phase3-panel__header">
                                            <el-icon :size="14" color="#5ed6c8"><Document /></el-icon>
                                            <span>Treatment Plan Evaluation</span>
                                        </div>
                                        <div class="eval-phase3-panel__body">
                                            <div class="eval-stats" v-if="report.phase4.treatment_stats">
                                                <div class="eval-stat">
                                                    <span class="eval-stat__label">Filled Items</span>
                                                    <span class="eval-stat__value">{{ report.phase4.treatment_stats.filled_categories }}</span>
                                                </div>
                                                <div class="eval-stat">
                                                    <span class="eval-stat__label">Empty Items</span>
                                                    <span class="eval-stat__value">{{ report.phase4.treatment_stats.empty_categories }}</span>
                                                </div>
                                                <div class="eval-stat">
                                                    <span class="eval-stat__label">Total Items</span>
                                                    <span class="eval-stat__value">{{ report.phase4.treatment_stats.total_categories }}</span>
                                                </div>
                                            </div>
                                            <div class="eval-phase4-grid">
                                                <div class="eval-basis-card" v-if="phase4StandardPlanEntries.length">
                                                    <div class="eval-basis-card__title">Standard Treatment Plan</div>
                                                    <div class="eval-basis-card__list">
                                                        <div v-for="item in phase4StandardPlanEntries" :key="'standard-' + item.label + item.content" class="eval-basis-item">
                                                            <div class="eval-basis-item__label">{{ item.label }}</div>
                                                            <div class="eval-basis-item__content eval-markdown eval-markdown--compact" v-html="renderMarkdown(item.content)"></div>
                                                        </div>
                                                    </div>
                                                </div>
                                                <div class="eval-basis-card eval-basis-card--phase4-submitted" v-if="phase4PlanEntries.length">
                                                    <div class="eval-basis-card__title">Submitted Treatment Plan</div>
                                                    <div class="eval-basis-card__list eval-basis-card__list--themed">
                                                        <div v-for="item in phase4PlanEntries" :key="item.label" class="eval-basis-item">
                                                            <div class="eval-basis-item__label">{{ item.label }}</div>
                                                            <div class="eval-basis-item__content eval-markdown eval-markdown--compact" v-html="renderMarkdown(item.content)"></div>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="eval-phase3-panel">
                                        <div class="eval-phase3-panel__header">
                                            <el-icon :size="14" color="#67c23a"><DataAnalysis /></el-icon>
                                            <span>Treatment Subjective Evaluation</span>
                                        </div>
                                        <div class="eval-phase3-panel__body">
                                            <template v-if="phase4TreatmentSubjective">
                                                <div class="eval-section eval-section--compact">
                                                    <div class="eval-section__label">Treatment Subjective Review</div>
                                                    <div class="eval-empathy">
                                                        <div class="eval-hp-bar">
                                                            <div class="eval-hp-bar__track">
                                                                <div class="eval-hp-bar__fill" :style="hpBarStyle(phase4TreatmentSubjective.score || 0)"></div>
                                                            </div>
                                                            <span class="eval-hp-bar__text">{{ empathyLevelDisplay(phase4TreatmentSubjective.score || 0) }}</span>
                                                        </div>
                                                        <div class="eval-scroll-card" v-if="subjectiveReasonText(phase4TreatmentSubjective)">
                                                            <div class="eval-scroll-card__title">Reviewer Reasoning</div>
                                                            <div class="eval-scroll-card__body eval-empathy__reason eval-markdown" v-html="renderMarkdown(subjectiveReasonText(phase4TreatmentSubjective))"></div>
                                                        </div>
                                                    </div>
                                                </div>
                                            </template>
                                            <div v-else class="eval-note">
                                                <span>No treatment content was submitted, so subjective treatment evaluation was skipped.</span>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </transition>
                </div>

                <div class="eval-result-footer">
                    <el-button
                        type="primary"
                        size="large"
                        round
                        @click="goToPatients"
                        class="eval-result-footer__btn"
                    >
                        <el-icon :size="16"><HomeFilled /></el-icon>
                        Back to Patient List
                    </el-button>
                    <el-button
                        size="large"
                        round
                        @click="goToHistory"
                        class="eval-result-footer__btn"
                    >
                        View History
                    </el-button>
                </div>
            </div>
        </div>
    `,

    data() {
        return {
            caseId: '',
            caseInfo: null,
            phase2ExamResults: {},
            collapsedPhases: {
                phase1: false,
                phase2: false,
                phase3: false,
                phase4: false,
            },
            report: {
                phase1: null,
                phase2: null,
                phase3_full: null,
                phase4: null,
            },
            loading: true,
            allDone: false,

            phases: [
                { key: 'phase1', label: 'Interview', status: 'pending' },   // pending / loading / done / error
                { key: 'phase2', label: 'Examination', status: 'pending' },
                { key: 'phase3', label: 'Diagnosis', status: 'pending' },
                { key: 'phase4', label: 'Treatment', status: 'pending' },
            ],

            phaseDetails: {
                phase1: 'Analyzing interview dialogue and extracting clinical signals...',
                phase2: 'Comparing selected examinations with standard plan...',
                phase3: 'Evaluating case writing quality and diagnostic reasoning...',
                phase4: 'Evaluating treatment plan quality and safety...',
            },

            retrying: false,
        };
    },

    computed: {
        Document() { return ElementPlusIconsVue.Document; },
        DataAnalysis() { return ElementPlusIconsVue.DataAnalysis; },
        Notebook() { return ElementPlusIconsVue.Notebook; },
        HomeFilled() { return ElementPlusIconsVue.HomeFilled; },

        diagnosisEval() {
            if (this.report.phase3_full && this.report.phase3_full.diagnosis) {
                return this.report.phase3_full.diagnosis;
            }
            return null;
        },

        phase3ClinicalNoteSubjective() {
            return this.report.phase3_full?.clinical_note_subjective || null;
        },

        phase3DiagnosticRigorSubjective() {
            return this.report.phase3_full?.diagnostic_rigor_subjective || null;
        },

        phase4TreatmentSubjective() {
            return this.report.phase4?.treatment_subjective || null;
        },

        professionEvaluationParsed() {
            return this.parseProfessionEvaluationV2(this.report.phase1?.profession_evaluation?.raw_response);
        },

        professionEvaluationItems() {
            return this.professionEvaluationParsed.items;
        },

        professionEvaluationSummary() {
            return this.professionEvaluationParsed.summary;
        },

        phase3OverallScore() {
            if (!this.report.phase3_full) {
                return null;
            }
            const score = this.report.phase3_full.overall_score;
            return score === null || score === undefined ? null : score;
        },

        phase3Narrative() {
            const writing = this.caseWritingEval;
            const diagnosis = this.diagnosisEval;
            if (!writing && !diagnosis) {
                return '';
            }

            const writingScore = writing?.total_score ?? 0;
            const diagnosisScore = diagnosis?.total_score ?? 0;
            const stronger = writingScore >= diagnosisScore ? 'Case writing' : 'Diagnostic judgment';
            const weaker = writingScore < diagnosisScore ? 'case writing' : 'diagnostic reasoning';
            return `${stronger} performed relatively more stably, while ${weaker} still has room for improvement. In the Phase 3 overall evaluation, case writing and diagnostic ability are weighted equally.`;
        },

        phase3CaseBasis() {
            const record = this.caseWritingEval?.true_record;
            if (!record) return [];
            const labelMap = {
                chief_complaint: 'Standard Chief Complaint',
                physical_examination: 'Standard Physical Examination',
                mental_examination: 'Standard Mental Status Examination',
                past_family_history: 'Standard Past History / Family History',
            };
            return Object.keys(record)
                .filter((key) => record[key])
                .map((key) => ({
                    label: labelMap[key] || key,
                    content: record[key],
                }));
        },

        phase3CaseReasoningCards() {
            const dimensions = this.caseWritingEval?.dimensions || {};
            return Object.values(dimensions)
                .map((section) => {
                    const reasoningItems = (section.scoring_results || [])
                        .map((result) => {
                            const element = result.element || 'Scoring Item';
                            const coverage = result.coverage_reasoning ? `Coverage: ${result.coverage_reasoning}` : '';
                            const accuracy = result.accuracy_reasoning ? `Accuracy: ${result.accuracy_reasoning}` : '';
                            return [element, coverage, accuracy].filter(Boolean).join('\uff1b');
                        })
                        .filter(Boolean);
                    const content = reasoningItems.length
                        ? reasoningItems.join('\\n\\n')
                        : (section.detail || '');
                    if (!content) return null;
                    return {
                        label: `${section.section_name} Scoring Reasoning`,
                        score: this.formatPhase3FivePointScore(section.score),
                        content,
                    };
                })
                .filter(Boolean);
        },

        phase3SubmittedCaseForm() {
            const phase3 = this.getPhase3StoredResult();
            return phase3?.caseForm || null;
        },

        phase3SubmittedDiagnosis() {
            const phase3 = this.getPhase3StoredResult();
            if (!phase3) return null;
            return {
                category: phase3.category,
                disease: phase3.disease,
                reason: phase3.reason,
                diagnoses: phase3.diagnoses,
            };
        },

        phase3SubmittedDiagnosisList() {
            const diagnosis = this.phase3SubmittedDiagnosis;
            if (!diagnosis) return [];
            const fromGroups = Array.isArray(diagnosis.diagnoses)
                ? diagnosis.diagnoses.flatMap((item) => Array.isArray(item?.diseases) ? item.diseases : [])
                : [];
            const merged = [...fromGroups, diagnosis.disease].filter(Boolean);
            return [...new Set(merged)];
        },

        phase3DoctorCaseBasis() {
            const caseForm = this.phase3SubmittedCaseForm;
            if (!caseForm) return [];
            const sections = [
                { label: 'Name', value: caseForm.name },
                { label: 'Age', value: caseForm.age },
                { label: 'Gender', value: caseForm.gender },
                { label: 'Chief Complaint', value: caseForm.chiefComplaint },
                { label: 'Family History', value: caseForm.familyHistory },
                { label: 'Past History', value: caseForm.pastHistory },
                { label: 'Physical Examination', value: caseForm.physicalExam },
                { label: 'Mental Status Exam', value: caseForm.mentalExam },
                { label: 'Auxiliary Examinations', value: caseForm.auxiliaryExam },
            ];
            return sections
                .map((item) => ({
                    label: item.label,
                    content: this.formatBasisContent(item.value),
                }))
                .filter((item) => item.content);
        },

        phase3CaseDimensionCards() {
            const dimensions = this.caseWritingEval?.dimensions || {};
            return Object.values(dimensions)
                .map((section) => {
                    if (!section) return null;
                    const coverage = section.coverage_percentage !== undefined
                        ? `Coverage: ${section.coverage_percentage.toFixed(0)}%`
                        : '';
                    const accuracy = section.accuracy_percentage !== undefined
                        ? `Accuracy: ${section.accuracy_percentage.toFixed(0)}%`
                        : '';
                    return {
                        label: section.section_name || 'Case Writing Dimension',
                        score: this.formatPhase3FivePointScore(section.score),
                        rawScore: section.score,
                        detail: section.detail || '',
                        subDetail: [coverage, accuracy].filter(Boolean).join(' | '),
                    };
                })
                .filter((item) => item && (item.detail || item.subDetail));
        },

        phase3DiagnosisCompare() {
            const diagnosis = this.diagnosisEval;
            if (!diagnosis) return [];
            const sections = [
                { label: 'True Diagnosis Category', value: diagnosis.disease_type?.true || this.caseInfo?.realCategory },
                { label: "Doctor's Submitted Diagnosis Category", value: diagnosis.disease_type?.predicted || this.phase3SubmittedDiagnosis?.category },
                { label: 'True Specific Diagnosis', value: diagnosis.diagnostic_correctness?.true || this.caseInfo?.realDisorder },
                { label: "Doctor's Specific Diagnosis", value: diagnosis.diagnostic_correctness?.predicted || this.phase3SubmittedDiagnosisList },
                { label: "Doctor's Diagnostic Reasoning", value: diagnosis.diagnostic_reasoning?.submitted_reason || this.phase3SubmittedDiagnosis?.reason },
            ];
            return sections
                .map((item) => ({
                    label: item.label,
                    content: this.formatBasisContent(item.value),
                }))
                .filter((item) => item.content);
        },

        phase3DiagnosisBasis() {
            return this.phase3DiagnosisCompare;
        },

        phase3DiagnosisReasoningCards() {
            const diagnosis = this.diagnosisEval;
            if (!diagnosis) return [];
            const cards = [
                {
                    label: 'Diagnostic Reasoning',
                    score: diagnosis.diagnostic_reasoning?.score !== undefined
                        ? this.formatPhase3FivePointScore(diagnosis.diagnostic_reasoning.score)
                        : '',
                    content: diagnosis.diagnostic_reasoning?.detail || '',
                },
                {
                    label: 'Comprehensive Judgment',
                    score: diagnosis.comprehensive?.score !== undefined
                        ? this.formatPhase3FivePointScore(diagnosis.comprehensive.score)
                        : '',
                    content: diagnosis.comprehensive?.detail || '',
                },
            ];
            return cards.filter((item) => item.content);
        },

        phase4OverallScore() {
            return this.phase4TreatmentSubjective?.score ?? null;
        },

        phase4Narrative() {
            const score = this.phase4OverallScore;
            if (score === null || score === undefined) {
                return '';
            }
            if (score >= 4) {
                return 'Treatment plan is relatively complete with strong overall suitability.';
            }
            if (score >= 3) {
                return 'Treatment plan has a basic framework, but some treatment details still need refinement.';
            }
            return 'Treatment plan coverage is still limited and needs key interventions based on diagnosis.';
        },

        caseWritingEval() {
            const phase3 = this.report.phase3_full;
            if (!phase3 || phase3._fallback) return null;
            if (phase3.case_writing) return phase3.case_writing;
            if (phase3.true_record || phase3.dimensions) {
                return {
                    true_record: phase3.true_record || {},
                    dimensions: phase3.dimensions || {},
                    total_score: phase3.total_actual_max ? (phase3.total_actual_score / phase3.total_actual_max) * 5 : 0,
                    total_percentage: phase3.total_percentage || 0,
                };
            }
            return null;
        },

        phase4PlanEntries() {
            const details = this.report.phase4?.treatment_stats?.details || {};
            return Object.entries(details)
                .filter(([, value]) => this.isPhase4MeaningfulValue(value))
                .map(([label, value]) => ({
                    label,
                    content: String(value).trim(),
                }));
        },

        phase4StandardPlanEntries() {
            const standard = this.report.phase4?.standard_treatment || [];
            return standard
                .filter((item) => item && String(item).trim())
                .map((item, index) => ({
                    label: `Standard Plan ${index + 1}`,
                    content: String(item).trim(),
                }));
        },

        phase4ReasoningCards() {
            const subjective = this.report.phase4?.treatment_subjective;
            if (!subjective) return [];
            const cards = [];
            if (subjective.score !== undefined && subjective.score !== null) {
                cards.push({
                    label: 'Total Score',
                    score: this.formatFivePointScore(subjective.score),
                    content: `Average score from 5 reviewers: ${this.formatFivePointScore(subjective.score)}.`,
                });
            }
            if (Array.isArray(subjective.scores) && subjective.scores.length) {
                cards.push({
                    label: 'Reviewer Scores',
                    score: '',
                    content: subjective.scores.join(' / '),
                });
            }
            const rawResponses = Array.isArray(subjective.raw_responses) && subjective.raw_responses.length
                ? subjective.raw_responses
                : Array.isArray(subjective.individual_results)
                    ? subjective.individual_results.map((item) => item?.raw_response).filter(Boolean)
                    : Array.isArray(subjective.analyses)
                        ? subjective.analyses.filter(Boolean)
                        : [];
            if (rawResponses.length) {
                rawResponses
                    .filter(Boolean)
                    .forEach((text, index) => {
                        cards.push({
                            label: `Reviewer ${index + 1}`,
                            score: '',
                            content: text,
                        });
                    });
            }
            return cards;
        },

        doctorExamList() {
            const selected = this.phase2ExamResults || {};
            const gold = this.caseInfo?.auxiliaryExamination || {};
            return Object.keys(selected).map((name) => {
                return {
                    name: this.translateExamLabel(name),
                    statusText: Object.prototype.hasOwnProperty.call(gold, name) ? 'Matches Standard' : 'Extra Examination',
                    statusClass: Object.prototype.hasOwnProperty.call(gold, name) ? 'eval-exam-pill--correct' : 'eval-exam-pill--wrong',
                };
            });
        },

        goldExamList() {
            const gold = this.caseInfo?.auxiliaryExamination || {};
            return Object.keys(gold).map((name) => {
                return {
                    name: this.translateExamLabel(name),
                    statusText: Object.prototype.hasOwnProperty.call(this.phase2ExamResults || {}, name) ? 'Completed' : 'Missing',
                    statusClass: Object.prototype.hasOwnProperty.call(this.phase2ExamResults || {}, name) ? 'eval-exam-pill--correct' : 'eval-exam-pill--missing',
                };
            });
        },

        currentPhaseLabel() {
            const loading = this.phases.find(p => p.status === 'loading');
            if (loading) return loading.label;
            const pending = this.phases.find(p => p.status === 'pending');
            if (pending) return pending.label;
            return 'Overall';
        },

        currentPhaseDetail() {
            const loading = this.phases.find((phase) => phase.status === 'loading');
            if (loading) {
                return this.phaseDetails[loading.key] || 'Preparing evaluation data...';
            }
            const pending = this.phases.find((phase) => phase.status === 'pending');
            if (pending) {
                return this.phaseDetails[pending.key] || 'Preparing evaluation data...';
            }
            return 'Generating final comprehensive evaluation report...';
        },

        allPhasesFailed() {
            return this.allDone && this.phases.every((phase) => phase.status === 'error');
        },
    },

    methods: {
        async startUnifiedEvaluation() {
            try {
                await this.evaluatePhase1();
                await this.evaluatePhase2();
                await this.evaluatePhase3();
                await this.evaluatePhase4();
            } catch (err) {
                console.error('[UnifiedEval] Unexpected error during unified evaluation:', err);
            } finally {
                this.allDone = true;
                await this.saveFinalRecord();
            }
        },

        async evaluatePhase1() {
            this.phases[0].status = 'loading';
            try {
                const messagesStr = sessionStorage.getItem('phase2_messages');
                if (messagesStr) {
                    const messages = JSON.parse(messagesStr);
                    this.report.phase1 = await this.withTimeout(
                        API.evaluatePhase(1, this.caseId, { messages }),
                        'Phase 1 evaluation'
                    );
                } else {
                    this.report.phase1 = { _fallback: true, error: 'Missing interview data' };
                }
                this.phases[0].status = 'done';
            } catch (err) {
                console.error('[UnifiedEval] Phase 1 evaluation generation failed:', err);
                this.report.phase1 = { _fallback: true, error: err.message };
                this.phases[0].status = 'error';
            }
        },

        async evaluatePhase2() {
            this.phases[1].status = 'loading';
            try {
                const phase2Results = JSON.parse(sessionStorage.getItem('phase2_checkedResults') || '{}');
                this.phase2ExamResults = phase2Results;
                this.report.phase2 = await this.withTimeout(
                    API.getPhase2Accuracy(this.caseId, phase2Results),
                    'Phase 2 evaluation'
                );
                this.phases[1].status = 'done';
            } catch (err) {
                console.error('[UnifiedEval] Phase 2 evaluation generation failed:', err);
                this.report.phase2 = { _fallback: true, error: err.message };
                this.phases[1].status = 'error';
            }
        },

        async evaluatePhase3() {
            this.phases[2].status = 'loading';
            try {
                const phase3Result = JSON.parse(sessionStorage.getItem('phase3_result') || '{}');
                if (phase3Result && phase3Result.caseForm) {
                    this.report.phase3_full = await this.withTimeout(
                        API.evaluatePhase(3, this.caseId, {
                            case_form: phase3Result.caseForm,
                            diagnosis: {
                                category: phase3Result.category,
                                disease: phase3Result.disease,
                                reason: phase3Result.reason,
                                diagnoses: phase3Result.diagnoses,
                            },
                        }),
                        'Phase 3 evaluation',
                        PHASE3_EVAL_TIMEOUT_MS
                    );
                    sessionStorage.setItem('phase3_evaluation', JSON.stringify(this.report.phase3_full));
                } else {
                    this.report.phase3_full = { _fallback: true, error: 'Missing diagnosis data' };
                }
                this.phases[2].status = 'done';
            } catch (err) {
                console.error('[UnifiedEval] Phase 3 evaluation generation failed:', err);
                this.report.phase3_full = { _fallback: true, error: err.message };
                this.phases[2].status = 'error';
            }
        },

        async evaluatePhase4() {
            this.phases[3].status = 'loading';
            try {
                const treatmentRecord = this.getPhase4TreatmentRecord();
                this.report.phase4 = await this.withTimeout(
                    API.evaluatePhase(4, this.caseId, { treatment: treatmentRecord }),
                    'Phase 4 evaluation',
                    PHASE4_EVAL_TIMEOUT_MS
                );
                this.phases[3].status = 'done';
            } catch (err) {
                console.error('[UnifiedEval] Phase 4 evaluation generation failed:', err);
                this.report.phase4 = { _fallback: true, error: err.message };
                this.phases[3].status = 'error';
            }
        },

        async saveFinalRecord() {
            const recordId = sessionStorage.getItem('record_id') || this.caseId;
            console.log('[UnifiedEval] Saving evaluation report for recordId:', recordId);
            try {
                let conversation = null;
                try {
                    const msgsStr = sessionStorage.getItem('phase2_messages');
                    if (msgsStr) conversation = JSON.parse(msgsStr);
                } catch (e) { /* ignore */ }

                let exams = null;
                try {
                    const examsStr = sessionStorage.getItem('phase2_checkedResults');
                    if (examsStr) {
                        const parsed = JSON.parse(examsStr);
                        exams = Object.entries(parsed).map(([name, result]) => ({ name, result }));
                    }
                } catch (e) { /* ignore */ }

                let caseForm = null, diagnosis = null;
                try {
                    const phase3Str = sessionStorage.getItem('phase3_result');
                    if (phase3Str) {
                        const p3 = JSON.parse(phase3Str);
                        if (p3.caseForm) caseForm = p3.caseForm;
                        diagnosis = {
                            category: p3.category,
                            disease: p3.disease,
                            reason: p3.reason,
                            diagnoses: p3.diagnoses,
                        };
                    }
                } catch (e) { /* ignore */ }

                const treatment = this.getPhase4TreatmentRecord();

                const payload = { evaluation_report: this.report };
                if (conversation) payload.conversation = conversation;
                if (exams) payload.exams = exams;
                if (caseForm) { payload.caseForm = caseForm; }
                if (diagnosis) payload.diagnosis = diagnosis;
                if (this.hasMeaningfulTreatmentContent(treatment)) payload.treatment = treatment;

                console.log('[UnifiedEval] Submitting evaluation payload keys:', Object.keys(payload));
                console.log('[UnifiedEval] evaluation_report keys:', this.report ? Object.keys(this.report) : 'null');

                const result = await API.saveCaseRecord(recordId, payload);
                console.log('[UnifiedEval] Evaluation save result:', recordId, result);
                this.$message.success('Evaluation report saved');
            } catch (err) {
                console.error('[UnifiedEval] Failed to save evaluation report:', err);
                this.$message.warning('Failed to save evaluation report: ' + err.message);
            }
            sessionStorage.setItem('unified_eval_report', JSON.stringify(this.report));
        },

        evalDiagMetricClass(value) {
            if (value === null || value === undefined) return 'diag-metric--none';
            if (value >= 0.8) return 'diag-metric--good';
            if (value >= 0.5) return 'diag-metric--mid';
            return 'diag-metric--low';
        },

        formatPercentage(section) {
            if (section.percentage !== undefined) return section.percentage.toFixed(0) + '%';
            if (section.score !== undefined) return (section.score * 100).toFixed(0) + '%';
            return '--';
        },

        formatAccuracy(value) {
            if (value == null) return '--';
            const n = Number(value);
            return Number.isNaN(n) ? '--' : (n * 100).toFixed(0) + '%';
        },

        formatScore(value) {
            if (value == null) return '--';
            const n = Number(value);
            return Number.isNaN(n) ? String(value) : n.toFixed(2);
        },

        formatFivePointScore(score) {
            if (score == null) return '--';
            const value = Number(score);
            return Number.isNaN(value) ? String(score) : `${value.toFixed(2)} / 5`;
        },

        isPhase4MeaningfulValue(value) {
            if (value == null) return false;
            const text = String(value).trim();
            if (!text) return false;
            const normalized = text.toLowerCase();
            return normalized !== 'none' && normalized !== 'null' && normalized !== 'undefined' && text !== '无';
        },

        hasMeaningfulTreatmentContent(record) {
            if (!record || typeof record !== 'object') return false;
            return Object.values(record).some((value) => this.isPhase4MeaningfulValue(value));
        },

        buildTreatmentRecordFromDraft(draft) {
            const source = draft && typeof draft === 'object' ? draft : {};
            return {
                'Pharmacotherapy': source.medication ? String(source.medication).trim() : null,
                'Psychotherapy': source.psychotherapy ? String(source.psychotherapy).trim() : null,
                'Neuromodulation & Somatic Therapy': source.neuromodulation ? String(source.neuromodulation).trim() : null,
                'Psychosocial Intervention & Rehabilitation': source.psychosocial ? String(source.psychosocial).trim() : null,
                'Adjuvant Therapy': source.adjuvant ? String(source.adjuvant).trim() : null,
            };
        },

        getPhase4TreatmentRecord() {
            let treatmentRecord = {};
            try {
                const phase4Str = sessionStorage.getItem('phase4_result');
                if (phase4Str) {
                    const parsed = JSON.parse(phase4Str);
                    treatmentRecord = parsed?.treatment || {};
                }
            } catch (err) {
                console.warn('[UnifiedEval] Failed to parse phase4_result:', err);
            }

            if (this.hasMeaningfulTreatmentContent(treatmentRecord)) {
                return treatmentRecord;
            }

            try {
                const draftStr = sessionStorage.getItem('phase4_treatment');
                if (draftStr) {
                    const draft = JSON.parse(draftStr);
                    const rebuiltRecord = this.buildTreatmentRecordFromDraft(draft);
                    if (this.hasMeaningfulTreatmentContent(rebuiltRecord)) {
                        return rebuiltRecord;
                    }
                }
            } catch (err) {
                console.warn('[UnifiedEval] Failed to parse phase4_treatment:', err);
            }

            return treatmentRecord;
        },

        formatPhase3FivePointScore(score) {
            if (score == null) return '--';
            const value = Number(score);
            if (Number.isNaN(value)) return String(score);
            const normalized = value <= 1 ? value * 5 : value;
            return `${normalized.toFixed(2)} / 5`;
        },

        hpBarStyle(score) {
            const pct = Math.min(100, Math.max(0, (score / 5) * 100));
            let color;
            if (pct <= 20) color = 'linear-gradient(90deg, #f56c6c, #f78989)';
            else if (pct <= 40) color = 'linear-gradient(90deg, #e6a23c, #f0c78a)';
            else if (pct <= 60) color = 'linear-gradient(90deg, #e6c13c, #f0d48a)';
            else if (pct <= 80) color = 'linear-gradient(90deg, #67c23a, #95d479)';
            else color = 'linear-gradient(90deg, #3ec4b0, #5ed6c8)';
            return { width: pct + '%', background: color };
        },

        goToPatients() {
            const keys = ['phase2_messages', 'phase2_checkedResults', 'phase3_result', 'phase3_evaluation', 'phase4_result', 'unified_eval_report'];
            keys.forEach(k => sessionStorage.removeItem(k));
            this.$router.push('/patients');
        },

        goToHistory() {
            this.$router.push('/history');
        },

        togglePhaseCollapse(phaseKey) {
            this.collapsedPhases[phaseKey] = !this.collapsedPhases[phaseKey];
        },

        isPhaseCollapsed(phaseKey) {
            return !!this.collapsedPhases[phaseKey];
        },

        scoreClass(score) {
            if (score == null || Number.isNaN(Number(score))) return 'score-neutral';
            const value = Number(score);
            if (value >= 4 || value >= 0.8) return 'score-excellent';
            if (value >= 3 || value >= 0.6) return 'score-good';
            if (value >= 2 || value >= 0.4) return 'score-mid';
            return 'score-low';
        },

        empathyLevelDisplay(level) {
            return this.formatFivePointScore(level);
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

        subjectiveMetaText(subjective) {
            if (!subjective) return '';
            const lines = [];
            if (Array.isArray(subjective.scores) && subjective.scores.length) {
                lines.push(`Reviewer Scores: ${subjective.scores.map((item) => item ?? '--').join(' / ')}`);
            }
            if (subjective.parsed_count !== undefined) {
                lines.push(`Parsed reviewer count: ${subjective.parsed_count}`);
            }
            if (subjective.evidence) {
                lines.push(subjective.evidence);
            }
            return lines.join('\n');
        },

        getPhase3StoredResult() {
            try {
                return JSON.parse(sessionStorage.getItem('phase3_result') || 'null');
            } catch (err) {
                console.warn('[UnifiedEval] Failed to parse phase3_result:', err);
                return null;
            }
        },

        parseProfessionEvaluationV2(raw) {
            if (!raw) {
                return { items: [], summary: '' };
            }
            return {
                items: [],
                summary: String(raw).trim(),
            };
        },

        formatProfessionVerification(verification) {
            if (!verification) return '';
            if (typeof verification === 'string') return verification;
            if (Array.isArray(verification)) return verification.filter(Boolean).join('\n');
            if (typeof verification === 'object') {
                return Object.entries(verification)
                    .map(([key, value]) => `- ${key}: ${typeof value === 'object' ? JSON.stringify(value) : value}`)
                    .join('\n');
            }
            return String(verification);
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
                return window.marked.parse(text, EVAL_MARKDOWN_OPTIONS);
            }
            return this.escapeHtml(text).replace(/\n/g, '<br>');
        },

        async loadCaseInfo() {
            try {
                this.caseInfo = await API.getCaseInfo(this.caseId);
            } catch (err) {
                console.warn('[UnifiedEval] Failed to restore saved evaluation data:', err);
                this.caseInfo = null;
            }
        },

        withTimeout(promise, label, timeoutMs = EVAL_REQUEST_TIMEOUT_MS) {
            return Promise.race([
                promise,
                new Promise((_, reject) => {
                    window.setTimeout(() => {
                        reject(new Error(`${label} timed out after ${Math.floor(timeoutMs / 1000)} seconds`));
                    }, timeoutMs);
                }),
            ]);
        },

        formatBasisContent(value) {
            if (!value) return '';
            if (Array.isArray(value)) {
                return value
                    .filter(Boolean)
                    .map((item) => this.translateDiagnosisCategoryLabel(item))
                    .join('; ');
            }
            if (typeof value === 'object') return JSON.stringify(value);
            return this.translateDiagnosisCategoryLabel(String(value).trim());
        },

        translateDiagnosisCategoryLabel(value) {
            if (!value) return '';
            return DIAGNOSIS_CATEGORY_LABELS[value] || value;
        },

        translateExamLabel(value) {
            if (!value) return '';
            const text = String(value).trim();
            const map = {
                '心电图': 'Electrocardiogram (ECG)',
                '脑电图': 'Electroencephalogram (EEG)',
                '头颅CT': 'Head CT',
                '头部CT': 'Head CT',
                '颅脑CT': 'Head CT',
                '头颅MRI': 'Head MRI',
                '头颅 MRI': 'Head MRI',
                '头部MRI': 'Head MRI',
                '头部 MRI': 'Head MRI',
                '颅脑MRI': 'Head MRI',
                '颅脑 MRI': 'Head MRI',
                '胸部CT': 'Chest CT',
                '胸片': 'Chest X-ray',
                '胸部X线': 'Chest X-ray',
                'X片': 'X-ray',
                '下颌骨片': 'Mandible X-ray',
                '血常规': 'Complete Blood Count',
                '尿常规': 'Urinalysis',
                '肝功能': 'Liver Function Test',
                '肾功能': 'Renal Function Test',
                '甲状腺功能': 'Thyroid Function Test',
                '甲状腺功能检查': 'Thyroid Function Test',
                '甲功': 'Thyroid Function Test',
                '血糖': 'Blood Glucose',
                '血脂': 'Lipid Panel',
                '电解质': 'Electrolyte Panel',
                '心肌酶': 'Cardiac Enzymes',
                '心脏彩超': 'Echocardiogram',
                '腹部彩超': 'Abdominal Ultrasound',
                'B超': 'Ultrasound',
                '毒品筛查': 'Drug Screen',
                '妊娠试验': 'Pregnancy Test',
                '梅毒筛查': 'Syphilis Screening',
                '梅毒血清学': 'Syphilis Serology',
                '乙肝两对半': 'Hepatitis B Panel',
                '维生素B12': 'Vitamin B12',
                '维生素 B12': 'Vitamin B12',
                '卡马西平血药浓度': 'Carbamazepine Blood Level',
                '丙戊酸钠血药浓度': 'Valproate Blood Level',
            };
            return map[text] || text;
        },

        init() {
            const phase4Result = JSON.parse(sessionStorage.getItem('phase4_result') || 'null');
            this.caseId =
                this.$route.query.id ||
                phase4Result?.caseId ||
                sessionStorage.getItem('final_case_id') ||
                sessionStorage.getItem('phase2_caseId') ||
                '';
            if (!this.caseId) {
                this.$message.warning('Case information not found');
                this.phases.forEach((phase) => { phase.status = 'error'; });
                this.allDone = true;
                this.loading = false;
                return;
            }

            this.loading = false;
            this.startUnifiedEvaluation();
        },
    },

    async mounted() {
        this.init();
        if (this.caseId) {
            await this.loadCaseInfo();
        }
    },
};
