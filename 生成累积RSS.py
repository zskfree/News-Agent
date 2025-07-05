"""
累积RSS Feed生成器 - 优化版

该脚本基于累积新闻文档生成RSS Feed，支持增量更新和严格去重
新增功能：
1. 基于历史记录的去重机制
2. 时间窗口控制，避免发布过旧的新闻
3. 内容指纹识别，防止相似内容重复
4. 发布历史跟踪，确保每次更新只包含新内容
"""

import os
import sys
import re
import json
import hashlib
from datetime import datetime, timedelta
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom
from urllib.parse import urlparse
import difflib

try:
    from src.ai_news_filter import NewsQualityFilter
    AI_FILTER_AVAILABLE = True
except ImportError:
    print("⚠️ AI筛选模块不可用，将跳过AI筛选功能")
    AI_FILTER_AVAILABLE = False

def create_content_fingerprint(title, link, description=""):
    """
    创建内容指纹，用于精确去重
    
    参数:
        title (str): 文章标题
        link (str): 文章链接
        description (str): 文章描述（可选）
        
    返回:
        str: 内容指纹
    """
    # 清理标题：移除特殊字符、标点符号，转换为小写
    clean_title = re.sub(r'[^\w\s]', '', title.lower()).strip()
    clean_title = ' '.join(clean_title.split())  # 标准化空格
    
    # 清理链接：移除查询参数和片段
    parsed_url = urlparse(link)
    clean_link = f"{parsed_url.netloc}{parsed_url.path}".lower()
    
    # 生成组合指纹
    content = f"{clean_title}|{clean_link}|{description[:100]}"
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def calculate_title_similarity(title1, title2):
    """
    计算两个标题的相似度
    
    参数:
        title1 (str): 标题1
        title2 (str): 标题2
        
    返回:
        float: 相似度 (0-1)
    """
    # 清理和标准化标题
    def clean_title(title):
        # 移除标点符号和特殊字符
        cleaned = re.sub(r'[^\w\s]', ' ', title.lower())
        # 标准化空格
        return ' '.join(cleaned.split())
    
    cleaned_title1 = clean_title(title1)
    cleaned_title2 = clean_title(title2)
    
    # 使用difflib计算相似度
    similarity = difflib.SequenceMatcher(None, cleaned_title1, cleaned_title2).ratio()
    
    # 同时检查词汇重叠度
    words1 = set(cleaned_title1.split())
    words2 = set(cleaned_title2.split())
    
    if words1 and words2:
        word_overlap = len(words1.intersection(words2)) / len(words1.union(words2))
        # 取两种方法的最大值
        similarity = max(similarity, word_overlap)
    
    return similarity

class RSSHistoryManager:
    """RSS发布历史管理器"""
    
    def __init__(self, history_file="rss_history.json"):
        self.history_file = history_file
        self.history_data = self.load_history()
    
    def load_history(self):
        """加载历史记录"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {"published_articles": {}, "last_update": {}}
    
    def save_history(self):
        """保存历史记录"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"  ⚠️ 保存历史记录失败: {e}")
    
    def is_article_published(self, category, fingerprint):
        """检查文章是否已发布"""
        category_articles = self.history_data["published_articles"].get(category, {})
        return fingerprint in category_articles
    
    def add_published_article(self, category, fingerprint, article_info):
        """添加已发布的文章记录"""
        if category not in self.history_data["published_articles"]:
            self.history_data["published_articles"][category] = {}
        
        self.history_data["published_articles"][category][fingerprint] = {
            "title": article_info["title"],
            "link": article_info["link"],
            "published_date": article_info.get("pub_date", ""),
            "first_seen": datetime.now().isoformat()
        }
    
    def update_last_update_time(self, category):
        """更新最后更新时间"""
        self.history_data["last_update"][category] = datetime.now().isoformat()
    
    def get_last_update_time(self, category):
        """获取最后更新时间"""
        last_update_str = self.history_data["last_update"].get(category)
        if last_update_str:
            try:
                return datetime.fromisoformat(last_update_str)
            except:
                pass
        return None
    
    def cleanup_old_records(self, days=30):
        """清理过旧的记录"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        for category in list(self.history_data["published_articles"].keys()):
            articles = self.history_data["published_articles"][category]
            
            # 清理过旧的文章记录
            articles_to_remove = []
            for fingerprint, article_info in articles.items():
                try:
                    first_seen = datetime.fromisoformat(article_info["first_seen"])
                    if first_seen < cutoff_date:
                        articles_to_remove.append(fingerprint)
                except:
                    # 如果解析失败，保守起见保留记录
                    pass
            
            for fingerprint in articles_to_remove:
                del articles[fingerprint]
            
            print(f"  🧹 分类 {category}: 清理了 {len(articles_to_remove)} 条过期记录")

def advanced_deduplicate_articles(articles, category, history_manager, 
                                max_articles=50, similarity_threshold=0.85,
                                time_window_hours=72, only_new_articles=True):
    """
    高级去重功能 - 增量更新模式
    
    参数:
        articles (list): 文章列表
        category (str): 分类
        history_manager (RSSHistoryManager): 历史管理器
        max_articles (int): 最大保留文章数
        similarity_threshold (float): 相似度阈值
        time_window_hours (int): 时间窗口（小时）
        only_new_articles (bool): 是否只返回新文章（增量更新模式）
        
    返回:
        list: 去重后的文章列表
    """
    if not articles:
        return []
    
    print(f"  🔍 开始增量去重，原始文章数: {len(articles)}")
    print(f"  📐 相似度阈值: {similarity_threshold}")
    print(f"  ⏰ 时间窗口: {time_window_hours} 小时")
    print(f"  🆕 增量模式: {only_new_articles}")
    
    # 获取上次更新时间 - 关键改动
    last_update_time = history_manager.get_last_update_time(category)
    
    # 时间截止点
    time_cutoff = datetime.now() - timedelta(hours=time_window_hours)
    
    # 如果是增量更新模式且有历史更新时间，使用更严格的时间筛选
    if only_new_articles and last_update_time:
        # 使用上次更新时间作为截止点，只取更新的文章
        time_cutoff = max(time_cutoff, last_update_time)
        print(f"  📅 增量更新：只获取 {last_update_time.strftime('%Y-%m-%d %H:%M')} 之后的文章")
    
    deduplicated_articles = []
    seen_fingerprints = set()
    removed_reasons = {
        "已发布": 0,
        "URL重复": 0,
        "标题相似": 0,
        "过旧": 0,
        "超出限制": 0,
        "早于上次更新": 0  # 新增统计项
    }
    
    for article in articles:
        title = article.get('title', '').strip()
        link = article.get('link', '').strip()
        pub_date_str = article.get('pub_date', '')
        
        if not title or not link:
            continue
        
        # 1. 检查发布时间是否在窗口内（增强版）
        article_too_old = False
        try:
            if pub_date_str and pub_date_str != '时间未知':
                # 尝试解析发布时间
                for fmt in ['%Y-%m-%d %H:%M', '%a, %d %b %Y %H:%M:%S %Z', 
                           '%a, %d %b %Y %H:%M:%S GMT', '%Y-%m-%d %H:%M:%S']:
                    try:
                        pub_date = datetime.strptime(pub_date_str, fmt)
                        
                        # 增量更新模式：检查是否早于上次更新时间
                        if only_new_articles and last_update_time and pub_date <= last_update_time:
                            removed_reasons["早于上次更新"] += 1
                            article_too_old = True
                            break
                        
                        # 常规时间窗口检查
                        if pub_date < time_cutoff:
                            removed_reasons["过旧"] += 1
                            article_too_old = True
                            break
                        break
                    except ValueError:
                        continue
                else:
                    # 如果所有格式都失败，在增量模式下跳过
                    if only_new_articles and last_update_time:
                        removed_reasons["早于上次更新"] += 1
                        article_too_old = True
        except:
            # 解析失败，在增量模式下保守跳过
            if only_new_articles and last_update_time:
                removed_reasons["早于上次更新"] += 1
                article_too_old = True
        
        if article_too_old:
            continue
        
        # 2. 生成内容指纹
        fingerprint = create_content_fingerprint(title, link, article.get('description', ''))
        
        # 3. 检查是否已在历史记录中发布
        if history_manager.is_article_published(category, fingerprint):
            removed_reasons["已发布"] += 1
            continue
        
        # 4. 检查当前批次中的重复
        if fingerprint in seen_fingerprints:
            removed_reasons["URL重复"] += 1
            continue
        
        # 5. 检查与当前批次中其他文章的相似性
        is_similar = False
        for existing_article in deduplicated_articles:
            existing_title = existing_article.get('title', '')
            similarity = calculate_title_similarity(title, existing_title)
            
            if similarity > similarity_threshold:
                removed_reasons["标题相似"] += 1
                print(f"    🔄 相似标题 ({similarity:.2f}): {title[:30]}... ≈ {existing_title[:30]}...")
                is_similar = True
                break
        
        if is_similar:
            continue
        
        # 6. 检查是否已达到最大文章数
        if len(deduplicated_articles) >= max_articles:
            removed_reasons["超出限制"] += 1
            break
        
        # 添加到结果列表
        seen_fingerprints.add(fingerprint)
        deduplicated_articles.append(article)
        
        # 记录到历史管理器（标记为已发布）
        history_manager.add_published_article(category, fingerprint, article)
    
    # 输出去重统计
    total_removed = sum(removed_reasons.values())
    print(f"  ✅ 增量去重完成，移除 {total_removed} 篇文章，保留 {len(deduplicated_articles)} 篇新文章")
    for reason, count in removed_reasons.items():
        if count > 0:
            print(f"    - {reason}: {count} 篇")
    
    # 特别提示
    if only_new_articles and len(deduplicated_articles) == 0:
        print(f"  ℹ️ 没有找到新文章，RSS Feed将为空")
    elif only_new_articles:
        print(f"  🆕 本次更新将推送 {len(deduplicated_articles)} 篇全新文章")
    
    return deduplicated_articles

def parse_cumulative_markdown_optimized(md_file_path, category, history_manager, 
                                       max_recent_articles=50, time_window_hours=72,
                                       enable_ai_filter=True, ai_filter_count=10):
    """
    优化版Markdown解析，包含增量更新和AI筛选
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
    info['description'] = f"{category} 分类最新新闻，增量更新确保内容新鲜"
    
    # 提取文章（提取更多文章以便去重后仍有足够数量）
    extraction_limit = max_recent_articles * 10  # 增加提取倍数，确保有足够的候选文章
    article_pattern = r'#### \[(.+?)\]\((.+?)\)\s*(?:\*\*发布时间\*\*:\s*(.+?)(?:\n|$))?'
    articles = re.findall(article_pattern, content, re.MULTILINE | re.DOTALL)
    
    # 首先提取更多文章
    articles = articles[:extraction_limit]
    
    raw_articles = []
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
        
        raw_articles.append({
            'title': clean_title,
            'link': clean_link,
            'pub_date': rss_pub_time,
            'description': clean_title
        })
    
    # 进行增量去重处理
    deduplicated_articles = advanced_deduplicate_articles(
        raw_articles, category, history_manager, 
        max_recent_articles, time_window_hours=time_window_hours,
        only_new_articles=True
    )
    
    # 新增：AI筛选步骤
    if enable_ai_filter and AI_FILTER_AVAILABLE and len(deduplicated_articles) > ai_filter_count:
        try:
            print(f"  🤖 启动AI筛选功能...")
            ai_filter = NewsQualityFilter()
            filtered_articles = ai_filter.filter_articles(
                deduplicated_articles, category, ai_filter_count
            )
            info['articles'] = filtered_articles
            
            # 更新历史记录（只记录筛选后的文章）
            for article in filtered_articles:
                fingerprint = create_content_fingerprint(
                    article['title'], article['link'], article.get('description', '')
                )
                history_manager.add_published_article(category, fingerprint, article)
                
        except Exception as e:
            print(f"  ❌ AI筛选失败，使用去重后的文章: {e}")
            info['articles'] = deduplicated_articles[:ai_filter_count]
    else:
        if not enable_ai_filter:
            print(f"  🔧 AI筛选已禁用")
        elif not AI_FILTER_AVAILABLE:
            print(f"  ⚠️ AI筛选模块不可用")
        else:
            print(f"  📊 文章数量不足，跳过AI筛选")
        info['articles'] = deduplicated_articles[:ai_filter_count]
    
    return info

def get_original_rss_filename(category):
    """根据分类获取原有的RSS文件名"""
    category_filename_map = {
        'Finance': 'financefreenewsagent.xml',
        'finance': 'financefreenewsagent.xml',
        'Technology': 'technologyfreenewsagent.xml',
        'technology': 'technologyfreenewsagent.xml',
        'AI': 'aifreenewsagent.xml',
        'ai': 'aifreenewsagent.xml',
        '人工智能': 'aifreenewsagent.xml',
    }
    
    if category in category_filename_map:
        return category_filename_map[category]
    
    category_lower = category.lower()
    for key, filename in category_filename_map.items():
        if key.lower() == category_lower:
            return filename
    
    safe_category = category.lower().replace(' ', '').replace('_', '').replace('-', '')
    return f"{safe_category}freenewsagent.xml"

def read_existing_rss_metadata(xml_file_path):
    """读取现有RSS文件的元数据"""
    metadata = {}
    
    if not os.path.exists(xml_file_path):
        return metadata
    
    try:
        with open(xml_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
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
    """根据分类获取认证信息"""
    follow_challenges = {
        'ai': {
            'feedId': '150782771375663104',
            'userId': 'DdasOQb1gouc5RwqkaQc4KLscHJhfeeW'
        },
        'technology': {
            'feedId': '150782874584542208',
            'userId': 'DdasOQb1gouc5RwqkaQc4KLscHJhfeeW'
        },
        'finance': {
            'feedId': '150806458867930112',
            'userId': 'DdasOQb1gouc5RwqkaQc4KLscHJhfeeW'
        }
    }
    
    category_lower = category.lower()
    if category_lower in ['人工智能']:
        category_lower = 'ai'
    
    return follow_challenges.get(category_lower, None)

def generate_cumulative_rss_xml(news_info, category, base_url="https://zskksz.asia/News-Agent", 
                               existing_metadata=None):
    """生成累积RSS XML内容"""
    rss = Element('rss')
    rss.set('version', '2.0')
    rss.set('xmlns:atom', 'http://www.w3.org/2005/Atom')
    
    channel = SubElement(rss, 'channel')
    
    original_filename = get_original_rss_filename(category)
    
    title = SubElement(channel, 'title')
    title.text = f"{category} 新闻汇总 - Free News Agent"
    
    link = SubElement(channel, 'link')
    link.text = f"{base_url}/feed/{original_filename}"
    
    description = SubElement(channel, 'description')
    description.text = f"{category} 分类的最新新闻汇总，由 Free News Agent 自动生成，Gemini AI 筛选优质内容。"
    
    language = SubElement(channel, 'language')
    language.text = "zh-CN"
    
    pub_date = SubElement(channel, 'pubDate')
    pub_date.text = news_info.get('pub_date', datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT'))
    
    last_build_date = SubElement(channel, 'lastBuildDate')
    last_build_date.text = datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT')
    
    generator = SubElement(channel, 'generator')
    generator.text = "News Agent RSS Generator v2.0 (Optimized)"
    
    # 添加认证信息
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
    """获取累积新闻文件列表"""
    if not os.path.exists(news_dir):
        print(f"❌ 累积新闻目录不存在: {news_dir}")
        return []
    
    news_files = []
    for filename in os.listdir(news_dir):
        if filename.endswith('_cumulative.md'):
            news_files.append(os.path.join(news_dir, filename))
    
    return news_files

def extract_category_from_cumulative_filename(filename):
    """从累积文件名中提取分类名称"""
    basename = os.path.basename(filename)
    category = basename.replace('_cumulative.md', '')
    return category

def main():
    """主函数：生成增量RSS Feed"""
    print("=" * 60)
    print("📡 累积RSS Feed生成器 - AI筛选版 v1.0")
    print("=" * 60)
    
    # 配置参数
    news_dir = "cumulative_news"
    feed_dir = "feed"
    base_url = "https://zskksz.asia/News-Agent"
    max_articles_per_feed = 50  # 增加候选文章数
    ai_filter_count = 10  # AI筛选后的目标数量
    time_window_hours = 48
    similarity_threshold = 0.85
    enable_ai_filter = True  # 是否启用AI筛选
    
    print(f"📋 配置信息:")
    print(f"  - 累积新闻目录: {news_dir}")
    print(f"  - Feed输出目录: {feed_dir}")
    print(f"  - 基础URL: {base_url}")
    print(f"  - 候选文章数: {max_articles_per_feed}")
    print(f"  - AI筛选数量: {ai_filter_count}")
    print(f"  - 时间窗口: {time_window_hours} 小时")
    print(f"  - AI筛选: {'启用' if enable_ai_filter else '禁用'}")
    print(f"  - 模式: 增量更新 + AI筛选优质新闻")
    print()
    
    # 初始化历史管理器
    history_manager = RSSHistoryManager()
    print("📚 初始化RSS历史管理器...")
    
    # 清理过期记录
    history_manager.cleanup_old_records(days=30)
    
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
    total_new_articles = 0
    categories_with_updates = []
    categories_no_updates = []
    
    # 为每个分类生成RSS Feed
    for news_file in news_files:
        category = extract_category_from_cumulative_filename(news_file)
        print(f"🔄 处理分类: {category}")
        
        # 显示上次更新时间
        last_update = history_manager.get_last_update_time(category)
        if last_update:
            print(f"  📅 上次更新: {last_update.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            print(f"  📅 首次运行，将获取所有文章")
        
        try:
            # 使用增量更新+AI筛选解析
            news_info = parse_cumulative_markdown_optimized(
                news_file, category, history_manager, 
                max_articles_per_feed, time_window_hours,
                enable_ai_filter, ai_filter_count
            )
            
            if not news_info:
                print(f"  ❌ 解析失败")
                failed_count += 1
                continue
            
            article_count = len(news_info.get('articles', []))
            total_new_articles += article_count
            
            if article_count == 0:
                print(f"  📄 没有新文章，跳过RSS生成")
                categories_no_updates.append(category)
                success_count += 1  # 仍然算作成功，只是没有更新
                
                # 更新历史记录时间（即使没有新文章）
                history_manager.update_last_update_time(category)
                continue
            
            print(f"  📄 包含 {article_count} 篇新文章")
            categories_with_updates.append((category, article_count))
            
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
            
            # 更新历史记录
            history_manager.update_last_update_time(category)
            
            print(f"  ✅ 更新成功: {original_filename}")
            success_count += 1
            
        except Exception as e:
            print(f"  ❌ 生成失败: {e}")
            import traceback
            traceback.print_exc()
            failed_count += 1
    
    # 保存历史记录
    history_manager.save_history()
    
    # 输出统计结果
    print("\n" + "=" * 60)
    print("📊 增量更新结果统计:")
    print("=" * 60)
    print(f"  ✅ 成功处理: {success_count} 个分类")
    print(f"  ❌ 处理失败: {failed_count} 个分类")
    print(f"  🆕 新文章总数: {total_new_articles}")
    print(f"   输出目录: {os.path.abspath(feed_dir)}")
    
    if categories_with_updates:
        print(f"\n📡 有更新的分类 ({len(categories_with_updates)} 个):")
        for category, count in categories_with_updates:
            original_filename = get_original_rss_filename(category)
            print(f"  - {category}: {count} 篇新文章 → {base_url}/feed/{original_filename}")
    
    if categories_no_updates:
        print(f"\n💤 无更新的分类 ({len(categories_no_updates)} 个):")
        for category in categories_no_updates:
            print(f"  - {category}: 没有新文章")
    
    if total_new_articles > 0:
        print(f"\n🎉 增量更新完成！用户将只收到 {total_new_articles} 篇全新文章！")
    else:
        print(f"\n😴 本次运行没有新文章，RSS Feed保持不变")
    
    return success_count > 0

if __name__ == "__main__":
    success = main()
    
    if success:
        print("\n🎯 任务完成！")
    else:
        print("\n💥 任务失败！")
        sys.exit(1)