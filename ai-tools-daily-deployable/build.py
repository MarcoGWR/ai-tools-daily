"""
构建脚本

读取 data/ 目录下所有日期 JSON 文件，内联到 v2-template.html 模板中，
生成 v2-standalone.html（部署产物）。

使用方式：
    python build.py
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
TEMPLATE = ROOT / "v2-template.html"
OUTPUT = ROOT / "v2-standalone.html"


def main():
    # 扫描所有日期 JSON 文件（排除 .raw.json）
    json_files = sorted(DATA_DIR.glob("*.json"), reverse=True)
    json_files = [f for f in json_files if not f.name.endswith(".raw.json")]

    if not json_files:
        print("⚠️  data/ 目录下没有数据文件")
        return

    # 构建数据对象
    data_obj = {}
    for jf in json_files:
        date_str = jf.stem  # e.g. "2026-03-23"
        with open(jf, "r", encoding="utf-8") as f:
            data_obj[date_str] = json.load(f)
        print(f"  加载 {date_str}: {len(data_obj[date_str])} 条")

    # 同时更新模板中的 availableDates
    data_json = json.dumps(data_obj, ensure_ascii=False, indent=None)

    # 读取模板
    with open(TEMPLATE, "r", encoding="utf-8") as f:
        html = f.read()

    # 替换占位符
    html = html.replace("__DATA_PLACEHOLDER__", data_json)

    # 写入产物
    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"\n✅ 构建完成: {OUTPUT} ({len(html)} bytes)")
    print(f"   包含 {len(data_obj)} 天数据，共 {sum(len(v) for v in data_obj.values())} 条工具")


if __name__ == "__main__":
    main()
