/**
 * Phase2Check 组件
 * Phase 2 — 辅助检查（选择 + 提交）
 *
 * 居中单面板：选择检查项目 → tag 展示 → 提交检查
 * 不展示任何检查结果，结果延迟到最终评价阶段
 */
const Phase2Check = {
    template: `
        <div class="phase2-page">
            <!-- 背景图 -->
            <div class="phase2-page__bg"></div>

            <!-- 顶部栏 -->
            <header class="phase2-header">
                <div class="phase2-header__left">
                    <el-button text @click="goBack" class="phase2-header__back-btn">
                        <el-icon><ArrowLeft /></el-icon>
                        返回
                    </el-button>
                    <h3 class="phase2-header__title">辅助检查</h3>
                    <span class="phase2-header__subtitle">第二阶段</span>
                </div>
                <div class="phase2-header__right">
                    <span class="phase2-header__patient">
                        患者 {{ caseId }}
                    </span>
                    <el-button
                        v-if="step === 'results'"
                        type="primary"
                        size="small"
                        round
                        @click="goToNextPhase"
                        class="phase2-header__next-btn"
                    >
                        进行病历书写
                    </el-button>
                </div>
            </header>

            <!-- 主内容区（居中单面板） -->
            <div class="phase2-content">
                <!-- 步骤1: 选择检查项目 -->
                <div v-if="step === 'selecting'" class="phase2-form-card">
                    <div class="phase2-form-card__header">
                        <h2 class="phase2-form-card__title">选择辅助检查项目</h2>
                        <p class="phase2-form-card__subtitle">
                            请根据问诊情况，选择需要进行的辅助检查
                        </p>
                    </div>

                    <!-- 检查选择器 -->
                    <div class="phase2-selector" ref="selectorRef">
                        <label class="phase2-selector__label">检查项目</label>

                        <!-- 标签容器 -->
                        <div class="phase2-selector__input" @click.self="openDropdown">
                            <!-- 已选标签 -->
                            <transition-group name="phase2-tag" tag="div" class="phase2-selector__tags">
                                <div
                                    v-for="exam in selectedExams"
                                    :key="exam"
                                    class="phase2-tag"
                                >
                                    <span class="phase2-tag__text">{{ exam }}</span>
                                    <span class="phase2-tag__delete" @click.stop="removeExam(exam)" title="删除">
                                        <el-icon :size="12"><Close /></el-icon>
                                    </span>
                                </div>
                            </transition-group>

                            <!-- 添加按钮 -->
                            <div class="phase2-tag phase2-tag--add" @click.stop="openDropdown">
                                <el-icon :size="14" class="phase2-tag__add-icon"><Plus /></el-icon>
                                <span>添加检查</span>
                            </div>

                            <!-- 空状态提示 -->
                            <div v-if="selectedExams.length === 0" class="phase2-selector__placeholder">
                                点击「添加检查」选择辅助检查项目
                            </div>

                            <!-- 下拉面板 -->
                            <div v-show="dropdownVisible" class="phase2-dropdown" @click.stop>
                                <div class="phase2-dropdown__body">
                                    <!-- 左侧：分类列表 -->
                                    <div class="phase2-dropdown__categories">
                                        <div class="phase2-dropdown__section-title">检查分类</div>
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
                                    <!-- 右侧：具体项目 -->
                                    <div class="phase2-dropdown__exams">
                                        <div v-if="!activeCategory" class="phase2-dropdown__empty">
                                            请先在左侧选择一个检查分类
                                        </div>
                                        <template v-else-if="activeCategory === '其他'">
                                            <div class="phase2-dropdown__section-title">
                                                自定义检查项目
                                            </div>
                                            <div class="phase2-custom-input">
                                                <input
                                                    v-model="customExamInput"
                                                    class="phase2-custom-input__field"
                                                    placeholder="输入自定义检查项目，按回车添加"
                                                    @keyup.enter="addCustomExam"
                                                />
                                                <el-button
                                                    size="small"
                                                    round
                                                    @click="addCustomExam"
                                                    class="phase2-custom-input__btn"
                                                >
                                                    添加
                                                </el-button>
                                            </div>
                                            <!-- 已添加的自定义项目 -->
                                            <div
                                                v-for="exam in customExams"
                                                :key="exam"
                                                class="phase2-dropdown__exam-item"
                                                :class="{
                                                    'phase2-dropdown__exam-item--selected': selectedExams.includes(exam),
                                                }"
                                                @click="toggleExam(exam)"
                                            >
                                                <span class="phase2-dropdown__exam-item__text">{{ exam }}</span>
                                                <el-icon v-if="selectedExams.includes(exam)" :size="14" color="#5ed6c8"><Check /></el-icon>
                                            </div>
                                            <div v-if="customExams.length === 0" class="phase2-dropdown__empty">
                                                还没有自定义项目，请在上方输入
                                            </div>
                                        </template>
                                        <template v-else>
                                            <div class="phase2-dropdown__section-title">
                                                {{ activeCategory }} — 检查项目
                                            </div>
                                            <div
                                                v-for="exam in getExamsForCategory(activeCategory)"
                                                :key="exam"
                                                class="phase2-dropdown__exam-item"
                                                :class="{
                                                    'phase2-dropdown__exam-item--selected': selectedExams.includes(exam),
                                                }"
                                                @click="toggleExam(exam)"
                                            >
                                                <span class="phase2-dropdown__exam-item__text">{{ exam }}</span>
                                                <el-icon v-if="selectedExams.includes(exam)" :size="14" color="#5ed6c8"><Check /></el-icon>
                                            </div>
                                        </template>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- 提交按钮 -->
                    <div class="phase2-form__actions">
                        <el-button
                            type="primary"
                            size="large"
                            round
                            @click="handleSubmit"
                            :loading="submitting"
                            :disabled="selectedExams.length === 0"
                            class="phase2-form__submit-btn"
                        >
                            提交检查
                        </el-button>
                    </div>
                </div>

                <!-- 步骤2: 过场动画 -->
                <div v-if="step === 'loading'" class="phase2-form-card phase2-form-card--center-text">
                    <div class="phase2-loading-animation">
                        <img src="/static/bg/mentaleval.png" alt="" class="phase2-loading-animation__icon" />
                        <div class="phase2-loading-animation__title">正在返回结果</div>
                        <div class="phase2-loading-animation__dots">
                            <span class="phase2-loading-animation__dot" :style="{ animationDelay: '0s' }"></span>
                            <span class="phase2-loading-animation__dot" :style="{ animationDelay: '0.2s' }"></span>
                            <span class="phase2-loading-animation__dot" :style="{ animationDelay: '0.4s' }"></span>
                        </div>
                    </div>
                </div>

                <!-- 步骤3: 展示结果 -->
                <div v-if="step === 'results'" class="phase2-form-card phase2-form-card--results">
                    <div class="phase2-form-card__header">
                        <h2 class="phase2-form-card__title">辅助检查结果</h2>
                        <p class="phase2-form-card__subtitle">
                            以下是您选择的辅助检查返回结果
                        </p>
                    </div>

                    <!-- 检查结果列表 -->
                    <div class="phase2-results-list">
                        <div
                            v-for="(result, exam) in checkedResults"
                            :key="exam"
                            class="phase2-result-item"
                            :class="result === '无' ? 'phase2-result-item--none' : 'phase2-result-item--has'"
                        >
                            <div class="phase2-result-item__header">
                                <span class="phase2-result-item__name">{{ exam }}</span>
                                <el-tag
                                    :type="result === '无' ? 'info' : 'success'"
                                    size="small"
                                    class="phase2-result-item__tag"
                                >
                                    {{ result === '无' ? '无异常' : '有异常' }}
                                </el-tag>
                            </div>
                            <div v-if="result !== '无'" class="phase2-result-item__content">
                                {{ result }}
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- 保存状态提示 -->
            <transition name="eval-fade">
                <div v-if="saving" class="eval-overlay">
                    <div class="eval-overlay__content">
                        <img src="/static/bg/eval.png" alt="" class="eval-overlay__icon" />
                        <div class="eval-overlay__text">正在提交检查请求...</div>
                    </div>
                </div>
            </transition>
        </div>
    `,

    data() {
        return {
            caseId: '',
            step: 'selecting',          // 'selecting' | 'loading' | 'results'
            selectedExams: [],
            checkedResults: {},
            dropdownVisible: false,
            activeCategory: '',
            customExamInput: '',
            customExams: [],
            submitting: false,
            saving: false,
            examCategories: [
                "实验室检查",
                "影像学检查",
                "内镜检查",
                "病理与细胞学检查",
                "功能检查/生理检查",
                "遗传与分子检测",
                "其他",
            ],
            examMapping: {
                "实验室检查": [
                    "血常规", "凝血功能", "血糖", "肝功能", "肾功能", "血脂", "电解质",
                    "心肌酶", "炎症指标", "激素水平", "尿常规", "尿蛋白定量", "尿沉渣",
                    "尿培养", "粪常规", "隐血试验", "寄生虫检查", "病原学检测",
                    "脑脊液检查", "胸水检查", "腹水检查", "关节液检查", "细菌培养",
                    "真菌培养", "药敏试验", "病毒抗体检测", "核酸检测", "自身抗体",
                    "免疫球蛋白", "补体", "过敏原检测", "肿瘤标志物",
                ],
                "影像学检查": [
                    "胸片", "骨关节X线", "消化道造影", "腹部超声", "泌尿系超声",
                    "甲状腺超声", "乳腺超声", "超声心动图", "血管超声", "头颅CT",
                    "胸部CT", "腹部CT", "增强CT", "CTA", "头颅MRI", "脊柱MRI",
                    "关节MRI", "增强MRI", "MRA", "PET-CT", "骨扫描", "甲状腺核素显像",
                    "心肌灌注显像", "冠脉CTA", "DSA", "其他造影检查",
                ],
                "内镜检查": [
                    "胃镜", "肠镜", "十二指肠镜", "胶囊内镜", "支气管镜", "膀胱镜",
                    "输尿管镜", "宫腔镜", "膝关节镜", "肩关节镜", "腹腔镜", "胸腔镜",
                ],
                "病理与细胞学检查": [
                    "胃黏膜活检", "肝穿刺活检", "肺穿刺活检", "淋巴结活检",
                    "术中冰冻病理", "宫颈涂片", "痰细胞学", "胸腹水细胞学",
                    "细针穿刺细胞学", "肿瘤相关基因突变", "融合基因", "免疫组化相关检测",
                ],
                "功能检查/生理检查": [
                    "心电图", "动态心电图", "运动平板试验", "动态血压", "肺功能",
                    "支气管舒张试验", "弥散功能检查", "脑电图", "诱发电位", "肌电图",
                    "神经传导速度检查", "胃动力检查", "24小时pH监测", "听力测试",
                    "前庭功能检查",
                ],
                "遗传与分子检测": [
                    "染色体核型分析", "染色体微阵列", "遗传病基因检测", "肿瘤驱动基因检测",
                    "药物基因组学检测", "DNA检测", "RNA检测", "病原体核酸检测",
                    "液体活检", "无创产前筛查", "胚胎遗传学检测",
                ],
                "其他": [],
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
        },

        getExamsForCategory(cat) {
            return this.examMapping[cat] || [];
        },

        addCustomExam() {
            const name = this.customExamInput.trim();
            if (!name) return;
            if (this.selectedExams.includes(name) || this.customExams.includes(name)) {
                this.$message.warning('该检查已存在');
                return;
            }
            this.customExams.push(name);
            this.selectedExams.push(name);
            this.customExamInput = '';
        },

        toggleExam(exam) {
            if (this.selectedExams.includes(exam)) {
                this.selectedExams = this.selectedExams.filter(e => e !== exam);
            } else {
                this.selectedExams.push(exam);
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
            if (this.selectedExams.length === 0) {
                this.$message.warning('请至少选择一项辅助检查');
                return;
            }

            this.submitting = true;
            this.saving = true;

            // 进入过场动画
            this.step = 'loading';

            // 构建检查结果对象（key=检查名, value=从后端查询的真实结果）
            const checkedResults = {};
            for (const exam of this.selectedExams) {
                try {
                    const result = await API.checkExam(this.caseId, exam);
                    checkedResults[exam] = result;
                } catch (err) {
                    console.error('[Phase2Check] 检查查询失败:', exam, err);
                    checkedResults[exam] = '无';
                }
            }

            // 保存检查数据到 sessionStorage（供后续阶段和评价使用）
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
                console.error('[Phase2Check] 保存记录失败:', err);
            }

            // 过场动画 1 秒后展示结果
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
