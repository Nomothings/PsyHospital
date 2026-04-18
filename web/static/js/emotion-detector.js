/**
 * Emotion Detector
 * 从患者回复中提取情绪状态
 *
 * 输入: 患者的回复文本（包含 [情绪] 标记）
 * 输出: emotion 状态码
 *
 * 情绪列表:
 *   neutral  - 平静
 *   sad      - 悲伤
 *   anxious  - 焦虑
 *   angry    - 愤怒/防御
 *   excited  - 激动/躁狂
 *   flat     - 淡漠/木僵
 */
const EmotionDetector = {
    /**
     * 从患者回复中提取情绪
     * @param {string} text - 患者的回复文本
     * @param {string} prevEmotion - 上一轮的情绪状态（备用）
     * @returns {string} 情绪状态码
     */
    detect(text, prevEmotion = 'neutral') {
        if (!text || !text.trim()) return 'neutral';

        // 从文本中提取情绪标记 [xxx]
        const emotionMap = {
            '平静': 'neutral',
            '悲伤': 'sad',
            '焦虑': 'anxious',
            '愤怒': 'angry',
            '激动': 'excited',
            '淡漠': 'flat',
        };

        // 匹配开头的 [情绪] 标记
        const match = text.match(/^\s*\[(平静|悲伤|焦虑|愤怒|激动|淡漠)\]/);
        if (match) {
            const emotion = emotionMap[match[1]] || 'neutral';
            console.log('[EmotionDetector] 检测到情绪:', match[1], '->', emotion, '原文:', text.substring(0, 20));
            return emotion;
        }

        console.log('[EmotionDetector] 未检测到情绪标记，保持:', prevEmotion);
        // 未找到标记时回退到上一轮情绪
        return prevEmotion === 'neutral' ? 'neutral' : prevEmotion;
    },

    /**
     * 移除文本中的情绪标记
     * @param {string} text - 患者的回复文本
     * @returns {string} 移除标记后的文本
     */
    clean(text) {
        if (!text) return text;
        return text.replace(/^\s*\[(平静|悲伤|焦虑|愤怒|激动|淡漠)\]\s*/, '').trim();
    },
};
