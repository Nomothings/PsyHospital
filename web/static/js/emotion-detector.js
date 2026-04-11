/**
 * Emotion Detector
 * 从患者回复文本推断当前情绪状态
 *
 * 输入: 患者最新回复文本
 * 输出: emotion 状态码
 */
const EmotionDetector = {
    /**
     * 根据患者回复文本推断情绪
     * @param {string} text - 患者的回复文本
     * @param {string} prevEmotion - 上一轮的情绪状态
     * @returns {string} 情绪状态码
     */
    detect(text, prevEmotion = 'neutral') {
        if (!text) return 'neutral';

        const t = text.toLowerCase();

        // 愤怒 / 敌意
        if (this.hasAnger(t)) return 'angry';

        // 痛苦 / 绝望
        if (this.hasDistress(t)) return 'distressed';

        // 防御 / 抗拒
        if (this.hasDefensive(t)) return 'defensive';

        // 紧张 / 恐惧
        if (this.hasNervous(t)) return 'nervous';

        // 悲伤 / 绝望
        if (this.hasSad(t)) return 'sad';

        // 怀疑 / 多疑
        if (this.hasSuspicious(t)) return 'suspicious';

        // 困惑 / 迷茫
        if (this.hasConfused(t)) return 'confused';

        // 犹豫
        if (this.hasHesitant(t)) return 'hesitant';

        // 放松 / 积极
        if (this.hasRelaxed(t)) return 'relaxed';

        // 默认返回上一轮情绪或平静
        return prevEmotion === 'neutral' ? 'neutral' : prevEmotion;
    },

    // ---- 关键词规则 ----

    hasAnger(t) {
        const keywords = [
            '凭什么', '你凭什么', '凭什么这样', '凭什么说',
            '你根本', '你根本不懂', '你不懂', '你们都是',
            '别管我', '别管', '我不想', '我不想说', '烦死了',
            '闭嘴', '滚', '你算', '你以为', '我不需要',
            '你凭什么问我', '关你什么事',
        ];
        return keywords.some(k => t.includes(k));
    },

    hasDistress(t) {
        const keywords = [
            '撑不住', '撑不下去', '受不了', '受不了了',
            '绝望', '活不下去', '不想活', '死了算了',
            '痛苦', '太痛苦', '好痛苦', '我好累', '好累',
            '撑不下去了', '我快', '我快不行了',
            '我害怕', '我怕', '我真的很怕',
            '我不知道怎么办', '我该怎么办', '怎么办',
            '我怕自己再也', '怕自己再也',
        ];
        return keywords.some(k => t.includes(k));
    },

    hasDefensive(t) {
        const keywords = [
            '我没觉得', '我觉得没问题', '我没有', '我没有病',
            '这不是', '这不是我', '这不是我的', '不是我的错',
            '我没有问题', '我挺好的', '我挺好的',
            '我觉得还好', '还好吧', '没什么大不了的',
            '你不用', '你不用这样', '不用你管',
            '我不想谈这个', '不想谈', '别问了',
            '我没什么可说的', '我不想说这个',
            '我没有觉得', '我不觉得',
        ];
        return keywords.some(k => t.includes(k));
    },

    hasNervous(t) {
        const keywords = [
            '害怕', '怕', '恐惧', '紧张', '慌', '心慌',
            '发抖', '哆嗦', '喘不过气', '喘不上气',
            '手抖', '心跳快', '心跳加速', '胸闷',
            '不敢', '怕人', '怕人看到',
            '我紧张', '我很紧张', '好紧张',
            '我有点慌', '我慌了',
            '怕别人', '怕别人看到',
        ];
        return keywords.some(k => t.includes(k));
    },

    hasSad(t) {
        const keywords = [
            '心情不好', '心情差', '心情很差', '心情不好',
            '没意思', '没意义', '没意思', '什么都没意思',
            '提不起兴趣', '没兴趣', '没动力',
            '想哭', '想哭', '忍不住哭', '老是哭',
            '难过', '伤心', '好难过', '好伤心',
            '活着没意思', '不想活', '想离开',
            '没人理解', '没人关心', '没人懂我',
            '孤独', '好孤独', '一个人',
            '低落', '很低落', '一直很低落',
        ];
        return keywords.some(k => t.includes(k));
    },

    hasSuspicious(t) {
        const keywords = [
            '监控', '监听', '跟踪', '监视', '被监视',
            '他们', '他们在', '他们在看我', '他们知道',
            '阴谋', '阴谋', '有人要害我', '要害我',
            '控制', '被控制', '控制我', '他们在控制',
            '不相信', '我不相信', '谁也不信', '不敢相信',
            '有人在', '有人在看', '有人在盯着',
            '不安全', '觉得不安全', '觉得不对劲',
            '被盯', '被跟踪', '跟踪我',
        ];
        return keywords.some(k => t.includes(k));
    },

    hasConfused(t) {
        const keywords = [
            '不知道', '我不清楚', '记不清', '想不起来',
            '记不得', '忘了', '忘记了',
            '搞不懂', '不明白', '我不明白',
            '好像', '好像是', '可能是', '大概是',
            '我不确定', '不确定', '好像不是',
            '说不清', '说不清楚',
            '我记不起来', '想不起来了',
        ];
        return keywords.some(k => t.includes(k));
    },

    hasHesitant(t) {
        const keywords = [
            '……', '…', '。。', '。。。',
            '那个', '嗯', '呃', '啊',
            '好像', '可能', '也许', '大概',
            '我', '我……', '我想想', '让我想想',
            '不知道怎么说', '我不知道怎么说',
            '不太确定', '有点', '有点那个',
        ];
        const dots = (t.match(/…/g) || []).length;
        const ellipsis = (t.match(/\.\.\./g) || []).length;
        if (dots >= 2 || ellipsis >= 2) return true;
        return keywords.filter(k => t.includes(k)).length >= 3;
    },

    hasRelaxed(t) {
        const keywords = [
            '好多了', '好多了', '舒服多了', '轻松',
            '谢谢', '谢谢你', '感谢您的',
            '是的', '对的', '嗯', '嗯嗯',
            '还好', '挺好的', '还可以',
            '我试试', '我愿意试试', '我想试试',
            '我明白了', '我懂了', '我知道了',
            '谢谢医生', '谢谢你的',
            '好', '好的', '嗯好',
            '我会试试', '我愿意',
        ];
        return keywords.some(k => t.includes(k));
    },
};
