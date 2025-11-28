"""
累积新闻生成脚本

获取所有RSS订阅源的历史新闻，追加到累积的Markdown文档中
"""

import sys
import os
import argparse
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from news_agent.config_loader import load_config
from news_agent.rss.reader import generate_historical_news_by_categories


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='生成累积新闻汇总')
    parser.add_argument('--max-articles', type=int, default=100, help='每个源最多获取的文章数')
    parser.add_argument('--max-reports', type=int, default=10, help='最多保留的汇总报告数')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🔄 累积新闻汇总生成器")
    print("=" * 60)
    
    # 加载配置
    config = load_config()
    paths = config['paths']
    rss_sources = config['rss_sources']
    
    if not rss_sources:
        print("❌ 没有加载到任何RSS订阅源配置")
        return False
    
    output_dir = str(paths['cumulative_news'])
    
    print(f"📋 配置信息:")
    print(f"  - 输出目录: {output_dir}")
    print(f"  - RSS源数量: {len(rss_sources)}")
    print(f"  - 每源最大文章数: {args.max_articles}")
    print(f"  - 最大汇总报告数: {args.max_reports}")
    
    # 统计分类
    categories = {}
    for source in rss_sources:
        category = source.get('category', '未分类')
        categories[category] = categories.get(category, 0) + 1
    
    print(f"\n📂 发现 {len(categories)} 个分类:")
    for category, count in categories.items():
        print(f"  - {category}: {count} 个订阅源")
    
    print("\n" + "-" * 60)
    
    # 生成累积新闻
    print("🔄 开始获取历史新闻并更新累积文档...")
    results = generate_historical_news_by_categories(
        rss_sources=rss_sources,
        output_dir=output_dir,
        max_articles_per_source=args.max_articles,
        max_summary_reports=args.max_reports
    )
    
    if not results:
        print("❌ 处理失败")
        return False
    
    # 输出结果统计
    print("\n" + "=" * 60)
    print("📊 处理结果统计:")
    print("=" * 60)
    
    successful_categories = []
    failed_categories = []
    total_new_articles = 0
    total_duplicate_articles = 0
    
    for category, result in results.items():
        if result.get('success', False):
            successful_categories.append(category)
            new_count = result.get('new_count', 0)
            duplicate_count = result.get('duplicate_count', 0)
            total_new_articles += new_count
            total_duplicate_articles += duplicate_count
            
            print(f"✅ {category}:")
            print(f"   📄 文件: {os.path.basename(result['file_path'])}")
            print(f"   🆕 新增文章: {new_count}")
            print(f"   🔄 重复文章: {duplicate_count}")
            print(f"   🔗 订阅源数: {result.get('source_count', 0)}")
        else:
            failed_categories.append(category)
            error_msg = result.get('error', '未知错误')
            print(f"❌ {category}: {error_msg}")
    
    print(f"\n📈 总体统计:")
    print(f"  ✅ 成功处理: {len(successful_categories)}/{len(results)} 个分类")
    print(f"  🆕 新增文章总数: {total_new_articles}")
    print(f"  🔄 重复文章总数: {total_duplicate_articles}")
    print(f"  📁 输出目录: {os.path.abspath(output_dir)}")
    
    if failed_categories:
        print(f"  ❌ 失败分类: {', '.join(failed_categories)}")
    
    print(f"\n🎉 累积新闻更新完成！")
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
