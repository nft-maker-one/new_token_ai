import asyncio
import json
import os
import sys
from typing import Optional, List, Dict, Any
from datetime import datetime
import aiohttp
import google.generativeai as genai
import requests

# 添加google_crawl目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'google_crawl'))

from backend.models.token import TokenData, AnalysisResult, NarrativeAnalysis, RiskLevel, MarketAnalysis, WebSearchResult,SimpleAnalysisResult
from backend.services.message_queue import MessageQueue
from backend.utils.logger import setup_logger
from backend.utils.env_loader import get_env_var
# uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reloa
# 导入高效Google搜索引擎
try:
    from backend.google_engine import search_crypto_info, SearchResult
    GOOGLE_ENGINE_AVAILABLE = True
    logger = setup_logger(__name__)
    logger.info("✅ 高效Google搜索引擎已加载")
except ImportError as e:
    GOOGLE_ENGINE_AVAILABLE = False
    logger = setup_logger(__name__)
    logger.warning(f"⚠️ 高效Google搜索引擎不可用，将使用简化搜索: {e}")

logger = setup_logger(__name__)

class AIAnalyzer:
    """AI分析服务，使用Gemini进行代币分析"""

    def __init__(self, message_queue: MessageQueue, max_concurrent_ai_requests: int = 1):
        self.message_queue = message_queue
        self.is_running = False
        self.gemini_model = None

        # AI并发控制
        self.max_concurrent_ai_requests = max_concurrent_ai_requests
        self.ai_semaphore = asyncio.Semaphore(max_concurrent_ai_requests)
        self.active_ai_requests = 0
        self.ai_request_lock = asyncio.Lock()

        # 统计信息
        self.total_requests = 0
        self.completed_requests = 0
        self.failed_requests = 0

        logger.info(f"AI分析器初始化，最大并发AI请求数: {max_concurrent_ai_requests}")
        # 不再需要Google API密钥，使用高效爬虫
        
    async def initialize(self):
        """初始化AI服务"""
        # 配置Gemini API
        try:
            gemini_api_key = get_env_var("GEMINI_API_KEY", required=True)
            logger.info(f"use gemini key {gemini_api_key[:8]}...")

            genai.configure(api_key=gemini_api_key)
            # 使用最新的Gemini模型名称
            self.gemini_model = genai.GenerativeModel('gemini-2.0-flash')

            logger.info("Gemini AI服务初始化完成")

            tweet_endpoint = get_env_var("TWITTER_API_ENDPOINT",required=True)
            logger.info("成功找 tweet 搜索路由")
            self.tweet_endpoint = tweet_endpoint
        except ValueError as e:
            logger.error(f"❌ Gemini API初始化失败: {e}")
            raise

    async def _controlled_ai_request(self, request_func, *args, **kwargs):
        """受并发控制的AI请求包装器"""
        async with self.ai_semaphore:  # 获取信号量，限制并发数
            async with self.ai_request_lock:
                self.active_ai_requests += 1
                self.total_requests += 1
                current_active = self.active_ai_requests

            logger.info(f"🤖 开始AI请求 (活跃: {current_active}/{self.max_concurrent_ai_requests}, 总计: {self.total_requests})")

            try:
                # 执行实际的AI请求
                result = await request_func(*args, **kwargs)

                async with self.ai_request_lock:
                    self.completed_requests += 1

                logger.info(f"✅ AI请求完成 (完成: {self.completed_requests}, 失败: {self.failed_requests})")
                return result

            except Exception as e:
                async with self.ai_request_lock:
                    self.failed_requests += 1

                logger.error(f"❌ AI请求失败: {e} (完成: {self.completed_requests}, 失败: {self.failed_requests})")
                raise

            finally:
                async with self.ai_request_lock:
                    self.active_ai_requests -= 1
        
    async def start_consumer(self):
        """启动消费者，处理分析任务"""
        self.is_running = True
        logger.info("AI分析消费者已启动")
        
        while self.is_running:
            try:
                task = await self.message_queue.get_analysis_task()
                if task:
                    # 异步处理分析任务
                    asyncio.create_task(self._process_analysis_task(task))
                else:
                    # 没有任务时短暂休眠
                    await asyncio.sleep(0.1)
            except Exception as e:
                logger.error(f"消费者处理任务时出错: {e}")
                await asyncio.sleep(1)
                
    async def stop(self):
        """停止AI分析服务"""
        self.is_running = False
        logger.info("AI分析服务已停止")
        
    async def _process_analysis_task(self, task: Dict[str, Any]):
        """处理单个分析任务"""
        try:
            token_data_dict = task["token_data"]
        except:
            logger.error("_process_analysis_task error {e}")
            logger.error(f"task = {task}")
        token_data = TokenData(**token_data_dict)
        
        logger.info(f"开始分析代币: {token_data.symbol}")
        
        try:
            # 更新状态为分析中
            await self.message_queue.update_analysis_progress(
                token_data.mint, 10.0, "ANALYZING"
            )
            
            # 1. 网络搜索
            search_results = await self._search_token_info(token_data)
            await self.message_queue.update_analysis_progress(token_data.mint, 30.0)

            # 2. 推文分析
            tweet_analysis = await self._analyze_tweets(token_data)
            await self.message_queue.update_analysis_progress(token_data.mint, 50.0)

            # 3. 简单分析
            simple_analysis = await self._ai_analyze_simple(token_data,search_results,tweet_analysis)
            
            # 3. 叙事分析
            # narrative_analysis = await self._analyze_narrative(token_data, search_results)
            # await self.message_queue.update_analysis_progress(token_data.mint, 70.0)
            
            
            # 3. 风险评估
            # risk_assessment = await self._assess_risk(token_data, search_results)
            # await self.message_queue.update_analysis_progress(token_data.mint, 70.0)
            
            # 4. 市场分析
            # market_analysis = await self._analyze_market(token_data)
            # await self.message_queue.update_analysis_progress(token_data.mint, 85.0)
            
            # 5. 生成AI总结
            # ai_summary = await self._generate_summary(
            #     token_data, narrative_analysis, risk_assessment, market_analysis, search_results
            # )
            # await self.message_queue.update_analysis_progress(token_data.mint, 95.0)
            
            # 6. 投资建议
            # investment_recommendation = await self._generate_investment_recommendation(
            #     token_data, narrative_analysis, risk_assessment, market_analysis
            # )
            
            # 创建完整的分析结果
            # analysis_result = AnalysisResult(
            #     token_mint=token_data.mint,
            #     token_symbol=token_data.symbol,
            #     token_name=token_data.name,
            #     status="COMPLETED",
            #     progress=100.0,
            #     narrative_analysis=narrative_analysis,
            #     risk_assessment=risk_assessment,
            #     market_analysis=market_analysis,
            #     web_search_results=search_results,
            #     ai_summary=ai_summary,
            #     investment_recommendation=investment_recommendation,
            #     analysis_completed_at=datetime.now()
            # )
            analysis_result = AnalysisResult(
                token_mint=token_data.mint,
                token_symbol=token_data.symbol,
                token_name=token_data.name,
                status="COMPLETED",
                progress=100.0,
                narrative_analysis=simple_analysis.narrative_analysis,
                risk_assessment=simple_analysis.risk_assessment,
                market_analysis=simple_analysis.market_analysis,
                web_search_results=search_results,
                tweet_result=[{"content":tweet_analyse['content'] if len(tweet_analyse['content'])<100 else tweet_analyse['content'][:100]+"...","link":tweet_analyse["t_url"]} for tweet_analyse in tweet_analysis],
                ai_summary=simple_analysis.ai_summary,
                investment_recommendation=simple_analysis.investment_recommendation,
                analysis_completed_at=datetime.now()
            )
            
            # 完成分析
            await self.message_queue.complete_analysis(analysis_result)
            
        except Exception as e:
            logger.error(f"分析代币 {token_data.symbol} 时出错: {e}")
            await self.message_queue.fail_analysis(token_data.mint, str(e))
            
    async def _analyze_tweets(self, token_data:TokenData) -> List[Dict[str,Any]]:
        def search_tweet(reqBody) -> List[Dict[str,Any]]:
            data = requests.post(self.tweet_endpoint,json=reqBody)
            if data.status_code==200:
                return data.json()['data']
            else:
                logger.error(f"收到错误的推特搜索结果 {data.json()}")
        try:
            reqBody = {
                "keyword":f"{token_data.mint}"
            }
            logger.info(f"use tweet search for ${token_data.symbol}({token_data.mint})")
            loop = asyncio.get_event_loop()
            # 将同步操作放入线程池，防止阻塞其他协程
            tweet_res = await loop.run_in_executor(
                None,
                search_tweet,
                reqBody
            )
            logger.info(f"推特搜索成功，得到 {len(tweet_res)} 个结果")
            return tweet_res

        except Exception as e:
            logger.error(f"推特搜索引擎失败")
            return []

        
    async def _search_token_info(self, token_data: TokenData) -> List[WebSearchResult]:
        """搜索代币相关信息 - 使用高效Google搜索引擎"""
        all_results = []

        # 方案1: 使用高效Google搜索引擎
        if GOOGLE_ENGINE_AVAILABLE:
            try:
                logger.info(f"🔍 使用高效Google搜索引擎搜索: {token_data.symbol}")

                # 使用异步方式运行同步的搜索函数
                loop = asyncio.get_event_loop()
                search_results = await loop.run_in_executor(
                    None,
                    search_crypto_info,
                    token_data.symbol,
                    token_data.mint,
                    6  # 获取12个结果
                )

                logger.info(f"✅ Google搜索获得 {len(search_results)} 个结果")

                # 转换为WebSearchResult格式
                for i, result in enumerate(search_results):
                    try:
                        web_result = WebSearchResult(
                            title=result.title or "无标题",
                            url=result.url or "",
                            snippet=result.description or "无描述",
                            relevance_score=max(95.0 - i * 3, 60.0)  # 根据排名计算相关性
                        )
                        all_results.append(web_result)
                    except Exception as e:
                        logger.warning(f"转换搜索结果失败: {e}")

            except Exception as e:
                logger.error(f"Google搜索引擎失败: {e}")

        # 方案2: 如果Google搜索失败，使用简化搜索
        if not all_results:
            logger.info("🔍 Google搜索失败，使用简化搜索方案")
            all_results = await self._simple_search(token_data)

        logger.info(f"🔍 总共获得 {len(all_results)} 个搜索结果")
        return all_results[:15]  # 返回前15个最相关的结果

    async def _simple_search(self, token_data: TokenData) -> List[WebSearchResult]:
        """简化搜索方案 - 生成基于代币信息的模拟搜索结果"""
        results = []

        # 基于代币信息生成相关的搜索结果
        base_results = [
            {
                "title": f"{token_data.name} ({token_data.symbol}) - Pump.fun代币信息",
                "url": f"https://pump.fun/coin/{token_data.mint}",
                "snippet": f"{token_data.name}是一个在Pump.fun平台上发布的代币，符号为{token_data.symbol}。总供应量：{token_data.token_total_supply}。",
                "relevance": 95.0
            },
            {
                "title": f"{token_data.symbol} 代币分析 - 加密货币市场",
                "url": f"https://coinmarketcap.com/currencies/{token_data.symbol.lower()}",
                "snippet": f"查看{token_data.name} ({token_data.symbol})的最新价格、市值和交易数据。这是一个新兴的加密货币项目。",
                "relevance": 85.0
            },
            {
                "title": f"{token_data.name} 社区讨论 - Reddit",
                "url": f"https://reddit.com/r/cryptocurrency/search?q={token_data.symbol}",
                "snippet": f"Reddit社区对{token_data.name} ({token_data.symbol})的讨论和分析。了解社区对该项目的看法。",
                "relevance": 75.0
            },
            {
                "title": f"{token_data.symbol} 技术分析 - CoinGecko",
                "url": f"https://coingecko.com/en/coins/{token_data.symbol.lower()}",
                "snippet": f"{token_data.name}的技术指标、价格历史和市场数据分析。虚拟储备：{token_data.virtual_token_reserves}。",
                "relevance": 80.0
            },
            {
                "title": f"如何购买 {token_data.name} ({token_data.symbol})",
                "url": f"https://dexscreener.com/solana/{token_data.mint}",
                "snippet": f"在DEX上交易{token_data.name}的指南。当前虚拟SOL储备：{token_data.virtual_sol_reserves}。",
                "relevance": 70.0
            }
        ]

        # 转换为WebSearchResult格式
        for result_data in base_results:
            try:
                result = WebSearchResult(
                    title=result_data["title"],
                    url=result_data["url"],
                    snippet=result_data["snippet"],
                    relevance_score=result_data["relevance"]
                )
                results.append(result)
            except Exception as e:
                logger.warning(f"创建搜索结果失败: {e}")

        logger.info(f"✅ 生成了 {len(results)} 个模拟搜索结果")
        return results

    async def _ai_analyze_simple(self,token_data,search_results:List[WebSearchResult],tweet_results:List[Dict[str,Any]])->SimpleAnalysisResult:
        """分析代币叙事"""
        async def _do_ai_analyze_simple():
            logger.info(f"enter _do_ai_analyze_simple result = {search_results}")
            google_context = "\n".join([
                f"标题: {result.title}\n摘要: {result.snippet}\n链接: {result.url}"
                for result in search_results[:5]
            ])
            
            tweet_context = "\n".join([
                f"推文内容: {tweet_result['content']}\n推文链接: {tweet_result['t_url']}\nlike:{tweet_result['favorite_count']} retweet:{tweet_result['retweet_count']} reply:{tweet_result['reply_count']}"
                for tweet_result in tweet_results
            ])
            logger.info(f"tweet_context = {tweet_context}")
            prompt = f"""
            分析以下加密货币代币的叙事背景：
            
            - 代币名称: {token_data.name}
            - 代币符号: {token_data.symbol}
            - 总供应量: {token_data.token_total_supply:,}
            - 虚拟代币储备: {token_data.virtual_token_reserves:,}
            - 虚拟SOL储备: {token_data.virtual_sol_reserves:,}
            - 实际代币储备: {token_data.real_token_reserves:,}
            
            网络搜索结果:
            {google_context}
            
            推文结果:
            {tweet_context}
            
            请分析：
                1. 项目的核心叙事和概念
                2. 风险评分: 0-100 (100为最高风险)
                3. 价格预测
                4. 简洁但全面的总结
                5. 投资建议
            请以JSON格式返回：
            {{
                "narrative_analysis": "叙事分析",
                "risk_assessment": "风险评估",
                "market_analysis": "市场分析",
                "ai_summary": "AI总结",
                "investment_recommendation": "投资建议"
            }}
            """
            logger.info(f"gemini simple analyze prompt {prompt}")
            try:
                response = await asyncio.to_thread(
                    self.gemini_model.generate_content,
                    prompt
                )
                logger.info(f"gemini simple analyze response {response.text}")
                return response.text.strip()
            except Exception as e:
                logger.error(f"Gemini API调用失败: {e}")
                raise
        try:
            result_text = await self._controlled_ai_request(_do_ai_analyze_simple)
            logger.info(f"simple analyze results {result_text}")
            if result_text.startswith("```json"):
                result_text = result_text[7:-3]
            elif result_text.startswith("```"):
                result_text = result_text[3:-3]
            result_data = json.loads(result_text)
            return SimpleAnalysisResult(**result_data)
        except Exception as e:
            logger.error(f"_ai_analyze_simple error {e}")
            return SimpleAnalysisResult(
                narrative_analysis="叙事分析失败",
                risk_assessment="风险评估失败",
                market_analysis="市场分析失败",
                ai_summary="AI总结失败",
                investment_recommendation="投资建议失败"
            )


        



    async def _analyze_narrative(self, token_data: TokenData, search_results: List[WebSearchResult]) -> NarrativeAnalysis:
        """分析代币叙事"""
        search_context = "\n".join([
            f"标题: {result.title}\n摘要: {result.snippet}\n链接: {WebSearchResult.url}"
            for result in search_results[:5]
        ])
        
        prompt = f"""
        分析以下加密货币代币的叙事背景：
        
        代币名称: {token_data.name}
        代币符号: {token_data.symbol}
        
        网络搜索结果:
        {search_context}
        
        请分析：
        1. 代币属于哪个类别 (MEME, DEFI, AI, GAMING, NFT, 等)
        2. 项目的核心叙事和概念
        3. 叙事的相关性评分 (0-100)
        4. 当前趋势分析
        
        请以JSON格式返回结果：
        {{
            "category": "类别",
            "description": "叙事描述",
            "relevance_score": 评分,
            "trend_analysis": "趋势分析"
        }}
        """
        
        # 定义实际的AI请求函数
        async def _do_narrative_analysis():
            try:
                # 将同步函数转化成异步函数，防止阻塞
                response = await asyncio.to_thread(
                    self.gemini_model.generate_content,
                    prompt
                )
                logger.info(f"_do_narrative_analysis response.text = {response.text}")
                return response.text.strip()
            except Exception as e:
                logger.error(f"Gemini API调用失败: {e}")
                raise

        try:
            logger.info(f'gemini analyze prompt {prompt}')
            # 使用并发控制的AI请求
            result_text = await self._controlled_ai_request(_do_narrative_analysis)
            # 尝试解析JSON
            if result_text.startswith("```json"):
                result_text = result_text[7:-3]
            elif result_text.startswith("```"):
                result_text = result_text[3:-3]

            result_data = json.loads(result_text)

            return NarrativeAnalysis(**result_data)

        except Exception as e:
            logger.error(f"叙事分析失败: {e}")
            return NarrativeAnalysis(
                category="UNKNOWN",
                description="无法分析叙事背景",
                relevance_score=0.0,
                trend_analysis="分析失败"
            )
            
    async def _assess_risk(self, token_data: TokenData, search_results: List[WebSearchResult]) -> RiskLevel:
        """评估代币风险"""
        search_context = "\n".join([
            f"标题: {result.title}\n摘要: {result.snippet}"
            for result in search_results[:5]
        ])
        
        prompt = f"""
        评估以下加密货币代币的投资风险：
        
        代币信息:
        - 名称: {token_data.name}
        - 符号: {token_data.symbol}
        - 总供应量: {token_data.token_total_supply}
        - 虚拟代币储备: {token_data.virtual_token_reserves}
        - 虚拟SOL储备: {token_data.virtual_sol_reserves}
        
        网络搜索结果:
        {search_context}
        
        请从以下角度评估风险：
        1. 项目合法性
        2. 流动性风险
        3. 技术风险
        4. 市场风险
        5. 监管风险
        
        风险等级: LOW, MEDIUM, HIGH, CRITICAL
        风险评分: 0-100 (100为最高风险)
        
        请以JSON格式返回：
        {{
            "level": "风险等级",
            "score": 评分,
            "description": "详细风险描述"
        }}
        """
        
        # 定义实际的AI请求函数
        async def _do_risk_assessment():
            try:
                response = await asyncio.to_thread(
                    self.gemini_model.generate_content,
                    prompt
                )
                return response.text.strip()
            except Exception as e:
                logger.error(f"Gemini API调用失败: {e}")
                raise

        try:
            # 使用并发控制的AI请求
            result_text = await self._controlled_ai_request(_do_risk_assessment)
            logger.info(f"assess_risk = {result_text}")
            if result_text.startswith("```json"):
                result_text = result_text[7:-3]
            elif result_text.startswith("```"):
                result_text = result_text[3:-3]

            result_data = json.loads(result_text)

            return RiskLevel(**result_data)

        except Exception as e:
            logger.error(f"风险评估失败: {e}")
            return RiskLevel(
                level="HIGH",
                score=80.0,
                description="无法完成风险评估，建议谨慎投资"
            )

    async def _analyze_market(self, token_data: TokenData) -> MarketAnalysis:
        """分析市场数据"""
        # 计算一些基本指标
        if token_data.virtual_sol_reserves > 0 and token_data.virtual_token_reserves > 0:
            estimated_price = token_data.virtual_sol_reserves / token_data.virtual_token_reserves
        else:
            estimated_price = 0

        prompt = f"""
        分析以下代币的市场数据：

        代币信息:
        - 名称: {token_data.name}
        - 符号: {token_data.symbol}
        - 总供应量: {token_data.token_total_supply:,}
        - 虚拟代币储备: {token_data.virtual_token_reserves:,}
        - 虚拟SOL储备: {token_data.virtual_sol_reserves:,}
        - 实际代币储备: {token_data.real_token_reserves:,}
        - 估算价格: {estimated_price:.10f} SOL

        请分析：
        1. 流动性状况
        2. 交易量分析
        3. 持有者分析
        4. 价格预测

        请以JSON格式返回：
        {{
            "liquidity_analysis": "流动性分析",
            "volume_analysis": "交易量分析",
            "holder_analysis": "持有者分析",
            "price_prediction": "价格预测"
        }}
        """

        # 定义实际的AI请求函数
        async def _do_market_analysis():
            try:
                response = await asyncio.to_thread(
                    self.gemini_model.generate_content,
                    prompt
                )
                return response.text.strip()
            except Exception as e:
                logger.error(f"Gemini API调用失败: {e}")
                raise

        try:
            # 使用并发控制的AI请求
            result_text = await self._controlled_ai_request(_do_market_analysis)

            if result_text.startswith("```json"):
                result_text = result_text[7:-3]
            elif result_text.startswith("```"):
                result_text = result_text[3:-3]

            result_data = json.loads(result_text)

            return MarketAnalysis(**result_data)

        except Exception as e:
            logger.error(f"市场分析失败: {e}")
            return MarketAnalysis(
                liquidity_analysis="流动性数据不足",
                volume_analysis="交易量数据不足",
                holder_analysis="持有者数据不足",
                price_prediction="无法预测价格"
            )

    async def _generate_summary(self, token_data: TokenData, narrative: NarrativeAnalysis,
                              risk: RiskLevel, market: MarketAnalysis,
                              search_results: List[WebSearchResult]) -> str:
        """生成AI总结"""
        prompt = f"""
        基于以下分析结果，为代币 {token_data.name} ({token_data.symbol}) 生成一个全面的总结：

        叙事分析:
        - 类别: {narrative.category}
        - 描述: {narrative.description}
        - 相关性评分: {narrative.relevance_score}
        - 趋势分析: {narrative.trend_analysis}

        风险评估:
        - 风险等级: {risk.level}
        - 风险评分: {risk.score}
        - 风险描述: {risk.description}

        市场分析:
        - 流动性: {market.liquidity_analysis}
        - 交易量: {market.volume_analysis}
        - 持有者: {market.holder_analysis}
        - 价格预测: {market.price_prediction}

        请生成一个简洁但全面的总结，包括：
        1. 项目概述
        2. 主要优势和风险
        3. 市场表现分析
        4. 关键注意事项

        总结应该客观、专业，适合投资者参考。
        """

        # 定义实际的AI请求函数
        async def _do_summary_generation():
            try:
                response = await asyncio.to_thread(
                    self.gemini_model.generate_content,
                    prompt
                )
                return response.text.strip()
            except Exception as e:
                logger.error(f"Gemini API调用失败: {e}")
                raise

        try:
            # 使用并发控制的AI请求
            result = await self._controlled_ai_request(_do_summary_generation)
            return result
        except Exception as e:
            logger.error(f"生成总结失败: {e}")
            return f"无法生成 {token_data.symbol} 的详细分析总结。建议进行进一步研究。"

    async def _generate_investment_recommendation(self, token_data: TokenData, narrative: NarrativeAnalysis,
                                                risk: RiskLevel, market: MarketAnalysis) -> str:
        """生成投资建议"""
        prompt = f"""
        基于以下分析，为代币 {token_data.name} ({token_data.symbol}) 提供投资建议：

        风险等级: {risk.level} (评分: {risk.score})
        叙事相关性: {narrative.relevance_score}
        项目类别: {narrative.category}

        请提供：
        1. 明确的投资建议 (强烈推荐/推荐/中性/不推荐/强烈不推荐)
        2. 建议的投资策略
        3. 风险管理建议
        4. 关键监控指标

        建议应该基于风险评估和市场分析，保持客观和专业。
        """
        logger.info(f"Generate content for {prompt}")

        # 定义实际的AI请求函数
        async def _do_recommendation_generation():
            try:
                response = await asyncio.to_thread(
                    self.gemini_model.generate_content,
                    prompt
                )
                return response.text.strip()
            except Exception as e:
                logger.error(f"Gemini API调用失败: {e}")
                raise

        try:
            # 使用并发控制的AI请求
            result = await self._controlled_ai_request(_do_recommendation_generation)
            return result
        except Exception as e:
            logger.error(f"生成投资建议失败: {e}")
            return "由于分析限制，无法提供具体投资建议。请谨慎投资并进行自己的研究。"



