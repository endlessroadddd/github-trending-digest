# 🤖 GitHub Trending Digest

> GitHub 每日/周榜自动爬取 · AI 智能分类 · 推送到 Telegram

每分钟 GitHub 有哪些爆款项目？这个工具帮你自动追踪，自动分类，每天推送到你的 Telegram。

---

## ✨ 功能

- 🕷️ **自动爬取** GitHub Trending 榜单（今日/本周/本月）
- 🤖 **AI 分类** - 用 LLM 自动给仓库起中文昵称 + 归类
- 📱 **Telegram 推送** - 格式化消息，直接发到你的 Telegram
- ⏰ **定时任务** - 每天早上自动跑，无需人工干预
- 📊 **分类排行** - 告别混乱列表，按类别清晰展示

---

## 🗂️ 项目结构

```
github-trending-digest/
├── scrape.py          # 爬虫：抓 GitHub Trending 页面
├── classify.py        # AI 分类器：调用 LLM 自动分类
├── send_telegram.py  # 推送器：发消息到 Telegram
├── run.py            # 主脚本：一键跑完全流程
├── .env.example      # 环境变量模板
├── requirements.txt  # Python 依赖
└── data/             # 缓存数据（gitignore）
    └── trending_*.json
```

---

## 🚀 5 分钟快速上手

### 第一步：安装依赖

需要 **Python 3.10+**，打开终端：

```bash
# 克隆仓库
git clone https://github.com/endlessroadddd/github-trending-digest.git
cd github-trending-digest

# 创建虚拟环境（推荐）
python3 -m venv venv
source venv/bin/activate      # macOS/Linux
# venv\Scripts\activate       # Windows

# 安装依赖
pip install -r requirements.txt
```

### 第二步：配置 .env

复制配置文件：

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入你的配置：

```bash
# ─── AI 分类 ───────────────────────────────
# MiniMax API（推荐，国内可用）
OPENAI_API_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...   # 你的 MiniMax API Key
OPENAI_BASE_URL=https://api.minimax.chat/v1
OPENAI_MODEL=MiniMax-Text-01

# OpenAI API（如果你用 OpenAI）
# OPENAI_API_KEY=sk-xxxxx
# OPENAI_BASE_URL=https://api.openai.com/v1
# OPENAI_MODEL=gpt-4o-mini

# ─── Telegram 推送 ───────────────────────────
TELEGRAM_BOT_TOKEN=123456789:ABCDEFGHIJKLMNabcdefghijk   # 你的 Bot Token
TELEGRAM_CHAT_ID=7036379795                               # 你的 Chat ID
```

> **怎么获取 Telegram Bot Token？**
> 1. 在 Telegram 搜索 `@BotFather`
> 2. 发送 `/newbot`，按提示创建机器人
> 3. 复制 BotFather 给你的 `token`，填入 `TELEGRAM_BOT_TOKEN`
>
> **怎么获取 Chat ID？**
> 1. 在 Telegram 搜索 `@userinfobot`
> 2. 给它发一条消息
> 3. 它会回复你的 `id`，这就是 `TELEGRAM_CHAT_ID`

### 第三步：测试运行

```bash
# 测试日报（今日榜单）
python run.py

# 测试周报（本周榜单）
python run.py --type weekly
```

看到 `🎉 完成！` 就说明成功了，去 Telegram 检查是否收到消息。

---

## ⚙️ 手动运行

```bash
# 完整流程（日报）
python run.py

# 完整流程（周报）
python run.py --type weekly

# 只抓特定语言
python run.py --language Python
python run.py --language JavaScript

# 单独运行某个步骤
python scrape.py --since daily --output data/test.json
python classify.py --input data/test.json --output data/classified.json
python send_telegram.py --input data/classified.json --type daily
```

---

## ⏰ 设置定时任务（每天自动推送）

### macOS / Linux：用 crontab

```bash
# 编辑定时任务
crontab -e

# 每天早上 8 点跑日报
0 8 * * * cd /Users/你/路径/github-trending-digest && /usr/bin/python3 run.py >> logs/cron.log 2>&1

# 每周一早上 8 点跑周报
0 8 * * 1 cd /Users/你/路径/github-trending-digest && /usr/bin/python3 run.py --type weekly >> logs/weekly.log 2>&1
```

### Windows：用任务计划程序

1. 搜索「任务计划程序」→ 创建基本任务
2. 触发器：每天 8:00
3. 操作：启动程序 → 选择 `run.py`
4. 起始位置：填项目文件夹路径

### 或者：用 GitHub Actions（免费云端定时）

项目已内置 `.github/workflows/daily.yml`，Fork 后在 Settings → Secrets 添加：

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`
- `OPENAI_MODEL`

然后 Actions 会自动每天 8:00 运行。

---

## 🔧 常见问题

### 1. 爬虫返回空列表？

GitHub 有反爬机制，多试几次或换个时间段。如果频繁失败，考虑加代理或用 GitHub API。

### 2. AI 分类失败？

- 检查 `OPENAI_API_KEY` 是否正确
- 检查 `OPENAI_BASE_URL` 是否和你的 API 匹配
- 查看终端输出的错误信息

### 3. Telegram 消息发送失败？

- 确认 `TELEGRAM_BOT_TOKEN` 有效
- 确认 `TELEGRAM_CHAT_ID` 正确
- 确认 Bot 被添加到你的频道/群组（如果是群组的话）

### 4. 怎么修改推送时间？

修改 crontab 里的小时数字即可，例如改成 9:30：
```bash
30 9 * * * ...
```

---

## 🎨 自定义

### 修改 AI 分类的 prompt

打开 `classify.py`，找到 `SYSTEM_PROMPT` 变量，修改系统提示词即可改变分类逻辑。

### 修改消息格式

打开 `send_telegram.py`，找到 `build_daily_message` 函数，修改返回的消息格式。

### 添加新语言支持

修改 `scrape.py` 里的 `language` 参数，支持：Python / JavaScript / TypeScript / Rust / Go / Java 等。

---

## 📌 依赖

- Python 3.10+
- requests
- beautifulsoup4
- openai
- python-dotenv

---

## 📄 License

MIT · 随便用，改成你自己的也行 😄
