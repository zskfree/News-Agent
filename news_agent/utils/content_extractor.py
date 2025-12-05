"""
RSS文章内容提取模块

提供从RSS Entry中提取完整文章信息的功能，支持多种RSS格式
包括处理缺失字段的优雅降级
"""

import re
import html
from typing import Dict, Optional
from html.parser import HTMLParser


class HTMLStripper(HTMLParser):
    """HTML标签移除器"""
    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.fed = []
    
    def handle_data(self, data):
        self.fed.append(data)
    
    def get_data(self):
        return ''.join(self.fed)


def strip_html_tags(html_text: str) -> str:
    """
    移除HTML标签，保留文本内容
    
    参数:
        html_text (str): 包含HTML标签的文本
        
    返回:
        str: 纯文本
    """
    if not html_text:
        return ""
    
    try:
        # 首先解码HTML实体
        decoded = html.unescape(html_text)
        
        # 移除HTML标签
        stripper = HTMLStripper()
        stripper.feed(decoded)
        text = stripper.get_data()
        
        # 清理多余的空白符
        text = ' '.join(text.split())
        
        return text
    except Exception as e:
        # 如果解析失败，使用正则表达式
        text = re.sub(r'<[^>]+>', '', html_text)
        text = html.unescape(text)
        return ' '.join(text.split())


def extract_article_content(entry, max_description_length: int = 500) -> Dict[str, Optional[str]]:
    """
    从RSS Entry中提取完整的文章内容信息
    
    参数:
        entry: RSS entry对象（feedparser解析的对象）
        max_description_length (int): 摘要的最大字符数
        
    返回:
        Dict: 包含以下字段的字典
            - title: 文章标题
            - link: 文章链接
            - description: 文章摘要/描述（优先级：summary > content > description）
            - content: 完整内容
            - author: 作者
            - pub_date: 发布日期
            - updated: 更新日期
            - category: 分类标签
            - source: 来源标签
    """
    content_info = {
        'title': None,
        'link': None,
        'description': None,
        'content': None,
        'author': None,
        'pub_date': None,
        'updated': None,
        'category': None,
        'source': None,
    }
    
    # 提取标题
    content_info['title'] = getattr(entry, 'title', None)
    if content_info['title']:
        content_info['title'] = strip_html_tags(content_info['title']).strip()
    
    # 提取链接
    content_info['link'] = getattr(entry, 'link', None)
    
    # 提取作者
    content_info['author'] = getattr(entry, 'author', None)
    
    # 提取发布时间
    content_info['pub_date'] = getattr(entry, 'published', None)
    
    # 提取更新时间
    content_info['updated'] = getattr(entry, 'updated', None)
    
    # 提取分类（优先级：tags > category）
    if hasattr(entry, 'tags') and entry.tags:
        # 取第一个标签
        try:
            tags = entry.tags
            if tags and isinstance(tags, list) and len(tags) > 0:
                # 尝试获取标签的term或label字段
                first_tag = tags[0]
                if isinstance(first_tag, dict):
                    content_info['category'] = first_tag.get('term') or first_tag.get('label')
                else:
                    content_info['category'] = str(first_tag)
        except Exception:
            pass
    
    if not content_info['category']:
        content_info['category'] = getattr(entry, 'category', None)
    
    # 提取来源（优先级：source.title > source）
    if hasattr(entry, 'source'):
        source = entry.source
        if isinstance(source, dict):
            content_info['source'] = source.get('title', None)
        else:
            content_info['source'] = str(source)
    
    # 提取描述/摘要 - 优先级顺序很重要
    description = None
    
    # 优先级1: content字段（某些RSS使用content而不是summary）
    if hasattr(entry, 'content') and entry.content:
        content_list = entry.content
        if isinstance(content_list, list) and len(content_list) > 0:
            content_item = content_list[0]
            if isinstance(content_item, dict) and 'value' in content_item:
                description = strip_html_tags(content_item['value'])
            elif isinstance(content_item, str):
                description = strip_html_tags(content_item)
        content_info['content'] = description
    
    # 优先级2: summary字段
    if not description and hasattr(entry, 'summary'):
        summary = getattr(entry, 'summary', None)
        if summary:
            description = strip_html_tags(summary)
    
    # 优先级3: description字段
    if not description and hasattr(entry, 'description'):
        desc = getattr(entry, 'description', None)
        if desc:
            description = strip_html_tags(desc)
    
    # 优先级4: subtitle字段（某些RSS源使用）
    if not description and hasattr(entry, 'subtitle'):
        subtitle = getattr(entry, 'subtitle', None)
        if subtitle:
            description = strip_html_tags(subtitle)
    
    # 优先级5: 生成从标题和内容的组合摘要
    if not description:
        # 尝试从其他字段生成摘要
        if hasattr(entry, 'id'):
            entry_id = entry.id
            if entry_id:
                description = f"来源: {entry_id}"
    
    # 清理和截断描述
    if description:
        # 移除多余的空白符
        description = ' '.join(description.split())
        
        # 截断到最大长度，但不在单词中间
        if len(description) > max_description_length:
            truncated = description[:max_description_length]
            # 找到最后一个完整的词
            last_space = truncated.rfind(' ')
            if last_space > max_description_length * 0.8:  # 确保不会删除太多内容
                description = truncated[:last_space] + "..."
            else:
                description = truncated + "..."
    
    content_info['description'] = description or ""
    
    return content_info


def extract_articles_batch(entries, max_description_length: int = 500) -> list:
    """
    批量提取文章内容
    
    参数:
        entries: RSS entries列表
        max_description_length (int): 摘要最大长度
        
    返回:
        list: 提取的文章信息列表
    """
    articles = []
    for entry in entries:
        try:
            article = extract_article_content(entry, max_description_length)
            articles.append(article)
        except Exception as e:
            print(f"  ⚠️ 提取文章内容失败: {e}")
            continue
    
    return articles


def format_article_info(article: Dict) -> str:
    """
    格式化文章信息为可读的字符串
    
    参数:
        article (Dict): 文章信息字典
        
    返回:
        str: 格式化的文章信息
    """
    lines = []
    
    if article.get('title'):
        lines.append(f"📌 标题: {article['title']}")
    
    if article.get('author'):
        lines.append(f"✍️ 作者: {article['author']}")
    
    if article.get('pub_date'):
        lines.append(f"🕐 发布时间: {article['pub_date']}")
    
    if article.get('category'):
        lines.append(f"📂 分类: {article['category']}")
    
    if article.get('source'):
        lines.append(f"📰 来源: {article['source']}")
    
    if article.get('link'):
        lines.append(f"🔗 链接: {article['link']}")
    
    if article.get('description'):
        lines.append(f"📄 摘要: {article['description']}")
    
    return '\n'.join(lines)


if __name__ == "__main__":
    # 测试内容提取
    print("🧪 测试内容提取器...")
    
    # 创建测试对象
    class MockEntry:
        def __init__(self):
            self.title = "Test Article <b>Title</b>"
            self.link = "https://example.com/article"
            self.author = "John Doe"
            self.published = "Mon, 28 Nov 2025 10:00:00 GMT"
            self.summary = "This is a <i>summary</i> with <b>HTML</b> tags"
            self.category = "Technology"
            self.tags = [{'term': 'AI', 'label': 'Artificial Intelligence'}]
    
    test_entry = MockEntry()
    
    result = extract_article_content(test_entry)
    print("\n📋 提取结果:")
    for key, value in result.items():
        print(f"  {key}: {value}")
    
    print("\n📝 格式化输出:")
    print(format_article_info(result))