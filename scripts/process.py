"""
数据处理脚本

读取 collect.py 产出的原始数据，通过 LLM 提取结构化信息，生成最终的每日 JSON。

使用方式：
    python scripts/process.py                   # 处理昨日数据
    python scripts/process.py --date 2026-03-22 # 处理指定日期

环境变量：
    OPENAI_API_KEY  - OpenAI API Key（必需）
"""

import json
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"

sys.path.insert(0, str(ROOT / "scripts"))
from config import EXTRACT_MODEL, EXTRACT_TEMPERATURE, EXTRACT_PROMPT, CATEGORIES


def get_target_date():
    if len(sys.argv) > 1 and sys.argv[1] == "--date" and len(sys.argv) > 2:
        return sys.argv[2]
    yesterday = datetime.now() - timedelta(days=1)
    return yesterday.strftime("%Y-%m-%d")


def classify_by_keywords(text):
    """基于关键词的快速分类（作为 LLM 分类的兜底）"""
    for cat, keywords in CATEGORIES.items():
        if any(kw in text for kw in keywords):
            return cat
    return "其他"


def extract_with_llm(note):
    """调用 LLM 提取结构化信息"""
    try:
        from openai import OpenAI
        client = OpenAI()

        prompt = EXTRACT_PROMPT.format(
            title=note.get("title", ""),
            content=note.get("desc", ""),
            author=note.get("author", "")
        )

        response = client.chat.completions.create(
            model=EXTRACT_MODEL,
            temperature=EXTRACT_TEMPERATURE,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )

        result = json.loads(response.choices[0].message.content)
        return result

    except Exception as e:
        print(f"  ⚠️ LLM 提取失败: {e}")
        # 兜底：用关键词分类
        text = note.get("title", "") + note.get("desc", "")
        return {
            "tool_name": note.get("title", "")[:20],
            "tool_type": classify_by_keywords(text),
            "core_feature": "",
            "platform_url": "",
            "is_free": "免费增值",
            "device": "Web",
            "region": "国内",
            "summary": note.get("desc", "")[:80]
        }


def process_note(note, extracted):
    """合并原始数据和 LLM 提取结果，生成最终格式"""
    return {
        "id": note.get("id", ""),
        "tool_name": extracted.get("tool_name", ""),
        "tool_type": extracted.get("tool_type", "其他"),
        "title": note.get("title", ""),
        "summary": extracted.get("summary", ""),
        "core_feature": extracted.get("core_feature", ""),
        "platform_url": extracted.get("platform_url", ""),
        "note_url": note.get("note_url", ""),
        "author": note.get("author", ""),
        "publish_date": note.get("publish_date", ""),
        "liked_count": note.get("liked_count", 0),
        "collected_count": note.get("collected_count", 0),
        "comment_count": note.get("comment_count", 0),
        "is_free": extracted.get("is_free", "免费增值"),
        "device": extracted.get("device", "Web"),
        "region": extracted.get("region", "国内"),
        "cover_image": note.get("cover_image", f"https://picsum.photos/seed/{note.get('id','x')}/400/350")
    }


def main():
    target_date = get_target_date()
    raw_file = DATA_DIR / f"{target_date}.raw.json"
    output_file = DATA_DIR / f"{target_date}.json"

    print(f"=== AI 工具日报 · 数据处理 ===")
    print(f"目标日期: {target_date}")

    # 读取原始数据
    if not raw_file.exists():
        print(f"⚠️  原始数据文件不存在: {raw_file}")
        print("   请先运行 python scripts/collect.py")
        sys.exit(1)

    with open(raw_file, "r", encoding="utf-8") as f:
        raw_notes = json.load(f)

    print(f"读取原始数据: {len(raw_notes)} 条")

    if len(raw_notes) == 0:
        print("⚠️  无数据需要处理")
        sys.exit(0)

    # 检查 API Key
    api_key = os.environ.get("OPENAI_API_KEY")
    use_llm = bool(api_key)
    if not use_llm:
        print("⚠️  未配置 OPENAI_API_KEY，将使用关键词分类（精度较低）")

    # 逐条处理
    results = []
    for i, note in enumerate(raw_notes):
        print(f"  [{i+1}/{len(raw_notes)}] 处理: {note.get('title', '')[:30]}...")

        if use_llm:
            extracted = extract_with_llm(note)
            time.sleep(0.5)  # 避免 rate limit
        else:
            text = note.get("title", "") + note.get("desc", "")
            extracted = {
                "tool_name": note.get("title", "")[:20],
                "tool_type": classify_by_keywords(text),
                "core_feature": "",
                "platform_url": "",
                "is_free": "免费增值",
                "device": "Web",
                "region": "国内",
                "summary": note.get("desc", "")[:80]
            }

        processed = process_note(note, extracted)
        results.append(processed)

    # 按热度排序
    results.sort(key=lambda t: t["liked_count"] + t["collected_count"] * 1.5 + t["comment_count"] * 2, reverse=True)

    # 保存
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 处理完成，共 {len(results)} 条，已保存: {output_file}")

    # 清理 raw 文件（可选）
    # raw_file.unlink()


if __name__ == "__main__":
    main()
