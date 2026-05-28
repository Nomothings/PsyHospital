/**
 * Phase Evaluation Mixin
 * Provides a unified state machine and methods for all phases that require evaluation
 *
 * State transitions:
 *   idle -> loading -> showing -> done -> (external navigation to next phase)
 *
 * Usage:
 *   mixins: [EvalMixin]
 *
 * Components must implement:
 *   - getEvalPayload(): returns the evaluation request parameters for the phase
 *   - getPhaseNumber(): returns the phase number
 *   - getCaseId(): returns the current case ID
 *   - onEvalConfirmed(): executes navigation to the next phase after user confirmation
 */
const EvalMixin = {
    data() {
        return {
            // Evaluation state: 'idle' | 'loading' | 'showing' | 'done'
            evalState: 'idle',
            evalData: {},
            evalError: null,
        };
    },

    methods: {
        /**
         * Start the evaluation process
         * Called by the component's "End Phase" button
         */
        async startEvaluation() {
            if (this.evalState !== 'idle') return;

            this.evalState = 'loading';
            this.evalError = null;
            this.evalData = {};

            try {
                const phase = this.getPhaseNumber();
                const caseId = this.getCaseId();
                const payload = this.getEvalPayload();

                console.log(`[EvalMixin] Starting evaluation for Phase ${phase}, caseId=${caseId}`, payload);

                this.evalData = await API.evaluatePhase(phase, caseId, payload);
                console.log(`[EvalMixin] Evaluation result:`, this.evalData);

                this.evalState = 'showing';
            } catch (err) {
                console.error(`[EvalMixin] Evaluation failed:`, err);
                this.evalError = err.message || 'Unknown error';

                // Show panel even on failure, with basic statistics
                this.evalData = this.getFallbackEvalData();
                this.evalState = 'showing';
            }
        },

        /**
         * User clicks "Proceed to Next Phase"
         */
        confirmAndProceed() {
            if (this.evalState !== 'showing' && this.evalState !== 'done') return;
            this.evalState = 'done';
            this.onEvalConfirmed();
        },

        /**
         * Reset evaluation state
         */
        resetEvaluation() {
            this.evalState = 'idle';
            this.evalData = {};
            this.evalError = null;
        },

        // ---- The following methods must be implemented by the component ----

        getPhaseNumber() {
            throw new Error('Component must implement getPhaseNumber()');
        },

        getCaseId() {
            throw new Error('Component must implement getCaseId()');
        },

        getEvalPayload() {
            throw new Error('Component must implement getEvalPayload()');
        },

        getFallbackEvalData() {
            return {
                phase: this.getPhaseNumber(),
                case_id: this.getCaseId(),
                _fallback: true,
            };
        },

        onEvalConfirmed() {
            throw new Error('Component must implement onEvalConfirmed()');
        },
    },
};
