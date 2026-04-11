/**
 * PhaseView 组件
 * 单个阶段的展示框架 - 加载阶段数据和评估结果
 * 各阶段的具体展示内容由用户后续填充
 */
const PhaseView = {
    props: {
        caseId: { type: String, required: true },
        model: { type: String, required: true },
        phase: { type: Number, required: true },
    },

    template: `
        <div class="phase-view">
            <el-row :gutter="20" v-if="phaseData">
                <!-- 左侧: 阶段输出 -->
                <el-col :span="12">
                    <el-card shadow="never">
                        <template #header>
                            <span style="font-weight:600;">{{ phaseTitle }}</span>
                        </template>

                        <!-- Phase 1: 对话 -->
                        <div v-if="phase === 1">
                            <div class="conversation-scroll">
                                <div v-for="(msg, idx) in conversation" :key="idx"
                                     class="conversation-item" :class="msg.role">
                                    <div class="conversation-item__role">
                                        {{ roleLabel(msg.role) }}
                                    </div>
                                    <div class="conversation-item__content">
                                        {{ msg.content }}
                                    </div>
                                    <div class="conversation-item__time">
                                        {{ msg.timestamp || '' }}
                                    </div>
                                </div>
                            </div>
                            <el-divider />
                            <div style="font-size:13px;color:#909399;">
                                总轮数: {{ conversationStats.totalTurns }} |
                                医生: {{ conversationStats.doctorTurns }} |
                                患者: {{ conversationStats.patientTurns }}
                            </div>
                        </div>

                        <!-- Phase 2: 检查推荐 -->
                        <div v-else-if="phase === 2">
                            <el-table :data="examinationTable" stripe border size="small">
                                <el-table-column prop="name" label="检查项目" />
                                <el-table-column prop="requested" label="医生请求" width="80" align="center">
                                    <template #default="{ row }">
                                        <el-tag :type="row.requested ? 'success' : 'info'" size="small">
                                            {{ row.requested ? '是' : '否' }}
                                        </el-tag>
                                    </template>
                                </el-table-column>
                                <el-table-column prop="result" label="结果" />
                            </el-table>
                        </div>

                        <!-- Phase 3: 临床病历 -->
                        <div v-else-if="phase === 3">
                            <div v-if="interviewData?.syntactic_formulation" style="white-space:pre-wrap;line-height:1.8;">
                                {{ interviewData.syntactic_formulation }}
                            </div>
                            <div v-else class="placeholder">
                                <div class="placeholder__icon">📋</div>
                                <div class="placeholder__text">暂无临床病历</div>
                            </div>
                        </div>

                        <!-- Phase 4: 诊断类别 -->
                        <div v-else-if="phase === 4">
                            <div v-if="interviewData?.diagnostic_categories">
                                <el-tag v-for="(cat, idx) in interviewData.diagnostic_categories"
                                        :key="idx" type="primary" class="diagnosis-tag">
                                    {{ cat }}
                                </el-tag>
                            </div>
                            <div v-else class="placeholder">
                                <div class="placeholder__icon">🏷️</div>
                                <div class="placeholder__text">暂无诊断类别</div>
                            </div>
                        </div>

                        <!-- Phase 5: 诊断假设 -->
                        <div v-else-if="phase === 5">
                            <el-timeline v-if="interviewData?.diagnostic_hypotheses">
                                <el-timeline-item v-for="(h, idx) in interviewData.diagnostic_hypotheses"
                                                  :key="idx"
                                                  :type="isCorrectDiagnosis(h) ? 'success' : 'warning'">
                                    <strong>{{ h }}</strong>
                                    <el-tag size="small" :type="isCorrectDiagnosis(h) ? 'success' : 'danger'"
                                          style="margin-left:8px;">
                                        {{ isCorrectDiagnosis(h) ? '命中' : '未命中' }}
                                    </el-tag>
                                </el-timeline-item>
                            </el-timeline>
                            <div v-else class="placeholder">
                                <div class="placeholder__icon">💡</div>
                                <div class="placeholder__text">暂无诊断假设</div>
                            </div>
                        </div>

                        <!-- Phase 6: 鉴别诊断 -->
                        <div v-else-if="phase === 6">
                            <el-timeline v-if="interviewData?.differential_diagnosis">
                                <el-timeline-item v-for="(d, idx) in interviewData.differential_diagnosis"
                                                  :key="idx"
                                                  type="primary"
                                                  :hollow="!isCorrectDiagnosis(d)">
                                    <strong>{{ d }}</strong>
                                    <el-tag size="small" :type="isCorrectDiagnosis(d) ? 'success' : 'danger'"
                                          style="margin-left:8px;">
                                        {{ isCorrectDiagnosis(d) ? '命中' : '未命中' }}
                                    </el-tag>
                                </el-timeline-item>
                            </el-timeline>
                            <div v-else class="placeholder">
                                <div class="placeholder__icon">🔬</div>
                                <div class="placeholder__text">暂无最终诊断</div>
                            </div>
                        </div>
                    </el-card>
                </el-col>

                <!-- 右侧: 评估结果 -->
                <el-col :span="12">
                    <el-card shadow="never">
                        <template #header>
                            <span style="font-weight:600;">评估结果</span>
                        </template>

                        <div v-if="evaluationData">
                            <!-- Phase 1 评估 -->
                            <div v-if="phase === 1">
                                <el-descriptions :column="2" border size="small">
                                    <el-descriptions-item label="主诉覆盖率">
                                        {{ evalData?.coverage_stats?.chief_complaint_coverage || 0 }}%
                                    </el-descriptions-item>
                                    <el-descriptions-item label="精神状态覆盖率">
                                        {{ evalData?.coverage_stats?.mental_status_coverage || 0 }}%
                                    </el-descriptions-item>
                                    <el-descriptions-item label="整体覆盖率">
                                        {{ evalData?.coverage_stats?.overall_coverage || 0 }}%
                                    </el-descriptions-item>
                                    <el-descriptions-item label="对话轮数">
                                        {{ evalData?.conversation_stats?.total_turns || 0 }}
                                    </el-descriptions-item>
                                </el-descriptions>
                                <!-- 占位: 共情度/专业度评估 -->
                                <div class="placeholder" style="margin-top:16px;">
                                    <div class="placeholder__text">共情度与专业度评估内容待填充</div>
                                </div>
                            </div>

                            <!-- Phase 2 评估 -->
                            <div v-else-if="phase === 2">
                                <el-row :gutter="12">
                                    <el-col :span="6" v-for="(val, key) in evalData?.metrics" :key="key">
                                        <div class="metric-card">
                                            <div class="metric-card__value">{{ (val * 100).toFixed(1) }}%</div>
                                            <div class="metric-card__label">{{ key }}</div>
                                        </div>
                                    </el-col>
                                </el-row>
                                <el-divider />
                                <el-descriptions :column="2" border size="small">
                                    <el-descriptions-item label="预测数">{{ evalData?.counts?.predicted_count }}</el-descriptions-item>
                                    <el-descriptions-item label="Gold数">{{ evalData?.counts?.gold_count }}</el-descriptions-item>
                                    <el-descriptions-item label="TP">{{ evalData?.counts?.tp }}</el-descriptions-item>
                                    <el-descriptions-item label="FP">{{ evalData?.counts?.fp }}</el-descriptions-item>
                                    <el-descriptions-item label="FN">{{ evalData?.counts?.fn }}</el-descriptions-item>
                                    <el-descriptions-item label="NONE">{{ evalData?.counts?.none_count }}</el-descriptions-item>
                                </el-descriptions>
                            </div>

                            <!-- Phase 3 评估 -->
                            <div v-else-if="phase === 3">
                                <div style="text-align:center;margin-bottom:16px;">
                                    <div style="font-size:36px;font-weight:700;color:#409EFF;">
                                        {{ evalData?.total_percentage || 0 }}%
                                    </div>
                                    <div style="color:#909399;">总分</div>
                                </div>
                                <div v-for="(dim, name) in evalData?.dimensions" :key="name"
                                     style="margin-bottom:12px;">
                                    <div style="display:flex;justify-content:space-between;font-size:13px;margin-bottom:4px;">
                                        <span>{{ dimensionLabel(name) }}</span>
                                        <span>{{ dim.percentage || 0 }}%</span>
                                    </div>
                                    <el-progress :percentage="dim.percentage || 0" :stroke-width="14" />
                                </div>
                            </div>

                            <!-- Phase 4-6 评估 -->
                            <div v-else>
                                <el-row :gutter="12">
                                    <el-col :span="6" v-for="(val, key) in evalData?.metrics || evalData?.set_metrics" :key="key">
                                        <div class="metric-card">
                                            <div class="metric-card__value">{{ (val * 100).toFixed(1) }}%</div>
                                            <div class="metric-card__label">{{ key }}</div>
                                        </div>
                                    </el-col>
                                </el-row>
                                <div v-if="evalData?.primary_metrics" style="margin-top:16px;">
                                    <el-divider content-position="left">主诊断排序</el-divider>
                                    <el-descriptions :column="3" border size="small">
                                        <el-descriptions-item label="Exact Match">{{ evalData.primary_metrics.primary_exact_match }}</el-descriptions-item>
                                        <el-descriptions-item label="Hit@3">{{ evalData.primary_metrics.primary_hit_at_k }}</el-descriptions-item>
                                        <el-descriptions-item label="Recip Rank">{{ evalData.primary_metrics.primary_reciprocal_rank?.toFixed(4) }}</el-descriptions-item>
                                    </el-descriptions>
                                </div>
                                <div v-if="evalData?.ranking_metrics" style="margin-top:16px;">
                                    <el-divider content-position="left">排序一致性</el-divider>
                                    <el-descriptions :column="2" border size="small">
                                        <el-descriptions-item label="POA">{{ evalData.ranking_metrics.poa ?? 'N/A' }}</el-descriptions-item>
                                        <el-descriptions-item label="nDCG">{{ evalData.ranking_metrics.ndcg?.toFixed(4) }}</el-descriptions-item>
                                    </el-descriptions>
                                </div>
                                <!-- 预测 vs 真实 -->
                                <div style="margin-top:16px;">
                                    <el-divider content-position="left">预测 vs 真实</el-divider>
                                    <div style="font-size:13px;margin-bottom:6px;">预测:</div>
                                    <el-tag v-for="(p, i) in evalData?.predicted_categories || evalData?.predicted_hypotheses || evalData?.predicted_diagnoses"
                                            :key="'p'+i" class="diagnosis-tag"
                                            :type="isCorrectDiagnosis(p) ? 'success' : 'danger'">
                                        {{ p }}
                                    </el-tag>
                                    <div style="font-size:13px;margin:8px 0 6px;">真实:</div>
                                    <el-tag v-for="(t, i) in evalData?.true_categories || evalData?.true_disorders || []"
                                            :key="'t'+i" class="diagnosis-tag" type="info">
                                        {{ t }}
                                    </el-tag>
                                </div>
                            </div>
                        </div>

                        <!-- 无评估数据 -->
                        <div v-else class="placeholder">
                            <div class="placeholder__icon">📊</div>
                            <div class="placeholder__text">暂无评估数据</div>
                        </div>
                    </el-card>
                </el-col>
            </el-row>

            <!-- 加载/错误状态 -->
            <el-skeleton :rows="10" animated v-if="loading" />
            <el-empty v-if="error" :description="error" />
        </div>
    `,

    data() {
        return {
            phaseData: null,
            loading: false,
            error: null,
            groundTruth: null,
        };
    },

    computed: {
        phaseTitle() {
            const titles = {
                1: "病史采集",
                2: "检查推荐",
                3: "临床病历",
                4: "诊断类别",
                5: "诊断假设",
                6: "鉴别诊断",
            };
            return titles[this.phase] || `阶段 ${this.phase}`;
        },

        interviewData() {
            return this.phaseData?.interview;
        },

        evaluationData() {
            return this.phaseData?.evaluation;
        },

        evalData() {
            return this.evaluationData;
        },

        conversation() {
            return this.interviewData?.conversation || [];
        },

        conversationStats() {
            const conv = this.conversation;
            return {
                totalTurns: conv.filter(c => c.role === "patient").length,
                doctorTurns: conv.filter(c => c.role === "doctor").length,
                patientTurns: conv.filter(c => c.role === "patient").length,
            };
        },

        examinationTable() {
            const interview = this.interviewData;
            if (!interview) return [];
            const requested = new Set(interview.examinations || []);
            const results = interview.examination_results || {};

            // 合并所有检查项
            const allItems = new Set([
                ...Object.keys(results),
                ...Object.keys(requested),
            ]);

            return [...allItems].map(name => ({
                name,
                requested: requested.has(name),
                result: results[name] || "无结果",
            }));
        },
    },

    methods: {
        roleLabel(role) {
            const labels = { doctor: "医生", patient: "患者", system: "系统" };
            return labels[role] || role;
        },

        dimensionLabel(name) {
            const labels = {
                chief_complaint: "主诉",
                physical_examination: "体格检查",
                mental_examination: "精神检查",
                past_family_history: "既往史/家族史",
            };
            return labels[name] || name;
        },

        isCorrectDiagnosis(diagnosis) {
            if (!this.groundTruth?.realDisorder) return false;
            return this.groundTruth.realDisorder.includes(diagnosis);
        },

        async loadData() {
            this.loading = true;
            this.error = null;
            try {
                this.phaseData = await API.getPhase(this.caseId, this.phase, this.model);
                // 加载 ground truth 用于诊断命中判断
                try {
                    this.groundTruth = await API.getGroundTruth(this.caseId);
                } catch {
                    this.groundTruth = null;
                }
            } catch (err) {
                this.error = err.message;
            } finally {
                this.loading = false;
            }
        },
    },

    watch: {
        // phase 变化时重新加载
        phase() {
            this.loadData();
        },
    },

    mounted() {
        this.loadData();
    },
};
