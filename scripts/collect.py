"""
数据采集脚本

采集前一自然日的小红书 AI 工具相关帖子。
支持多数据源：千瓜 API（主力）、RSS 聚合（补充）、轻量网页抓取（备选）。

使用方式：
    python scripts/collect.py                   # 采集昨日数据
    python scripts/collect.py --date 2026-03-22 # 采集指定日期

环境变量：
    DATA_SOURCE_API_KEY  - 千瓜/新榜 API Key（可选）
"""

import json
import os
import sys
import hashlib
from datetime import datetime, timedelta
from pathlib import Path

# 项目根目录
ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

sys.path.insert(0, str(ROOT / "scripts"))
from config import KEYWORDS_MUST, BLACKLIST_KEYWORDS


def get_target_date():
    """获取目标日期（默认昨天）"""
    if len(sys.argv) > 1 and sys.argv[1] == "--date" and len(sys.argv) > 2:
        return sys.argv[2]
    yesterday = datetime.now() - timedelta(days=1)
    return yesterday.strftime("%Y-%m-%d")


def generate_note_id(title, author):
    """根据标题和作者生成稳定的去重 ID"""
    raw = f"{title}_{author}"
    return "note_" + hashlib.md5(raw.encode()).hexdigest()[:12]


# ============================================================
# 数据源 1：千瓜/新榜 API（推荐，需付费）
# ============================================================
def collect_from_qiangua(target_date):
    """
    通过千瓜数据 API 采集小红书帖子。
    
    接入步骤：
    1. 注册千瓜数据 https://www.qian-gua.com 或新榜 https://www.newrank.cn
    2. 购买 API 套餐（基础版约 300 元/月）
    3. 获取 API Key，设为环境变量 DATA_SOURCE_API_KEY
    
    API 示例（千瓜）：
    POST https://api.qian-gua.com/open/v1/note/search
    Headers: { "Authorization": "Bearer YOUR_API_KEY" }
    Body: { "keyword": "AI工具", "sort": "time", "date_range": "2026-03-22,2026-03-22" }
    """
    api_key = os.environ.get("DATA_SOURCE_API_KEY")
    if not api_key:
        print("[千瓜] 未配置 DATA_SOURCE_API_KEY，跳过")
        return []

    # TODO: 接入真实 API 后取消注释
    # import requests
    # results = []
    # for keyword in KEYWORDS_MUST[:3]:  # 取前3个核心关键词搜索
    #     resp = requests.post(
    #         "https://api.qian-gua.com/open/v1/note/search",
    #         headers={"Authorization": f"Bearer {api_key}"},
    #         json={
    #             "keyword": keyword,
    #             "sort": "time",
    #             "date_range": f"{target_date},{target_date}",
    #             "page": 1,
    #             "page_size": 50
    #         },
    #         timeout=30
    #     )
    #     data = resp.json()
    #     for note in data.get("data", {}).get("list", []):
    #         results.append({
    #             "id": note["note_id"],
    #             "title": note["title"],
    #             "desc": note["content"],
    #             "author": note["author_name"],
    #             "publish_date": target_date,
    #             "liked_count": note.get("like_count", 0),
    #             "collected_count": note.get("collect_count", 0),
    #             "comment_count": note.get("comment_count", 0),
    #             "note_url": f"https://www.xiaohongshu.com/explore/{note['note_id']}",
    #             "cover_image": note.get("cover", ""),
    #         })
    # return results

    print("[千瓜] API 采集逻辑待接入，返回空列表")
    return []


# ============================================================
# 数据源 2：RSS / 资讯聚合
# ============================================================
def collect_from_rss(target_date):
    """
    从 RSS 源聚合 AI 工具相关内容。
    
    推荐 RSS 源：
    - 少数派 AI 标签: https://sspai.com/feed
    - 36Kr AI 频道: https://36kr.com/feed （需过滤）
    - Product Hunt: https://www.producthunt.com/feed
    - AI 工具集: https://ai-bot.cn/feed
    """
    # TODO: 实现 RSS 解析
    # import feedparser
    # feed = feedparser.parse("https://ai-bot.cn/feed")
    # results = []
    # for entry in feed.entries:
    #     pub_date = entry.get("published_parsed")
    #     if pub_date:
    #         entry_date = datetime(*pub_date[:3]).strftime("%Y-%m-%d")
    #         if entry_date == target_date:
    #             results.append({...})
    # return results

    print("[RSS] RSS 采集逻辑待接入，返回空列表")
    return []


# ============================================================
# 数据源 3：小红书轻量网页抓取（备选，注意合规）
# ============================================================
def collect_from_xiaohongshu_web(target_date):
    """
    轻量抓取小红书搜索结果页。
    
    ⚠️ 合规提醒：
    - 请求频率控制在 5 秒/次以上
    - 仅抓取公开搜索结果的标题和摘要
    - 不登录、不获取私密内容
    - 遵守 robots.txt
    
    技术路径：
    - 使用 Playwright/Puppeteer 模拟浏览器
    - 小红书 Web 搜索: https://www.xiaohongshu.com/search_result?keyword=AI工具
    - 需处理 X-s/X-t 签名（逆向 JS）或直接用无头浏览器渲染
    """
    # TODO: 实现网页抓取（需安装 playwright）
    print("[小红书] 网页抓取逻辑待接入，返回空列表")
    return []


# ============================================================
# 主函数：聚合所有数据源
# ============================================================
def keyword_filter(notes):
    """关键词过滤：必须包含核心词，排除黑名单"""
    filtered = []
    for note in notes:
        text = note.get("title", "") + note.get("desc", "")
        # 必须命中至少一个核心关键词
        if not any(kw in text for kw in KEYWORDS_MUST):
            continue
        # 排除黑名单
        if any(kw in text for kw in BLACKLIST_KEYWORDS):
            continue
        filtered.append(note)
    return filtered


def dedup_notes(notes):
    """去重：按 ID 去重"""
    seen = set()
    unique = []
    for note in notes:
        nid = note.get("id", generate_note_id(note.get("title", ""), note.get("author", "")))
        note["id"] = nid
        if nid not in seen:
            seen.add(nid)
            unique.append(note)
    return unique


def main():
    target_date = get_target_date()
    output_file = DATA_DIR / f"{target_date}.json"

    print(f"=== AI 工具日报 · 数据采集 ===")
    print(f"目标日期: {target_date}")
    print(f"输出文件: {output_file}")
    print()

    # 从各数据源采集
    all_notes = []

    notes_qg = collect_from_qiangua(target_date)
    print(f"  千瓜 API: {len(notes_qg)} 条")
    all_notes.extend(notes_qg)

    notes_rss = collect_from_rss(target_date)
    print(f"  RSS 聚合: {len(notes_rss)} 条")
    all_notes.extend(notes_rss)

    notes_xhs = collect_from_xiaohongshu_web(target_date)
    print(f"  小红书抓取: {len(notes_xhs)} 条")
    all_notes.extend(notes_xhs)

    print(f"\n原始总量: {len(all_notes)} 条")

    # 过滤 & 去重
    all_notes = keyword_filter(all_notes)
    print(f"关键词过滤后: {len(all_notes)} 条")

    all_notes = dedup_notes(all_notes)
    print(f"去重后: {len(all_notes)} 条")

    # 保存原始数据（供 process.py 使用）
    raw_file = DATA_DIR / f"{target_date}.raw.json"
    with open(raw_file, "w", encoding="utf-8") as f:
        json.dump(all_notes, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 原始数据已保存: {raw_file}")

    if len(all_notes) == 0:
        print("⚠️  未采集到数据。请检查数据源配置。")
        print("    提示：首次使用请先配置至少一个数据源（千瓜 API / RSS / 手动录入）")
        print("    你也可以手动在 data/ 目录中创建 JSON 数据文件进行测试。")


if __name__ == "__main__":
    main()
