/**
 * Emotion Detector
 * Parse leading patient emotion tags and map them to the six avatar states.
 */
const EmotionDetector = {
    /**
     * @param {string} text
     * @param {string} prevEmotion
     * @returns {string}
     */
    detect(text, prevEmotion = 'neutral') {
        if (!text || !String(text).trim()) {
            return 'neutral';
        }

        const emotionMap = {
            'neutral': 'neutral',
            'calm': 'neutral',
            'sad': 'sad',
            'depressed': 'sad',
            'down': 'sad',
            'tired': 'sad',
            'hopeless': 'sad',
            'anxious': 'anxious',
            'confused': 'anxious',
            'afraid': 'anxious',
            'fearful': 'anxious',
            'nervous': 'anxious',
            'worried': 'anxious',
            'uneasy': 'anxious',
            'alert': 'anxious',
            'angry': 'angry',
            'irritable': 'angry',
            'hostile': 'angry',
            'defensive': 'angry',
            'excited': 'excited',
            'agitated': 'excited',
            'eager': 'excited',
            'talkative': 'excited',
            'flat': 'flat',
            'apathetic': 'flat',
            'indifferent': 'flat',
            'mute': 'flat',
            'reserved': 'flat',
            'numb': 'flat',
            '平静': 'neutral',
            '中性': 'neutral',
            '安静': 'neutral',
            '悲伤': 'sad',
            '沮丧': 'sad',
            '低落': 'sad',
            '疲惫': 'sad',
            '绝望': 'sad',
            '焦虑': 'anxious',
            '困惑': 'anxious',
            '害怕': 'anxious',
            '恐惧': 'anxious',
            '紧张': 'anxious',
            '担心': 'anxious',
            '不安': 'anxious',
            '警惕': 'anxious',
            '愤怒': 'angry',
            '烦躁': 'angry',
            '敌意': 'angry',
            '易怒': 'angry',
            '防御': 'angry',
            '激动': 'excited',
            '兴奋': 'excited',
            '亢奋': 'excited',
            '急切': 'excited',
            '话多': 'excited',
            '淡漠': 'flat',
            '冷漠': 'flat',
            '冷淡': 'flat',
            '木僵': 'flat',
            '少语': 'flat',
            '无感': 'flat',
            '骞抽潤': 'neutral',
            '鎮蹭激': 'sad',
            '娌抚': 'sad',
            '浣庤惤': 'sad',
            '鐤叉儷': 'sad',
            '缁濇湜': 'sad',
            '鐒﹁檻': 'anxious',
            '鍥版儜': 'anxious',
            '瀹虫€?': 'anxious',
            '鎭愭儳': 'anxious',
            '绱у紶': 'anxious',
            '鎷呭績': 'anxious',
            '涓嶅畨': 'anxious',
            '璀︽儠': 'anxious',
            '鎰ゆ€?': 'angry',
            '鐑﹁簛': 'angry',
            '鏁屾剰': 'angry',
            '鏄撴€?': 'angry',
            '闃插尽': 'angry',
            '婵€鍔?': 'excited',
            '鍏村': 'excited',
            '浜㈠': 'excited',
            '鎬ュ垏': 'excited',
            '璇濆': 'excited',
            '娣℃紶': 'flat',
            '鍐锋紶': 'flat',
            '鍐锋贰': 'flat',
            '鏈ㄥ兊': 'flat',
            '灏戣': 'flat',
            '鏃犳劅': 'flat',
        };

        const match = String(text).match(/^\s*\[([^\]\r\n]+)\]/);
        if (match) {
            const rawTag = match[1].trim().toLowerCase();
            const emotion = emotionMap[rawTag];
            if (emotion) {
                return emotion;
            }
        }

        return prevEmotion || 'neutral';
    },

    /**
     * Remove SEARCH tags and leading emotion tags before rendering patient text.
     * @param {string} text
     * @returns {string}
     */
    clean(text) {
        if (!text) {
            return text;
        }

        return String(text)
            .replace(/\s*\[SEARCH_[^\]\r\n]+\]\s*/g, ' ')
            .replace(/^(?:\s*\[[^\]\r\n]{1,20}\]\s*)+/, '')
            .replace(/\s{2,}/g, ' ')
            .trim();
    },
};
