"""
RSS历史记录管理模块

管理已发布文章的历史记录，支持去重和增量更新
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, Optional


class RSSHistoryManager:
    """RSS发布历史管理器"""
    
    def __init__(self, history_file: Optional[str] = None):
        """
        初始化历史管理器
        
        参数:
            history_file (str, optional): 历史文件路径，默认使用data/rss_history.json
        """
        if history_file is None:
            from ..config_loader import get_project_paths
            paths = get_project_paths()
            history_file = paths['data'] / 'rss_history.json'
        
        self.history_file = str(history_file)
        self.history_data = self.load_history()
    
    def load_history(self) -> Dict:
        """
        加载历史记录
        
        返回:
            Dict: 历史数据字典
        """
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"  ⚠️ 加载历史记录失败: {e}")
        
        return {"published_articles": {}, "last_update": {}}
    
    def save_history(self) -> None:
        """保存历史记录到文件"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
            
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"  ⚠️ 保存历史记录失败: {e}")
    
    def is_article_published(self, category: str, fingerprint: str) -> bool:
        """
        检查文章是否已发布
        
        参数:
            category (str): 分类
            fingerprint (str): 文章指纹
            
        返回:
            bool: 是否已发布
        """
        category_articles = self.history_data["published_articles"].get(category, {})
        return fingerprint in category_articles
    
    def add_published_article(self, category: str, fingerprint: str, article_info: Dict) -> None:
        """
        添加已发布的文章记录
        
        参数:
            category (str): 分类
            fingerprint (str): 文章指纹
            article_info (Dict): 文章信息
        """
        if category not in self.history_data["published_articles"]:
            self.history_data["published_articles"][category] = {}
        
        self.history_data["published_articles"][category][fingerprint] = {
            "title": article_info.get("title", ""),
            "link": article_info.get("link", ""),
            "published_date": article_info.get("pub_date", ""),
            "first_seen": datetime.now().isoformat()
        }
    
    def update_last_update_time(self, category: str) -> None:
        """
        更新最后更新时间
        
        参数:
            category (str): 分类
        """
        self.history_data["last_update"][category] = datetime.now().isoformat()
    
    def get_last_update_time(self, category: str) -> Optional[datetime]:
        """
        获取最后更新时间
        
        参数:
            category (str): 分类
            
        返回:
            Optional[datetime]: 最后更新时间，如果不存在则返回None
        """
        last_update_str = self.history_data["last_update"].get(category)
        if last_update_str:
            try:
                return datetime.fromisoformat(last_update_str)
            except Exception as e:
                print(f"  ⚠️ 解析更新时间失败: {e}")
        return None
    
    def cleanup_old_records(self, days: int = 30) -> None:
        """
        清理过旧的记录
        
        参数:
            days (int): 保留天数，默认30天
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        total_removed = 0
        for category in list(self.history_data["published_articles"].keys()):
            articles = self.history_data["published_articles"][category]
            
            # 清理过旧的文章记录
            articles_to_remove = []
            for fingerprint, article_info in articles.items():
                try:
                    first_seen = datetime.fromisoformat(article_info.get("first_seen", ""))
                    if first_seen < cutoff_date:
                        articles_to_remove.append(fingerprint)
                except:
                    # 如果解析失败，保守起见保留记录
                    pass
            
            for fingerprint in articles_to_remove:
                del articles[fingerprint]
            
            removed_count = len(articles_to_remove)
            total_removed += removed_count
            
            if removed_count > 0:
                print(f"  🧹 分类 {category}: 清理了 {removed_count} 条过期记录")
        
        if total_removed > 0:
            print(f"  ✅ 总计清理了 {total_removed} 条过期记录")
            self.save_history()
    
    def get_category_stats(self, category: str) -> Dict:
        """
        获取分类统计信息
        
        参数:
            category (str): 分类
            
        返回:
            Dict: 统计信息
        """
        articles = self.history_data["published_articles"].get(category, {})
        last_update = self.get_last_update_time(category)
        
        return {
            'article_count': len(articles),
            'last_update': last_update.isoformat() if last_update else None,
            'category': category
        }
    
    def get_all_stats(self) -> Dict:
        """
        获取所有分类的统计信息
        
        返回:
            Dict: 所有分类的统计信息
        """
        stats = {}
        total_articles = 0
        
        for category in self.history_data["published_articles"].keys():
            category_stats = self.get_category_stats(category)
            stats[category] = category_stats
            total_articles += category_stats['article_count']
        
        stats['_total'] = {
            'categories': len(stats),
            'total_articles': total_articles
        }
        
        return stats


if __name__ == "__main__":
    # 测试历史管理器
    print("🧪 测试RSS历史管理器...")
    
    manager = RSSHistoryManager()
    
    # 添加测试文章
    test_article = {
        'title': '测试文章',
        'link': 'https://example.com/test',
        'pub_date': '2025-11-28 10:00'
    }
    
    fingerprint = 'test_fingerprint_123'
    category = 'Test'
    
    print(f"\n📝 添加文章到分类 '{category}'...")
    manager.add_published_article(category, fingerprint, test_article)
    manager.update_last_update_time(category)
    manager.save_history()
    
    print(f"✅ 文章是否已发布: {manager.is_article_published(category, fingerprint)}")
    print(f"🕐 最后更新时间: {manager.get_last_update_time(category)}")
    
    print(f"\n📊 统计信息:")
    stats = manager.get_all_stats()
    for cat, info in stats.items():
        if cat != '_total':
            print(f"  {cat}: {info['article_count']} 篇文章")
