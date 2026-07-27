# AI-CV

AI 智能简历适配与岗位匹配系统 —— 基于 DeepSeek 大模型的求职全流程辅助工具。

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Flask Version](https://img.shields.io/badge/flask-3.x-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)

## 核心功能

- **简历智能解析**：支持 PDF/Word 上传，AI 自动解析为结构化信息
- **AI 简历优化**：五维度智能优化（关键词适配、技能补充、STAR 排版等）
- **岗位手动录入与智能匹配**：手动录入真实岗位，AI 匹配打分 + 技能提升建议
- **面试题库**：基于岗位 JD 和简历，AI 预测面试官提问并生成回答思路
- **公司黑名单**：标记不感兴趣的公司，避免重复关注
- **本地安全存储**：数据仅本地存储，多用户隔离，零云端上传

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python 3.10+ / Flask 3.x / SQLAlchemy / SQLite |
| 前端 | Vue 3 + Element Plus（CDN 方式，无需构建） |
| AI | DeepSeek API（OpenAI 兼容协议） |
| 文件处理 | pdfplumber、python-docx、reportlab |

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

国内网络加速：

```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 2. 配置

首次运行会自动从 `config.example.yaml` 生成 `config.yaml`，如需使用 AI 功能，请填写 DeepSeek API Key：

```yaml
deepseek:
  api_key: "sk-你的API Key"  # https://platform.deepseek.com 申请
```

> 不配置也能启动，AI 相关功能将不可用。

### 3. 启动服务

```bash
python run.py
```

启动成功后访问 **http://127.0.0.1:5000**

## 使用流程

```
注册登录 → 创建求职诉求模板 → 上传简历 → AI优化简历
    → 手动录入岗位 → 选择简历+岗位匹配 → 生成面试题
```

### 各模块说明

#### 1. 仪表盘
展示简历数量、求职诉求模板数、岗位数量、面试题数量等概览信息，提供快速入口和使用指南。

#### 2. 我的简历
- 上传 PDF/Word 简历，系统自动解析为结构化数据
- 支持 AI 五维度优化（关键词适配、技能补充、STAR 排版等）
- 可下载优化后的 PDF 简历

#### 3. 求职诉求
创建求职诉求模板，设定目标岗位、城市、薪资范围、工作年限、学历等硬性条件，作为岗位匹配的筛选标准。

#### 4. 岗位匹配
- **手动录入岗位**：用户手动录入真实岗位信息（岗位名称、公司、JD、原链接等）
- **智能匹配**：选择一份简历 + 一个岗位 + 求职诉求模板，点击「开始匹配」
- **匹配结果**：系统生成匹配度评分（0-100分）+ 匹配摘要
- **技能提升建议**：识别缺失技能，给出具体的学习建议（如：该岗位需要某些技能，而你目前没有，建议精进哪部分）

#### 5. 面试题库
- **生成面试题**：选择一份简历 + 一个岗位，AI 根据岗位 JD 和简历内容生成面试官可能提问的问题清单
- **问题分类**：行为面试题、技术考察题、项目经验题、技能深挖题、文化匹配题
- **每道题包含**：考察要点、回答思路、示例答案、加分点
- **按岗位管理**：每个岗位单独生成面试题，支持按岗位筛选查看

#### 6. 公司黑名单
标记不感兴趣的公司，避免重复关注。

#### 7. 系统设置
- 查看 DeepSeek AI 配置状态
- 修改个人信息（昵称、目标岗位、目标城市等）
- 重置密码

## 项目结构

```
AI-CV/
├── app/                        # 后端应用
│   ├── __init__.py             # 应用工厂
│   ├── models/                 # 数据模型
│   │   ├── user.py             # 用户模型
│   │   ├── resume.py           # 简历及关联模型
│   │   ├── template.py         # 求职诉求模板
│   │   ├── job.py              # 岗位、匹配记录、黑名单
│   │   └── interview.py        # 面试问题模型
│   ├── routes/                 # API 路由
│   │   ├── auth.py             # 认证（注册/登录）
│   │   ├── resume.py           # 简历管理
│   │   ├── template.py         # 求职诉求
│   │   ├── job.py              # 岗位匹配
│   │   ├── interview.py        # 面试题库
│   │   ├── system.py           # 系统配置
│   │   └── blacklist.py        # 公司黑名单
│   ├── services/               # 业务服务
│   │   ├── ai_service.py       # DeepSeek AI 调用
│   │   ├── resume_parser.py    # 简历解析
│   │   ├── resume_optimizer.py # 简历优化
│   │   ├── job_matcher.py      # 岗位匹配引擎
│   │   ├── interview_service.py# 面试题生成
│   │   └── job_platform.py     # 岗位数据源
│   └── utils/                  # 工具（JWT、响应封装、Token 容错）
├── static/                     # 前端静态资源
│   ├── index.html              # SPA 入口
│   ├── css/app.css             # 自定义样式
│   └── js/
│       ├── api.js              # API 封装
│       ├── app.js              # 主应用入口
│       └── components/         # 页面组件
│           ├── dashboard.js    # 仪表盘
│           ├── resume.js       # 我的简历
│           ├── template.js     # 求职诉求
│           ├── job.js          # 岗位匹配
│           ├── interview.js    # 面试题库
│           ├── blacklist.js    # 公司黑名单
│           └── settings.js     # 系统设置
├── data/                       # 本地数据（自动创建）
│   ├── app.db                  # SQLite 数据库
│   ├── resumes/                # 上传的简历
│   ├── optimized/              # AI 优化后 PDF
│   └── logs/                   # 日志
├── config.yaml                 # 配置文件（需自行创建）
├── config.example.yaml         # 配置模板
├── requirements.txt            # Python 依赖
└── run.py                      # 启动入口
```

## API 接口

所有接口返回统一 JSON 格式：`{code, success, message, data}`

| 模块 | 接口 | 方法 | 说明 |
|------|------|------|------|
| 认证 | `/api/auth/register` | POST | 用户注册 |
| 认证 | `/api/auth/login` | POST | 用户登录 |
| 简历 | `/api/resume/upload` | POST | 上传并解析简历 |
| 简历 | `/api/resume/:id/optimize` | POST | 生成 AI 优化建议 |
| 求职诉求 | `/api/template` | GET/POST | 模板管理 |
| 岗位 | `/api/job` | GET/POST | 岗位列表/手动录入 |
| 岗位 | `/api/job/match` | POST | 单岗位智能匹配 |
| 面试题库 | `/api/interview/generate` | POST | 生成面试题 |
| 面试题库 | `/api/interview` | GET | 面试题列表 |
| 系统 | `/api/system/config` | GET | 系统配置状态 |

## 安全与隐私

- **本地存储**：所有数据存储在 `data/` 目录，不上传云端
- **多用户隔离**：每条数据都带 `user_id`，查询时强制过滤
- **密码安全**：使用 PBKDF2-SHA256 哈希，不存储明文
- **JWT 鉴权**：所有业务接口需携带 Bearer Token

## 常见问题

**Q：启动时报 `ModuleNotFoundError`**

重新安装依赖：`pip install -r requirements.txt`

**Q：AI 功能报错**

检查 `config.yaml` 中 `api_key` 是否正确，或确认网络能访问 `https://api.deepseek.com`

**Q：PDF 生成中文显示为方块**

系统会自动注册常见中文字体。如仍异常，请确认系统存在 `simhei.ttf`（Windows）或 `PingFang.ttc`（macOS）

**Q：如何备份数据**

直接复制整个 `data/` 目录即可

**Q：为什么没有自动拉取岗位功能**

国内主流招聘平台（BOSS直聘、智联招聘、前程无忧等）均未开放个人开发者岗位查询 API，因此本系统采用手动录入岗位的方式，用户可从招聘网站复制岗位信息录入系统进行匹配分析。

## 许可证

MIT License

---

**祝求职顺利！**
