"""
使用示例 - 展示如何使用基于正确Google引擎的爬虫
"""
import os
import time
from google_search_crawler import GoogleSearchCrawler, MarketAnalysisCrawler

def example_basic_crawling():
    """基础爬取示例"""
    print("=== 基础爬取示例 ===")
    
    crawler = GoogleSearchCrawler()
    
    # 单个查询爬取
    queries = [
        "人工智能创业机会",
        "区块链技术应用",
        "新能源汽车市场分析"
    ]
    
    for query in queries:
        print(f"\n正在爬取: {query}")
        result = crawler.crawl_and_store(
            query=query,
            num_results=20,
            query_intent='research'
        )
        
        if result['success']:
            print(f"✓ 成功爬取 {result['results_count']} 条结果")
            stats = result['stats']
            print(f"  - 唯一域名: {stats.get('unique_domains', 0)}")
            print(f"  - 主要信息源: {list(stats.get('domain_distribution', {}).keys())[:3]}")
        else:
            print(f"✗ 爬取失败: {result['message']}")
        
        # 避免请求过于频繁
        time.sleep(3)

def example_batch_crawling():
    """批量爬取示例"""
    print("\n=== 批量爬取示例 ===")
    
    # 创建批量查询文件
    batch_queries = [
        "Python编程教程",
        "机器学习算法",
        "数据科学工具",
        "深度学习框架",
        "人工智能应用"
    ]
    
    batch_file = "batch_queries.txt"
    with open(batch_file, 'w', encoding='utf-8') as f:
        for query in batch_queries:
            f.write(f"{query}\n")
    
    crawler = GoogleSearchCrawler()
    
    print(f"批量爬取 {len(batch_queries)} 个查询...")
    result = crawler.batch_crawl(
        queries=batch_queries,
        num_results_per_query=15
    )
    
    print(f"批量爬取完成:")
    print(f"  成功: {result['successful_queries']}/{len(batch_queries)}")
    print(f"  总结果: {result['total_results']} 条")
    
    # 清理临时文件
    if os.path.exists(batch_file):
        os.remove(batch_file)

def example_search_and_export():
    """搜索和导出示例"""
    print("\n=== 搜索和导出示例 ===")
    
    crawler = GoogleSearchCrawler()
    
    # 搜索已存储的数据
    print("搜索已存储的数据...")
    results = crawler.search_stored_results(
        query="人工智能",
        min_quality_score=0.5,
        size=10
    )
    
    if results:
        print(f"找到 {len(results)} 条高质量结果:")
        for i, result in enumerate(results[:3], 1):
            print(f"{i}. {result.get('title', 'N/A')}")
            print(f"   质量分数: {result.get('quality_score', 0):.2f}")
            print(f"   分类: {result.get('category', 'N/A')}")
    
    # 导出训练数据
    print("\n导出大模型训练数据...")
    
    # 导出JSONL格式
    jsonl_data = crawler.export_training_data(
        output_format='jsonl',
        min_quality_score=0.6,
        output_file='training_data.jsonl'
    )
    
    if jsonl_data:
        lines = jsonl_data.count('\n') + 1
        print(f"✓ JSONL格式导出完成: {lines} 条记录")
    
    # 导出指令-响应对格式
    instruction_data = crawler.export_training_data(
        output_format='instruction_pairs',
        min_quality_score=0.6,
        output_file='instruction_pairs.jsonl'
    )
    
    if instruction_data:
        lines = instruction_data.count('\n') + 1
        print(f"✓ 指令对格式导出完成: {lines} 条记录")

def example_market_analysis():
    """市场分析示例"""
    print("\n=== 市场分析示例 ===")
    
    market_crawler = MarketAnalysisCrawler()
    
    # 分析特定市场领域
    sector = "人工智能"
    print(f"分析市场领域: {sector}")
    
    result = market_crawler.analyze_market_sector(
        sector=sector,
        num_results=50
    )
    
    print(f"市场分析完成:")
    print(f"  成功查询: {result['successful_queries']}")
    print(f"  收集数据: {result['total_results']} 条")
    
    # 生成市场报告
    report_file = f"{sector}_market_report.md"
    report = market_crawler.generate_market_report(
        sector=sector,
        output_file=report_file
    )
    
    print(f"  报告文件: {report_file}")
    
    # 监控创业趋势
    print(f"\n监控创业趋势...")
    industries = ["人工智能", "区块链", "新能源"]
    
    trend_result = market_crawler.monitor_startup_trends(
        industries=industries,
        num_results=30
    )
    
    print(f"趋势监控完成:")
    print(f"  涉及行业: {len(industries)}")
    print(f"  收集数据: {trend_result['total_results']} 条")

def example_advanced_features():
    """高级功能示例"""
    print("\n=== 高级功能示例 ===")
    
    crawler = GoogleSearchCrawler()
    
    # 获取系统统计信息
    print("系统统计信息:")
    stats = crawler.get_stats()
    
    if stats:
        print(f"  总文档数: {stats.get('total_documents', 0):,}")
        print(f"  索引大小: {stats.get('index_size', 0):,} bytes")
        
        # 分类分布
        categories = stats.get('categories', {})
        if categories:
            print(f"  内容分类:")
            for category, count in list(categories.items())[:5]:
                print(f"    {category}: {count} 条")
        
        # 语言分布
        languages = stats.get('languages', {})
        if languages:
            print(f"  语言分布:")
            for lang, count in languages.items():
                lang_name = {'zh': '中文', 'en': '英文', 'mixed': '混合'}.get(lang, lang)
                print(f"    {lang_name}: {count} 条")
    
    # 获取训练数据样本
    print(f"\n训练数据样本:")
    samples = crawler.get_training_data_sample(size=3)
    
    for i, sample in enumerate(samples, 1):
        print(f"\n样本 {i}:")
        print(f"  查询: {sample.get('query', 'N/A')}")
        print(f"  标题: {sample.get('title', 'N/A')[:50]}...")
        print(f"  质量分数: {sample.get('quality_score', 0):.2f}")
        print(f"  训练文本预览:")
        training_text = sample.get('llm_training_text', '')
        print(f"    {training_text[:100]}...")

def example_custom_search_parameters():
    """自定义搜索参数示例"""
    print("\n=== 自定义搜索参数示例 ===")
    
    crawler = GoogleSearchCrawler()
    
    # 使用自定义参数
    result = crawler.crawl_and_store(
        query="machine learning tutorial",
        num_results=30,
        query_intent='educational',
        lang='en',
        region='us',
        safe='active',
        sleep_interval=1.5,
        timeout=15
    )
    
    if result['success']:
        print(f"✓ 自定义参数爬取成功")
        print(f"  结果数: {result['results_count']}")
        print(f"  查询意图: educational")
        print(f"  语言: 英文")
        print(f"  区域: 美国")
    
    # 按分类搜索
    print(f"\n按分类搜索教程内容:")
    tutorial_results = crawler.search_stored_results(
        category='tutorial',
        min_quality_score=0.7,
        size=5
    )
    
    for i, result in enumerate(tutorial_results, 1):
        print(f"{i}. {result.get('title', 'N/A')}")
        print(f"   分类: {result.get('category', 'N/A')}")
        print(f"   质量: {result.get('quality_score', 0):.2f}")

def main():
    """运行所有示例"""
    print("Google搜索爬虫使用示例")
    print("基于正确的Google搜索引擎")
    print("=" * 50)
    
    try:
        # 基础功能示例
        example_basic_crawling()
        
        # 批量爬取示例
        example_batch_crawling()
        
        # 搜索和导出示例
        example_search_and_export()
        
        # 市场分析示例
        example_market_analysis()
        
        # 高级功能示例
        example_advanced_features()
        
        # 自定义参数示例
        example_custom_search_parameters()
        
        print("\n" + "=" * 50)
        print("🎉 所有示例执行完成!")
        print("\n💡 提示:")
        print("- 所有数据已存储在Elasticsearch中")
        print("- 可以使用命令行工具进行更多操作")
        print("- 导出的训练数据可直接用于大模型训练")
        print("- 支持多种查询意图和内容分类")
        
    except KeyboardInterrupt:
        print("\n示例被用户中断")
    except Exception as e:
        print(f"示例执行出错: {e}")

if __name__ == "__main__":
    main()
