#!/usr/bin/env python3
"""
GitHub Trending 爬虫
抓取 GitHub 今日 / 本周 / 本月 热门仓库
"""

import argparse
import json
import sys
import time
from datetime import datetime
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup


def parse_stars(star_str: str) -> int:
    """解析 stars 数字字符串，如 '12.7k' -> 12700"""
    s = star_str.strip().lower()
    if s.endswith('k'):
        return int(float(s[:-1]) * 1000)
    elif s.endswith('m'):
        return int(float(s[:-1]) * 1000000)
    return int(s.replace(',', ''))


def scrape_github_trending(language=None, spoken_lang=None, since="daily") -> list[dict]:
    """
    抓取 GitHub Trending 页面

    Args:
        language: 编程语言，如 'Python'，None 表示不限
        spoken_lang: 口语语言，如 'Any'
        since: 时间范围 'daily' | 'weekly' | 'monthly'

    Returns:
        list[dict] - 每个仓库的信息
    """
    base_url = "https://github.com/trending"
    params = {}

    if language and language != "Any":
        base_url += "/" + quote(language.strip().lower(), safe="")
    if spoken_lang and spoken_lang != "Any":
        params["spoken_language_code"] = spoken_lang

    if since != "daily":
        params["since"] = since

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }

    print(f"[爬虫] 正在抓取 GitHub Trending ({since})...")
    print(f"[爬虫] URL: {base_url}，参数: {params}")

    response = requests.get(base_url, params=params, headers=headers, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    articles = soup.find_all("article", class_="Box-row")

    repos = []
    for article in articles:
        try:
            # 仓库名：owner / repo
            full_name_tag = article.find("h2")
            if not full_name_tag:
                continue
            full_name = full_name_tag.get_text(strip=True)
            if "/" not in full_name:
                continue

            owner, repo_name = full_name.split("/", 1)

            # 描述
            desc_tag = article.find("p")
            description = desc_tag.get_text(strip=True) if desc_tag else ""

            # 英文描述（用 data-original-category 里的原始语言）
            # 页面语言跟随浏览器，这里直接用当前抓到的 description

            # 数字信息
            star_link = article.find("a", href=lambda h: h and "stargazers" in h)
            fork_link = article.find("a", href=lambda h: h and "forks" in h)

            star_text = star_link.get_text(strip=True).replace(",", "") if star_link else "0"
            fork_text = fork_link.get_text(strip=True).replace(",", "") if fork_link else "0"

            stars = parse_stars(star_text)
            forks = parse_stars(fork_text)

            # 今日/周/月 新增 stars（页面显示的数值）
            # Trending 页面不直接显示"新增数"，只能取当前总星数

            # 语言
            lang_tag = article.find("span", itemprop="programmingLanguage")
            lang = lang_tag.get_text(strip=True) if lang_tag else "Unknown"

            repo_url = f"https://github.com/{full_name}"

            repos.append({
                "owner": owner,
                "name": repo_name,
                "full_name": full_name,
                "description": description,
                "stars": stars,
                "forks": forks,
                "language": lang,
                "url": repo_url,
                "rank": len(repos) + 1,
            })
        except Exception as e:
            print(f"[警告] 解析仓库失败: {e}")
            continue

    print(f"[爬虫] 成功抓取 {len(repos)} 个仓库")
    return repos


def save_repos(repos: list[dict], filepath: str):
    """保存到 JSON 文件"""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump({
            "fetched_at": datetime.now().isoformat(),
            "total": len(repos),
            "repos": repos
        }, f, ensure_ascii=False, indent=2)
    print(f"[爬虫] 数据已保存到 {filepath}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="爬取 GitHub Trending")
    parser.add_argument("--since", "-s", default="daily",
                        choices=["daily", "weekly", "monthly"],
                        help="时间范围: daily(今日) / weekly(本周) / monthly(本月)")
    parser.add_argument("--language", "-l", default=None,
                        help="编程语言，如 Python, JavaScript, TypeScript 等")
    parser.add_argument("--output", "-o", default=None,
                        help="输出 JSON 文件路径")
    args = parser.parse_args()

    repos = scrape_github_trending(
        language=args.language,
        since=args.since,
    )

    if args.output:
        save_repos(repos, args.output)
    else:
        print(json.dumps(repos[:3], ensure_ascii=False, indent=2))
