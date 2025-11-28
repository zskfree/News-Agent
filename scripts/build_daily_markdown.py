"""
日报Markdown生成脚本

生成所有分类的最近新闻汇总报告
"""

import sys
import os
import argparse
from datetime import datetime
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from news_agent.config_loader import load_config
from news_agent.rss.reader import generate_all_categories_news


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='生成日报Markdown新闻汇总')
    parser.add_argument('--hours', type=int, default=24, help='时间范围（小时）')
    parser.add_argument('--output-dir', type=str, help='输出目录（默认：news/YYYYMMDD）')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🚀 RSS新闻汇总报告生成器")
    print("=" * 60)
    
    # 加载配置
    config = load_config()
    paths = config['paths']
    rss_sources = config['rss_sources']
    
    if not rss_sources:
        print("❌ 没有加载到任何RSS订阅源配置")
        return False
    
    # 确定输出目录
    if args.output_dir:
        output_dir = args.output_dir
    else:
        timestamp = datetime.now().strftime('%Y%m%d')
        output_dir = paths['root'] / "news" / timestamp
    
    output_dir = str(output_dir)
    
    print(f"📋 配置信息:")
    print(f"  - RSS源数量: {len(rss_sources)}")
    print(f"  - 时间范围: 最近 {args.hours} 小时")
    print(f"  - 输出目录: {output_dir}")
    
    # 统计分类
    categories = {}
    for source in rss_sources:
        category = source.get('category', '未分类')
        categories[category] = categories.get(category, 0) + 1
    
    print(f"\n📂 发现 {len(categories)} 个分类:")
    for category, count in categories.items():
        print(f"  - {category}: {count} 个订阅源")
    
    print("\n" + "-" * 60)
    
    # 生成新闻报告
    print("🔄 开始生成新闻汇总报告...")
    results = generate_all_categories_news(
        rss_sources=rss_sources,
        hours_limit=args.hours,
        output_dir=output_dir
    )
    
    if not results:
        print("❌ 报告生成失败")
        return False
    
    # 输出生成结果统计
    print("\n" + "=" * 60)
    print("📊 生成结果统计:")
    print("=" * 60)
    
    successful_categories = []
    failed_categories = []
    total_articles = 0
    
    for category, result in results.items():
        if result.get('success', False):
            successful_categories.append(category)
            total_articles += result.get('article_count', 0)
            
            print(f"✅ {category}:")
            print(f"   📄 文件: {os.path.basename(result['file_path'])}")
            print(f"   📰 文章数: {result.get('article_count', 0)}")
            print(f"   🔗 订阅源数: {result.get('source_count', 0)}")
        else:
            failed_categories.append(category)
            error_msg = result.get('error', '未知错误')
            print(f"❌ {category}: {error_msg}")
    
    print(f"\n📈 总体统计:")
    print(f"  ✅ 成功生成: {len(successful_categories)}/{len(results)} 个分类")
    print(f"  📰 文章总数: {total_articles}")
    print(f"  📁 输出目录: {os.path.abspath(output_dir)}")
    
    if failed_categories:
        print(f"  ❌ 失败分类: {', '.join(failed_categories)}")
    
    # 检查总览报告
    summary_files = [f for f in os.listdir(output_dir) if f.startswith('summary_report_')]
    if summary_files:
        summary_file = summary_files[0]
        print(f"  📋 总览报告: {summary_file}")
    
    print(f"\n🎉 报告生成完成！")
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
