"""
RSS订阅源读取模块

该模块提供了从RSS订阅源读取数据的功能。
"""

import feedparser
import gc
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
import os
from collections import defaultdict
import hashlib
import json


def read_rss_feed(url):
    """
    从给定的 URL 读取 RSS 订阅源并返回条目列表。
    
    参数:
        url (str): RSS 订阅源的 URL。
        
    返回:
        list: RSS 订阅源中的条目列表。
    """
    try:
        # 设置超时和用户代理
        feed = feedparser.parse(url, agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        if hasattr(feed, 'entries') and feed.entries:
            entries = list(feed.entries)  # 创建副本以避免内存引用问题
            del feed  # 显式删除feed对象
            gc.collect()  # 强制垃圾回收
            return entries
        else:
            print(f"RSS订阅源 {url} 没有条目或格式不正确")
            return []
    except Exception as e:
        print(f"读取 RSS 订阅源 {url} 时出错: {e}")
        return []

def display_feed_entries(entries):
    """
    显示 RSS 订阅源中的条目。
    
    参数:
        entries (list): RSS 订阅源中的条目列表。
    """
    if not entries:
        print("没有找到任何条目。")
        return
    
    for i, entry in enumerate(entries):
        try:
            title = getattr(entry, 'title', '无标题')
            link = getattr(entry, 'link', '#')
            published = getattr(entry, 'published', '未知时间')
            print(f"标题: {title}\n链接: {link}\n发布时间: {published}\n")
        except Exception as e:
            print(f"处理第 {i+1} 个条目时出错: {e}")
            continue

def get_recent_articles_summary(rss_urls, hours_limit=24, output_file=None, rss_sources=None):
    """
    读取指定RSS订阅源列表中的所有订阅源，获取指定时间范围内的文章信息，
    并生成Markdown格式的汇总报告。
    
    参数:
        rss_urls (list): RSS订阅源URL列表
        hours_limit (int): 时间限制（小时），默认24小时
        output_file (str, optional): 输出文件路径，如果提供则保存到文件
        rss_sources (list): RSS源配置信息，用于获取源名称
        
    返回:
        str: Markdown格式的汇总报告
    """
    # 计算时间截止点
    cutoff_time = datetime.now() - timedelta(hours=hours_limit)
    
    # 存储所有符合条件的文章
    all_articles = []
    
    print(f"开始读取 {len(rss_urls)} 个RSS订阅源...")
    print(f"筛选条件：最近 {hours_limit} 小时内的文章")
    print("-" * 50)
    
    for i, url in enumerate(rss_urls, 1):
        print(f"[{i}/{len(rss_urls)}] 正在读取: {url}")
        
        try:
            # 读取RSS订阅源
            entries = read_rss_feed(url)
            
            if not entries:
                print(f"  -> 没有找到文章")
                continue
                
            # 筛选最近的文章
            recent_entries = []
            for entry in entries:
                try:
                    # 尝试解析发布时间
                    published_time = None
                    
                    # 尝试多种时间字段
                    for time_field in ['published', 'updated', 'created']:
                        if hasattr(entry, time_field):
                            time_str = getattr(entry, time_field)
                            try:
                                # 尝试使用 parsedate_to_datetime 解析
                                published_time = parsedate_to_datetime(time_str)
                                break
                            except (TypeError, ValueError):
                                # 如果失败，尝试其他格式
                                try:
                                    # 尝试解析 struct_time 格式
                                    if hasattr(entry, f'{time_field}_parsed'):
                                        time_struct = getattr(entry, f'{time_field}_parsed')
                                        if time_struct:
                                            published_time = datetime(*time_struct[:6])
                                            break
                                except:
                                    continue
                    
                    # 如果成功解析时间且在时间范围内
                    if published_time and published_time > cutoff_time:
                        article_info = {
                            'title': getattr(entry, 'title', '无标题'),
                            'link': getattr(entry, 'link', '#'),
                            'published': published_time.strftime('%Y-%m-%d %H:%M'),
                            'source_url': url
                        }
                        recent_entries.append(article_info)
                        
                except Exception as e:
                    # 如果时间解析失败，仍然包含文章（假设是最近的）
                    article_info = {
                        'title': getattr(entry, 'title', '无标题'),
                        'link': getattr(entry, 'link', '#'),
                        'published': getattr(entry, 'published', '时间未知'),
                        'source_url': url
                    }
                    recent_entries.append(article_info)
                    continue
            
            all_articles.extend(recent_entries)
            print(f"  -> 找到 {len(recent_entries)} 篇符合条件的文章")
            
            # 清理内存
            del entries
            gc.collect()
            
        except Exception as e:
            print(f"  -> 读取失败: {e}")
            continue
    
    print("-" * 50)
    print(f"汇总完成，共找到 {len(all_articles)} 篇文章")
    
    # 按发布时间排序（最新的在前）
    try:
        all_articles.sort(key=lambda x: datetime.strptime(x['published'], '%Y-%m-%d %H:%M') 
                         if x['published'] != '时间未知' else datetime.min, reverse=True)
    except:
        # 如果排序失败，保持原顺序
        pass
    
    # 生成Markdown格式报告
    markdown_content = generate_markdown_report(all_articles, hours_limit, rss_sources)
    
    # 如果指定了输出文件，保存到文件
    if output_file:
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            print(f"报告已保存到: {output_file}")
        except Exception as e:
            print(f"保存文件时出错: {e}")
    
    return markdown_content

def generate_markdown_report(articles, hours_limit, rss_sources=None):
    """
    生成Markdown格式的新闻汇总报告
    
    参数:
        articles (list): 文章信息列表
        hours_limit (int): 时间限制（小时）
        rss_sources (list): RSS源配置信息，用于获取源名称和网站URL
        
    返回:
        str: Markdown格式的报告
    """
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    # 构建Markdown内容
    md_lines = [
        f"# 新闻汇总报告",
        f"",
        f"**生成时间**: {current_time}",
        f"**时间范围**: 最近 {hours_limit} 小时",
        f"**文章总数**: {len(articles)}",
        f"",
        f"---",
        f""
    ]
    
    if not articles:
        md_lines.append("**暂无符合条件的文章**")
    else:
        # 按来源分组
        sources = {}
        for article in articles:
            source_url = article['source_url']
            if source_url not in sources:
                sources[source_url] = []
            sources[source_url].append(article)
        
        # 生成每个来源的文章列表
        for source_url, source_articles in sources.items():
            # 获取源名称和网站URL
            source_name = source_url  # 默认使用RSS URL作为名称
            website_url = source_url  # 默认使用RSS URL作为链接
            
            if rss_sources:
                # 从rss_sources中查找对应的配置
                for source in rss_sources:
                    if source.get('rss') == source_url:  # 注意这里应该是'rss'字段
                        source_name = source.get('name', source_url)
                        # 优先使用website字段，如果没有则使用url字段，最后使用RSS URL
                        website_url = source.get('website') or source.get('url') or source_url
                        break
            
            # 生成可点击的来源标题
            md_lines.append(f"## 📰 来源: [{source_name}]({website_url})")
            md_lines.append(f"")
            
            for article in source_articles:
                title = article['title'].replace('[', '\\[').replace(']', '\\]')  # 转义Markdown特殊字符
                link = article['link']
                published = article['published']
                
                md_lines.append(f"### [{title}]({link})")
                md_lines.append(f"**发布时间**: {published}")
                md_lines.append(f"")
            
            md_lines.append("---")
            md_lines.append("")
    
    return '\n'.join(md_lines)

def generate_news_by_categories(rss_sources, hours_limit=24, output_dir="news"):
    """
    按分类读取RSS订阅源，为每个分类生成独立的Markdown新闻汇总报告。
    
    参数:
        rss_sources (list): RSS源配置信息列表
        hours_limit (int): 时间限制（小时），默认24小时
        output_dir (str): 输出目录，默认为"news"
        
    返回:
        dict: 每个分类的报告生成结果 {category: {"success": bool, "file_path": str, "article_count": int}}
    """
    # 确保输出目录存在
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"创建输出目录: {output_dir}")
    
    # 按分类分组RSS源
    categories = defaultdict(list)
    for source in rss_sources:
        category = source.get('category', '未分类')
        categories[category].append(source)
    
    print(f"发现 {len(categories)} 个分类: {list(categories.keys())}")
    print("="*60)
    
    results = {}
    
    # 为每个分类生成报告
    for category, sources in categories.items():
        print(f"\n处理分类: {category} ({len(sources)} 个订阅源)")
        print("-" * 40)
        
        try:
            # 提取该分类下的所有RSS URL
            rss_urls = [source.get('rss') for source in sources if source.get('rss')]
            
            if not rss_urls:
                print(f"  分类 '{category}' 没有有效的RSS订阅源")
                results[category] = {
                    "success": False, 
                    "file_path": None, 
                    "article_count": 0,
                    "error": "没有有效的RSS订阅源"
                }
                continue
            
            # 生成文件名（处理特殊字符）
            safe_category = category.replace(' ', '_').replace('/', '_').replace('\\', '_')
            timestamp = datetime.now().strftime('%Y%m%d')
            filename = f"{safe_category}_{timestamp}.md"
            output_file = os.path.join(output_dir, filename)
            
            # 生成该分类的新闻汇总
            markdown_content = get_recent_articles_summary(
                rss_urls=rss_urls,
                hours_limit=hours_limit,
                output_file=output_file,
                rss_sources=sources  # 只传递该分类的源信息
            )
            
            # 统计文章数量
            article_count = markdown_content.count('### [') if markdown_content else 0
            
            results[category] = {
                "success": True,
                "file_path": output_file,
                "article_count": article_count,
                "source_count": len(sources)
            }
            
            print(f"  ✓ 分类 '{category}' 报告生成成功")
            print(f"    文件: {output_file}")
            print(f"    文章数: {article_count}")
            
        except Exception as e:
            print(f"  ✗ 分类 '{category}' 报告生成失败: {e}")
            results[category] = {
                "success": False,
                "file_path": None,
                "article_count": 0,
                "error": str(e)
            }
    
    # 生成汇总报告
    generate_summary_report(results, output_dir, hours_limit)
    
    return results

def generate_summary_report(results, output_dir, hours_limit):
    """
    生成各分类新闻汇总的总览报告
    
    参数:
        results (dict): 各分类的生成结果
        output_dir (str): 输出目录
        hours_limit (int): 时间限制（小时）
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    summary_file = os.path.join(output_dir, f"summary_report_{timestamp}.md")
    
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    md_lines = [
        "# 新闻汇总总览报告",
        "",
        f"**生成时间**: {current_time}",
        f"**时间范围**: 最近 {hours_limit} 小时",
        f"**分类总数**: {len(results)}",
        "",
        "---",
        ""
    ]
    
    # 统计信息
    total_articles = sum(r.get('article_count', 0) for r in results.values())
    successful_categories = sum(1 for r in results.values() if r.get('success', False))
    
    md_lines.extend([
        "## 📊 统计信息",
        "",
        f"- **文章总数**: {total_articles}",
        f"- **成功分类**: {successful_categories}/{len(results)}",
        "",
        "---",
        ""
    ])
    
    # 各分类详情
    md_lines.extend([
        "## 📂 分类详情",
        ""
    ])
    
    for category, result in results.items():
        if result.get('success', False):
            file_name = os.path.basename(result['file_path'])
            article_count = result.get('article_count', 0)
            source_count = result.get('source_count', 0)
            
            md_lines.extend([
                f"### ✅ {category}",
                f"- **文章数量**: {article_count}",
                f"- **订阅源数量**: {source_count}",
                f"- **报告文件**: [{file_name}](./{file_name})",
                ""
            ])
        else:
            error_msg = result.get('error', '未知错误')
            md_lines.extend([
                f"### ❌ {category}",
                f"- **状态**: 生成失败",
                f"- **错误**: {error_msg}",
                ""
            ])
    
    # 保存总览报告
    try:
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(md_lines))
        print(f"\n📋 总览报告已生成: {summary_file}")
    except Exception as e:
        print(f"\n❌ 总览报告生成失败: {e}")

def generate_all_categories_news(rss_sources, hours_limit=24, output_dir="news"):
    """
    一键生成所有分类的新闻汇总报告
    
    参数:
        config_file_path (str): RSS配置文件路径，默认使用标准路径
        hours_limit (int): 时间限制（小时），默认24小时
        output_dir (str): 输出目录，默认为"news"
        
    返回:
        dict: 生成结果
    """
    try:
        if not rss_sources:
            print("❌ 没有加载到任何RSS订阅源配置")
            return {}
        
        print(f"📚 成功加载 {len(rss_sources)} 个RSS订阅源配置")
        
        # 按分类生成新闻报告
        results = generate_news_by_categories(
            rss_sources=rss_sources,
            hours_limit=hours_limit,
            output_dir=output_dir
        )
        
        # 输出最终统计
        print("\n" + "="*60)
        print("📈 最终统计:")
        successful = sum(1 for r in results.values() if r.get('success', False))
        total_articles = sum(r.get('article_count', 0) for r in results.values())
        
        print(f"  ✅ 成功生成: {successful}/{len(results)} 个分类")
        print(f"  📰 文章总数: {total_articles}")
        print(f"  📁 输出目录: {os.path.abspath(output_dir)}")
        
        return results
        
    except Exception as e:
        print(f"❌ 生成新闻报告时发生错误: {e}")
        return {}


def generate_article_hash(title, link):
    """
    生成文章的唯一哈希值，用于去重
    
    参数:
        title (str): 文章标题
        link (str): 文章链接
        
    返回:
        str: 文章的哈希值
    """
    # 使用标题和链接的组合生成哈希，确保唯一性
    content = f"{title.strip()}{link.strip()}"
    return hashlib.md5(content.encode('utf-8')).hexdigest()

def load_existing_articles(file_path):
    """
    从现有的MD文件中加载已存在的文章哈希值
    
    参数:
        file_path (str): MD文件路径
        
    返回:
        set: 已存在文章的哈希值集合
    """
    existing_hashes = set()
    
    if not os.path.exists(file_path):
        return existing_hashes
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 使用正则表达式提取所有文章链接和标题
        import re
        article_pattern = r'### \[(.+?)\]\((.+?)\)'
        articles = re.findall(article_pattern, content)
        
        for title, link in articles:
            # 清理转义字符
            clean_title = title.replace('\\[', '[').replace('\\]', ']').strip()
            clean_link = link.strip()
            article_hash = generate_article_hash(clean_title, clean_link)
            existing_hashes.add(article_hash)
            
    except Exception as e:
        print(f"加载现有文章时出错: {e}")
    
    return existing_hashes

def get_all_historical_articles(rss_urls, output_file=None, rss_sources=None, max_articles_per_source=50):
    """
    获取所有RSS订阅源的历史新闻（不限时间），并去重追加到累积文档中
    
    参数:
        rss_urls (list): RSS订阅源URL列表
        output_file (str): 输出文件路径
        rss_sources (list): RSS源配置信息，用于获取源名称
        max_articles_per_source (int): 每个源最多获取的文章数量，防止文件过大
        
    返回:
        dict: 包含新增文章信息和统计数据
    """
    print(f"开始获取 {len(rss_urls)} 个RSS订阅源的历史新闻...")
    print(f"每个订阅源最多获取 {max_articles_per_source} 篇文章")
    print("-" * 50)
    
    # 加载现有文章哈希值
    existing_hashes = set()
    if output_file:
        existing_hashes = load_existing_articles(output_file)
        print(f"已加载 {len(existing_hashes)} 个现有文章的哈希值")
    
    # 存储所有新文章
    new_articles = []
    duplicate_count = 0
    source_stats = {}
    
    for i, url in enumerate(rss_urls, 1):
        print(f"[{i}/{len(rss_urls)}] 正在读取: {url}")
        
        try:
            # 读取RSS订阅源
            entries = read_rss_feed(url)
            
            if not entries:
                print(f"  -> 没有找到文章")
                source_stats[url] = {"new": 0, "duplicate": 0, "total": 0}
                continue
            
            # 限制文章数量
            entries = entries[:max_articles_per_source]
            
            new_count = 0
            dup_count = 0
            
            for entry in entries:
                try:
                    title = getattr(entry, 'title', '无标题')
                    link = getattr(entry, 'link', '#')
                    
                    # 生成文章哈希值
                    article_hash = generate_article_hash(title, link)
                    
                    # 检查是否重复
                    if article_hash in existing_hashes:
                        dup_count += 1
                        continue
                    
                    # 解析发布时间
                    published_time = None
                    for time_field in ['published', 'updated', 'created']:
                        if hasattr(entry, time_field):
                            time_str = getattr(entry, time_field)
                            try:
                                published_time = parsedate_to_datetime(time_str)
                                break
                            except (TypeError, ValueError):
                                try:
                                    if hasattr(entry, f'{time_field}_parsed'):
                                        time_struct = getattr(entry, f'{time_field}_parsed')
                                        if time_struct:
                                            published_time = datetime(*time_struct[:6])
                                            break
                                except:
                                    continue
                    
                    article_info = {
                        'title': title,
                        'link': link,
                        'published': published_time.strftime('%Y-%m-%d %H:%M') if published_time else '时间未知',
                        'source_url': url,
                        'hash': article_hash
                    }
                    
                    new_articles.append(article_info)
                    existing_hashes.add(article_hash)  # 添加到已存在集合中
                    new_count += 1
                    
                except Exception as e:
                    print(f"  -> 处理文章时出错: {e}")
                    continue
            
            source_stats[url] = {
                "new": new_count, 
                "duplicate": dup_count, 
                "total": len(entries)
            }
            duplicate_count += dup_count
            
            print(f"  -> 新增 {new_count} 篇，重复 {dup_count} 篇")
            
            # 清理内存
            del entries
            gc.collect()
            
        except Exception as e:
            print(f"  -> 读取失败: {e}")
            source_stats[url] = {"new": 0, "duplicate": 0, "total": 0, "error": str(e)}
            continue
    
    print("-" * 50)
    print(f"汇总完成，共找到 {len(new_articles)} 篇新文章，跳过 {duplicate_count} 篇重复文章")
    
    # 按发布时间排序（最新的在前）
    try:
        new_articles.sort(key=lambda x: datetime.strptime(x['published'], '%Y-%m-%d %H:%M') 
                         if x['published'] != '时间未知' else datetime.min, reverse=True)
    except:
        pass
    
    # 如果有新文章且指定了输出文件，追加到文件
    if new_articles and output_file:
        append_articles_to_file(new_articles, output_file, rss_sources)
    
    return {
        'new_articles': new_articles,
        'new_count': len(new_articles),
        'duplicate_count': duplicate_count,
        'source_stats': source_stats
    }

def append_articles_to_file(new_articles, output_file, rss_sources=None):
    """
    将新文章追加到现有的MD文件中
    
    参数:
        new_articles (list): 新文章列表
        output_file (str): 输出文件路径
        rss_sources (list): RSS源配置信息
    """
    try:
        # 读取现有内容
        existing_content = ""
        if os.path.exists(output_file):
            with open(output_file, 'r', encoding='utf-8') as f:
                existing_content = f.read()
        
        # 生成新文章的Markdown内容
        new_content = generate_cumulative_markdown_report(new_articles, rss_sources, existing_content)
        
        # 写入文件
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"成功追加 {len(new_articles)} 篇新文章到: {output_file}")
        
    except Exception as e:
        print(f"追加文章到文件时出错: {e}")

def generate_cumulative_markdown_report(new_articles, rss_sources=None, existing_content=""):
    """
    生成累积的Markdown格式报告
    
    参数:
        new_articles (list): 新文章列表
        rss_sources (list): RSS源配置信息
        existing_content (str): 现有文件内容
        
    返回:
        str: 更新后的Markdown内容
    """
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    # 如果是新文件，创建头部
    if not existing_content:
        md_lines = [
            f"# 累积新闻汇总",
            f"",
            f"**首次创建时间**: {current_time}",
            f"**最后更新时间**: {current_time}",
            f"",
            f"---",
            f""
        ]
    else:
        # 更新现有文件的最后更新时间
        import re
        md_lines = existing_content.split('\n')
        
        # 更新最后更新时间
        for i, line in enumerate(md_lines):
            if line.startswith('**最后更新时间**:'):
                md_lines[i] = f"**最后更新时间**: {current_time}"
                break
        else:
            # 如果找不到更新时间行，在第5行插入
            if len(md_lines) > 4:
                md_lines.insert(4, f"**最后更新时间**: {current_time}")
    
    # 如果有新文章，添加到开头
    if new_articles:
        # 找到第一个文章开始的位置（在---后面）
        insert_pos = len(md_lines)
        for i, line in enumerate(md_lines):
            if line.strip() == "---" and i < len(md_lines) - 1:
                insert_pos = i + 2  # 在---后面的空行后插入
                break
        
        # 按来源分组新文章
        sources = {}
        for article in new_articles:
            source_url = article['source_url']
            if source_url not in sources:
                sources[source_url] = []
            sources[source_url].append(article)
        
        # 生成新文章内容
        new_lines = [f"## 🆕 最新更新 ({current_time})"]
        
        for source_url, source_articles in sources.items():
            # 获取源名称和网站URL
            source_name = source_url
            website_url = source_url
            
            if rss_sources:
                for source in rss_sources:
                    if source.get('rss') == source_url:
                        source_name = source.get('name', source_url)
                        website_url = source.get('website') or source.get('url') or source_url
                        break
            
            new_lines.append(f"### 📰 来源: [{source_name}]({website_url})")
            new_lines.append("")
            
            for article in source_articles:
                title = article['title'].replace('[', '\\[').replace(']', '\\]')
                link = article['link']
                published = article['published']
                
                new_lines.append(f"#### [{title}]({link})")
                new_lines.append(f"**发布时间**: {published}")
                new_lines.append("")
        
        new_lines.extend(["---", ""])
        
        # 插入新内容
        md_lines[insert_pos:insert_pos] = new_lines
    
    return '\n'.join(md_lines)

def generate_historical_news_by_categories(rss_sources, output_dir="cumulative_news", max_articles_per_source=50):
    """
    按分类获取历史新闻并追加到累积文档中
    
    参数:
        rss_sources (list): RSS源配置信息列表
        output_dir (str): 输出目录
        max_articles_per_source (int): 每个源最多获取的文章数量
        
    返回:
        dict: 每个分类的处理结果
    """
    # 确保输出目录存在
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"创建输出目录: {output_dir}")
    
    # 按分类分组RSS源
    categories = defaultdict(list)
    for source in rss_sources:
        category = source.get('category', '未分类')
        categories[category].append(source)
    
    print(f"发现 {len(categories)} 个分类: {list(categories.keys())}")
    print("="*60)
    
    results = {}
    
    # 为每个分类处理新闻
    for category, sources in categories.items():
        print(f"\n处理分类: {category} ({len(sources)} 个订阅源)")
        print("-" * 40)
        
        try:
            # 提取该分类下的所有RSS URL
            rss_urls = [source.get('rss') for source in sources if source.get('rss')]
            
            if not rss_urls:
                print(f"  分类 '{category}' 没有有效的RSS订阅源")
                results[category] = {
                    "success": False,
                    "error": "没有有效的RSS订阅源",
                    "new_count": 0,
                    "duplicate_count": 0
                }
                continue
            
            # 生成累积文件名
            safe_category = category.replace(' ', '_').replace('/', '_').replace('\\', '_')
            filename = f"{safe_category}_cumulative.md"
            output_file = os.path.join(output_dir, filename)
            
            # 获取历史新闻
            result = get_all_historical_articles(
                rss_urls=rss_urls,
                output_file=output_file,
                rss_sources=sources,
                max_articles_per_source=max_articles_per_source
            )
            
            results[category] = {
                "success": True,
                "file_path": output_file,
                "new_count": result['new_count'],
                "duplicate_count": result['duplicate_count'],
                "source_count": len(sources),
                "source_stats": result['source_stats']
            }
            
            print(f"  ✓ 分类 '{category}' 处理完成")
            print(f"    文件: {output_file}")
            print(f"    新增文章: {result['new_count']}")
            print(f"    重复文章: {result['duplicate_count']}")
            
        except Exception as e:
            print(f"  ✗ 分类 '{category}' 处理失败: {e}")
            results[category] = {
                "success": False,
                "error": str(e),
                "new_count": 0,
                "duplicate_count": 0
            }
    
    # 生成汇总报告
    generate_cumulative_summary_report(results, output_dir)
    
    return results

def generate_cumulative_summary_report(results, output_dir):
    """
    生成累积新闻的汇总报告
    
    参数:
        results (dict): 各分类的处理结果
        output_dir (str): 输出目录
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    summary_file = os.path.join(output_dir, f"cumulative_summary_{timestamp}.md")
    
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    md_lines = [
        "# 累积新闻汇总报告",
        "",
        f"**生成时间**: {current_time}",
        f"**分类总数**: {len(results)}",
        "",
        "---",
        ""
    ]
    
    # 统计信息
    total_new = sum(r.get('new_count', 0) for r in results.values())
    total_duplicate = sum(r.get('duplicate_count', 0) for r in results.values())
    successful_categories = sum(1 for r in results.values() if r.get('success', False))
    
    md_lines.extend([
        "## 📊 统计信息",
        "",
        f"- **新增文章总数**: {total_new}",
        f"- **重复文章总数**: {total_duplicate}",
        f"- **成功分类**: {successful_categories}/{len(results)}",
        "",
        "---",
        ""
    ])
    
    # 各分类详情
    md_lines.extend([
        "## 📂 分类详情",
        ""
    ])
    
    for category, result in results.items():
        if result.get('success', False):
            file_name = os.path.basename(result['file_path'])
            new_count = result.get('new_count', 0)
            duplicate_count = result.get('duplicate_count', 0)
            source_count = result.get('source_count', 0)
            
            md_lines.extend([
                f"### ✅ {category}",
                f"- **新增文章**: {new_count}",
                f"- **重复文章**: {duplicate_count}",
                f"- **订阅源数量**: {source_count}",
                f"- **累积文件**: [{file_name}](./{file_name})",
                ""
            ])
        else:
            error_msg = result.get('error', '未知错误')
            md_lines.extend([
                f"### ❌ {category}",
                f"- **状态**: 处理失败",
                f"- **错误**: {error_msg}",
                ""
            ])
    
    # 保存汇总报告
    try:
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(md_lines))
        print(f"\n📋 汇总报告已生成: {summary_file}")
    except Exception as e:
        print(f"\n❌ 汇总报告生成失败: {e}")


# 示例用法
if __name__ == "__main__":
    try:
        # 选择运行模式
        print("请选择运行模式:")
        print("1. 生成单个分类的新闻汇总 (如AI分类)")
        print("2. 生成所有分类的新闻汇总")
        
        choice = input("请输入选择 (1 或 2): ").strip()
        
        if choice == "1":
            # 原有的单分类模式
            from load_rss_url import load_rss_sources, get_rss_urls_by_category
            RSS_CONFIG_FILE = r'RSS feed URL\rss_feed_url.json'
            rss_sources = load_rss_sources(RSS_CONFIG_FILE)

            # 筛选AI相关的RSS订阅源
            ai_rss_urls = get_rss_urls_by_category(rss_sources, category='AI')

            if not ai_rss_urls:
                print("没有找到AI相关的RSS订阅源。")
            else:
                # 生成最近24小时的新闻汇总报告
                output_file = f"news_summary_{datetime.now().strftime('%Y%m%d')}.md"
                markdown_report = get_recent_articles_summary(
                    rss_urls=ai_rss_urls,
                    hours_limit=24,  # 可以修改时间限制
                    output_file=output_file,
                    rss_sources=rss_sources  # 传递RSS源信息
                )
                
                print("\n" + "="*50)
                print("Markdown报告预览:")
                print("="*50)
                print(markdown_report[:500] + "..." if len(markdown_report) > 500 else markdown_report)
        
        elif choice == "2":
            # 新的多分类模式
            print("\n🚀 开始生成所有分类的新闻汇总报告...")
            
            from load_rss_url import load_rss_sources
            # 加载RSS订阅源配置
            RSS_CONFIG_FILE = r'RSS feed URL\rss_feed_url.json'
            rss_sources = load_rss_sources(RSS_CONFIG_FILE)
            
            # 可以自定义参数
            hours_limit = 24  # 时间限制
            timestamp = datetime.now().strftime('%Y%m%d')
            output_dir = f"news/{timestamp}"  # 输出目录

            results = generate_all_categories_news(
                rss_sources=rss_sources,
                hours_limit=hours_limit,
                output_dir=output_dir
            )
            
            if results:
                print(f"\n✨ 所有报告已生成完成，请查看 '{output_dir}' 目录")
            else:
                print("\n❌ 报告生成失败")
        
        else:
            print("无效的选择，程序退出。")
                
    except Exception as e:
        print(f"程序运行时出错: {e}")
    finally:
        gc.collect()
