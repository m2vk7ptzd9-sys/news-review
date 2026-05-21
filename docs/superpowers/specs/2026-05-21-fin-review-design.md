# FinReview — 每日投资信息聚合系统

## 概述

个人投资信息聚合工具，每天自动从全互联网收集财经文章，用 LLM 进行摘要、分类和重要性排序，通过 CLI 和 Web 面板呈现。

## 目标用户

个人投资者，关注 A股/港股/美股、宏观经济、基金、加密货币等综合投资信息。

## 技术栈

- 语言：Python 3.11+
- Web 框架：FastAPI + Jinja2 模板
- 存储：SQLite
- 采集：feedparser + requests/BeautifulSoup + playwright
- AI 处理：Claude API
- CLI：rich 库构建终端 UI

## 架构

```
采集器 (Collector) → 处理器 (Processor) → 存储 (SQLite) → 展示 (CLI + Web)
```

三个模块相互独立，通过数据库和消息解耦。

## 采集器

### 数据源

| 渠道 | 方式 | 频率 | 示例 |
|------|------|------|------|
| RSS 源 | feedparser | 每 2 小时 | 财联社、华尔街见闻、Reuters |
| 静态爬虫 | requests + BS4 | 每 4 小时 | 东方财富、新浪财经新闻列表 |
| 动态页面 | playwright | 每天 1-2 次 | 雪球热帖、微博话题 |
| 官方渠道 | RSS/HTTP | 触发式 | 央行、证监会发布 |

### 去重策略

- URL 指纹去重（主键级别）
- 标题相似度去重（不同平台转载同一新闻）
- 已入库文章跳过

## 处理器

每篇新文章依次经过：

1. **粗过滤** — 关键词黑名单，排除娱乐/体育/非投资科技等内容；标题不含任何投资关键词（如股市/基金/利率等）且来源为娱乐类站点则直接丢弃
2. **LLM 批处理** — 每 5-10 篇合为一批调用 Claude API，减少请求次数。API 返回每篇的结构化 JSON。配有速率限制（每分钟最多 3 批）避免触发 API 限流
3. **入库** — 写入 SQLite

### LLM 输出格式

```json
{
  "summary": "央行宣布降准0.5个百分点...",
  "category": "货币政策",
  "tags": ["降准", "流动性", "利好"],
  "importance": 8,
  "reason": "直接影响A股资金面"
}
```

### 分类体系

- `#market` 市场走势 — 大盘、指数、资金面
- `#policy` 政策解读 — 货币政策、监管、行业政策
- `#stock` 个股分析 — 财报、公告、研报
- `#macro` 宏观经济 — GDP、CPI、PMI、就业
- `#fund` 基金/ETF — 基金动态、持仓变化
- `#crypto` 加密资产 — BTC/ETH 等
- `#industry` 行业动态 — 新能源、AI、消费等

### 重要性评分

- 9-10：重大政策、黑天鹅、核心资产财报
- 7-8：重要政策信号、主要指数异动
- 5-6：行业层面变化
- 3-4：一般资讯
- 1-2：噪音

## 存储

SQLite 单文件数据库，主要表 `articles`：

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增主键 |
| title | TEXT | 标题 |
| url | TEXT UNIQUE | 原文链接（可回溯来源） |
| source | TEXT | 来源名称 |
| content_text | TEXT | 抓取正文 |
| summary | TEXT | LLM 摘要 |
| category | TEXT | 分类 |
| tags | TEXT | JSON 数组 |
| importance | INTEGER | 1-10 |
| reason | TEXT | 评分理由 |
| published_at | DATETIME | 原文发布时间 |
| collected_at | DATETIME | 采集时间 |
| is_read | BOOLEAN | 是否已读 |

## 展示

### CLI — `fin-review` 命令

- `fin-review today` — 查看今日简报，按重要性从高到低排列
- `fin-review top` — 今日高重要性精选
- `fin-review history --date 2026-05-20` — 查看某天
- `fin-review search --keyword "降准"` — 搜索
- 每条条目显示：标题、来源、摘要、分类标签、重要性分数、原文链接

### Web 面板

- 首页：今日简报，按重要性排列
- 筛选：按日期、分类、来源、重要性区间
- 详情：点击进入文章详情页
- 每日精选 Top N

## 每日工作流

```
08:00 — 清晨采集（隔夜外盘 + 早间新闻）
        → LLM 处理 → 生成当日简报
09:00 — 用户通过 CLI 或 Web 查看简报
12:00 — 午间增量采集
        → LLM 处理增量文章
18:00 — 盘后采集（A股收盘 + 傍晚新闻）
        → LLM 处理增量文章
```

### 断电兜底

电脑关机时定时器不触发。启动时检查上次采集时间，如果错过 ≥4 小时则补采，一次性处理堆积文章。CLI 启动时自动执行此检查。

## 目录结构

```
fin-review/
├── collector/
│   ├── __init__.py
│   ├── sources/
│   │   ├── __init__.py
│   │   ├── base.py          # 采集器基类
│   │   ├── rss.py           # RSS 源适配器
│   │   ├── scraper.py       # 静态爬虫适配器
│   │   └── dynamic.py       # 动态页面适配器
│   ├── dedup.py             # 去重逻辑
│   └── scheduler.py         # 定时调度
├── processor/
│   ├── __init__.py
│   ├── summarizer.py        # LLM 摘要
│   ├── classifier.py        # 分类打标
│   └── scorer.py            # 重要性评分
├── storage/
│   ├── __init__.py
│   ├── models.py            # ORM 模型
│   └── db.py                # 数据库操作
├── web/
│   ├── __init__.py
│   ├── app.py               # FastAPI 应用
│   ├── templates/           # Jinja2 模板
│   └── static/              # CSS/JS
├── cli/
│   ├── __init__.py
│   └── main.py              # CLI 入口
├── config/
│   ├── __init__.py
│   └── settings.py          # 配置
├── main.py                  # 入口
└── requirements.txt
```
