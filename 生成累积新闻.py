"""
生成累积新闻汇总

该脚本获取所有RSS订阅源的历史新闻，并追加到累积的Markdown文档中，
包含去重功能，适合定期执行更新。
"""

import sys
import os
from datetime import datetime

try:
    from src.rss_read import generate_historical_news_by_categories
    from src.load_rss_url import load_rss_sources
except ImportError as e:
    print(f"❌ 导入模块失败: {e}")
    print("请确保src目录中包含rss_read.py和load_rss_url.py文件")
    sys.exit(1)

def main():
    """
    主函数：生成累积新闻汇总
    """
    print("=" * 60)
    print("🔄 累积新闻汇总生成器")
    print("=" * 60)
    
    # 配置参数 - 使用跨平台路径
    RSS_CONFIG_FILE = os.path.join('RSS feed URL', 'rss_feed_url.json')
    output_dir = "cumulative_news"  # 累积新闻输出目录
    max_articles_per_source = 100000  # 每个源最多获取的文章数量
    max_summary_reports = 10  # 最多保留的汇总报告数量
    
    print(f"📋 配置信息:")
    print(f"  - RSS配置文件: {RSS_CONFIG_FILE}")
    print(f"  - 输出目录: {output_dir}")
    print(f"  - 每源最大文章数: {max_articles_per_source}")
    print(f"  - 最大汇总报告数: {max_summary_reports}")
    print()
    
    # 检查RSS配置文件是否存在
    if not os.path.exists(RSS_CONFIG_FILE):
        print(f"❌ RSS配置文件不存在: {RSS_CONFIG_FILE}")
        
        # 调试：显示当前目录结构
        print("\n🔍 调试信息 - 当前目录结构:")
        print(f"   当前工作目录: {os.getcwd()}")
        print("   根目录内容:")
        for item in os.listdir('.'):
            if os.path.isdir(item):
                print(f"     📁 {item}/")
            else:
                print(f"     📄 {item}")
        
        # 检查是否有相似的目录
        similar_dirs = [d for d in os.listdir('.') if 'rss' in d.lower() or 'feed' in d.lower() or 'url' in d.lower()]
        if similar_dirs:
            print("   相关目录:")
            for dir_name in similar_dirs:
                print(f"     📁 {dir_name}/")
                if os.path.isdir(dir_name):
                    try:
                        files = os.listdir(dir_name)
                        for file in files[:5]:  # 只显示前5个文件
                            print(f"        📄 {file}")
                        if len(files) > 5:
                            print(f"        ... 还有 {len(files) - 5} 个文件")
                    except:
                        pass
        
        return False
    
    try:
        # 加载RSS源配置
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
        
        # 生成累积新闻汇总
        print("🔄 开始获取历史新闻并更新累积文档...")
        results = generate_historical_news_by_categories(
            rss_sources=rss_sources,
            output_dir=output_dir,
            max_articles_per_source=max_articles_per_source,
            max_summary_reports=max_summary_reports
        )
        
        if not results:
            print("❌ 处理失败")
            return False
        
        # 输出处理结果统计
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
        
        # 检查汇总报告是否生成
        if os.path.exists(output_dir):
            summary_files = [f for f in os.listdir(output_dir) if f.startswith('cumulative_summary_')]
            if summary_files:
                summary_file = sorted(summary_files)[-1]  # 获取最新的汇总报告
                print(f"  📋 汇总报告: {summary_file}")
        
        print(f"\n🎉 累积新闻更新完成！请查看目录: {os.path.abspath(output_dir)}")
        return True
        
    except Exception as e:
        print(f"❌ 处理时发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False

def show_help():
    """
    显示帮助信息
    """
    print("=" * 60)
    print("📖 累积新闻汇总生成器")
    print("=" * 60)
    print()
    print("功能说明:")
    print("  - 获取所有RSS订阅源的历史新闻（不限时间范围）")
    print("  - 自动去重，避免重复添加相同文章")
    print("  - 将新文章追加到累积的Markdown文档中")
    print("  - 按分类生成独立的累积文档")
    print("  - 适合定期执行，持续更新新闻库")
    print()
    print("输出文件:")
    print("  - cumulative_news/分类名_cumulative.md")
    print("  - cumulative_news/cumulative_summary_YYYYMMDD_HHMM.md")
    print()
    print("去重机制:")
    print("  - 基于文章标题和链接生成唯一哈希值")
    print("  - 自动跳过已存在的文章")
    print("  - 新文章追加到文档开头，保持时间顺序")
    print()
    print("使用方法:")
    print("  python 生成累积新闻.py")
    print("  python 生成累积新闻.py --help")
    print()
    print("建议定期执行（如每天一次），保持新闻库的更新")

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