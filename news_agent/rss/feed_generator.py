"""
RSS Feed XML生成模块

提供RSS Feed XML文件的生成功能
"""

from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom
from datetime import datetime
from typing import Dict, List, Optional


def get_category_follow_challenge(category: str) -> Optional[Dict]:
    """
    根据分类获取认证信息
    
    参数:
        category (str): 分类名称
        
    返回:
        Optional[Dict]: 认证信息字典，如果没有则返回None
    """
    follow_challenges = {
        'ai': {
            'feedId': '217166864192638976',
            'userId': '150738471966655488'
        },
        'technology': {
            'feedId': '217164540264016896',
            'userId': '150738471966655488'
        },
        'finance': {
            'feedId': '217167357570321408',
            'userId': '150738471966655488'
        }
    }
    
    category_lower = category.lower()
    if category_lower in ['人工智能']:
        category_lower = 'ai'
    
    return follow_challenges.get(category_lower, None)


def get_rss_filename(category: str) -> str:
    """
    根据分类获取RSS文件名
    
    参数:
        category (str): 分类名称
        
    返回:
        str: RSS文件名
    """
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
    
    # 默认格式
    safe_category = category.lower().replace(' ', '').replace('_', '').replace('-', '')
    return f"{safe_category}freenewsagent.xml"


def generate_rss_xml(news_info: Dict, category: str, 
                    base_url: str = "https://zskksz.asia/News-Agent",
                    existing_metadata: Optional[Dict] = None) -> str:
    """
    生成RSS XML内容
    
    参数:
        news_info (Dict): 新闻信息字典，包含title, description, pub_date, articles等
        category (str): 分类名称
        base_url (str): 网站基础URL
        existing_metadata (Dict, optional): 现有RSS的元数据
        
    返回:
        str: 格式化的RSS XML字符串
    """
    rss = Element('rss')
    rss.set('version', '2.0')
    rss.set('xmlns:atom', 'http://www.w3.org/2005/Atom')
    
    channel = SubElement(rss, 'channel')
    
    rss_filename = get_rss_filename(category)
    
    # 频道基本信息
    title = SubElement(channel, 'title')
    title.text = f"{category} 新闻汇总 - Free News Agent"
    
    link = SubElement(channel, 'link')
    link.text = f"{base_url}/feed/{rss_filename}"
    
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
    atom_link.set('href', f"{base_url}/feed/{rss_filename}")
    atom_link.set('rel', 'self')
    atom_link.set('type', 'application/rss+xml')
    
    # 添加文章项目
    for article in news_info.get('articles', []):
        item = SubElement(channel, 'item')
        
        item_title = SubElement(item, 'title')
        item_title.text = article.get('title', '无标题')
        
        item_link = SubElement(item, 'link')
        item_link.text = article.get('link', '#')
        
        item_description = SubElement(item, 'description')
        desc = article.get('description', article.get('title', ''))
        item_description.text = f"<![CDATA[{desc}]]>"
        
        item_pub_date = SubElement(item, 'pubDate')
        item_pub_date.text = article.get('pub_date', pub_date.text)
        
        # 添加GUID
        guid = SubElement(item, 'guid')
        guid.set('isPermaLink', 'true')
        guid.text = article.get('link', '#')
        
        # 添加分类
        item_category = SubElement(item, 'category')
        item_category.text = category
    
    # 格式化XML
    rough_string = tostring(rss, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ", encoding='utf-8').decode('utf-8')


def read_existing_rss_metadata(xml_file_path: str) -> Dict:
    """
    读取现有RSS文件的元数据
    
    参数:
        xml_file_path (str): RSS XML文件路径
        
    返回:
        Dict: 元数据字典
    """
    import os
    
    metadata = {}
    
    if not os.path.exists(xml_file_path):
        return metadata
    
    try:
        from xml.etree import ElementTree as ET
        tree = ET.parse(xml_file_path)
        root = tree.getroot()
        
        # 提取follow_challenge信息
        follow_challenge = root.find('.//follow_challenge')
        if follow_challenge is not None:
            feed_id_elem = follow_challenge.find('feedId')
            user_id_elem = follow_challenge.find('userId')
            
            if feed_id_elem is not None and user_id_elem is not None:
                metadata['follow_challenge'] = {
                    'feedId': feed_id_elem.text,
                    'userId': user_id_elem.text
                }
    
    except Exception as e:
        print(f"  ⚠️ 读取RSS元数据失败: {e}")
    
    return metadata


if __name__ == "__main__":
    # 测试RSS生成
    print("🧪 测试RSS Feed生成...")
    
    test_news = {
        'title': '测试新闻',
        'description': '这是一个测试',
        'pub_date': datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT'),
        'articles': [
            {
                'title': 'GPT-5发布',
                'link': 'https://example.com/gpt5',
                'description': 'OpenAI发布GPT-5',
                'pub_date': datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT')
            }
        ]
    }
    
    xml_content = generate_rss_xml(test_news, 'AI')
    print("\n生成的RSS XML (前500字符):")
    print(xml_content[:500])
