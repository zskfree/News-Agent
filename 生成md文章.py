"""
生成所有的rss订阅源的markdown文档

该脚本调用src模块中的函数，按分类生成不同的新闻汇总报告，
并生成包含所有分类统计信息的总览报告。
"""

import sys
import os
from datetime import datetime

try:
    from src.rss_read import generate_all_categories_news
    from src.load_rss_url import load_rss_sources
except ImportError as e:
    print(f"❌ 导入模块失败: {e}")
    print("请确保src目录中包含rss_read.py和load_rss_url.py文件")
    sys.exit(1)

def main():
    """
    主函数：生成所有分类的新闻汇总报告
    """
    print("=" * 60)
    print("🚀 开始生成RSS新闻汇总报告")
    print("=" * 60)
    
    # 配置参数
    RSS_CONFIG_FILE = r'RSS feed URL\rss_feed_url.json'
    hours_limit = 24  # 时间限制（小时）
    timestamp = datetime.now().strftime('%Y%m%d')
    output_dir = f"news/{timestamp}"  # 输出目录，按日期组织
    
    print(f"📋 配置信息:")
    print(f"  - RSS配置文件: {RSS_CONFIG_FILE}")
    print(f"  - 时间范围: 最近 {hours_limit} 小时")
    print(f"  - 输出目录: {output_dir}")
    print()
    
    # 检查RSS配置文件是否存在
    if not os.path.exists(RSS_CONFIG_FILE):
        print(f"❌ RSS配置文件不存在: {RSS_CONFIG_FILE}")
        return False
    
    try:
        # 加载并显示RSS源信息
        print("📚 加载RSS订阅源配置...")
        rss_sources = load_rss_sources(RSS_CONFIG_FILE)
        
        if not rss_sources:
            print("❌ 没有加载到任何RSS订阅源配置")
            return False
        
        print(f"✅ 成功加载 {len(rss_sources)} 个RSS订阅源")
        
        # 统计分类信息
        categories = {}
        for source in rss_sources:
            category = source.get('category', '未分类')
            categories[category] = categories.get(category, 0) + 1
        
        print(f"\n📂 发现 {len(categories)} 个分类:")
        for category, count in categories.items():
            print(f"  - {category}: {count} 个订阅源")
        
        print("\n" + "-" * 60)
        
        # 生成所有分类的新闻报告
        print("🔄 开始生成新闻汇总报告...")
        results = generate_all_categories_news(
            rss_sources=rss_sources,
            hours_limit=hours_limit,
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
        
        # 检查总览报告是否生成
        summary_files = [f for f in os.listdir(output_dir) if f.startswith('summary_report_')]
        if summary_files:
            summary_file = summary_files[0]
            print(f"  📋 总览报告: {summary_file}")
        
        print(f"\n🎉 报告生成完成！请查看目录: {os.path.abspath(output_dir)}")
        return True
        
    except Exception as e:
        print(f"❌ 生成报告时发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False

def show_help():
    """
    显示帮助信息
    """
    print("=" * 60)
    print("📖 RSS新闻汇总报告生成器")
    print("=" * 60)
    print()
    print("功能说明:")
    print("  - 自动读取RSS配置文件中的所有订阅源")
    print("  - 按分类生成独立的Markdown新闻汇总报告")
    print("  - 生成包含所有分类统计信息的总览报告")
    print("  - 支持时间筛选（默认最近24小时）")
    print()
    print("输出文件:")
    print("  - news/YYYYMMDD/分类名_YYYYMMDD.md")
    print("  - news/YYYYMMDD/summary_report_YYYYMMDD_HHMM.md")
    print()
    print("使用方法:")
    print("  python 生成md文章.py")
    print("  python 生成md文章.py --help")

if __name__ == "__main__":
    # 检查命令行参数
    if len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h', 'help']:
        show_help()
    else:
        # 执行主程序
        success = main()
        
        if success:
            print("\n🎯 任务完成！")
        else:
            print("\n💥 任务失败！")
            sys.exit(1)