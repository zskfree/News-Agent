"""
新闻文章整合模块

该模块提供读取指定分类的Markdown新闻文章的功能。
"""

import os
from datetime import datetime
from typing import List, Optional

def get_today_news_content(news_dir: str = "news", 
                          categories_filter: List[str] = None) -> str:
    """
    读取今日指定分类的Markdown文档内容
    
    参数:
        news_dir (str): 新闻目录，默认为"news"
        categories_filter (List[str]): 分类过滤器，指定要读取的分类
        
    返回:
        str: 所有指定分类文档的完整内容
    """
    # 获取今日日期
    date = datetime.now().strftime('%Y%m%d')
    date_dir = os.path.join(news_dir, date)
    
    if not os.path.exists(date_dir):
        print(f"目录不存在: {date_dir}")
        return ""
    
    all_content = []
    
    # 遍历目录中的Markdown文件
    for filename in os.listdir(date_dir):
        if filename.endswith('.md') and not filename.startswith('summary_'):
            # 提取分类名（文件名格式：分类名_日期.md）
            category = filename.replace(f'_{date}.md', '').replace('_', ' ')
            
            # 如果指定了分类过滤器，检查是否在过滤列表中
            if categories_filter and category not in categories_filter:
                continue
            
            file_path = os.path.join(date_dir, filename)
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    all_content.append(content)
                    print(f"✅ 读取文档: {category}")
            except Exception as e:
                print(f"❌ 读取文件失败 {file_path}: {e}")
                continue
    
    if not all_content:
        return "没有找到指定分类的文档。"
    
    # 用分隔符连接所有内容
    return "\n\n".join(all_content)

def generate_selection_prompt(news_content: str, max_articles: int = 10) -> str:
    """
    生成文章筛选提示词，要求AI返回相同格式的Markdown内容
    
    参数:
        news_content (str): 原始新闻内容
        max_articles (int): 最大筛选文章数
        
    返回:
        str: 完整的筛选提示词
    """
    
    prompt = f"""
原始内容：
```markdown
{news_content}
```
请从以上新闻内容中筛选出最多 {max_articles} 篇最优质、最有价值的文章。

筛选标准：
1. 技术创新性和重要性
2. 行业影响力和实用价值
3. 信息质量和可靠性
4. 时效性和关注度

请保持原有的Markdown格式，包括：
- 相同的标题层级 (##, ###)
- 相同的链接格式 [标题](链接)
- 相同的发布时间格式
- 相同的分类结构

只返回筛选后的文章内容，不要添加任何说明或总结，不需要添加额外的文本，禁止添加代码块或其他格式化元素。
"""

    return prompt

# 示例用法
if __name__ == "__main__":
    from load_rss_url import get_all_categories, load_rss_sources
    # RSS订阅源配置文件路径
    RSS_CONFIG_FILE = r'RSS feed URL\rss_feed_url.json'
    
    # 加载RSS订阅源配置
    sources = load_rss_sources(RSS_CONFIG_FILE)
    # 获取所有分类
    categories = get_all_categories(sources)

    # 读取今日新闻
    content = get_today_news_content(categories_filter=categories[:1])

    # 生成筛选提示词
    prompt = generate_selection_prompt(content, max_articles=30)
    
    print("提示词长度:", len(prompt))
    print("\n提示词预览:")
    print(prompt[:1000000] + "..." if len(prompt) > 300 else prompt)
