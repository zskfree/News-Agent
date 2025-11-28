"""
News Agent - RSS新闻聚合与生成系统

一个自动化的新闻聚合系统，支持：
- RSS订阅源管理
- 新闻内容抓取与去重
- AI驱动的内容筛选
- Markdown与RSS Feed生成
"""

__version__ = "2.0.0"
__author__ = "News-Agent Contributors"

from .config_loader import load_config, load_rss_sources, get_project_paths
from .rss.reader import read_rss_feed
from .filters.ai_news_filter import NewsQualityFilter

__all__ = [
    'load_config',
    'load_rss_sources',
    'get_project_paths',
    'read_rss_feed',
    'NewsQualityFilter',
]
