"""
配置加载模块

提供统一的配置管理，支持环境变量和默认路径
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Optional


def get_project_root() -> Path:
    """
    获取项目根目录
    
    返回:
        Path: 项目根目录路径
    """
    # 从当前文件向上查找项目根目录（包含README.md的目录）
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "README.md").exists():
            return parent
    # 如果找不到，返回当前文件的父目录的父目录
    return current.parent.parent


def get_project_paths() -> Dict[str, Path]:
    """
    获取项目各目录路径
    
    返回:
        Dict[str, Path]: 包含各目录路径的字典
    """
    root = get_project_root()
    
    return {
        'root': root,
        'config': Path(os.getenv('NEWS_AGENT_CONFIG_DIR', root / 'config')),
        'data': Path(os.getenv('NEWS_AGENT_DATA_DIR', root / 'data')),
        'outputs': Path(os.getenv('NEWS_AGENT_OUTPUT_DIR', root / 'outputs')),
        'logs': Path(os.getenv('NEWS_AGENT_LOG_DIR', root / 'logs')),
        'feed': Path(os.getenv('NEWS_AGENT_FEED_DIR', root / 'outputs' / 'feed')),
        'cumulative_news': Path(os.getenv('NEWS_AGENT_CUMULATIVE_DIR', root / 'outputs' / 'cumulative_news')),
    }


def load_rss_sources(config_file: Optional[str] = None) -> List[Dict[str, str]]:
    """
    从JSON配置文件加载RSS订阅源
    
    参数:
        config_file (str, optional): 配置文件路径，默认使用标准位置
        
    返回:
        List[Dict[str, str]]: RSS订阅源配置列表
    """
    if config_file is None:
        paths = get_project_paths()
        config_file = paths['config'] / 'rss_feed_urls.json'
    
    config_file = Path(config_file)
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            rss_sources = json.load(f)
            
        if not isinstance(rss_sources, list):
            print(f"❌ 配置格式错误：期望列表，实际为 {type(rss_sources)}")
            return []
            
        return rss_sources
        
    except FileNotFoundError:
        print(f"❌ 配置文件未找到: {config_file}")
        return []
    except json.JSONDecodeError as e:
        print(f"❌ JSON解析失败: {config_file}\n   详细信息: {e}")
        return []
    except PermissionError:
        print(f"❌ 文件访问权限不足: {config_file}")
        return []
    except Exception as e:
        print(f"❌ 加载配置时发生错误: {e}")
        return []


def get_rss_urls_by_category(rss_sources: List[Dict[str, str]], 
                             category: Optional[str] = None) -> List[str]:
    """
    根据分类筛选RSS订阅URL
    
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


def get_all_categories(rss_sources: List[Dict[str, str]]) -> List[str]:
    """
    获取所有分类列表
    
    参数:
        rss_sources (List[Dict[str, str]]): RSS订阅源配置列表
        
    返回:
        List[str]: 排序后的分类列表
    """
    categories = set()
    for source in rss_sources:
        category = source.get('category', '未分类')
        categories.add(category)
    
    return sorted(categories)


def display_rss_sources(rss_sources: List[Dict[str, str]]) -> None:
    """
    格式化显示RSS订阅源信息
    
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


def load_config() -> Dict:
    """
    加载完整的应用配置
    
    返回:
        Dict: 应用配置字典
    """
    paths = get_project_paths()
    
    # 确保必要的目录存在
    for key, path in paths.items():
        if key not in ['root']:
            path.mkdir(parents=True, exist_ok=True)
    
    config = {
        'paths': paths,
        'rss_sources': load_rss_sources(),
        'settings': {
            'hours_limit': int(os.getenv('NEWS_AGENT_HOURS_LIMIT', '24')),
            'max_articles_per_source': int(os.getenv('NEWS_AGENT_MAX_ARTICLES', '100')),
            'ai_filter_enabled': os.getenv('NEWS_AGENT_AI_FILTER', 'true').lower() == 'true',
            'ai_filter_count': int(os.getenv('NEWS_AGENT_AI_FILTER_COUNT', '5')),
            'similarity_threshold': float(os.getenv('NEWS_AGENT_SIMILARITY_THRESHOLD', '0.85')),
            'time_window_hours': int(os.getenv('NEWS_AGENT_TIME_WINDOW', '72')),
        }
    }
    
    return config


if __name__ == "__main__":
    # 测试配置加载
    print("🔧 测试配置加载...")
    print("\n📁 项目路径:")
    paths = get_project_paths()
    for name, path in paths.items():
        print(f"  {name}: {path}")
    
    print("\n📚 RSS订阅源:")
    sources = load_rss_sources()
    if sources:
        display_rss_sources(sources[:3])  # 只显示前3个
        print(f"... 还有 {len(sources) - 3} 个订阅源")
        
        print("\n📂 分类统计:")
        categories = get_all_categories(sources)
        for category in categories:
            count = len([s for s in sources if s.get('category') == category])
            print(f"  {category}: {count} 个")
    else:
        print("  未加载到订阅源")
    
    print("\n⚙️ 完整配置:")
    config = load_config()
    print(f"  时间限制: {config['settings']['hours_limit']} 小时")
    print(f"  AI筛选: {'启用' if config['settings']['ai_filter_enabled'] else '禁用'}")
