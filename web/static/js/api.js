/**
 * Frontend API helper.
 * Keeps all request entry points for the Flask backend in one place.
 */
const API = {
    BASE_URL: "",

    async request(path) {
        try {
            const response = await fetch(this.BASE_URL + path);
            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.error || `HTTP ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error(`[API] ${path} request failed:`, error);
            throw error;
        }
    },

    async getCases() {
        return this.request("/api/cases");
    },

    async getRandomCase(mode = "common") {
        return this.request(`/api/cases/random?mode=${mode}`);
    },

    async getCaseCounts() {
        return this.request("/api/cases/counts");
    },

    async getModels() {
        return this.request("/api/models");
    },

    async getModelCases(modelName) {
        return this.request(`/api/models/${modelName}/cases`);
    },

    async getCaseInfo(caseId) {
        return this.request(`/api/case/${caseId}/info`);
    },

    async getCaseSummary(caseId, modelName) {
        return this.request(`/api/case/${caseId}/summary/${modelName}`);
    },

    async getPhase(caseId, phase, modelName) {
        return this.request(`/api/case/${caseId}/phase/${phase}/${modelName}`);
    },

    async getGroundTruth(caseId) {
        return this.request(`/api/ground_truth/${caseId}`);
    },

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

    async endChat(sessionId) {
        try {
            await fetch(this.BASE_URL + "/api/chat/end", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ session_id: sessionId }),
            });
        } catch {
            // Ignore cleanup errors.
        }
    },

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

    async getCaseRecord(recordId) {
        const response = await fetch(this.BASE_URL + `/api/record/${recordId}`);
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.error || `HTTP ${response.status}`);
        }
        return await response.json();
    },

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

    async getHistoryList() {
        return this.request("/api/history/list");
    },

    async getHistoryDetail(caseId) {
        return this.request(`/api/history/${caseId}`);
    },

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

    async evaluatePhase(phase, caseId, extra = {}) {
        const payload = { case_id: caseId, ...extra };
        const response = await fetch(this.BASE_URL + `/api/evaluate/${phase}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.error || `HTTP ${response.status}`);
        }
        return await response.json();
    },

    async getPhase2Accuracy(caseId, examResults = {}) {
        console.log("[API.getPhase2Accuracy] POST /api/evaluate/phase2-accuracy, caseId:", caseId, "examResults:", JSON.stringify(examResults));
        const response = await fetch(this.BASE_URL + "/api/evaluate/phase2-accuracy", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                case_id: caseId,
                exam_results: examResults,
            }),
        });
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.error || `HTTP ${response.status}`);
        }
        const data = await response.json();
        console.log("[API.getPhase2Accuracy] response:", JSON.stringify(data));
        return data;
    },

    async getPhase3FullEvaluation(caseId, caseForm, diagnosis) {
        return this.evaluatePhase(3, caseId, {
            case_form: caseForm,
            diagnosis,
        });
    },
};
