# News Agent 📰

一个自动化的新闻聚合和RSS订阅源生成器，基于GitHub Actions自动运行，支持多分类新闻汇总。

## ✨ 项目亮点

- 🏗️ **模块化架构** - 全新Python包结构，易于维护和扩展
- ✅ **自动化新闻聚合** - 从多个RSS源自动收集新闻
- 🔄 **智能去重** - 基于内容指纹的高效去重算法
- 🤖 **AI筛选** - 集成Gemini AI智能筛选优质内容
- 📡 **RSS Feed生成** - 符合W3C标准的RSS 2.0订阅源
- 🌐 **GitHub Pages托管** - 免费、稳定的RSS订阅服务
- ⏰ **定时更新** - 每日3次自动更新（北京时间 7:00, 12:00, 16:00）
- 🏷️ **分类管理** - 支持AI、科技、财经等多个分类

## 📊 当前订阅源

| 分类 | RSS订阅地址 | 状态 |
|------|------------|------|
| 🤖 AI-人工智能 | `https://zskksz.asia/News-Agent/feed/aifreenewsagent.xml` | ✅ |
| 💻 Technology-科技 | `https://zskksz.asia/News-Agent/feed/technologyfreenewsagent.xml` | ✅ |
| 💰 Finance-财经 | `https://zskksz.asia/News-Agent/feed/financefreenewsagent.xml` | ✅ |

## 🛠️ 项目结构

```
News-Agent/
├── 📁 news_agent/              # 核心Python包（重构后）
│   ├── __init__.py
│   ├── config_loader.py        # 统一配置管理
│   ├── 📁 rss/                 # RSS处理模块
│   │   ├── reader.py           # RSS读取与解析
│   │   └── feed_generator.py  # RSS XML生成
│   ├── 📁 filters/             # 内容筛选
│   │   └── ai_news_filter.py  # AI驱动筛选
│   ├── 📁 history/             # 历史记录
│   │   └── rss_history.py     # 发布历史管理
│   └── 📁 utils/               # 工具函数
│       └── deduplicate.py     # 去重算法
├── 📁 scripts/                 # 入口脚本
│   ├── build_cumulative_feed.py   # 生成累积RSS Feed
│   ├── build_cumulative_news.py   # 获取累积新闻
│   └── build_daily_markdown.py    # 生成日报Markdown
├── 📁 config/                  # 配置文件
│   └── rss_feed_urls.json      # RSS订阅源配置
├── 📁 data/                    # 数据存储
│   └── rss_history.json        # 发布历史记录
├── 📁 outputs/                 # 输出文件
│   ├── feed/                   # RSS订阅源
│   └── cumulative_news/        # 累积新闻文档
├── 📁 logs/                    # 日志文件
├── 📁 legacy_scripts/          # 旧版脚本（备份）
├── index.html                  # GitHub Pages首页
└── requirements.txt            # Python依赖
```

### 📦 模块说明

- **news_agent**: 核心业务逻辑包，模块化设计便于维护和测试
  - `config_loader`: 统一的配置加载，支持环境变量
  - `rss/`: RSS订阅源处理（读取、解析、生成）
  - `filters/`: 内容筛选（AI驱动的质量筛选）
  - `history/`: 历史记录管理（去重、增量更新）
  - `utils/`: 通用工具函数（指纹生成、相似度计算）

- **scripts**: CLI入口脚本，调用news_agent包的功能
  - `build_cumulative_feed.py`: 基于累积新闻生成RSS Feed
  - `build_cumulative_news.py`: 获取所有历史新闻并去重
  - `build_daily_markdown.py`: 生成最近24小时的新闻日报

- **config**: 配置文件目录（支持环境变量覆盖）
- **data**: 持久化数据（历史记录、缓存等）
- **outputs**: 生成的输出文件（RSS、Markdown等）
- **logs**: 运行日志

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 基本使用

使用模块化脚本（推荐）：

```bash
# 生成累积新闻（获取所有历史）
python scripts/build_cumulative_news.py

# 生成RSS Feed（增量更新）
python scripts/build_cumulative_feed.py

# 生成日报Markdown（最近24小时）
python scripts/build_daily_markdown.py --hours 24
```

### 3. 高级用法

```bash
# 只处理指定分类
python scripts/build_cumulative_feed.py --category AI

# 自定义文章数量
python scripts/build_cumulative_news.py --max-articles 200

# 禁用AI筛选
python scripts/build_cumulative_feed.py --no-ai-filter

# 清理旧历史记录（30天前）
python scripts/build_cumulative_feed.py --cleanup-days 30

# 查看帮助
python scripts/build_cumulative_feed.py --help
```

### 4. 环境变量配置（可选）

自定义路径和API密钥：

```bash
# Windows PowerShell
$env:NEWS_AGENT_CONFIG_DIR="D:\custom\config"
$env:NEWS_AGENT_DATA_DIR="D:\custom\data"
$env:NEWS_AGENT_OUTPUT_DIR="D:\custom\outputs"
$env:GEMINI_API_KEY="your-api-key"

# Linux/Mac
export NEWS_AGENT_CONFIG_DIR="/custom/config"
export NEWS_AGENT_DATA_DIR="/custom/data"
export NEWS_AGENT_OUTPUT_DIR="/custom/outputs"
export GEMINI_API_KEY="your-api-key"
```

## ⚙️ 配置说明

### RSS订阅源配置

编辑 `config/rss_feed_urls.json` 添加新的RSS源：

```json
[
    {
        "name": "订阅源名称",
        "category": "AI",
        "language": "zh",
        "rss": "https://example.com/rss",
        "website": "https://example.com"
    }
]
```

**字段说明**:

- `name`: 订阅源显示名称
- `category`: 分类（AI/Technology/Finance等）
- `language`: 语言代码（zh/en）
- `rss`: RSS订阅地址
- `website`: 源网站地址（可选）

### 重要路径

| 类型 | 路径 | 说明 |
|------|------|------|
| 📝 配置文件 | `config/rss_feed_urls.json` | RSS订阅源配置 |
| 💾 历史记录 | `data/rss_history.json` | 发布历史（自动生成） |
| 📡 RSS输出 | `outputs/feed/*.xml` | RSS订阅源文件 |
| 📰 新闻输出 | `outputs/cumulative_news/*.md` | 累积新闻文档 |
| 📋 日志文件 | `logs/` | 运行日志 |

## 🤖 自动化部署

### GitHub Actions设置

1. **Fork此仓库**到您的GitHub账号
2. **启用GitHub Pages**: Settings → Pages → Source: GitHub Actions
3. **配置密钥（可选）**: Settings → Secrets → New repository secret
   - `GEMINI_API_KEY`: Gemini AI API密钥（用于智能筛选）
4. **完成** - 系统将自动运行并部署

### 工作流说明

- ⏰ **定时触发**: 每日3次（北京时间 7:00, 12:00, 16:00）
- 🔄 **自动更新**: 获取最新新闻并生成RSS
- ✅ **结构验证**: 检查目录和配置文件完整性
- 📤 **自动部署**: 发布到GitHub Pages
- 📊 **统计报告**: 显示文件数量和大小

### 手动触发

在GitHub仓库页面：

1. 点击 "Actions" 标签
2. 选择 "Daily Update" 工作流
3. 点击 "Run workflow" 按钮

## 📂 输出文件

- **RSS订阅源**: `outputs/feed/*.xml`
- **累积新闻**: `outputs/cumulative_news/*_cumulative.md`
- **汇总报告**: `outputs/cumulative_news/cumulative_summary_*.md`

## 🔗 快速订阅

复制任意RSS地址到您的RSS阅读器：

- **Folo**: 支持
- **FeedReader**: 支持
- **Feedly**: 支持
- **RSS Reader**: 支持
- **其他标准RSS阅读器**: 支持

## 💻 Python API使用

### 导入模块

```python
from news_agent.config_loader import load_config, load_rss_sources
from news_agent.rss import read_rss_feed, generate_all_categories_news
from news_agent.history import RSSHistoryManager
from news_agent.filters import NewsQualityFilter
from news_agent.utils import create_content_fingerprint, calculate_title_similarity
```

### 配置管理

```python
# 加载完整配置
config = load_config()
paths = config['paths']
settings = config['settings']

# 只加载RSS源
sources = load_rss_sources()
```

### RSS处理

```python
# 读取单个RSS源
articles = read_rss_feed('https://example.com/rss')

# 生成所有分类新闻
results = generate_all_categories_news(
    rss_sources=sources,
    hours_limit=24,
    output_dir='outputs/news'
)
```

### 历史管理

```python
manager = RSSHistoryManager()

# 检查文章是否已发布
is_published = manager.is_article_published('AI', fingerprint)

# 添加已发布文章
manager.add_published_article('AI', fingerprint, article_info)
manager.save_history()

# 清理30天前的记录
manager.cleanup_old_records(days=30)
```

### AI筛选

```python
filter_instance = NewsQualityFilter()

# 筛选优质文章
filtered = filter_instance.filter_articles(
    articles=articles,
    category='AI',
    target_count=10
)
```

## 🔍 故障排查

### 找不到配置文件

```bash
# 检查文件是否存在
ls config/rss_feed_urls.json

# 设置环境变量
export NEWS_AGENT_CONFIG_DIR="/path/to/config"
```

### 导入模块失败

```python
# 确保项目根目录在Python路径中
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
```

### AI筛选失败

```bash
# 检查API密钥
echo $GEMINI_API_KEY

# 禁用AI筛选
python scripts/build_cumulative_feed.py --no-ai-filter
```

## 📊 项目统计

- 📰 **支持新闻源**: 15+ 个高质量RSS源
- 🏷️ **分类数量**: 3个主要分类 (AI/科技/财经)
- 🔄 **更新频率**: 每日3次（7:00, 12:00, 16:00 CST）
- 📱 **兼容性**: 支持所有标准RSS阅读器
- 🏗️ **代码质量**: 模块化设计，易于维护和扩展

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

1. Fork本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

**⭐ 如果这个项目对您有帮助，请给个Star支持！**

🌐 **在线访问**: [Free News Agent](https://zskksz.asia/News-Agent)  
📧 **问题反馈**: [GitHub Issues](https://github.com/zskfree/News-Agent/issues)  
💬 **讨论交流**: [GitHub Discussions](https://github.com/zskfree/News-Agent/discussions)
