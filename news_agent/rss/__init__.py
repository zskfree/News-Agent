"""
RSS处理模块

提供RSS订阅源的读取、解析和内容生成功能
"""

from .reader import (
    read_rss_feed,
    get_recent_articles_summary,
    generate_news_by_categories,
    generate_all_categories_news,
    get_all_historical_articles,
    generate_historical_news_by_categories
)

__all__ = [
    'read_rss_feed',
    'get_recent_articles_summary',
    'generate_news_by_categories',
    'generate_all_categories_news',
    'get_all_historical_articles',
    'generate_historical_news_by_categories',
]
