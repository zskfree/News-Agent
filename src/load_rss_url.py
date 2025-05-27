"""
RSS订阅源数据加载模块

该模块提供了从JSON文件加载RSS订阅源配置的功能。
"""

import json
from typing import List, Dict, Optional


def load_rss_sources(file_path: str) -> List[Dict[str, str]]:
    """
    从指定的JSON文件中加载RSS订阅源配置列表。
    
    参数:
        file_path (str): 包含RSS订阅源配置的JSON文件路径
        
    返回:
        List[Dict[str, str]]: RSS订阅源配置列表，每个配置包含以下字段：
            - name: 订阅源名称
            - category: 分类（如'AI', 'Technology', 'Finance'）
            - language: 语言（如'zh', 'en'）
            - rss: RSS订阅URL
            
    异常:
        当文件不存在、JSON格式错误或其他IO错误时，返回空列表并打印错误信息
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            rss_sources = json.load(file)
            
            # 验证数据格式
            if not isinstance(rss_sources, list):
                print(f"数据格式错误：期望列表格式，实际为 {type(rss_sources)}")
                return []
                
            return rss_sources
            
    except FileNotFoundError:
        print(f"错误：文件未找到 - {file_path}")
        return []
    except json.JSONDecodeError as e:
        print(f"错误：JSON解码失败 - {file_path}，详细信息：{e}")
        return []
    except PermissionError:
        print(f"错误：文件访问权限不足 - {file_path}")
        return []
    except Exception as e:
        print(f"错误：加载RSS订阅源时发生未知错误 - {e}")
        return []


def get_rss_urls_by_category(rss_sources: List[Dict[str, str]], 
                           category: Optional[str] = None) -> List[str]:
    """
    根据分类筛选并提取RSS订阅URL。
    
    参数:
        rss_sources (List[Dict[str, str]]): RSS订阅源配置列表
        category (Optional[str]): 指定分类，为None时返回所有URL
        
    返回:
        List[str]: 筛选后的RSS订阅URL列表
    """
    if category is None:
        return [source.get('rss', '') for source in rss_sources if source.get('rss')]
    
    filtered_urls = []
    for source in rss_sources:
        if source.get('category') == category and source.get('rss'):
            filtered_urls.append(source['rss'])
    
    return filtered_urls


def display_rss_sources(rss_sources: List[Dict[str, str]]) -> None:
    """
    格式化显示RSS订阅源信息。
    
    参数:
        rss_sources (List[Dict[str, str]]): RSS订阅源配置列表
    """
    if not rss_sources:
        print("没有可显示的RSS订阅源。")
        return
    
    print(f"共加载 {len(rss_sources)} 个RSS订阅源：")
    print("-" * 80)
    
    for i, source in enumerate(rss_sources, 1):
        name = source.get('name', '未知')
        category = source.get('category', '未分类')
        language = source.get('language', '未知')
        rss_url = source.get('rss', '无URL')
        
        print(f"{i:2d}. {name}")
        print(f"    分类: {category} | 语言: {language}")
        print(f"    URL: {rss_url}")
        print()

def get_all_categories(rss_sources: List[Dict[str, str]]) -> List[str]:
    """
    获取所有RSS订阅源的分类列表。
    
    参数:
        rss_sources (List[Dict[str, str]]): RSS订阅源配置列表
        
    返回:
        List[str]: 所有分类的唯一列表
    """
    categories = set()
    for source in rss_sources:
        category = source.get('category', '未分类')
        categories.add(category)
    
    return sorted(categories)


if __name__ == "__main__":
    # RSS订阅源配置文件路径
    RSS_CONFIG_FILE = r'RSS feed URL\rss_feed_url.json'
    
    # 加载RSS订阅源配置
    sources = load_rss_sources(RSS_CONFIG_FILE)
    
    if sources:
        # 显示所有订阅源
        display_rss_sources(sources)
        
        # 按分类统计
        categories = {}
        for source in sources:
            category = source.get('category', '未分类')
            categories[category] = categories.get(category, 0) + 1
        
        print("分类统计:")
        for category, count in categories.items():
            print(f"  {category}: {count} 个")
        
        # 示例：获取特定分类的URL
        ai_urls = get_rss_urls_by_category(sources, 'AI')
        print(f"\nAI分类订阅源数量: {len(ai_urls)}")
        
    else:
        print("未能加载任何RSS订阅源配置。")