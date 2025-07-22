
import nltk
import jieba
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
import pickle
import string
import re
import asyncio

from backend.services.translate import translate_english

# 下载必要的 NLTK 数据（首次运行）
# nltk.download('punkt')
# nltk.download('stopwords')

def preprocess_text(text, language='chinese'):
    """
    预处理文本：保留中英文、数字、标点和空格，分词并移除停用词。
    """
    # 保留中文、英文、数字、标点和空格
    text = re.sub(r'[^\u4e00-\u9fff a-zA-Z0-9\s,.!?]', '', text)

    # 分离中文和英文部分
    chinese_parts = re.findall(r'[\u4e00-\u9fff]+', text)
    english_parts = re.findall(r'[a-zA-Z]+', text)

    # 中文分词
    chinese_words = []
    for part in chinese_parts:
        chinese_words.extend(jieba.lcut(part))

    # 英文分词
    english_words = []
    for part in english_parts:
        english_words.extend(nltk.word_tokenize(part.lower()))
    
    # 合并词列表
    words = chinese_words + english_words
    
    # 移除停用词（中文和英文）
    stop_words = set(stopwords.words('chinese') + stopwords.words('english'))
    words = [word for word in words if word not in stop_words and word.strip()]


    return words
def load_keyword_model(model_path='keyword_model.pkl'):
    """
    加载保存的关键词模型。
    """
    try:
        with open(model_path, 'rb') as f:
            word_freq = pickle.load(f)
        print(f"模型已从 {model_path} 加载")
        return word_freq
    except FileNotFoundError:
        print(f"模型文件 {model_path} 不存在")
        return None

def extract_keywords(text, model_path='keyword_model.pkl', n=5, priority_keywords=None)->list[str]:
    """
    从文本中提取前 n 个关键词，使用预训练模型，优先考虑语料库中的关键词。
    
    参数：
    - text: 输入文本
    - model_path: 预训练模型路径
    - n: 返回的关键词数量
    - priority_keywords: 优先级关键词列表（可选）
    """
    # 加载模型
    corpus_keywords = load_keyword_model(model_path)
    if not corpus_keywords:
        return []
    
    # 预处理输入文本
    words = preprocess_text(text)
    text_cleaned = ' '.join(words)
    
    # 计算 TF-IDF 分数
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform([text_cleaned])
    feature_names = vectorizer.get_feature_names_out()
    tfidf_scores = tfidf_matrix.toarray()[0]
    
    # 创建关键词及其 TF-IDF 分数的字典
    keyword_tfidf = {feature_names[i]: tfidf_scores[i] for i in range(len(feature_names))}
    
    # 综合评分：结合 TF-IDF 和语料库频率，并为优先级关键词加权
    combined_scores = {}
    priority_weight = 3.0  # 优先级关键词的额外权重（可调整）
    
    for word in keyword_tfidf:
        if word in corpus_keywords:
            # 语料库中的关键词获得基于频率的加权
            score = keyword_tfidf[word] * (1 + corpus_keywords[word])
            # 如果是优先级关键词，进一步增加权重
            if priority_keywords and word in priority_keywords:
                score *= priority_weight
            combined_scores[word] = score
        else:
            combined_scores[word] = keyword_tfidf[word]
    
    # 按综合分数排序关键词
    sorted_keywords = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)
    
    # 返回前 n 个关键词
    return sorted_keywords[:n]


async def extract_crypto_tag(text)->list[str]:
    tasks = [translate_english(kv[0]) for kv in extract_keywords(text, model_path='D:/ai_crypto/init/tokenization_alg/keyword_model.pkl', n=3, priority_keywords=[]) ]
    return await asyncio.gather(*tasks)

res = extract_crypto_tag("由于缺乏明确的用例、合作伙伴关系或社区支持，PROTEST 代币的市场分析非常困难。 空投抗议的概念可能吸引那些对特定事业充满热情的人，但也可能面临来自监管机构的审查，以及因与政治运动挂钩而导致的价格波动。 网络搜索结果显示，加密货币已被用于抗议活动，但同时也显示了公众对某些加密货币（如比特币在萨尔瓦多的使用）的抗议。 此外，代币供应量的差异表明存在潜在风险，用户应审慎判断。 总的来说，该代币的市场需求和长期可持续性高度不确定。 由于该项目还处于早期阶段，流动性可能较低，并且价格容易受到操纵。")

print(res)