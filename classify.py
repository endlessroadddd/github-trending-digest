#!/usr/bin/env python3
"""
AI 分类器
用 LLM API 将 GitHub Trending 仓库按类别分组

支持: MiniMax API / OpenAI Compatible API
需要用户在 .env 中配置:
  OPENAI_API_KEY=your_api_key
  OPENAI_BASE_URL=https://api.minimax.chat/v1  (MiniMax)
  OPENAI_BASE_URL=https://api.openai.com/v1     (OpenAI)
  OPENAI_MODEL=gpt-4o-mini
"""

import argparse
import json
import os
import sys
import re
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

# 加载 .env
load_dotenv()

# ========== 配置 ==========
API_KEY = os.getenv("OPENAI_API_KEY", "")
BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.minimax.chat/v1")
MODEL = os.getenv("OPENAI_MODEL", "MiniMax-Text-01")

# ========== 系统提示词 ==========
SYSTEM_PROMPT = """你是一个专业的开源项目分类助手。

我会给你一批 GitHub Trending 仓库的信息（仓库名、描述、语言），你需要：
1. 为每个仓库起一个**简短中文昵称**（3-8字），让人一看就知道这个项目是干什么的
2. 将所有仓库**分成若干类别**，同类别的仓库归在一起
3. 按**每类内按今日 stars 降序**排列

注意：
- 类别数量要合理（通常 3-6 个），不要分太细也不要太粗
- 每个类别需要一个**简洁的中文名称**（如：AI 编程智能体、RAG与文档、模型加速 等）
- 如果某个仓库描述太短无法判断，根据仓库名推测
- 输出格式必须是可以被 json.loads 解析的 JSON
"""

USER_PROMPT_TEMPLATE = """请将以下 {total} 个 GitHub Trending 仓库分类并起昵称：

{repos_text}

请输出 JSON 格式，结构如下：
{{
  "categories": [
    {{
      "name": "类别名称",
      "repos": [
        {{
          "rank_in_category": 1,
          "full_name": "owner/repo",
          "nickname": "简短中文昵称（3-8字）",
          "description": "一句话描述（原文保留）",
          "stars": 12345,
          "today_stars": "今日新增 stars（如页面有显示）",
          "language": "语言",
          "url": "https://github.com/..."
        }}
      ]
    }}
  ],
  "summary": "一句话总结今日趋势"
}}

**重要**：nickname 必须是中文，简短精准，体现项目核心功能。不要超过8个字。"""


def build_user_prompt(repos: list[dict]) -> str:
    """构建用户提示词"""
    # 取前 20 个仓库（避免 token 超出）
    repos_to_classify = repos[:20]

    repos_text = "\n".join([
        f"{i+1}. [{r['language']}] {r['full_name']} | {r.get('description', 'N/A')}"
        for i, r in enumerate(repos_to_classify)
    ])

    return USER_PROMPT_TEMPLATE.format(
        total=len(repos_to_classify),
        repos_text=repos_text
    )


def classify_repos(repos: list[dict]) -> dict:
    """
    调用 LLM API 对仓库进行分类

    Returns:
        dict - 包含 categories 和 summary
    """
    if not API_KEY:
        print("[分类器] ❌ 未配置 OPENAI_API_KEY，请检查 .env 文件")
        sys.exit(1)

    print(f"[分类器] 使用模型: {MODEL}")
    print(f"[分类器] API Base: {BASE_URL}")

    client = OpenAI(
        api_key=API_KEY,
        base_url=BASE_URL,
    )

    user_prompt = build_user_prompt(repos)

    print("[分类器] 正在调用 LLM 分类...")

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            max_tokens=4096,
        )

        raw = response.choices[0].message.content.strip()

        # 尝试提取 JSON（去掉 markdown 代码块）
        json_match = re.search(r"```(?:json)?\s*([\s\S]+?)```", raw)
        if json_match:
            raw = json_match.group(1)

        result = json.loads(raw)
        print("[分类器] ✅ 分类完成")
        return result

    except json.JSONDecodeError as e:
        print(f"[分类器] ❌ JSON 解析失败: {e}")
        print(f"[分类器] 原始输出:\n{raw[:500]}")
        sys.exit(1)
    except Exception as e:
        print(f"[分类器] ❌ API 调用失败: {e}")
        sys.exit(1)


def save_classified_data(data: dict, filepath: str):
    """保存分类结果"""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[分类器] 分类结果已保存到 {filepath}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI 分类 GitHub Trending 仓库")
    parser.add_argument("--input", "-i", required=True,
                        help="scrape.py 输出的 JSON 文件路径")
    parser.add_argument("--output", "-o", default=None,
                        help="分类结果输出路径（默认 stdout）")
    args = parser.parse_args()

    # 读取爬虫数据
    with open(args.input, encoding="utf-8") as f:
        data = json.load(f)

    repos = data.get("repos", [])
    if not repos:
        print("[分类器] 错误: 仓库列表为空")
        sys.exit(1)

    result = classify_repos(repos)

    if args.output:
        save_classified_data(result, args.output)
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
