/**
 * API 客户端
 * 封装所有与后端 Flask API 的通信
 */
const API = {
    BASE_URL: "",

    // 请求封装
    async request(path) {
        try {
            const response = await fetch(this.BASE_URL + path);
            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.error || `HTTP ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error(`[API] ${path} 请求失败:`, error);
            throw error;
        }
    },

    // 获取所有病例
    async getCases() {
        return this.request("/api/cases");
    },

    // 随机抽取病例
    async getRandomCase(mode = "common") {
        return this.request(`/api/cases/random?mode=${mode}`);
    },

    // 获取各模式病例数量
    async getCaseCounts() {
        return this.request("/api/cases/counts");
    },

    // 获取已有结果的模型列表
    async getModels() {
        return this.request("/api/models");
    },

    // 获取指定模型下已有结果的病例
    async getModelCases(modelName) {
        return this.request(`/api/models/${modelName}/cases`);
    },

    // 获取病例基本信息
    async getCaseInfo(caseId) {
        return this.request(`/api/case/${caseId}/info`);
    },

    // 获取完整流程摘要
    async getCaseSummary(caseId, modelName) {
        return this.request(`/api/case/${caseId}/summary/${modelName}`);
    },

    // 获取单个阶段数据
    async getPhase(caseId, phase, modelName) {
        return this.request(`/api/case/${caseId}/phase/${phase}/${modelName}`);
    },

    // 获取 Ground Truth
    async getGroundTruth(caseId) {
        return this.request(`/api/ground_truth/${caseId}`);
    },

    // --- 实时问诊对话 ---

    // 开始问诊会话
    async startChat(caseId) {
        const response = await fetch(this.BASE_URL + "/api/chat/start", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ case_id: caseId }),
        });
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.error || `HTTP ${response.status}`);
        }
        return await response.json();
    },

    // 发送消息
    async sendMessage(sessionId, message) {
        const response = await fetch(this.BASE_URL + "/api/chat/send", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ session_id: sessionId, message }),
        });
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.error || `HTTP ${response.status}`);
        }
        return await response.json();
    },

    // 结束会话
    async endChat(sessionId) {
        try {
            await fetch(this.BASE_URL + "/api/chat/end", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ session_id: sessionId }),
            });
        } catch {
            // 忽略结束请求的错误
        }
    },

    // --- Phase 2: 检查选择匹配 ---

    // 查询患者病例中的辅助检查结果
    async checkExam(caseId, examName) {
        const response = await fetch(this.BASE_URL + "/api/check/exam", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                case_id: caseId,
                exam_name: examName,
            }),
        });
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.error || `HTTP ${response.status}`);
        }
        const data = await response.json();
        return data.result;
    },

    // 检查某个疾病分类是否在对话中命中
    async checkCategory(caseId, category, messages) {
        const response = await fetch(this.BASE_URL + "/api/check/category", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                case_id: caseId,
                category,
                messages,
            }),
        });
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.error || `HTTP ${response.status}`);
        }
        return await response.json();
    },

    // --- Phase 3: 病历书写 + 诊断 ---

    // 提交病历书写
    async submitCaseWriting(caseId, caseText) {
        const response = await fetch(this.BASE_URL + "/api/case-writing/submit", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                case_id: caseId,
                case_text: caseText,
            }),
        });
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.error || `HTTP ${response.status}`);
        }
        return await response.json();
    },

    // 提交诊断
    async submitDiagnosis(caseId, diagnosis) {
        const response = await fetch(this.BASE_URL + "/api/diagnosis/submit", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                case_id: caseId,
                ...diagnosis,
            }),
        });
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.error || `HTTP ${response.status}`);
        }
        return await response.json();
    },

    // --- 问诊过程记录 ---

    // 保存问诊记录
    async saveCaseRecord(recordId, record) {
        const response = await fetch(this.BASE_URL + "/api/record/save", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                case_id: recordId,
                ...record,
            }),
        });
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.error || `HTTP ${response.status}`);
        }
        return await response.json();
    },

    // 获取问诊记录
    async getCaseRecord(recordId) {
        const response = await fetch(this.BASE_URL + `/api/record/${recordId}`);
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.error || `HTTP ${response.status}`);
        }
        return await response.json();
    },

    // --- Phase 4: 诊疗 ---

    // 提交治疗方案
    async submitTreatment(caseId, treatment) {
        const response = await fetch(this.BASE_URL + "/api/treatment/submit", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                case_id: caseId,
                treatment,
            }),
        });
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.error || `HTTP ${response.status}`);
        }
        return await response.json();
    },

    // --- 问诊历史记录 ---

    // 获取问诊历史列表
    async getHistoryList() {
        return this.request("/api/history/list");
    },

    // 获取问诊历史详情（按 case_id 读取）
    async getHistoryDetail(caseId) {
        return this.request(`/api/history/${caseId}`);
    },

    // 删除问诊历史
    async deleteHistory(caseId) {
        const response = await fetch(this.BASE_URL + `/api/history/${caseId}`, {
            method: "DELETE",
        });
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.error || `HTTP ${response.status}`);
        }
        return await response.json();
    },
};
