#!/usr/bin/env python3
"""
Telegram 推送器
读取分类好的数据，生成格式化消息，推送到 Telegram
"""

import argparse
import json
import os
import sys
import re
from datetime import datetime

import requests
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")


# ========== 消息格式化 ==========

EMOJI_RANK = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]


def fmt_stars(n: int) -> str:
    if n >= 1000:
        return f"{n/1000:.1f}k".replace(".0k", "k")
    return str(n)


def build_daily_message(categories: list[dict], summary: str = "") -> str:
    """构建每日榜单消息"""
    lines = []

    lines.append("📊 GitHub Trending · 今日分类排行")
    lines.append("━" * 26)

    for cat in categories:
        cat_name = cat.get("name", "其他")
        repos = cat.get("repos", [])

        lines.append(f"\n🤖 {cat_name}")
        lines.append("━" * 20)

        for r in repos[:10]:  # 每类最多10个
            rank = r.get("rank_in_category", 0)
            emoji = EMOJI_RANK[rank - 1] if rank <= len(EMOJI_RANK) else f"{rank}️⃣"
            nickname = r.get("nickname", r.get("full_name", ""))
            full_name = r.get("full_name", "")
            desc = r.get("description", "")
            stars = r.get("stars", 0)
            url = r.get("url", "")

            lines.append(f"{emoji} {nickname}")
            if desc:
                lines.append(f"   💬 {desc}")
            lines.append(f"   ⭐ {fmt_stars(stars)} | {full_name}")
            lines.append(f"   🔗 {url}")
            lines.append("")

        if len(repos) > 10:
            lines.append(f"   ... 还有 {len(repos) - 10} 个")

    if summary:
        lines.append("━" * 26)
        lines.append(f"📌 {summary}")

    lines.append("━" * 26)
    lines.append(f"🌐 完整榜单：https://github.com/trending")
    lines.append(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M')} · Bot 自动推送")

    return "\n".join(lines)


def build_weekly_message(categories: list[dict], summary: str = "") -> str:
    """构建周榜消息"""
    lines = []

    lines.append("📊 GitHub Trending · 本周周榜")
    lines.append("━" * 26)

    # 找出所有仓库按 stars 排序，取前 20 作为周榜
    all_repos = []
    for cat in categories:
        for r in cat.get("repos", []):
            r["_category"] = cat.get("name", "其他")
            all_repos.append(r)

    all_repos.sort(key=lambda x: x.get("stars", 0), reverse=True)

    lines.append(f"\n🏆 本周 TOP 20 热榜")
    lines.append("━" * 20)

    for i, r in enumerate(all_repos[:20], 1):
        emoji = EMOJI_RANK[i - 1] if i <= len(EMOJI_RANK) else f"{i}️⃣"
        nickname = r.get("nickname", r.get("full_name", ""))
        full_name = r.get("full_name", "")
        desc = r.get("description", "")
        stars = r.get("stars", 0)
        cat = r.get("_category", "")
        url = r.get("url", "")

        lines.append(f"{emoji} {nickname} [{cat}]")
        if desc:
            lines.append(f"   💬 {desc}")
        lines.append(f"   ⭐ {fmt_stars(stars)} | {full_name}")
        lines.append("")

    if summary:
        lines.append("━" * 26)
        lines.append(f"📌 {summary}")

    lines.append("━" * 26)
    lines.append(f"🌐 完整榜单：https://github.com/trending?since=weekly")
    lines.append(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M')} · Bot 自动推送")

    return "\n".join(lines)


# ========== 发送 ==========

def send_telegram(text: str) -> bool:
    """通过 Telegram Bot API 发送消息"""
    if not TELEGRAM_BOT_TOKEN:
        print("[推送] ❌ 未配置 TELEGRAM_BOT_TOKEN，请检查 .env")
        return False
    if not TELEGRAM_CHAT_ID:
        print("[推送] ❌ 未配置 TELEGRAM_CHAT_ID，请检查 .env")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "MarkdownV2",
        "disable_web_page_preview": False,
    }

    # MarkdownV2 对特殊字符需要转义，先尝试不用 parse_mode
    # 实际上我们消息里用了 emoji + Markdown，改用 HTML 模式
    payload.pop("parse_mode", None)

    try:
        resp = requests.post(url, json=payload, timeout=15)
        resp.raise_for_status()
        result = resp.json()
        if result.get("ok"):
            print(f"[推送] ✅ 消息发送成功 (chat_id={TELEGRAM_CHAT_ID})")
            return True
        else:
            print(f"[推送] ❌ 发送失败: {result}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"[推送] ❌ 请求失败: {e}")
        return False


# ========== 主程序 ==========

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Telegram 推送 GitHub Trending")
    parser.add_argument("--input", "-i", required=True,
                        help="classify.py 输出的 JSON 文件路径")
    parser.add_argument("--type", "-t", default="daily",
                        choices=["daily", "weekly"],
                        help="daily(日报) / weekly(周报)")
    args = parser.parse_args()

    with open(args.input, encoding="utf-8") as f:
        data = json.load(f)

    categories = data.get("categories", [])
    summary = data.get("summary", "")

    if args.type == "weekly":
        text = build_weekly_message(categories, summary)
    else:
        text = build_daily_message(categories, summary)

    print(f"[推送] 消息长度: {len(text)} 字符")
    send_telegram(text)
