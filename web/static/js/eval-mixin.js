/**
 * 阶段评价混入
 * 为所有需要评价的阶段提供统一的状态机和方法
 *
 * 状态流转:
 *   idle -> loading -> showing -> done -> (外部跳转下一阶段)
 *
 * 使用方式:
 *   mixins: [EvalMixin]
 *
 * 组件必须实现:
 *   - getEvalPayload(): 返回该阶段的评价请求参数
 *   - getPhaseNumber(): 返回阶段编号
 *   - getCaseId(): 返回当前病例 ID
 *   - onEvalConfirmed(): 用户确认后执行的下一阶段跳转
 */
const EvalMixin = {
    data() {
        return {
            // 评价状态: 'idle' | 'loading' | 'showing' | 'done'
            evalState: 'idle',
            evalData: {},
            evalError: null,
        };
    },

    methods: {
        /**
         * 启动评价流程
         * 由组件的"结束阶段"按钮调用
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

                console.log(`[EvalMixin] 开始评价 Phase ${phase}, caseId=${caseId}`, payload);

                this.evalData = await API.evaluatePhase(phase, caseId, payload);
                console.log(`[EvalMixin] 评价结果:`, this.evalData);

                this.evalState = 'showing';
            } catch (err) {
                console.error(`[EvalMixin] 评价失败:`, err);
                this.evalError = err.message || '未知错误';

                // 即使失败也展示面板，附带基础统计
                this.evalData = this.getFallbackEvalData();
                this.evalState = 'showing';
            }
        },

        /**
         * 用户点击"进入下一阶段"
         */
        confirmAndProceed() {
            if (this.evalState !== 'showing' && this.evalState !== 'done') return;
            this.evalState = 'done';
            this.onEvalConfirmed();
        },

        /**
         * 重置评价状态
         */
        resetEvaluation() {
            this.evalState = 'idle';
            this.evalData = {};
            this.evalError = null;
        },

        // ---- 以下方法由组件实现 ----

        getPhaseNumber() {
            throw new Error('组件必须实现 getPhaseNumber()');
        },

        getCaseId() {
            throw new Error('组件必须实现 getCaseId()');
        },

        getEvalPayload() {
            throw new Error('组件必须实现 getEvalPayload()');
        },

        getFallbackEvalData() {
            return {
                phase: this.getPhaseNumber(),
                case_id: this.getCaseId(),
                _fallback: true,
            };
        },

        onEvalConfirmed() {
            throw new Error('组件必须实现 onEvalConfirmed()');
        },
    },
};
