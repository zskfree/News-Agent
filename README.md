# News Agent 📰

[English](#english) | [中文](#中文)

---

## English

An automated news aggregator and RSS feed generator, powered by GitHub Actions for scheduled execution, supporting multi-category news summaries.

### ✨ Highlights

- 🏗️ **Modular Architecture** - Modernized Python package structure for easy maintenance and expansion.
- ✅ **Automated Aggregation** - Seamless collection from various RSS sources.
- 🔄 **Smart Deduplication** - Efficient content fingerprint-based algorithm to ensure unique entries.
- 🤖 **AI Screening** - Integrated Gemini AI for intelligent high-quality content filtering.
- 📡 **RSS Feed Generation** - W3C-compliant RSS 2.0 standard feeds.
- 🌐 **GitHub Pages Hosting** - Free, stable, and serverless RSS hosting.
- ⏰ **Scheduled Updates** - 3 updates daily (CST 7:00, 12:00, 16:00).
- 🏷️ **Category Management** - Specialized feeds for AI, Technology, Finance, and more.

### 📊 Current Feeds

| Category | RSS Feed URL | Status |
|----------|--------------|--------|
| 🤖 AI-Artificial Intelligence | `https://zskksz.asia/News-Agent/feed/aifreenewsagent.xml` | ✅ |
| 💻 Technology-Frontier | `https://zskksz.asia/News-Agent/feed/technologyfreenewsagent.xml` | ✅ |
| 💰 Finance-Markets | `https://zskksz.asia/News-Agent/feed/financefreenewsagent.xml` | ✅ |

### 🛠️ Project Structure

```
News-Agent/
├── 📁 news_agent/              # Core Python Package
│   ├── config_loader.py        # Unified Config Management
│   ├── 📁 rss/                 # RSS Engine
│   ├── 📁 filters/             # AI Quality Filters
│   ├── 📁 history/             # Publication Tracking
│   └── 📁 utils/               # Algorithms & Utilities
├── 📁 scripts/                 # CLI Entry Scripts
├── 📁 config/                  # Configuration Files
├── 📁 data/                    # Persistent Storage (History/Cache)
├── 📁 outputs/                 # Generated Outputs (Feed/Markdown)
├── index.html                  # Cyber-Luxe Web Portal
└── requirements.txt            # Dependencies
```

### 🚀 Quick Start

#### 1. Installation
```bash
pip install -r requirements.txt
```

#### 2. Basic Usage
```bash
# Fetch all history and deduplicate
python scripts/build_cumulative_news.py

# Generate incremental RSS Feed
python scripts/build_cumulative_feed.py

# Generate Daily Summary (last 24h)
python scripts/build_daily_markdown.py --hours 24
```

### 🤖 Automation

1. **Fork** this repo.
2. **Enable GitHub Pages**: Settings → Pages → Source: GitHub Actions.
3. **Set Secrets (Optional)**: `GEMINI_API_KEY` for AI filtering.
4. **Done** - The system will run and deploy automatically on schedule.

---

## 中文

一个自动化的新闻聚合和RSS订阅源生成器，基于GitHub Actions自动运行，支持多分类新闻汇总。

### ✨ 项目亮点

- 🏗️ **模块化架构** - 全新Python包结构，易于维护和扩展
- ✅ **自动化新闻聚合** - 从多个RSS源自动收集新闻
- 🔄 **智能去重** - 基于内容指纹的高效去重算法
- 🤖 **AI筛选** - 集成Gemini AI智能筛选优质内容
- 📡 **RSS Feed生成** - 符合W3C标准的RSS 2.0订阅源
- 🌐 **GitHub Pages托管** - 免费、稳定的RSS订阅服务
- ⏰ **定时更新** - 每日3次自动更新（北京时间 7:00, 12:00, 16:00）
- 🏷️ **分类管理** - 支持AI、科技、财经等多个分类

### 📊 当前订阅源

| 分类 | RSS订阅地址 | 状态 |
|------|------------|------|
| 🤖 AI-人工智能 | `https://zskksz.asia/News-Agent/feed/aifreenewsagent.xml` | ✅ |
| 💻 Technology-科技 | `https://zskksz.asia/News-Agent/feed/technologyfreenewsagent.xml` | ✅ |
| 💰 Finance-财经 | `https://zskksz.asia/News-Agent/feed/financefreenewsagent.xml` | ✅ |

### 🛠️ 项目结构

```
News-Agent/
├── 📁 news_agent/              # 核心Python包
│   ├── config_loader.py        # 统一配置管理
│   ├── 📁 rss/                 # RSS处理模块
│   ├── 📁 filters/             # 内容筛选
│   ├── 📁 history/             # 历史记录
│   └── 📁 utils/               # 工具函数
├── 📁 scripts/                 # 入口脚本
├── 📁 config/                  # 配置文件
├── 📁 data/                    # 数据存储
├── 📁 outputs/                 # 输出文件
├── index.html                  # 赛博风格门户首页
└── requirements.txt            # Python依赖
```

### 🚀 快速开始

#### 1. 安装依赖
```bash
pip install -r requirements.txt
```

#### 2. 基本使用
```bash
# 生成累积新闻
python scripts/build_cumulative_news.py

# 生成RSS Feed
python scripts/build_cumulative_feed.py

# 生成日报Markdown
python scripts/build_daily_markdown.py --hours 24
```

### 🤖 自动化部署

1. **Fork此仓库**到您的GitHub账号
2. **启用GitHub Pages**: Settings → Pages → Source: GitHub Actions
3. **配置密钥（可选）**: `GEMINI_API_KEY`（用于智能筛选）
4. **完成** - 系统将自动运行并部署

---

## 📄 License

MIT License - See [LICENSE](LICENSE) for details.

**⭐ Support the project with a Star!**

🌐 **Live Demo**: [Free News Agent](https://zskksz.asia/News-Agent)  
📧 **Issues**: [GitHub Issues](https://github.com/zskfree/News-Agent/issues)
