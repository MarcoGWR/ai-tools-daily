# AI 工具日报

每日自动聚合小红书上的 AI 工具推荐，10:00 准时更新。

## 技术栈

- 前端：纯静态 HTML + CSS（shadcn/ui 风格）
- 数据：JSON 文件，按日期归档
- 采集：Python 脚本 + LLM 结构化提取
- 部署：Vercel（自动）
- 定时：GitHub Actions（每日 UTC 22:00 = 北京时间 06:00）

## 本地开发

```bash
# 预览
python3 -m http.server 8080
# 访问 http://localhost:8080/v2-standalone.html

# 手动采集（需配置环境变量）
python3 scripts/collect.py
python3 scripts/process.py
python3 build.py
```

## 环境变量

在 GitHub 仓库 Settings → Secrets and variables → Actions 中添加：

| 变量名 | 用途 |
|--------|------|
| `OPENAI_API_KEY` | GPT-4o-mini 结构化提取 |
| `DATA_SOURCE_API_KEY` | 千瓜/新榜 API Key（可选） |

## 目录结构

```
├── data/                    # 每日数据 JSON
│   ├── 2026-03-23.json
│   └── 2026-03-22.json
├── scripts/
│   ├── collect.py           # 数据采集
│   ├── process.py           # AI 清洗 + 结构化提取
│   └── config.py            # 关键词/分类配置
├── v2-template.html         # 网站模板
├── v2-standalone.html       # 构建产物（自动生成）
├── build.py                 # 构建脚本：数据内联到模板
├── requirements.txt         # Python 依赖
└── .github/workflows/
    └── daily-update.yml     # 定时任务
```

## License

MIT
