"""
基于正确Google引擎的搜索爬虫
"""
import logging
import sys
import os
from typing import List, Dict, Generator
from datetime import datetime

# 添加google_crawl目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'google_crawl'))

from google_crawl.google_engine import search, SearchResult
from elasticsearch_manager import ElasticsearchManager
import config

logger = logging.getLogger(__name__)

class GoogleSearchCrawler:
    """Google搜索爬虫，使用正确的搜索引擎"""
    
    def __init__(self):
        """初始化爬虫"""
        self.es_manager = ElasticsearchManager()
        logger.info("Google搜索爬虫初始化完成")
    
    def crawl_and_store(self, query: str, num_results: int = 50, 
                       query_intent: str = None, **kwargs) -> Dict:
        """爬取搜索结果并存储到Elasticsearch"""
        try:
            logger.info(f"开始爬取搜索结果: '{query}', 数量: {num_results}")
            
            # 设置默认参数
            search_params = {
                'num_results': num_results,
                'lang': config.LANGUAGE,
                'advanced': True,  # 使用advanced=True获取SearchResult对象
                'sleep_interval': config.SLEEP_INTERVAL,
                'timeout': config.REQUEST_TIMEOUT,
                'safe': config.SAFE_SEARCH,
                'region': config.REGION,
                'unique': True  # 确保结果唯一
            }
            
            # 更新用户提供的参数
            search_params.update(kwargs)
            
            # 执行搜索
            search_results = list(search(query, **search_params))
            
            if not search_results:
                logger.warning("没有获取到搜索结果")
                return {'success': False, 'message': '没有获取到搜索结果'}
            
            # 转换为字典格式
            formatted_results = self._format_search_results(search_results)
            logger.info(f"获取到 {len(formatted_results)} 条搜索结果")
            
            # 存储到Elasticsearch
            success = self.es_manager.save_search_results(
                formatted_results, query, query_intent
            )
            
            if success:
                # 计算统计信息
                stats = self._calculate_stats(formatted_results, query)
                logger.info(f"爬取完成，统计信息: {stats}")
                
                return {
                    'success': True,
                    'query': query,
                    'results_count': len(formatted_results),
                    'stats': stats
                }
            else:
                return {'success': False, 'message': '存储到Elasticsearch失败'}
                
        except Exception as e:
            logger.error(f"爬取过程中发生错误: {e}")
            return {'success': False, 'message': str(e)}
    
    def _format_search_results(self, search_results: List[SearchResult]) -> List[Dict]:
        """将SearchResult对象转换为字典格式"""
        formatted_results = []
        
        for rank, result in enumerate(search_results, 1):
            formatted_result = {
                'title': result.title,
                'url': result.url,
                'description': result.description,
                'rank': rank,
                'page_number': (rank - 1) // 10 + 1  # 计算页面编号
            }
            formatted_results.append(formatted_result)
        
        return formatted_results
    
    def _calculate_stats(self, results: List[Dict], query: str) -> Dict:
        """计算爬取统计信息"""
        if not results:
            return {}
        
        # 域名统计
        domains = {}
        for result in results:
            try:
                from urllib.parse import urlparse
                domain = urlparse(result['url']).netloc
                domains[domain] = domains.get(domain, 0) + 1
            except:
                domains['unknown'] = domains.get('unknown', 0) + 1
        
        # 内容长度统计
        title_lengths = [len(r.get('title', '')) for r in results]
        desc_lengths = [len(r.get('description', '')) for r in results]
        
        return {
            'total_results': len(results),
            'unique_domains': len(domains),
            'domain_distribution': dict(sorted(domains.items(), key=lambda x: x[1], reverse=True)[:10]),
            'avg_title_length': sum(title_lengths) / len(title_lengths) if title_lengths else 0,
            'avg_description_length': sum(desc_lengths) / len(desc_lengths) if desc_lengths else 0,
            'query': query,
            'crawl_time': datetime.now().isoformat()
        }
    
    def search_stored_results(self, query: str = None, category: str = None,
                            min_quality_score: float = 0.0, size: int = 100) -> List[Dict]:
        """搜索已存储的结果"""
        try:
            results = self.es_manager.search_training_data(
                query=query, 
                category=category,
                min_quality_score=min_quality_score,
                size=size
            )
            logger.info(f"从Elasticsearch搜索到 {len(results)} 条结果")
            return results
        except Exception as e:
            logger.error(f"搜索存储结果时发生错误: {e}")
            return []
    
    def export_training_data(self, output_format: str = 'jsonl', 
                           min_quality_score: float = 0.5, 
                           output_file: str = None) -> str:
        """导出大模型训练数据"""
        try:
            data = self.es_manager.export_for_llm_training(
                output_format=output_format,
                min_quality_score=min_quality_score
            )
            
            if output_file:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(data)
                logger.info(f"训练数据已导出到: {output_file}")
            
            return data
            
        except Exception as e:
            logger.error(f"导出训练数据时发生错误: {e}")
            return ""
    
    def batch_crawl(self, queries: List[str], num_results_per_query: int = 50,
                   query_intents: List[str] = None) -> Dict:
        """批量爬取多个查询"""
        results = {
            'successful_queries': 0,
            'failed_queries': 0,
            'total_results': 0,
            'query_results': {}
        }
        
        query_intents = query_intents or [None] * len(queries)
        
        for i, query in enumerate(queries):
            intent = query_intents[i] if i < len(query_intents) else None
            
            logger.info(f"批量爬取进度: {i+1}/{len(queries)} - {query}")
            
            result = self.crawl_and_store(
                query=query,
                num_results=num_results_per_query,
                query_intent=intent
            )
            
            if result['success']:
                results['successful_queries'] += 1
                results['total_results'] += result['results_count']
                results['query_results'][query] = result
            else:
                results['failed_queries'] += 1
                results['query_results'][query] = result
                logger.warning(f"查询失败: {query} - {result['message']}")
        
        logger.info(f"批量爬取完成: 成功 {results['successful_queries']}/{len(queries)}")
        return results
    
    def get_stats(self) -> Dict:
        """获取爬虫统计信息"""
        try:
            return self.es_manager.get_stats()
        except Exception as e:
            logger.error(f"获取统计信息时发生错误: {e}")
            return {}
    
    def get_training_data_sample(self, size: int = 10) -> List[Dict]:
        """获取训练数据样本"""
        return self.search_stored_results(size=size)

class MarketAnalysisCrawler(GoogleSearchCrawler):
    """专门用于市场分析的爬虫"""
    
    def __init__(self):
        super().__init__()
        self.market_categories = {
            'startup_opportunities': '创业机会',
            'market_trends': '市场趋势',
            'competitor_analysis': '竞争分析',
            'investment_insights': '投资洞察',
            'technology_trends': '技术趋势'
        }
    
    def analyze_market_sector(self, sector: str, num_results: int = 100) -> Dict:
        """分析特定市场领域"""
        queries = [
            f"{sector} 市场分析",
            f"{sector} 发展趋势",
            f"{sector} 创业机会",
            f"{sector} 投资前景",
            f"{sector} 竞争格局"
        ]
        
        intents = ['research', 'trend_analysis', 'opportunity', 'investment', 'competitive']
        
        return self.batch_crawl(queries, num_results_per_query=num_results//len(queries), 
                               query_intents=intents)
    
    def monitor_startup_trends(self, industries: List[str], num_results: int = 50) -> Dict:
        """监控创业趋势"""
        all_queries = []
        all_intents = []
        
        for industry in industries:
            queries = [
                f"{industry} 创业趋势 2024",
                f"{industry} 投资热点",
                f"{industry} 新兴公司"
            ]
            intents = ['trend_analysis', 'investment', 'startup_discovery']
            
            all_queries.extend(queries)
            all_intents.extend(intents)
        
        return self.batch_crawl(all_queries, num_results_per_query=num_results//len(all_queries),
                               query_intents=all_intents)
    
    def generate_market_report(self, sector: str, output_file: str = None) -> str:
        """生成市场报告"""
        # 分析市场领域
        analysis_result = self.analyze_market_sector(sector)
        
        # 搜索相关数据
        related_data = self.search_stored_results(
            query=sector,
            min_quality_score=0.6,
            size=200
        )
        
        # 生成报告
        report = self._generate_report_text(sector, analysis_result, related_data)
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report)
            logger.info(f"市场报告已生成: {output_file}")
        
        return report
    
    def _generate_report_text(self, sector: str, analysis_result: Dict, 
                            related_data: List[Dict]) -> str:
        """生成报告文本"""
        report = f"# {sector} 市场分析报告\n\n"
        report += f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        # 数据收集概况
        report += "## 数据收集概况\n"
        report += f"- 成功查询: {analysis_result.get('successful_queries', 0)}\n"
        report += f"- 总计数据: {analysis_result.get('total_results', 0)} 条\n"
        report += f"- 高质量数据: {len(related_data)} 条\n\n"
        
        # 主要信息源
        if related_data:
            domains = {}
            for item in related_data:
                domain = item.get('domain', 'unknown')
                domains[domain] = domains.get(domain, 0) + 1
            
            report += "## 主要信息源\n"
            for domain, count in sorted(domains.items(), key=lambda x: x[1], reverse=True)[:10]:
                report += f"- {domain}: {count} 条信息\n"
            report += "\n"
        
        # 关键发现
        report += "## 关键发现\n"
        categories = {}
        for item in related_data:
            category = item.get('category', 'general')
            categories[category] = categories.get(category, 0) + 1
        
        for category, count in categories.items():
            report += f"- {category}: {count} 条相关信息\n"
        
        report += "\n## 详细数据\n"
        report += "详细的搜索结果和分析数据已存储在Elasticsearch中，可通过API查询获取。\n"
        
        return report
