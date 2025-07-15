"""
高效Google搜索引擎
基于googlesearch库的优化版本
"""

from time import sleep
from bs4 import BeautifulSoup
from requests import get
from urllib.parse import unquote
import random
from backend.utils.logger import setup_logger

logger = setup_logger(__name__)


def get_useragent():
    """
    生成随机用户代理字符串，模拟各种软件版本的格式。
    
    Returns:
        str: 随机生成的用户代理字符串
    """
    lynx_version = f"Lynx/{random.randint(2, 3)}.{random.randint(8, 9)}.{random.randint(0, 2)}"
    libwww_version = f"libwww-FM/{random.randint(2, 3)}.{random.randint(13, 15)}"
    ssl_mm_version = f"SSL-MM/{random.randint(1, 2)}.{random.randint(3, 5)}"
    openssl_version = f"OpenSSL/{random.randint(1, 3)}.{random.randint(0, 4)}.{random.randint(0, 9)}"
    return f"{lynx_version} {libwww_version} {ssl_mm_version} {openssl_version}"


def _req(term, results, lang, start, proxies, timeout, safe, ssl_verify, region):
    """发送Google搜索请求"""
    try:
        resp = get(
            url="https://www.google.com/search",
            headers={
                "User-Agent": get_useragent(),
                "Accept": "*/*"
            },
            params={
                "q": term,
                "num": results + 2,  # 防止多次请求
                "hl": lang,
                "start": start,
                "safe": safe,
                "gl": region,
            },
            proxies=proxies,
            timeout=timeout,
            verify=ssl_verify,
            cookies={
                'CONSENT': 'PENDING+987',  # 绕过同意页面
                'SOCS': 'CAESHAgBEhIaAB',
            }
        )
        resp.raise_for_status()
        logger.debug(f"Google搜索请求成功: {term}")
        return resp
    except Exception as e:
        logger.error(f"Google搜索请求失败: {e}")
        raise


class SearchResult:
    """搜索结果类"""
    
    def __init__(self, url, title, description):
        self.url = url
        self.title = title
        self.description = description

    def __repr__(self):
        return f"SearchResult(url={self.url}, title={self.title}, description={self.description})"

    def __str__(self):
        return f"{self.title},{self.url},{self.description}\n"


def search(term, num_results=10, lang="en", proxy=None, advanced=False, 
          sleep_interval=0, timeout=5, safe="active", ssl_verify=None, 
          region=None, start_num=0, unique=False):
    """
    搜索Google搜索引擎
    
    Args:
        term: 搜索词
        num_results: 结果数量
        lang: 语言
        proxy: 代理
        advanced: 是否返回SearchResult对象
        sleep_interval: 请求间隔
        timeout: 超时时间
        safe: 安全搜索
        ssl_verify: SSL验证
        region: 地区
        start_num: 起始位置
        unique: 是否去重
        
    Yields:
        SearchResult或str: 搜索结果
    """
    logger.info(f"🔍 开始Google搜索: {term} (需要{num_results}个结果)")
    
    # 代理设置
    proxies = None
    if proxy and (proxy.startswith("https") or proxy.startswith("http") or proxy.startswith("socks5")):
        proxies = {"https": proxy, "http": proxy}

    start = start_num
    fetched_results = 0  # 跟踪总获取结果数
    fetched_links = set()  # 跟踪已见过的链接

    while fetched_results < num_results:
        try:
            # 发送请求
            resp = _req(term, num_results - start, lang, start, proxies, timeout, safe, ssl_verify, region)
            
            # 解析HTML
            soup = BeautifulSoup(resp.text, "html.parser")
            result_block = soup.find_all("div", class_="ezO2md")
            new_results = 0  # 跟踪本次迭代的新结果数

            logger.debug(f"找到 {len(result_block)} 个搜索结果块")

            for result in result_block:
                try:
                    # 在结果块中查找链接标签
                    link_tag = result.find("a", href=True)
                    # 在链接标签中查找标题标签
                    title_tag = link_tag.find("span", class_="CVA68e") if link_tag else None
                    # 在结果块中查找描述标签
                    description_tag = result.find("span", class_="FrIlee")

                    # 检查是否找到所有必要的标签
                    if link_tag and title_tag and description_tag:
                        # 提取并解码链接URL
                        link = unquote(link_tag["href"].split("&")[0].replace("/url?q=", "")) if link_tag else ""
                        
                        # 检查链接是否已获取过，如果需要唯一结果
                        if link in fetched_links and unique:
                            continue  # 如果链接不唯一则跳过此结果
                        
                        # 将链接添加到已获取链接集合
                        fetched_links.add(link)
                        
                        # 提取标题文本
                        title = title_tag.text if title_tag else ""
                        # 提取描述文本
                        description = description_tag.text if description_tag else ""
                        
                        # 增加获取结果计数
                        fetched_results += 1
                        # 增加本次迭代新结果计数
                        new_results += 1
                        
                        # 根据advanced标志返回结果
                        if advanced:
                            yield SearchResult(link, title, description)  # 返回SearchResult对象
                        else:
                            yield link  # 只返回链接

                        if fetched_results >= num_results:
                            break  # 如果已获取所需数量的结果则停止
                            
                except Exception as e:
                    logger.warning(f"解析搜索结果项失败: {e}")
                    continue

            if new_results == 0:
                logger.warning(f"查询 '{term}' 只找到 {fetched_results} 个结果，需要 {num_results} 个结果")
                break  # 如果本次迭代没有找到新结果则跳出循环

            start += 10  # 准备下一组结果
            if sleep_interval > 0:
                sleep(sleep_interval)
                
        except Exception as e:
            logger.error(f"搜索过程中出错: {e}")
            break

    logger.info(f"✅ Google搜索完成: {term} (获得{fetched_results}个结果)")


def search_crypto_info(token_symbol,token_ca,num_results=12):
    """
    专门用于加密货币信息搜索的便捷函数
    
    Args:
        token_name: 代币名称
        token_symbol: 代币符号
        num_results: 结果数量
        
    Returns:
        List[SearchResult]: 搜索结果列表
    """
    queries = [
        f"${token_symbol}[{token_ca}] cryptocurrency",
        f"${token_symbol}[{token_ca}] token pump.fun",
        # f"${token_symbol}[{token_ca}] crypto project analysis",
        # f"${token_symbol}[{token_ca}] meme coin review"
    ]
    
    all_results = []
    
    for query in queries:
        try:
            results = list(search(
                query,
                num_results=max(6, num_results // len(queries)),
                lang='en',
                advanced=True,
                sleep_interval=0.5,
                timeout=10,
                safe='active',
                unique=True
            ))
            all_results.extend(results)
            
            if len(all_results) >= num_results:
                break
                
        except Exception as e:
            logger.error(f"搜索查询 '{query}' 失败: {e}")
            continue
    
    return all_results[:num_results]
