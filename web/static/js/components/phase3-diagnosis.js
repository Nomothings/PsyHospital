/**
 * Phase3Diagnosis 组件
 * Phase 3 — 病历书写 + 诊断
 *
 * 左右分栏布局：
 *   左侧 — 患者基本信息、体格检查、辅助检查结果、对话记录（可滚动）
 *   右侧 — 医生病历书写文本框
 */
const Phase3Diagnosis = {
    template: `
        <div class="phase3-page">
            <!-- 背景图 -->
            <div class="phase3-page__bg"></div>

            <!-- 顶部栏 -->
            <header class="phase3-header">
                <div class="phase3-header__left">
                    <el-button text @click="goBack" class="phase3-header__back-btn">
                        <el-icon><ArrowLeft /></el-icon>
                        返回
                    </el-button>
                    <h3 class="phase3-header__title">
                        {{ subStep === 'caseWriting' ? '病历书写' : '诊断' }}
                    </h3>
                    <span class="phase3-header__subtitle">第三阶段</span>
                </div>
                <div class="phase3-header__right">
                    <span class="phase3-header__patient">
                        患者 {{ caseId }}
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
                        完成病历书写，进入诊断
                    </el-button>
                </div>
            </header>

            <!-- 主内容 -->
            <div class="phase3-content phase3-content--split">
                <!-- ======================== 步骤1: 病历书写 ======================== -->
                <template v-if="subStep === 'caseWriting'">
                    <!-- 左侧：患者信息面板 -->
                    <aside class="phase3-left-panel">
                        <!-- 患者基本信息 -->
                        <div class="phase3-panel-section" v-if="caseInfo">
                            <div class="phase3-panel-section__title">患者基本信息</div>
                            <div class="phase3-panel-section__content">
                                <div class="phase3-info-row">
                                    <span class="phase3-info-row__label">基本信息</span>
                                    <span class="phase3-info-row__value">{{ caseInfo.basicInfomation || '暂无' }}</span>
                                </div>
                            </div>
                        </div>

                        <!-- 体格检查报告 -->
                        <div class="phase3-panel-section" v-if="caseInfo && caseInfo.physicalExamination">
                            <div class="phase3-panel-section__title">体格检查报告</div>
                            <div class="phase3-panel-section__content phase3-panel-section__scroll">
                                <div class="phase3-physical-exam-text">{{ caseInfo.physicalExamination }}</div>
                            </div>
                        </div>

                        <!-- 辅助检查结果 -->
                        <div class="phase3-panel-section" v-if="Object.keys(phase2Results).length">
                            <div class="phase3-panel-section__title">辅助检查结果</div>
                            <div class="phase3-panel-section__content">
                                <div v-for="(result, exam) in phase2Results" :key="exam"
                                     class="phase3-exam-result-row"
                                     :class="result === '无' ? 'phase3-exam-result-row--none' : 'phase3-exam-result-row--has'">
                                    <span class="phase3-exam-result-row__name">{{ exam }}</span>
                                    <span class="phase3-exam-result-row__value">
                                        {{ result === '无' ? '无此项检查' : result }}
                                    </span>
                                </div>
                            </div>
                        </div>

                        <!-- 对话记录 -->
                        <div class="phase3-panel-section phase3-panel-section--chat" v-if="phase1Messages.length">
                            <div class="phase3-panel-section__title">
                                对话记录
                                <span class="phase3-panel-section__hint">（最近 {{ phase1Messages.length }} 条）</span>
                            </div>
                            <div class="phase3-panel-section__scroll phase3-chat-scroll">
                                <div v-for="(msg, idx) in phase1Messages" :key="idx"
                                     class="phase3-chat-msg"
                                     :class="msg.role">
                                    <span class="phase3-chat-msg__role">
                                        {{ msg.role === 'doctor' ? '医生' : '患者' }}
                                    </span>
                                    <span class="phase3-chat-msg__content">{{ msg.content }}</span>
                                </div>
                            </div>
                        </div>
                    </aside>

                    <!-- 右侧：病历书写 -->
                    <main class="phase3-right-panel">
                        <div class="phase3-case-writing-card">
                            <div class="phase3-case-writing-card__header">
                                <h2 class="phase3-case-writing-card__title">病历书写</h2>
                                <p class="phase3-case-writing-card__subtitle">
                                    请根据左侧信息填写病历表单
                                </p>
                            </div>

                            <!-- 患者信息填写区 -->
                            <div class="case-info-readonly" v-if="caseInfo">
                                <div class="case-info-readonly__grid">
                                    <div class="case-info-row">
                                        <span class="case-info-row__label">姓名</span>
                                        <input v-model="caseForm.name" class="case-info-row__input case-info-row__input--auto" placeholder="请输入" />
                                    </div>
                                    <div class="case-info-row">
                                        <span class="case-info-row__label">年龄</span>
                                        <input v-model="caseForm.age" class="case-info-row__input case-info-row__input--auto" placeholder="请输入" />
                                    </div>
                                    <div class="case-info-row">
                                        <span class="case-info-row__label">性别</span>
                                        <input v-model="caseForm.gender" class="case-info-row__input case-info-row__input--auto" placeholder="请输入" />
                                    </div>
                                </div>
                                <div class="case-info-divider"></div>
                                <div class="case-info-section">
                                    <span class="case-info-section__label">主诉</span>
                                    <textarea v-model="caseForm.chiefComplaint" class="case-info-section__input" rows="2" placeholder="请输入主诉"></textarea>
                                </div>
                                <div class="case-info-divider"></div>
                                <div class="case-info-section">
                                    <span class="case-info-section__label">家族史</span>
                                    <textarea v-model="caseForm.familyHistory" class="case-info-section__input" rows="2" placeholder="请输入家族史"></textarea>
                                </div>
                                <div class="case-info-divider"></div>
                                <div class="case-info-section">
                                    <span class="case-info-section__label">既往史</span>
                                    <textarea v-model="caseForm.pastHistory" class="case-info-section__input" rows="2" placeholder="请输入既往史"></textarea>
                                </div>
                                <div class="case-info-divider"></div>
                                <div class="case-info-section">
                                    <span class="case-info-section__label">体格检查</span>
                                    <textarea v-model="caseForm.physicalExam" class="case-info-section__input" rows="4" placeholder="请输入体格检查"></textarea>
                                </div>
                                <div class="case-info-divider"></div>
                                <div class="case-info-section">
                                    <span class="case-info-section__label">精神检查</span>
                                    <textarea v-model="caseForm.mentalExam" class="case-info-section__input" rows="3" placeholder="请输入精神检查"></textarea>
                                </div>
                                <div class="case-info-divider"></div>
                                <div class="case-info-section">
                                    <span class="case-info-section__label">辅助检查</span>
                                    <textarea v-model="caseForm.auxiliaryExam" class="case-info-section__input" rows="3" placeholder="请输入辅助检查"></textarea>
                                </div>
                            </div>
                        </div>
                    </main>
                </template>

                <!-- ======================== 步骤2: 诊断 ======================== -->
                <template v-else>
                    <div class="phase3-form-card">
                        <div class="phase3-form-card__header">
                            <h2 class="phase3-form-card__title">填写诊断</h2>
                            <p class="phase3-form-card__subtitle">
                                请根据已完成的病历，填写最终诊断信息
                            </p>
                            <el-tag type="success" effect="plain" size="small" style="margin-top: 8px;">
                                病历已书写
                            </el-tag>
                        </div>

                        <div class="phase3-form">
                            <!-- 诊断选择器 -->
                            <div class="diagnosis-selector" ref="diagnosisSelectorRef">
                                <label class="diagnosis-selector__label">诊断选择</label>

                                <!-- 组合标签容器 -->
                                <div class="diagnosis-selector__input" @click.self="openDropdown">
                                    <!-- 组合标签 -->
                                    <transition-group name="compound-tag" tag="div" class="diagnosis-selector__tags">
                                        <div
                                            v-for="tag in compoundTags"
                                            :key="tag.key"
                                            class="compound-tag"
                                            :class="{ 'compound-tag--removing': tag._removing }"
                                            :title="tag.category + ' — ' + (tag.disease || '未选择具体疾病')"
                                        >
                                            <!-- 大类 -->
                                            <span class="compound-tag__category">
                                                <el-icon :size="10" class="compound-tag__cat-icon"><Folder /></el-icon>
                                                {{ tag.category }}
                                            </span>
                                            <!-- 分隔符 -->
                                            <span class="compound-tag__sep"></span>
                                            <!-- 诊断项 -->
                                            <span class="compound-tag__disease">
                                                <span class="compound-tag__dot"></span>
                                                {{ tag.disease || '—' }}
                                            </span>
                                            <!-- 删除按钮 -->
                                            <span class="compound-tag__delete" @click.stop="removeCompoundTag(tag)" title="删除">
                                                <el-icon :size="13"><Close /></el-icon>
                                            </span>
                                        </div>
                                    </transition-group>

                                    <!-- 添加按钮 -->
                                    <div class="compound-tag compound-tag--add" @click.stop="openDropdown">
                                        <el-icon :size="14" class="compound-tag__add-icon"><Plus /></el-icon>
                                        <span>添加诊断</span>
                                    </div>

                                    <!-- 空状态提示 -->
                                    <div v-if="compoundTags.length === 0" class="diagnosis-selector__placeholder">
                                        点击「添加诊断」选择 ICD-11 疾病分类
                                    </div>

                                    <!-- 下拉面板 -->
                                    <div v-show="dropdownVisible" class="diagnosis-dropdown" @click.stop>
                                        <div class="diagnosis-dropdown__body">
                                            <!-- 左侧：大类列表 -->
                                            <div class="diagnosis-dropdown__categories">
                                                <div class="diagnosis-dropdown__section-title">诊断大类</div>
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
                                                    <span class="diagnosis-dropdown__cat-item__text">{{ cat }}</span>
                                                    <el-icon v-if="isSelectedCategory(cat)" :size="14" color="#5ed6c8"><Check /></el-icon>
                                                </div>
                                            </div>
                                            <!-- 右侧：疾病列表 -->
                                            <div class="diagnosis-dropdown__diseases">
                                                <div v-if="!activeCategory" class="diagnosis-dropdown__empty">
                                                    请先在左侧选择一个诊断大类
                                                </div>
                                                <template v-else>
                                                    <div class="diagnosis-dropdown__section-title">
                                                        {{ activeCategory }} — 具体疾病
                                                    </div>
                                                    <div
                                                        v-for="dis in getDiseasesForCategory(activeCategory)"
                                                        :key="dis"
                                                        class="diagnosis-dropdown__dis-item"
                                                        :class="{
                                                            'diagnosis-dropdown__dis-item--selected': isSelectedDisease(activeCategory, dis),
                                                        }"
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

                            <!-- 诊断理由 -->
                            <div class="diagnosis-selector__reason">
                                <label class="diagnosis-selector__label">诊断理由</label>
                                <textarea
                                    v-model="form.reason"
                                    class="diagnosis-selector__textarea"
                                    rows="6"
                                    placeholder="请说明诊断依据和推理过程…"
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
                                    完成诊断
                                </el-button>
                            </div>
                        </div>
                    </div>
                </template>
            </div>

            <!-- 评价加载遮罩 -->
            <transition name="eval-fade">
                <div v-if="evalState === 'loading'" class="eval-overlay">
                    <div class="eval-overlay__content">
                        <img src="/static/bg/eval.png" alt="" class="eval-overlay__icon" />
                        <div class="eval-overlay__text">正在进行阶段评价…</div>
                        <div class="eval-overlay__subtext">分析病历书写与诊断质量</div>
                    </div>
                </div>
            </transition>

            <!-- 评价结果面板 -->
            <transition name="eval-slide">
                <div v-if="evalState === 'showing' || evalState === 'done'" class="eval-panel">
                    <div class="eval-panel__inner">
                        <div class="eval-panel__header">
                            <el-icon :size="22" color="#5ed6c8"><CircleCheckFilled /></el-icon>
                            <h3 class="eval-panel__title">阶段评价完成</h3>
                            <el-tag type="success" size="small" effect="plain">Phase 3</el-tag>
                        </div>

                        <div class="eval-panel__body">
                            <!-- 病历书写统计 -->
                            <div class="eval-section" v-if="evalData.case_form_stats">
                                <div class="eval-section__title">
                                    <el-icon :size="14" color="#5ed6c8"><Document /></el-icon>
                                    病历书写完成度
                                </div>
                                <div class="eval-stats">
                                    <div class="eval-stat">
                                        <span class="eval-stat__label">已填项目</span>
                                        <span class="eval-stat__value">{{ evalData.case_form_stats.filled_fields }}/{{ evalData.case_form_stats.total_fields }}</span>
                                    </div>
                                    <div class="eval-stat">
                                        <span class="eval-stat__label">完成度</span>
                                        <span class="eval-stat__value">{{ evalData.case_form_stats.completeness }}%</span>
                                    </div>
                                </div>
                            </div>

                            <!-- 诊断统计 -->
                            <div class="eval-section" v-if="evalData.diagnosis_stats">
                                <div class="eval-section__title">
                                    <el-icon :size="14" color="#409eff"><Notebook /></el-icon>
                                    诊断情况
                                </div>
                                <div class="eval-stats">
                                    <div class="eval-stat">
                                        <span class="eval-stat__label">诊断大类</span>
                                        <span class="eval-stat__value">{{ evalData.diagnosis_stats.categories }}</span>
                                    </div>
                                    <div class="eval-stat">
                                        <span class="eval-stat__label">具体诊断</span>
                                        <span class="eval-stat__value">{{ evalData.diagnosis_stats.total_diseases }}</span>
                                    </div>
                                    <div class="eval-stat">
                                        <span class="eval-stat__label">诊断理由</span>
                                        <span class="eval-stat__value">{{ evalData.diagnosis_stats.has_reason ? '已填' : '未填' }}</span>
                                    </div>
                                </div>
                            </div>

                            <!-- 无评估数据提示 -->
                            <div v-if="!evalData.case_form_stats && !evalData.diagnosis_stats" class="eval-section eval-section--note">
                                <el-icon :size="16" color="#c0c4cc"><InfoFilled /></el-icon>
                                <span>评价服务暂时不可用，已跳过详细评估</span>
                            </div>
                        </div>

                        <div class="eval-panel__footer">
                            <el-button
                                type="primary"
                                size="large"
                                round
                                @click="confirmAndProceed"
                            >
                                好的，进入下一阶段
                            </el-button>
                        </div>
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

            // 诊断多选器状态
            dropdownVisible: false,
            activeCategory: '',
            selectedCategories: [],
            selectedDiseasesByCategory: {},

            categories: [
                "神经发育障碍",
                "精神分裂症或其他原发性精神病性障碍",
                "紧张症",
                "心境障碍",
                "焦虑或恐惧相关障碍",
                "强迫症或相关障碍",
                "应激相关障碍",
                "分离障碍",
                "喂养或进食障碍",
                "排泄障碍",
                "躯体痛苦或躯体体验障碍",
                "物质使用或成瘾行为所致障碍",
                "冲动控制障碍",
                "破坏性行为或解社会行为障碍",
                "人格障碍及相关特质",
                "性欲倒错障碍",
                "神经认知障碍",
                "妊娠、分娩或产褥期相关精神或行为障碍",
                "做作性障碍",
            ],
            diseaseMapping: {
                "神经发育障碍": [
                    "6A00 智力发育障碍",
                    "6A01 发育性言语或语言障碍",
                    "6A02 孤独症谱系障碍",
                    "6A03 发育性学习障碍",
                    "6A04 发育性运动协调障碍",
                    "6A05 注意缺陷多动障碍",
                    "6A06 刻板运动障碍",
                ],
                "精神分裂症或其他原发性精神病性障碍": [
                    "6A20 精神分裂症",
                    "6A21 分裂情感性障碍",
                    "6A22 分裂型障碍",
                    "6A23 急性短暂性精神病性障碍",
                    "6A24 妄想性障碍",
                ],
                "紧张症": [
                    "6A40 伴发于其他精神障碍的紧张症",
                    "6A41 物质或药物所致紧张症",
                ],
                "心境障碍": [
                    "6A60 双相情感障碍 I 型",
                    "6A61 双相情感障碍 II 型",
                    "6A62 环性心境障碍",
                    "6A70 单次发作抑郁障碍",
                    "6A71 复发性抑郁障碍",
                    "6A72 恶劣心境障碍",
                    "6A73 混合性抑郁和焦虑障碍",
                ],
                "焦虑或恐惧相关障碍": [
                    "6B00 广泛性焦虑障碍",
                    "6B01 惊恐障碍",
                    "6B02 广场恐惧症",
                    "6B03 特定恐惧症",
                    "6B04 社交焦虑障碍",
                    "6B05 分离焦虑障碍",
                    "6B06 选择性缄默症",
                ],
                "强迫症或相关障碍": [
                    "6B20 强迫症",
                    "6B21 躯体变形障碍",
                    "6B22 嗅觉参考障碍",
                    "6B23 疑病症",
                    "6B24 囤积障碍",
                    "6B25 以身体为中心的重复行为障碍",
                ],
                "应激相关障碍": [
                    "6B40 创伤后应激障碍",
                    "6B41 复杂性创伤后应激障碍",
                    "6B42 延长哀伤障碍",
                    "6B43 适应障碍",
                    "6B44 反应性依恋障碍",
                    "6B45 脱抑制性社会参与障碍",
                ],
                "分离障碍": [
                    "6B60 分离性神经症状障碍",
                    "6B61 分离性遗忘症",
                    "6B62 恍惚障碍",
                    "6B63 附体恍惚障碍",
                    "6B64 分离性身份障碍",
                    "6B65 部分分离性身份障碍",
                    "6B66 人格解体-现实解体障碍",
                ],
                "喂养或进食障碍": [
                    "6B80 神经性厌食",
                    "6B81 神经性贪食",
                    "6B82 暴食障碍",
                    "6B83 回避性/限制性摄食障碍",
                    "6B84 异食癖",
                    "6B85 反刍-反流障碍",
                ],
                "排泄障碍": [
                    "6C00 遗尿症",
                    "6C01 遗粪症",
                ],
                "躯体痛苦或躯体体验障碍": [
                    "6C20 躯体痛苦障碍",
                    "6C21 身体完整性烦躁障碍",
                ],
                "物质使用或成瘾行为所致障碍": [
                    "6C40 酒精使用所致障碍",
                    "6C41 大麻使用所致障碍",
                    "6C42 合成大麻素使用所致障碍",
                    "6C43 阿片类物质使用所致障碍",
                    "6C44 镇静催眠药或抗焦虑药使用所致障碍",
                    "6C45 可卡因使用所致障碍",
                    "6C46 苯丙胺类兴奋剂使用所致障碍",
                    "6C47 合成卡西酮使用所致障碍",
                    "6C48 咖啡因使用所致障碍",
                    "6C49 致幻剂使用所致障碍",
                    "6C4A 尼古丁使用所致障碍",
                    "6C4C MDMA 或相关药物使用所致障碍",
                    "6C4D 解离性药物使用所致障碍",
                    "6C4E 其他特定精神活性物质使用所致障碍",
                    "6C4F 多种特定精神活性物质使用所致障碍",
                    "6C4G 未知或未特定精神活性物质使用所致障碍",
                    "6C4H 非精神活性物质使用所致障碍",
                    "6C50 赌博障碍",
                    "6C51 游戏障碍",
                ],
                "冲动控制障碍": [
                    "6C70 纵火癖",
                    "6C71 偷窃癖",
                    "6C72 强迫性性行为障碍",
                ],
                "破坏性行为或解社会行为障碍": [
                    "6C90 对立违抗障碍",
                    "6C91 品行-解社会障碍",
                ],
                "人格障碍及相关特质": [
                    "6D10 人格障碍",
                ],
                "性欲倒错障碍": [
                    "6D30 露阴障碍",
                    "6D31 窥阴障碍",
                    "6D32 恋童障碍",
                    "6D33 强制性施虐障碍",
                    "6D34 摩擦障碍",
                    "6D35 涉及非同意个体的其他性欲倒错障碍",
                    "6D36 涉及独处行为或同意个体的性欲倒错障碍",
                ],
                "神经认知障碍": [
                    "6D70 谵妄",
                    "6D71 轻度神经认知障碍",
                    "6D72 遗忘障碍",
                    "6D80 阿尔茨海默病所致痴呆",
                    "6D81 脑血管病所致痴呆",
                    "6D82 路易体病所致痴呆",
                    "6D83 额颞叶痴呆",
                    "6D84 精神活性物质所致痴呆",
                    "6D85 其他疾病所致痴呆",
                    "6D86 痴呆的行为或心理障碍",
                ],
                "妊娠、分娩或产褥期相关精神或行为障碍": [
                    "6E20 妊娠、分娩或产褥期相关精神或行为障碍，不伴精神病性症状",
                    "6E21 妊娠、分娩或产褥期相关精神或行为障碍，伴精神病性症状",
                ],
                "做作性障碍": [
                    "6D50 施加于自身的做作性障碍",
                    "6D51 施加于他人的做作性障碍",
                ],
            },
            rules: {},
            // 评价状态: 'idle' | 'loading' | 'showing' | 'done'
            evalState: 'idle',
            evalData: {},
            evalError: null,
        };
    },

    computed: {
        ArrowLeft() { return ElementPlusIconsVue.ArrowLeft; },
        Close() { return ElementPlusIconsVue.Close; },
        Check() { return ElementPlusIconsVue.Check; },
        Plus() { return ElementPlusIconsVue.Plus; },
        Folder() { return ElementPlusIconsVue.Folder; },
        CircleCheckFilled() { return ElementPlusIconsVue.CircleCheckFilled; },
        Document() { return ElementPlusIconsVue.Document; },
        Notebook() { return ElementPlusIconsVue.Notebook; },
        InfoFilled() { return ElementPlusIconsVue.InfoFilled; },

        compoundTags() {
            const tags = [];
            for (const cat of this.selectedCategories) {
                const diseases = this.selectedDiseasesByCategory[cat] || [];
                if (diseases.length === 0) {
                    // 只有大类，没有子诊断
                    tags.push({
                        key: `cat:${cat}`,
                        category: cat,
                        disease: '',
                        type: 'category-only',
                        _removing: false,
                    });
                } else {
                    // 大类 + 每个疾病一个组合标签
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

    watch: {},

    methods: {
        // ---- 诊断选择器方法 ----
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
            if (!this.activeCategory && this.selectedCategories.length > 0) {
                this.activeCategory = this.selectedCategories[0];
            }
        },

        closeDropdown() {
            this.dropdownVisible = false;
        },

        toggleDropdown() {
            this.dropdownVisible = !this.dropdownVisible;
            if (this.dropdownVisible && !this.activeCategory && this.selectedCategories.length > 0) {
                this.activeCategory = this.selectedCategories[0];
            }
        },

        closeDropdown() {
            this.dropdownVisible = false;
        },

        selectCategory(cat) {
            if (!this.isSelectedCategory(cat)) {
                this.selectedCategories.push(cat);
                if (!this.selectedDiseasesByCategory[cat]) {
                    this.selectedDiseasesByCategory[cat] = [];
                }
            }
            // 选中大类后，立刻切到右侧显示该大类的疾病列表
            this.activeCategory = cat;
        },

        selectDisease(cat, dis) {
            if (!this.selectedDiseasesByCategory[cat]) {
                this.selectedDiseasesByCategory[cat] = [];
            }
            const diseases = this.selectedDiseasesByCategory[cat];
            if (!diseases.includes(dis)) {
                diseases.push(dis);
            } else {
                // 已选则取消
                this.selectedDiseasesByCategory[cat] = diseases.filter(d => d !== dis);
            }
        },

        removeCompoundTag(tag) {
            if (tag.type === 'category-only') {
                // 删除大类-only标签
                this.selectedCategories = this.selectedCategories.filter(c => c !== tag.category);
                delete this.selectedDiseasesByCategory[tag.category];
                if (this.activeCategory === tag.category) {
                    this.activeCategory = this.selectedCategories[0] || '';
                }
            } else {
                // 删除组合标签（大类 + 疾病）
                if (this.selectedDiseasesByCategory[tag.category]) {
                    this.selectedDiseasesByCategory[tag.category] = this.selectedDiseasesByCategory[tag.category].filter(d => d !== tag.disease);
                    // 如果该大类下没有疾病了，自动移除大类
                    if (this.selectedDiseasesByCategory[tag.category].length === 0) {
                        this.selectedCategories = this.selectedCategories.filter(c => c !== tag.category);
                        delete this.selectedDiseasesByCategory[tag.category];
                        if (this.activeCategory === tag.category) {
                            this.activeCategory = this.selectedCategories[0] || '';
                        }
                    }
                }
            }
        },

        removeTag(key) {
            // 兼容旧方法
            if (key.startsWith('cat:')) {
                const cat = key.slice(4);
                this.selectedCategories = this.selectedCategories.filter(c => c !== cat);
                delete this.selectedDiseasesByCategory[cat];
                if (this.activeCategory === cat) {
                    this.activeCategory = this.selectedCategories[0] || '';
                }
            } else if (key.startsWith('dis:')) {
                const parts = key.slice(4).split('::');
                const cat = parts[0];
                const dis = parts.slice(1).join('::');
                if (this.selectedDiseasesByCategory[cat]) {
                    this.selectedDiseasesByCategory[cat] = this.selectedDiseasesByCategory[cat].filter(d => d !== dis);
                }
            }
        },

        handleClickOutside(e) {
            const el = this.$refs.diagnosisSelectorRef;
            if (el && !el.contains(e.target)) {
                this.closeDropdown();
            }
        },

        // ---- 原有方法 ----
        goToDiagnosis() {
            if (!this.isCaseFormFilled) {
                this.$message.warning('请先填写完整病历表单');
                return;
            }
            this._lastCaseForm = { ...this.caseForm };
            sessionStorage.setItem('phase3_caseForm', JSON.stringify(this.caseForm));
            this.subStep = 'diagnosis';
            this.$message.success('病历已保存，请填写诊断信息');
        },

        async handleSubmit() {
            if (this.selectedCategories.length === 0) {
                this.$message.warning('请至少选择一个诊断类别');
                return;
            }
            if (!this.form.reason.trim()) {
                this.$message.warning('请填写诊断理由');
                return;
            }

            this.submitting = true;
            try {
                // 使用 record_id 确保所有数据整合到同一次问诊记录
                const recordId = sessionStorage.getItem('record_id') || this.caseId;

                // 构建诊断提交数据
                const allDiseases = [];
                const diagnoses = [];
                for (const cat of this.selectedCategories) {
                    const diseases = this.selectedDiseasesByCategory[cat] || [];
                    allDiseases.push(...diseases);
                    diagnoses.push({ category: cat, diseases });
                }

                // 兼容后端：第一个类别作为主要类别，第一个疾病作为主要疾病
                const primaryCategory = this.selectedCategories[0] || '';
                const primaryDisease = allDiseases[0] || '';

                await API.submitCaseWriting(recordId, JSON.stringify(this.caseForm));

                const result = await API.submitDiagnosis(recordId, {
                    category: primaryCategory,
                    disease: allDiseases.join('、') || primaryDisease,
                    reason: this.form.reason,
                });

                await API.saveCaseRecord(recordId, {
                    caseForm: { ...this.caseForm },
                    diagnosis: {
                        category: primaryCategory,
                        disease: allDiseases.join('、') || primaryDisease,
                        reason: this.form.reason,
                        diagnoses: diagnoses,
                    },
                });

                this.$message.success('第三阶段已完成');
                console.log('[Phase3Diagnosis] 提交成功:', result);

                // 保存诊断数据供评价使用
                this._lastDiagnosis = {
                    category: primaryCategory,
                    disease: allDiseases.join('、') || primaryDisease,
                    reason: this.form.reason,
                    diagnoses: diagnoses,
                };

                sessionStorage.setItem('phase3_result', JSON.stringify({
                    caseId: this.caseId,
                    caseForm: { ...this.caseForm },
                    category: primaryCategory,
                    disease: allDiseases.join('、') || primaryDisease,
                    reason: this.form.reason,
                    diagnoses: diagnoses,
                }));

                // 进入评价流程
                await this.startEvaluation();
            } catch (err) {
                this.$message.error('提交失败: ' + (err.message || '未知错误'));
                console.error('[Phase3Diagnosis] 提交失败:', err);
            } finally {
                this.submitting = false;
            }
        },

        goBack() {
            if (this.subStep === 'diagnosis') {
                this.subStep = 'caseWriting';
            } else {
                this.$router.push({ path: '/phase2', query: { id: this.caseId } });
            }
        },

        /**
         * 统一评价入口
         */
        async startEvaluation() {
            if (this.evalState !== 'idle') return;

            this.evalState = 'loading';
            this.evalError = null;
            this.evalData = {};

            const caseForm = this._lastCaseForm || { ...this.caseForm };
            const diagnosis = this._lastDiagnosis || {};

            try {
                console.log(`[Phase3Diagnosis] 开始评价 Phase 3, caseId=${this.caseId}`);
                this.evalData = await API.evaluatePhase(3, this.caseId, {
                    case_form: caseForm,
                    diagnosis: diagnosis,
                });
                console.log('[Phase3Diagnosis] 评价结果:', this.evalData);
                this.evalState = 'showing';
            } catch (err) {
                console.error('[Phase3Diagnosis] 阶段评价失败:', err);
                this.evalError = err.message || '未知错误';
                // 即使失败也展示面板
                const formFields = ['name', 'age', 'gender', 'chiefComplaint', 'familyHistory', 'pastHistory', 'physicalExam', 'mentalExam', 'auxiliaryExam'];
                const filledFields = formFields.filter(f => caseForm[f] && caseForm[f].trim()).length;
                this.evalData = {
                    phase: 3,
                    phase_name: '病历书写与诊断',
                    case_id: this.caseId,
                    case_form_stats: {
                        filled_fields: filledFields,
                        total_fields: formFields.length,
                        completeness: Math.round(filledFields / formFields.length * 100),
                    },
                    diagnosis_stats: {
                        categories: diagnosis.diagnoses ? diagnosis.diagnoses.length : 0,
                        total_diseases: diagnosis.diagnoses ? diagnosis.diagnoses.reduce((s, d) => s + (d.diseases ? d.diseases.length : 0), 0) : 0,
                        has_reason: !!diagnosis.reason,
                    },
                    _fallback: true,
                };
                this.evalState = 'showing';
            }
        },

        /**
         * 用户确认评价后进入下一阶段
         */
        confirmAndProceed() {
            if (this.evalState !== 'showing' && this.evalState !== 'done') return;
            this.evalState = 'done';
            this.$router.push({ path: '/phase4', query: { id: this.caseId } });
        },

        async loadPhaseData() {
            if (this.caseId) {
                try {
                    const info = await API.getCaseInfo(this.caseId);
                    this.caseInfo = info;

                    // 从 basicInfomation 中解析性别和年龄，自动填入表单
                    if (info && info.basicInfomation) {
                        const basicInfo = info.basicInfomation;

                        // 解析性别：匹配"男"或"女"
                        const genderMatch = basicInfo.match(/患者([男女])/);
                        if (genderMatch) {
                            this.caseForm.gender = genderMatch[1];
                        }

                        // 解析年龄：匹配"XX 岁"或"XX岁"
                        const ageMatch = basicInfo.match(/(\d+)\s*岁/);
                        if (ageMatch) {
                            this.caseForm.age = ageMatch[1];
                        }

                        // 姓名默认为"患者"
                        this.caseForm.name = '患者';
                    }
                } catch (err) {
                    console.error('[Phase3Diagnosis] 加载患者信息失败:', err);
                }
            }

            const messagesStr = sessionStorage.getItem('phase2_messages');
            console.log('[Phase3Diagnosis] phase2_messages raw:', messagesStr);
            if (messagesStr) {
                try {
                    const messages = JSON.parse(messagesStr);
                    console.log('[Phase3Diagnosis] parsed messages:', messages);
                    this.phase1Messages = messages.slice(-12);
                    console.log('[Phase3Diagnosis] phase1Messages:', this.phase1Messages);
                } catch (err) {
                    console.error('[Phase3Diagnosis] 解析 Phase 1 消息失败:', err);
                }
            } else {
                console.warn('[Phase3Diagnosis] 未找到 phase2_messages');
            }

            const resultsStr = sessionStorage.getItem('phase2_checkedResults');
            if (resultsStr) {
                try {
                    this.phase2Results = JSON.parse(resultsStr);
                } catch (err) {
                    console.error('[Phase3Diagnosis] 解析 Phase 2 结果失败:', err);
                }
            }

            const savedCaseForm = sessionStorage.getItem('phase3_caseForm');
            if (savedCaseForm) {
                try {
                    this.caseForm = JSON.parse(savedCaseForm);
                } catch (err) {
                    console.error('[Phase3Diagnosis] 解析已保存病历表单失败:', err);
                }
            }
        },
    },

    mounted() {
        this.caseId = this.$route.query.id || sessionStorage.getItem('phase2_caseId') || '';
        if (!this.caseId) {
            this.$message.warning('未找到病例信息，请从患者列表进入');
        }
        this.loadPhaseData();
        document.addEventListener('mousedown', this.handleClickOutside);
    },

    beforeUnmount() {
        document.removeEventListener('mousedown', this.handleClickOutside);
    },
};
