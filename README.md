# AI-CV

AI 智能简历适配与多平台岗位匹配投递系统 —— 基于 DeepSeek 大模型的求职全流程辅助工具。

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Flask Version](https://img.shields.io/badge/flask-3.x-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)

## ✨ 核心功能

- **📄 简历智能解析**：PDF/Word 上传，AI 自动解析为结构化信息
- **🚀 AI 简历优化**：五维度智能优化（关键词适配、技能补充、STAR 排版等）
- **🎯 多平台岗位匹配**：硬性条件过滤 + AI 软性打分（0-100 分）
- **💬 投递话术生成**：AI 定制打招呼话术和自我介绍
- **📊 投递管理**：状态追踪、去重、7 日趋势统计、Excel 导出
- **🔒 本地安全存储**：数据仅本地存储，多用户隔离，零云端上传

## 🛠 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python 3.10+ / Flask 3.x / SQLAlchemy / SQLite |
| 前端 | Vue 3 + Element Plus（CDN 方式，无需构建） |
| AI | DeepSeek API（OpenAI 兼容协议） |
| 文件处理 | pdfplumber、python-docx、reportlab、openpyxl |

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

国内网络加速：

```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 2. 配置（可选）

首次运行会自动生成 `config.yaml`，如需使用 AI 功能，请填写 DeepSeek API Key：

```yaml
deepseek:
  api_key: "sk-你的API Key"  # https://platform.deepseek.com 申请
```

> 不配置也能启动，AI 功能将不可用，岗位匹配走 Mock 演示模式。

### 3. 启动服务

```bash
python run.py
```

启动成功后访问 **http://127.0.0.1:5000**

## 📖 使用流程

```
注册登录 → 创建求职诉求模板 → 上传/创建简历 → AI优化简历
    → 一键拉取岗位 → AI匹配打分 → 生成投递话术 → 标记投递状态
```

### 详细说明

1. **求职诉求模板**：设定目标岗位、城市、薪资、工作年限等硬性条件
2. **简历管理**：上传 PDF/Word 自动解析，或手动创建
3. **AI 优化**：粘贴目标 JD，获取五维度优化建议并确认应用
4. **岗位匹配**：选择简历和模板，一键拉取并匹配，AI 打分排序
5. **投递辅助**：为每个岗位生成专属话术，支持批量生成和 Excel 导出

## 📁 项目结构

```
AI-CV/
├── app/                    # 后端应用
│   ├── models/             # 数据模型（User、Resume、Job、Template、Application）
│   ├── routes/             # API 路由（auth、resume、job、application）
│   ├── services/           # 业务服务（AI、简历解析、匹配引擎、话术生成）
│   └── utils/              # 工具（JWT、响应封装、Token 容错）
├── static/                 # 前端静态资源
│   ├── index.html          # SPA 入口
│   ├── css/app.css         # 自定义样式
│   └── js/components/      # 7 个页面组件
├── data/                   # 本地数据（自动创建）
│   ├── app.db              # SQLite 数据库
│   ├── resumes/            # 上传的简历
│   ├── optimized/          # AI 优化后 PDF
│   ├── exports/            # Excel 导出
│   └── logs/               # 日志
├── config.yaml             # 配置文件
├── requirements.txt        # Python 依赖
└── run.py                  # 启动入口
```

## 🔐 安全与隐私

- **本地存储**：所有数据存储在 `data/` 目录，不上传云端
- **多用户隔离**：每条数据都带 `user_id`，查询时强制过滤
- **密码安全**：使用 PBKDF2-SHA256 哈希，不存储明文
- **JWT 鉴权**：所有业务接口需携带 Bearer Token
- **合规访问**：仅查询公开岗位数据，无爬虫、无模拟登录、无自动投递

## 📝 API 接口

所有接口返回统一 JSON 格式：`{code, success, message, data}`

| 模块 | 接口 | 说明 |
|------|------|------|
| 认证 | `POST /api/auth/login` | 用户登录 |
| 简历 | `POST /api/resume/upload` | 上传并解析简历 |
| 优化 | `POST /api/resume/:id/optimize` | 生成 AI 优化建议 |
| 匹配 | `POST /api/job/fetch-match` | 一键拉取并匹配 |
| 话术 | `POST /api/application/batch-generate-scripts` | 批量生成话术 |
| 导出 | `POST /api/application/export-excel` | 导出 Excel 清单 |

## ❓ 常见问题

**Q：启动时报 `ModuleNotFoundError`**

重新安装依赖：`pip install -r requirements.txt`

**Q：AI 功能报错**

检查 `config.yaml` 中 `api_key` 是否正确，或确认网络能访问 `https://api.deepseek.com`

**Q：PDF 生成中文显示为方块**

系统会自动注册常见中文字体。如仍异常，请确认系统存在 `simhei.ttf`（Windows）或 `PingFang.ttc`（macOS）

**Q：如何备份数据**

直接复制整个 `data/` 目录即可

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

**祝求职顺利！** 🎉
