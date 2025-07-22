import re
import jieba
import nltk
from nltk.corpus import stopwords
from collections import Counter
import pickle
import os





def process_text(text):
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

def train_keyword_model(corpus_files, priority_keywords=None, output_path='keyword_model.pkl'):
    """
    从语料库文件列表中训练关键词模型，仅保留中英文，保存为 pickle 文件。
    
    参数：
    - corpus_files: 语料库文件路径列表
    - priority_keywords: 优先级关键词列表（可选）
    - output_path: 保存模型的路径
    """
    # 初始化关键词频率计数器,因为本次不需要避免极端大词的影响
    word_freq = Counter()
    
    # 处理每个语料库文件
    for file_path in corpus_files:
        if not os.path.exists(file_path):
            print(f"文件 {file_path} 不存在，跳过")
            continue
        print(file_path)
        with open(file_path, 'r', encoding='utf-8',errors='ignore') as f:
            text = f.read()
            # 预处理文本并更新频率
            words = process_text(text)
            word_freq.update(words)
    
    # 为优先级关键词加权（频率加倍）
    if priority_keywords:
        for keyword in priority_keywords:
            if keyword in word_freq:
                word_freq[keyword] *= 2  # 可调整权重因子
    
    # 保存模型
    with open(output_path, 'wb') as f:
        pickle.dump(word_freq, f)
    print(f"模型已保存至 {output_path}")
    
    return word_freq

# 示例用法
if __name__ == "__main__":
    # 假设语料库文件列表（支持多个 .txt 文件）
    # corpus_files = ['corpus1.txt', 'corpus2.txt']  # 替换为实际文件路径
    # 优先级关键词
    # priority_keywords = ['关键词', '自然语言', '提取']
    prefix = os.path.join("./train")
    corpus_files = [os.path.join(prefix, file) for file in os.listdir(prefix)]
   
    # 训练并保存模型
    model = train_keyword_model(corpus_files, [], 'keyword_model.pkl')


