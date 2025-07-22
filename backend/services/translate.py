from googletrans import Translator
import asyncio

async def translate_text(text, src='zh-cn', dest='en'):
    translator = Translator()
    try:
        translated = await translator.translate(text, src=src, dest=dest)
        return translated.text
    except Exception as e:
        return f"翻译失败: {str(e)}"

def is_chinese_or_english(keyword):
    """
    判断关键字是中文还是英文
    返回值: 'chinese'（全中文）, 'english'（全英文）, 'mixed'（混合或其他）
    """
    if not keyword:
        return 'empty'
    
    has_chinese = False
    has_english = False
    
    for char in keyword:
        # 中文字符范围：U+4E00 到 U+9FFF
        if '\u4e00' <= char <= '\u9fff':
            has_chinese = True
        # 英文字符范围：A-Z, a-z
        elif char.isalpha() and char.isascii():
            has_english = True
        # 其他字符（如数字、符号）不影响判断，但若只有其他字符则返回 'mixed'
    
    if has_chinese and has_english:
        return 'mixed'
    elif has_chinese:
        return 'chinese'
    elif has_english:
        return 'english'
    else:
        return 'mixed'  # 仅含数字、符号或其他字符


async def translate_english(word:str)->str:
    types = is_chinese_or_english(word)
    if types != "chinese":
        return word
    return await translate_text(word)

async def main():

    # 测试
    keywords = ["你好", "Hello", "你好Hello", "123", "你好123", "Hello123"]
    for kw in keywords:
        print(f"关键字: {kw} -> {is_chinese_or_english(kw)}")
    # 示例
    text = "你好，世界！"
    translated_text = await translate_text(text, src='zh-cn', dest='en')
    print(f"原文: {text}")
    print(f"译文: {translated_text}")

    # 反向翻译
    text_en = "Hello, World!"
    translated_text_cn = await translate_text(text_en, src='en', dest='zh-cn')
    print(f"原文: {text_en}")
    print(f"译文: {translated_text_cn}")

# asyncio.run(main())