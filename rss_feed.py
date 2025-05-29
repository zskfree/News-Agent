"""
RSS Feed 生成器

该脚本读取当天各分类的新闻Markdown文件，为每个分类生成对应的RSS XML文件，
保存到"feed"文件夹中，可作为RSS订阅源使用。
"""

import os
import sys
import re
from datetime import datetime
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom
from urllib.parse import quote

def parse_markdown_news(md_file_path):
    """
    解析Markdown新闻文件，提取文章信息
    
    参数:
        md_file_path (str): Markdown文件路径
        
    返回:
        dict: 包含新闻信息的字典
    """
    try:
        with open(md_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"❌ 无法读取文件 {md_file_path}: {e}")
        return None
    
    # 提取基本信息
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
    
    # 提取生成时间
    time_match = re.search(r'\*\*生成时间\*\*:\s*(.+)', content)
    if time_match:
        time_str = time_match.group(1).strip()
        try:
            # 尝试解析时间格式
            pub_date = datetime.strptime(time_str, '%Y-%m-%d %H:%M')
            info['pub_date'] = pub_date.strftime('%a, %d %b %Y %H:%M:%S GMT')
        except ValueError:
            info['pub_date'] = datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT')
    else:
        info['pub_date'] = datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT')
    
    # 提取文章总数作为描述
    count_match = re.search(r'\*\*文章总数\*\*:\s*(\d+)', content)
    if count_match:
        article_count = count_match.group(1)
        info['description'] = f"最新科技资讯汇总，包含 {article_count} 篇文章"
    else:
        info['description'] = "最新科技资讯汇总"
    
    # 提取所有文章
    # 匹配格式: ### [标题](链接)
    article_pattern = r'### \[(.+?)\]\((.+?)\)\s*(?:\*\*发布时间\*\*:\s*(.+?)(?:\n|$))?'
    articles = re.findall(article_pattern, content, re.MULTILINE | re.DOTALL)
    
    for title, link, pub_time in articles:
        # 清理标题中的转义字符
        clean_title = title.replace('\\[', '[').replace('\\]', ']').strip()
        clean_link = link.strip()
        clean_pub_time = pub_time.strip() if pub_time else ''
        
        # 转换发布时间格式
        rss_pub_time = ''
        if clean_pub_time:
            try:
                # 尝试多种时间格式
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
            'description': clean_title  # 使用标题作为描述
        })
    
    return info

def generate_rss_xml(news_info, category, base_url="https://your-domain.com"):
    """
    生成RSS XML内容
    
    参数:
        news_info (dict): 新闻信息
        category (str): 分类名称
        base_url (str): 网站基础URL
        
    返回:
        str: RSS XML字符串
    """
    # 创建RSS根元素
    rss = Element('rss')
    rss.set('version', '2.0')
    rss.set('xmlns:atom', 'http://www.w3.org/2005/Atom')
    
    # 创建channel元素
    channel = SubElement(rss, 'channel')
    
    # 添加频道信息
    title = SubElement(channel, 'title')
    title.text = f"{category} 新闻汇总 - Free News Agent"
    
    link = SubElement(channel, 'link')
    link.text = f"{base_url}/feed/{category.lower()}freenewsagent.xml"
    
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
    
    # 添加所有权认证标签
    follow_challenge = SubElement(channel, 'follow_challenge')
    feed_id = SubElement(follow_challenge, 'feedId')
    feed_id.text = "150741279739242496"
    user_id = SubElement(follow_challenge, 'userId')
    user_id.text = "DdasOQb1gouc5RwqkaQc4KLscHJhfeeW"
    
    # 添加atom:link自引用
    atom_link = SubElement(channel, 'atom:link')
    atom_link.set('href', f"{base_url}/feed/{category.lower()}freenewsagent.xml")
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
        
        # 添加GUID
        guid = SubElement(item, 'guid')
        guid.set('isPermaLink', 'true')
        guid.text = article['link']
        
        # 添加分类
        item_category = SubElement(item, 'category')
        item_category.text = category
    
    # 格式化XML
    rough_string = tostring(rss, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ", encoding='utf-8').decode('utf-8')

def get_today_news_files(news_dir="news"):
    """
    获取今天的新闻文件列表
    
    参数:
        news_dir (str): 新闻目录
        
    返回:
        list: 新闻文件路径列表
    """
    today = datetime.now().strftime('%Y%m%d')
    today_dir = os.path.join(news_dir, today)
    
    if not os.path.exists(today_dir):
        print(f"❌ 今日新闻目录不存在: {today_dir}")
        return []
    
    news_files = []
    for filename in os.listdir(today_dir):
        if filename.endswith('.md') and not filename.startswith('summary_'):
            news_files.append(os.path.join(today_dir, filename))
    
    return news_files

def extract_category_from_filename(filename):
    """
    从文件名中提取分类名称
    
    参数:
        filename (str): 文件名
        
    返回:
        str: 分类名称
    """
    # 文件名格式: 分类名_日期.md
    basename = os.path.basename(filename)
    name_part = basename.split('_')[0] if '_' in basename else basename.replace('.md', '')
    return name_part

def main():
    """
    主函数：生成RSS Feed XML文件
    """
    print("=" * 60)
    print("🔄 RSS Feed 生成器")
    print("=" * 60)
    
    # 配置参数
    news_dir = "news"
    feed_dir = "feed"
    base_url = "https://zskfree.github.io/News-Agent"  # 可以修改为您的域名
    
    print(f"📋 配置信息:")
    print(f"  - 新闻目录: {news_dir}")
    print(f"  - Feed输出目录: {feed_dir}")
    print(f"  - 基础URL: {base_url}")
    print()
    
    # 创建feed目录
    if not os.path.exists(feed_dir):
        os.makedirs(feed_dir)
        print(f"✅ 创建Feed目录: {feed_dir}")
    
    # 获取今天的新闻文件
    news_files = get_today_news_files(news_dir)
    
    if not news_files:
        print("❌ 没有找到今天的新闻文件")
        return False
    
    print(f"📰 找到 {len(news_files)} 个新闻文件")
    print("-" * 60)
    
    success_count = 0
    failed_count = 0
    
    # 为每个分类生成RSS Feed
    for news_file in news_files:
        category = extract_category_from_filename(news_file)
        print(f"🔄 处理分类: {category}")
        
        try:
            # 解析Markdown文件
            news_info = parse_markdown_news(news_file)
            
            if not news_info:
                print(f"  ❌ 解析失败")
                failed_count += 1
                continue
            
            article_count = len(news_info.get('articles', []))
            print(f"  📄 解析到 {article_count} 篇文章")
            
            # 生成RSS XML
            rss_xml = generate_rss_xml(news_info, category, base_url)
            
            # 保存XML文件
            xml_filename = f"{category.lower()}freenewsagent.xml"
            xml_path = os.path.join(feed_dir, xml_filename)
            
            with open(xml_path, 'w', encoding='utf-8') as f:
                f.write(rss_xml)
            
            print(f"  ✅ 生成成功: {xml_filename}")
            success_count += 1
            
        except Exception as e:
            print(f"  ❌ 生成失败: {e}")
            failed_count += 1
    
    # 输出统计结果
    print("\n" + "=" * 60)
    print("📊 生成结果统计:")
    print("=" * 60)
    print(f"  ✅ 成功生成: {success_count} 个RSS Feed")
    print(f"  ❌ 生成失败: {failed_count} 个")
    print(f"  📁 输出目录: {os.path.abspath(feed_dir)}")
    
    if success_count > 0:
        print(f"\n📡 RSS订阅地址:")
        for news_file in news_files:
            category = extract_category_from_filename(news_file)
            xml_filename = f"{category.lower()}.xml"
            if os.path.exists(os.path.join(feed_dir, xml_filename)):
                print(f"  - {category}: {base_url}/feed/{xml_filename}")
    
    print(f"\n🎉 RSS Feed生成完成！")
    return success_count > 0

def show_help():
    """
    显示帮助信息
    """
    print("=" * 60)
    print("📖 RSS Feed 生成器")
    print("=" * 60)
    print()
    print("功能说明:")
    print("  - 读取当天各分类的新闻Markdown文件")
    print("  - 为每个分类生成对应的RSS XML文件")
    print("  - 保存到feed文件夹中，可作为RSS订阅源")
    print("  - 支持标准RSS 2.0格式")
    print()
    print("输入文件:")
    print("  - news/YYYYMMDD/分类名_YYYYMMDD.md")
    print()
    print("输出文件:")
    print("  - feed/分类名.xml")
    print()
    print("使用方法:")
    print("  python 生成RSS_Feed.py")
    print("  python 生成RSS_Feed.py --help")
    print()
    print("注意事项:")
    print("  - 需要先运行新闻汇总生成器生成当天的新闻文件")
    print("  - 可以修改脚本中的base_url为您的实际域名")

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
