#!/usr/bin/env python3
"""
主运行脚本
一键完成：爬取 → AI分类 → 推送到 Telegram

用法:
  python run.py                          # 每日日报
  python run.py --type weekly             # 周报
  python run.py --type daily  --language Python  # 只爬 Python
"""

import argparse
import os
import sys
import subprocess
import json
from datetime import datetime

# ========== 路径配置 ==========
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

TODAY = datetime.now().strftime("%Y-%m-%d")


def run_cmd(cmd: list[str], desc: str) -> subprocess.CompletedProcess:
    """执行命令并打印结果"""
    print(f"\n>>> {desc}")
    print(f">>> {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=BASE_DIR)
    if result.returncode != 0:
        print(f"❌ {desc} 失败，退出码: {result.returncode}")
        sys.exit(1)
    print(f"✅ {desc} 完成")
    return result


def main():
    parser = argparse.ArgumentParser(description="GitHub Trending 自动推送")
    parser.add_argument("--type", "-t", default="daily",
                        choices=["daily", "weekly"],
                        help="daily=日报 / weekly=周报")
    parser.add_argument("--language", "-l", default=None,
                        help="只抓特定语言，如 Python / JavaScript")
    args = parser.parse_args()

    since = "weekly" if args.type == "weekly" else "daily"
    lang_flag = ["--language", args.language] if args.language else []

    # 输出文件
    scrape_file = os.path.join(DATA_DIR, f"trending_{since}_{TODAY}.json")
    classify_file = os.path.join(DATA_DIR, f"classified_{since}_{TODAY}.json")

    # Step 1: 爬取
    print(f"\n{'='*40}")
    print(f"Step 1: 爬取 GitHub Trending ({since})")
    print(f"{'='*40}")

    scrape_cmd = [
        sys.executable, "scrape.py",
        "--since", since,
        "--output", scrape_file,
    ] + lang_flag

    run_cmd(scrape_cmd, "爬取 GitHub Trending")

    # Step 2: AI 分类
    print(f"\n{'='*40}")
    print(f"Step 2: AI 分类")
    print(f"{'='*40}")

    classify_cmd = [
        sys.executable, "classify.py",
        "--input", scrape_file,
        "--output", classify_file,
    ]

    run_cmd(classify_cmd, "AI 分类")

    # Step 3: 推送到 Telegram
    print(f"\n{'='*40}")
    print(f"Step 3: 推送到 Telegram")
    print(f"{'='*40}")

    send_cmd = [
        sys.executable, "send_telegram.py",
        "--input", classify_file,
        "--type", args.type,
    ]

    run_cmd(send_cmd, "Telegram 推送")

    print(f"\n{'='*40}")
    print(f"🎉 完成！")
    print(f"{'='*40}")
    print(f"数据文件: {classify_file}")


if __name__ == "__main__":
    main()
