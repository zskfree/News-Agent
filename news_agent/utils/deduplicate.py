"""
内容去重工具模块

提供文章去重相关的工具函数
"""

import re
import hashlib
import difflib
from urllib.parse import urlparse
from typing import Tuple


def create_content_fingerprint(title: str, link: str, description: str = "") -> str:
    """
    创建内容指纹，用于精确去重
    
    参数:
        title (str): 文章标题
        link (str): 文章链接
        description (str): 文章描述（可选）
        
    返回:
        str: 内容指纹（SHA256哈希值）
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


def calculate_title_similarity(title1: str, title2: str) -> float:
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


def generate_article_hash(title: str, link: str) -> str:
    """
    生成文章的唯一哈希值（简化版指纹）
    
    参数:
        title (str): 文章标题
        link (str): 文章链接
        
    返回:
        str: 文章的MD5哈希值
    """
    content = f"{title.strip()}{link.strip()}"
    return hashlib.md5(content.encode('utf-8')).hexdigest()


def normalize_url(url: str) -> str:
    """
    标准化URL，移除查询参数和片段
    
    参数:
        url (str): 原始URL
        
    返回:
        str: 标准化后的URL
    """
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}".lower()


def extract_domain(url: str) -> str:
    """
    从URL中提取域名
    
    参数:
        url (str): URL
        
    返回:
        str: 域名
    """
    parsed = urlparse(url)
    return parsed.netloc.lower()


if __name__ == "__main__":
    # 测试去重函数
    print("🧪 测试去重工具...")
    
    title1 = "GPT-5 Released: A Major Breakthrough in AI"
    title2 = "GPT 5 Released A Major Breakthrough in AI"
    link1 = "https://example.com/article/123?utm_source=rss"
    link2 = "https://example.com/article/123"
    
    print(f"\n标题1: {title1}")
    print(f"标题2: {title2}")
    print(f"相似度: {calculate_title_similarity(title1, title2):.2%}")
    
    print(f"\nURL1: {link1}")
    print(f"URL2: {link2}")
    print(f"标准化URL1: {normalize_url(link1)}")
    print(f"标准化URL2: {normalize_url(link2)}")
    
    fp1 = create_content_fingerprint(title1, link1)
    fp2 = create_content_fingerprint(title2, link2)
    print(f"\n指纹1: {fp1[:16]}...")
    print(f"指纹2: {fp2[:16]}...")
    print(f"指纹相同: {fp1 == fp2}")
