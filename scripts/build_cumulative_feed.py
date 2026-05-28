"""
累积RSS Feed生成脚本

基于累积新闻文档生成RSS Feed，支持增量更新和严格去重
"""

import os
import sys
import re
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from news_agent.config_loader import get_project_paths, load_config
from news_agent.history.rss_history import RSSHistoryManager
from news_agent.utils.deduplicate import create_content_fingerprint, calculate_title_similarity
from news_agent.rss.feed_generator import generate_rss_xml, read_existing_rss_metadata, get_rss_filename

try:
    from news_agent.filters.ai_news_filter import NewsQualityFilter
    AI_FILTER_AVAILABLE = True
except ImportError:
    print("⚠️ AI筛选模块不可用，将跳过AI筛选功能")
    AI_FILTER_AVAILABLE = False


def parse_cumulative_markdown(md_file_path: str, category: str, 
                             history_manager: RSSHistoryManager,
                             max_recent_articles: int = 50,
                             time_window_hours: int = 72,
                             enable_ai_filter: bool = True,
                             ai_filter_count: int = 10) -> Dict:
    """
    解析累积Markdown文件并提取文章
    
    参数:
        md_file_path (str): Markdown文件路径
        category (str): 分类
        history_manager (RSSHistoryManager): 历史管理器
        max_recent_articles (int): 最多提取的文章数
        time_window_hours (int): 时间窗口（小时）
        enable_ai_filter (bool): 是否启用AI筛选
        ai_filter_count (int): AI筛选后保留的文章数
        
    返回:
        Dict: 包含文章列表的信息字典
    """
    try:
        with open(md_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"  ❌ 读取文件失败: {e}")
        return {}
    
    info = {
        'title': '',
        'description': '',
        'pub_date': '',
        'articles': []
    }
    
    # 提取标题
    title_match = re.search(r'^# (.+)', content, re.MULTILINE)
    if title_match:
        info['title'] = title_match.group(1).strip()
    
    # 提取最后更新时间
    time_match = re.search(r'\*\*最后更新时间\*\*:\s*(.+)', content)
    if time_match:
        time_str = time_match.group(1).strip()
        try:
            pub_date = datetime.strptime(time_str, '%Y-%m-%d %H:%M')
            info['pub_date'] = pub_date.strftime('%a, %d %b %Y %H:%M:%S GMT')
        except ValueError:
            info['pub_date'] = datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT')
    else:
        info['pub_date'] = datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT')
    
    info['description'] = f"{category} 分类最新新闻，增量更新确保内容新鲜"
    
    # 提取文章
    extraction_limit = max_recent_articles * 10
    article_pattern = r'#### \[(.+?)\]\((.+?)\)\s*(?:\*\*发布时间\*\*:\s*(.+?)(?:\n|$))?'
    articles = re.findall(article_pattern, content, re.MULTILINE | re.DOTALL)
    articles = articles[:extraction_limit]
    
    raw_articles = []
    time_cutoff = datetime.now() - timedelta(hours=time_window_hours)
    last_update_time = history_manager.get_last_update_time(category)
    
    for title, link, pub_time in articles:
        try:
            title_clean = title.replace('\\[', '[').replace('\\]', ']').strip()
            link_clean = link.strip()
            
            # 解析发布时间
            pub_datetime = None
            if pub_time:
                try:
                    pub_datetime = datetime.strptime(pub_time.strip(), '%Y-%m-%d %H:%M')
                except:
                    pass
            
            # 时间过滤
            if pub_datetime:
                if pub_datetime < time_cutoff:
                    continue
                if last_update_time and pub_datetime <= last_update_time:
                    continue
            
            # 生成指纹
            fingerprint = create_content_fingerprint(title_clean, link_clean)
            
            # 检查是否已发布
            if history_manager.is_article_published(category, fingerprint):
                continue
            
            article_info = {
                'title': title_clean,
                'link': link_clean,
                'pub_date': pub_datetime.strftime('%a, %d %b %Y %H:%M:%S GMT') if pub_datetime else info['pub_date'],
                'description': title_clean,
                'fingerprint': fingerprint
            }
            
            raw_articles.append(article_info)
            
        except Exception as e:
            print(f"  ⚠️ 解析文章失败: {e}")
            continue
    
    # 去重：标题相似度检查
    deduplicated = []
    for article in raw_articles:
        is_duplicate = False
        for existing in deduplicated:
            similarity = calculate_title_similarity(article['title'], existing['title'])
            if similarity > 0.85:
                is_duplicate = True
                break
        
        if not is_duplicate:
            deduplicated.append(article)
    
    print(f"  📊 提取 {len(raw_articles)} 篇新文章，去重后 {len(deduplicated)} 篇")
    
    # AI筛选
    if enable_ai_filter and AI_FILTER_AVAILABLE and len(deduplicated) > ai_filter_count:
        print(f"  🤖 启动AI筛选: {len(deduplicated)} → {ai_filter_count} 篇")
        try:
            filter_instance = NewsQualityFilter()
            deduplicated = filter_instance.filter_articles(deduplicated, category, ai_filter_count)
        except Exception as e:
            print(f"  ⚠️ AI筛选失败: {e}")
    
    # 限制数量
    deduplicated = deduplicated[:max_recent_articles]
    
    info['articles'] = deduplicated
    
    return info


def process_category(category: str, cumulative_file: Path, 
                    output_dir: Path, history_manager: RSSHistoryManager,
                    config: Dict) -> Dict:
    """
    处理单个分类的RSS生成
    
    参数:
        category (str): 分类名称
        cumulative_file (Path): 累积新闻文件路径
        output_dir (Path): 输出目录
        history_manager (RSSHistoryManager): 历史管理器
        config (Dict): 配置字典
        
    返回:
        Dict: 处理结果
    """
    print(f"\n📰 处理分类: {category}")
    print(f"  📄 累积文件: {cumulative_file.name}")
    
    settings = config['settings']
    
    # 解析Markdown
    news_info = parse_cumulative_markdown(
        str(cumulative_file),
        category,
        history_manager,
        max_recent_articles=settings.get('max_articles_per_source', 50),
        time_window_hours=settings.get('time_window_hours', 72),
        enable_ai_filter=settings.get('ai_filter_enabled', True),
        ai_filter_count=settings.get('ai_filter_count', 5)
    )
    
    if not news_info or not news_info.get('articles'):
        print(f"  ⚠️ 没有新文章，跳过")
        return {'success': False, 'reason': '没有新文章'}
    
    # 生成RSS XML
    rss_filename = get_rss_filename(category)
    rss_file_path = output_dir / rss_filename
    
    existing_metadata = read_existing_rss_metadata(str(rss_file_path))
    
    xml_content = generate_rss_xml(
        news_info, 
        category,
        base_url="https://zskksz.asia/News-Agent",
        existing_metadata=existing_metadata
    )
    
    # 保存文件
    with open(rss_file_path, 'w', encoding='utf-8') as f:
        f.write(xml_content)
    
    # 更新历史记录
    for article in news_info['articles']:
        history_manager.add_published_article(
            category,
            article['fingerprint'],
            article
        )
    
    history_manager.update_last_update_time(category)
    history_manager.save_history()
    
    print(f"  ✅ 成功生成RSS: {rss_filename}")
    print(f"  📊 包含 {len(news_info['articles'])} 篇新文章")
    
    return {
        'success': True,
        'file': rss_filename,
        'article_count': len(news_info['articles'])
    }


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='生成累积RSS Feed')
    parser.add_argument('--category', type=str, help='指定分类（不指定则处理所有）')
    parser.add_argument('--no-ai-filter', action='store_true', help='禁用AI筛选')
    parser.add_argument('--cleanup-days', type=int, default=30, help='清理多少天前的历史记录')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("📡 累积RSS Feed生成器")
    print("=" * 60)
    
    # 加载配置
    config = load_config()
    paths = config['paths']
    
    if args.no_ai_filter:
        config['settings']['ai_filter_enabled'] = False
    
    print(f"\n📁 输出目录: {paths['feed']}")
    print(f"📚 累积新闻目录: {paths['cumulative_news']}")
    
    # 初始化历史管理器
    history_manager = RSSHistoryManager()
    
    # 清理旧记录
    print(f"\n🧹 清理 {args.cleanup_days} 天前的历史记录...")
    history_manager.cleanup_old_records(days=args.cleanup_days)
    
    # 查找累积新闻文件
    cumulative_dir = Path(paths['cumulative_news'])
    if not cumulative_dir.exists():
        print(f"❌ 累积新闻目录不存在: {cumulative_dir}")
        return
    
    cumulative_files = list(cumulative_dir.glob('*_cumulative.md'))
    
    if not cumulative_files:
        print("❌ 没有找到累积新闻文件")
        return
    
    print(f"\n📂 发现 {len(cumulative_files)} 个累积新闻文件")
    
    # 处理分类
    results = {}
    for file_path in cumulative_files:
        # 从文件名提取分类
        category = file_path.stem.replace('_cumulative', '').replace('_', ' ').title()
        
        # 如果指定了分类，只处理该分类
        if args.category and category.lower() != args.category.lower():
            continue
        
        result = process_category(
            category,
            file_path,
            Path(paths['feed']),
            history_manager,
            config
        )
        
        results[category] = result
    
    # 输出统计
    print("\n" + "=" * 60)
    print("📊 生成统计:")
    print("=" * 60)
    
    successful = [cat for cat, res in results.items() if res.get('success')]
    total_articles = sum(res.get('article_count', 0) for res in results.values())
    
    print(f"✅ 成功: {len(successful)}/{len(results)} 个分类")
    print(f"📰 总文章数: {total_articles}")
    
    for category, result in results.items():
        if result.get('success'):
            print(f"  ✓ {category}: {result['article_count']} 篇")
        else:
            print(f"  ✗ {category}: {result.get('reason', '失败')}")
    
    print(f"\n🎉 RSS Feed生成完成！")


if __name__ == "__main__":
    main()
