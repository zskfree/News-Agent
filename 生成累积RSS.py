"""
累积RSS Feed生成器

该脚本基于累积新闻文档生成RSS Feed，支持增量更新，直接覆盖原有文件并保留认证信息
"""

import os
import sys
import re
from datetime import datetime
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom

def parse_cumulative_markdown(md_file_path, max_recent_articles=20):
    """
    解析累积Markdown文件，提取最近的文章信息
    
    参数:
        md_file_path (str): 累积Markdown文件路径
        max_recent_articles (int): RSS中包含的最大文章数
        
    返回:
        dict: 包含新闻信息的字典
    """
    try:
        with open(md_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"❌ 无法读取文件 {md_file_path}: {e}")
        return None
    
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
    
    # 设置描述
    info['description'] = "累积新闻汇总，持续更新的科技资讯"
    
    # 提取文章（优先提取最新的文章）
    article_pattern = r'#### \[(.+?)\]\((.+?)\)\s*(?:\*\*发布时间\*\*:\s*(.+?)(?:\n|$))?'
    articles = re.findall(article_pattern, content, re.MULTILINE | re.DOTALL)
    
    # 限制文章数量，只取最新的文章
    articles = articles[:max_recent_articles]
    
    for title, link, pub_time in articles:
        clean_title = title.replace('\\[', '[').replace('\\]', ']').strip()
        clean_link = link.strip()
        clean_pub_time = pub_time.strip() if pub_time else ''
        
        # 转换发布时间格式
        rss_pub_time = ''
        if clean_pub_time:
            try:
                for fmt in ['%Y-%m-%d %H:%M', '%a, %d %b %Y %H:%M:%S %z', '%Y-%m-%d %H:%M:%S']:
                    try:
                        dt = datetime.strptime(clean_pub_time, fmt)
                        rss_pub_time = dt.strftime('%a, %d %b %Y %H:%M:%S GMT')
                        break
                    except ValueError:
                        continue
            except:
                pass
        
        if not rss_pub_time:
            rss_pub_time = info['pub_date']
        
        info['articles'].append({
            'title': clean_title,
            'link': clean_link,
            'pub_date': rss_pub_time,
            'description': clean_title
        })
    
    return info

def get_original_rss_filename(category):
    """
    根据分类获取原有的RSS文件名
    
    参数:
        category (str): 分类名称
        
    返回:
        str: 原有的RSS文件名
    """
    # 定义分类到原有文件名的映射
    category_filename_map = {
        'Finance': 'financefreenewsagent.xml',
        'finance': 'financefreenewsagent.xml',
        'Technology': 'technologyfreenewsagent.xml',
        'technology': 'technologyfreenewsagent.xml',
        'AI': 'aifreenewsagent.xml',
        'ai': 'aifreenewsagent.xml',
        '人工智能': 'aifreenewsagent.xml',
    }
    
    # 首先尝试精确匹配
    if category in category_filename_map:
        return category_filename_map[category]
    
    # 然后尝试小写匹配
    category_lower = category.lower()
    for key, filename in category_filename_map.items():
        if key.lower() == category_lower:
            return filename
    
    # 如果没有找到映射，使用默认格式
    safe_category = category.lower().replace(' ', '').replace('_', '').replace('-', '')
    return f"{safe_category}freenewsagent.xml"

def read_existing_rss_metadata(xml_file_path):
    """
    读取现有RSS文件的元数据（如follow_challenge等）
    
    参数:
        xml_file_path (str): RSS文件路径
        
    返回:
        dict: 元数据字典
    """
    metadata = {}
    
    if not os.path.exists(xml_file_path):
        return metadata
    
    try:
        with open(xml_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 提取follow_challenge信息
        follow_challenge_match = re.search(
            r'<follow_challenge>\s*<feedId>(\d+)</feedId>\s*<userId>([^<]+)</userId>\s*</follow_challenge>',
            content, re.MULTILINE | re.DOTALL
        )
        
        if follow_challenge_match:
            metadata['follow_challenge'] = {
                'feedId': follow_challenge_match.group(1),
                'userId': follow_challenge_match.group(2)
            }
    
    except Exception as e:
        print(f"  读取RSS元数据时出错: {e}")
    
    return metadata

def get_category_follow_challenge(category):
    """
    根据分类获取认证信息
    
    参数:
        category (str): 分类名称
        
    返回:
        dict: 认证信息字典
    """
    # 定义分类对应的认证信息
    follow_challenges = {
        'ai': {
            'feedId': '150741279739242496',
            'userId': 'DdasOQb1gouc5RwqkaQc4KLscHJhfeeW'
        },
        'technology': {
            'feedId': '150742893699033088',
            'userId': 'DdasOQb1gouc5RwqkaQc4KLscHJhfeeW'
        },
        'finance': {
            'feedId': '150742893699033088',
            'userId': 'DdasOQb1gouc5RwqkaQc4KLscHJhfeeW'
        }
    }
    
    category_lower = category.lower()
    
    # 映射中文名称
    if category_lower in ['人工智能']:
        category_lower = 'ai'
    
    return follow_challenges.get(category_lower, None)

def generate_cumulative_rss_xml(news_info, category, base_url="https://zskfree.github.io/News-Agent", 
                               existing_metadata=None):
    """
    生成累积RSS XML内容，保持原有的元数据和认证信息
    
    参数:
        news_info (dict): 新闻信息
        category (str): 分类名称
        base_url (str): 基础URL
        existing_metadata (dict): 现有的元数据
        
    返回:
        str: RSS XML字符串
    """
    rss = Element('rss')
    rss.set('version', '2.0')
    rss.set('xmlns:atom', 'http://www.w3.org/2005/Atom')
    
    channel = SubElement(rss, 'channel')
    
    # 根据分类获取原有文件名
    original_filename = get_original_rss_filename(category)
    
    title = SubElement(channel, 'title')
    title.text = f"{category} 新闻汇总 - Free News Agent"
    
    link = SubElement(channel, 'link')
    link.text = f"{base_url}/feed/{original_filename}"
    
    description = SubElement(channel, 'description')
    description.text = f"{category} 分类的最新新闻汇总，由 Free News Agent 自动生成"
    
    language = SubElement(channel, 'language')
    language.text = "zh-CN"
    
    pub_date = SubElement(channel, 'pubDate')
    pub_date.text = news_info.get('pub_date', datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT'))
    
    last_build_date = SubElement(channel, 'lastBuildDate')
    last_build_date.text = datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT')
    
    generator = SubElement(channel, 'generator')
    generator.text = "News Agent RSS Generator"
    
    # 添加认证信息 - 优先使用现有的，如果没有则使用默认的
    follow_challenge_info = None
    if existing_metadata and 'follow_challenge' in existing_metadata:
        follow_challenge_info = existing_metadata['follow_challenge']
    else:
        follow_challenge_info = get_category_follow_challenge(category)
    
    if follow_challenge_info:
        follow_challenge = SubElement(channel, 'follow_challenge')
        feed_id = SubElement(follow_challenge, 'feedId')
        feed_id.text = follow_challenge_info['feedId']
        user_id = SubElement(follow_challenge, 'userId')
        user_id.text = follow_challenge_info['userId']
    
    # 添加atom:link自引用
    atom_link = SubElement(channel, 'atom:link')
    atom_link.set('href', f"{base_url}/feed/{original_filename}")
    atom_link.set('rel', 'self')
    atom_link.set('type', 'application/rss+xml')
    
    # 添加文章项目
    for article in news_info.get('articles', []):
        item = SubElement(channel, 'item')
        
        item_title = SubElement(item, 'title')
        item_title.text = article['title']
        
        item_link = SubElement(item, 'link')
        item_link.text = article['link']
        
        item_description = SubElement(item, 'description')
        item_description.text = f"<![CDATA[{article['description']}]]>"
        
        item_pub_date = SubElement(item, 'pubDate')
        item_pub_date.text = article['pub_date']
        
        guid = SubElement(item, 'guid')
        guid.set('isPermaLink', 'true')
        guid.text = article['link']
        
        item_category = SubElement(item, 'category')
        item_category.text = category
    
    # 格式化XML
    rough_string = tostring(rss, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ", encoding='utf-8').decode('utf-8')

def get_cumulative_news_files(news_dir="cumulative_news"):
    """
    获取累积新闻文件列表
    """
    if not os.path.exists(news_dir):
        print(f"❌ 累积新闻目录不存在: {news_dir}")
        return []
    
    news_files = []
    for filename in os.listdir(news_dir):
        if filename.endswith('_cumulative.md'):
            news_files.append(os.path.join(news_dir, filename))
    
    return news_files

def extract_category_from_cumulative_filename(filename):
    """
    从累积文件名中提取分类名称
    """
    basename = os.path.basename(filename)
    category = basename.replace('_cumulative.md', '')
    return category

def main():
    """
    主函数：生成累积RSS Feed，直接覆盖原有文件并保留认证信息
    """
    print("=" * 60)
    print("📡 累积RSS Feed生成器 (覆盖原有文件，保留认证)")
    print("=" * 60)
    
    # 配置参数
    news_dir = "cumulative_news"
    feed_dir = "feed"
    base_url = "https://zskfree.github.io/News-Agent"
    max_articles_per_feed = 100  # 每个RSS Feed最多包含的文章数
    
    print(f"📋 配置信息:")
    print(f"  - 累积新闻目录: {news_dir}")
    print(f"  - Feed输出目录: {feed_dir}")
    print(f"  - 基础URL: {base_url}")
    print(f"  - 每Feed最大文章数: {max_articles_per_feed}")
    print(f"  - 模式: 覆盖原有RSS文件并保留认证信息")
    print()
    
    # 创建feed目录
    if not os.path.exists(feed_dir):
        os.makedirs(feed_dir)
        print(f"✅ 创建Feed目录: {feed_dir}")
    
    # 获取累积新闻文件
    news_files = get_cumulative_news_files(news_dir)
    
    if not news_files:
        print("❌ 没有找到累积新闻文件")
        return False
    
    print(f"📰 找到 {len(news_files)} 个累积新闻文件")
    print("-" * 60)
    
    success_count = 0
    failed_count = 0
    
    # 为每个分类生成RSS Feed
    for news_file in news_files:
        category = extract_category_from_cumulative_filename(news_file)
        print(f"🔄 处理分类: {category}")
        
        try:
            # 解析Markdown文件
            news_info = parse_cumulative_markdown(news_file, max_articles_per_feed)
            
            if not news_info:
                print(f"  ❌ 解析失败")
                failed_count += 1
                continue
            
            article_count = len(news_info.get('articles', []))
            print(f"  📄 解析到 {article_count} 篇文章")
            
            # 获取原有RSS文件名
            original_filename = get_original_rss_filename(category)
            xml_path = os.path.join(feed_dir, original_filename)
            
            # 读取现有RSS文件的元数据
            existing_metadata = read_existing_rss_metadata(xml_path)
            if existing_metadata and 'follow_challenge' in existing_metadata:
                print(f"  📋 保留现有认证信息: feedId={existing_metadata['follow_challenge']['feedId']}")
            else:
                default_auth = get_category_follow_challenge(category)
                if default_auth:
                    print(f"  🔐 使用默认认证信息: feedId={default_auth['feedId']}")
                else:
                    print(f"  ⚠️ 未找到认证信息")
            
            # 生成RSS XML
            rss_xml = generate_cumulative_rss_xml(news_info, category, base_url, existing_metadata)
            
            # 直接覆盖原有XML文件
            with open(xml_path, 'w', encoding='utf-8') as f:
                f.write(rss_xml)
            
            print(f"  ✅ 覆盖更新成功: {original_filename}")
            success_count += 1
            
        except Exception as e:
            print(f"  ❌ 生成失败: {e}")
            failed_count += 1
    
    # 输出统计结果
    print("\n" + "=" * 60)
    print("📊 生成结果统计:")
    print("=" * 60)
    print(f"  ✅ 成功更新: {success_count} 个RSS Feed")
    print(f"  ❌ 更新失败: {failed_count} 个")
    print(f"  📁 输出目录: {os.path.abspath(feed_dir)}")
    print(f"  🔄 模式: 直接覆盖原有文件，保留认证信息")
    
    if success_count > 0:
        print(f"\n📡 更新的RSS订阅地址 (无需重新订阅):")
        for news_file in news_files:
            category = extract_category_from_cumulative_filename(news_file)
            original_filename = get_original_rss_filename(category)
            if os.path.exists(os.path.join(feed_dir, original_filename)):
                print(f"  - {category}: {base_url}/feed/{original_filename}")
    
    print(f"\n🎉 RSS Feed更新完成！用户无需重新订阅！")
    return success_count > 0

def show_help():
    """
    显示帮助信息
    """
    print("=" * 60)
    print("📖 累积RSS Feed生成器")
    print("=" * 60)
    print()
    print("功能说明:")
    print("  - 基于累积新闻文档生成RSS Feed")
    print("  - 直接覆盖原有的RSS文件，保持URL不变")
    print("  - 保留原有的认证信息（follow_challenge）")
    print("  - 支持从现有文件读取或使用默认认证信息")
    print("  - 用户无需重新订阅RSS源")
    print()
    print("文件映射:")
    print("  - Finance -> financefreenewsagent.xml")
    print("  - Technology -> technologyfreenewsagent.xml") 
    print("  - AI -> aifreenewsagent.xml")
    print("  - 其他分类 -> [分类名]freenewsagent.xml")
    print()
    print("认证信息:")
    print("  - 优先使用现有RSS文件中的认证信息")
    print("  - 如果没有则使用预定义的默认认证信息")
    print("  - 确保RSS Feed的所有权验证正常")
    print()
    print("输入文件:")
    print("  - cumulative_news/分类名_cumulative.md")
    print()
    print("输出文件:")
    print("  - feed/原有文件名.xml（直接覆盖）")
    print()
    print("使用方法:")
    print("  python 生成累积RSS.py")
    print("  python 生成累积RSS.py --help")

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