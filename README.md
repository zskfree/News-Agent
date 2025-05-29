# News Agent 📰

一个自动化的新闻聚合和RSS订阅源生成器，基于GitHub Actions自动运行，支持多分类新闻汇总。

## 🚀 特性

- ✅ **自动化新闻聚合** - 从多个RSS源收集新闻
- 🔄 **智能去重** - 基于哈希值避免重复文章
- 📡 **RSS Feed生成** - 自动生成标准RSS订阅源
- 🌐 **GitHub Pages托管** - 免费的RSS订阅服务
- ⏰ **定时更新** - 每日自动更新新闻内容
- 🏷️ **分类管理** - 支持AI、科技、财经等多个分类

## 📊 当前订阅源

| 分类 | RSS订阅地址 | 状态 |
|------|------------|------|
| 🤖 AI人工智能 | `https://zskksz.asia/News-Agent/feed/aifreenewsagent.xml` | ✅ |
| 💻 科技Technology | `https://zskksz.asia/News-Agent/feed/technologyfreenewsagent.xml` | ✅ |
| 💰 财经Finance | `https://zskksz.asia/News-Agent/feed/financefreenewsagent.xml` | ✅ |

## 🛠️ 项目结构

```
News-Agent/
├── 📁 src/                     # 核心模块
│   ├── rss_read.py            # RSS读取和新闻聚合
│   └── load_rss_url.py        # RSS源配置加载
├── 📁 RSS feed URL/           # RSS源配置
│   └── rss_feed_url.json      # 订阅源列表
├── 📁 feed/                   # 生成的RSS文件
├── 📁 cumulative_news/        # 累积新闻文档
├── 生成累积新闻.py              # 新闻聚合脚本
├── 生成累积RSS.py              # RSS生成脚本
├── daily_update.py            # 每日更新脚本
└── requirements.txt           # 依赖包
```

## 🔧 本地使用

### 安装依赖
```bash
pip install -r requirements.txt
```

### 手动更新
```bash
# 更新累积新闻
python 生成累积新闻.py

# 生成RSS Feed
python 生成累积RSS.py

# 或者一键执行
python daily_update.py
```

## 📝 配置RSS源

编辑 [`RSS feed URL/rss_feed_url.json`](RSS%20feed%20URL/rss_feed_url.json)：

```json
[
    {
        "name": "订阅源名称",
        "category": "分类名",
        "language": "zh/en",
        "rss": "https://example.com/rss"
    }
]
```

## 🤖 自动化部署

项目使用GitHub Actions实现自动化：

1. **Fork此仓库**
2. **启用GitHub Pages** (Settings → Pages → Source: GitHub Actions)
3. **配置完成** - 系统将每日自动更新

### GitHub Actions工作流
- ⏰ 每日UTC 00:00自动运行
- 🔄 自动更新新闻和RSS
- 📤 自动部署到GitHub Pages

## 📂 输出文件

- **RSS订阅源**: `feed/*.xml`
- **累积新闻**: `cumulative_news/*_cumulative.md`
- **汇总报告**: `cumulative_news/cumulative_summary_*.md`

## 🔗 快速订阅

复制任意RSS地址到您的RSS阅读器：
- **FeedReader**: 支持
- **Feedly**: 支持
- **RSS Reader**: 支持
- **其他标准RSS阅读器**: 支持

## 📊 项目统计

- 📰 **支持新闻源**: 10+ 个高质量RSS源
- 🏷️ **分类数量**: 3个主要分类 (AI/科技/财经)
- 🔄 **更新频率**: 每日自动更新
- 📱 **兼容性**: 支持所有标准RSS阅读器

## 🤝 贡献

欢迎提交Issue和Pull Request：

1. Fork项目
2. 创建特性分支
3. 提交更改
4. 发起Pull Request

## 📄 许可证

MIT License - 详见 LICENSE 文件

---

**⭐ 如果这个项目对您有帮助，请给个Star支持！**

🌐 **在线访问**: [https://zskksz.asia/News-Agent](https://zskksz.asia/News-Agent)