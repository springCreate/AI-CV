# AI 智能简历适配与多平台岗位匹配投递系统

基于 DeepSeek 大模型的求职全流程辅助工具，覆盖简历智能解析、AI 五维度优化、多平台岗位匹配、AI 投递话术生成、Excel 清单导出等核心能力。

> 数据仅本地存储，多用户隔离，零云端上传，无封号风险。

---

## 一、功能特性

| 模块 | 能力 |
|------|------|
| 用户体系 | 注册、登录、JWT 鉴权、多用户数据隔离、密码重置 |
| 简历管理 | PDF/Word 上传、AI 结构化解析、手动编辑、子模块增删改 |
| AI 简历优化 | 五维度优化（关键词适配、删减、技能补充、自我评价、STAR 排版），建议需手动确认 |
| PDF 导出 | 单页/多页自适应排版、中文支持、一键下载 |
| 求职诉求模板 | 多套模板、城市/薪资/双休/住宿/实习证明等维度、默认模板切换 |
| 岗位匹配 | 多平台 API 适配层、硬性过滤 + AI 软性打分（0-100 分） |
| 黑名单 | 公司黑名单管理、自动拦截 |
| 投递辅助 | AI 打招呼话术 + 自我介绍、批量生成、Excel 清单导出、快捷跳转 |
| 投递记录 | 状态管理（未投/已投/面试/Offer/拒绝）、去重、7 日趋势统计 |
| Token 容错 | DeepSeek 1048576 上限自动分片截断，杜绝 400 报错 |
| Mock 模式 | 无 API 配置时使用演示数据，完整流程可体验 |

---

## 二、技术栈

- **后端**：Python 3.10+ / Flask 3.x / SQLAlchemy / SQLite
- **前端**：Vue 3 + Element Plus（CDN 方式，无需 npm 构建）
- **AI**：DeepSeek API（OpenAI 兼容协议）
- **解析**：pdfplumber（PDF）、python-docx（Word）
- **导出**：reportlab（PDF）、openpyxl（Excel）

---

## 三、本地部署

### 1. 环境准备

需 Python 3.10 及以上版本：

```bash
python --version
```

如未安装，前往 [python.org](https://www.python.org/downloads/) 下载，安装时勾选 "Add Python to PATH"。

### 2. 安装依赖

在项目根目录打开命令行，执行：

```bash
pip install -r requirements.txt
```

> 国内网络可加速：`pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple`

### 3. 配置 DeepSeek API Key

首次运行 `run.py` 会自动从 `config.example.yaml` 复制生成 `config.yaml`。

编辑 `config.yaml`，填写你的 DeepSeek API Key：

```yaml
deepseek:
  base_url: "https://api.deepseek.com/v1"
  api_key: "sk-你的真实API Key"   # 在 https://platform.deepseek.com 申请
  model: "deepseek-chat"
```

> 不配置也能启动，但 AI 相关功能（解析、优化、打分、话术）将不可用，岗位匹配走 Mock 演示模式。

### 4. 启动服务

```bash
python run.py
```

启动成功后会看到：

```
============================================================
  AI 智能简历适配与多平台岗位匹配投递系统
============================================================
  访问地址: http://127.0.0.1:5000
  调试模式: 关闭
  数据目录: ...\data
============================================================
  按 Ctrl+C 停止服务
============================================================
```

### 5. 访问系统

浏览器打开 **http://127.0.0.1:5000** 即可使用。

首次访问请先注册账号。所有数据存储在项目根目录的 `data/` 文件夹内。

---

## 四、使用指南

### 4.1 上传与解析简历

1. 进入「我的简历」→ 点击「上传简历」
2. 选择 PDF 或 Word 简历文件
3. 系统自动调用 DeepSeek 解析为结构化信息（个人基础信息、教育、工作、项目、技能、自我评价）
4. 解析完成后可在详情对话框中手动修改、补充

### 4.2 AI 五维度简历优化

1. 在简历卡片点击「AI 优化」
2. 粘贴目标岗位 JD 全文，选择求职诉求模板（可选）
3. 点击「生成优化建议」，系统会从五个维度给出建议：
   - 关键词适配改写
   - 无关内容删减
   - 岗位技能补充
   - 专属自我评价生成
   - STAR 法则排版优化
4. 在各 Tab 中查看建议，可编辑自我评价、勾选要补充的技能
5. 点击「确认应用建议」后才会更新简历

### 4.3 配置求职诉求模板

1. 进入「求职诉求」→「新建模板」
2. 填写：模板名称、目标岗位、期望城市、薪资范围、工作年限、双休/不加班/包住宿等硬性条件
3. 实习专属：可开实习证明、最短月数
4. 关键词：用于 AI 软性匹配加权
5. 可创建多套模板，一键切换默认

### 4.4 一键拉取岗位并匹配

1. 进入「岗位匹配」
2. 顶部选择简历和求职诉求模板
3. 点击「一键拉取并匹配」
4. 系统会：
   - 从启用平台拉取岗位（未配置 API 时使用 Mock 演示数据）
   - 黑名单公司自动过滤
   - 硬性条件过滤（城市、薪资、双休等）
   - AI 软性打分（0-100 分）
5. 在「匹配记录」Tab 查看结果，可按分数、模板筛选

### 4.5 投递辅助

1. 进入「投递管理」
2. 在投递记录列表点击「话术」按钮，AI 为该岗位生成专属：
   - 打招呼话术（80-150 字，适配 BOSS直聘等 IM 平台）
   - 定制自我介绍（300-500 字，可作邮件正文）
3. 点击「复制」可一键复制到剪贴板
4. 点击「前往岗位页面投递」可跳转原链接
5. 投递后点击「标记已投」，系统自动记录投递时间，并去重

### 4.6 导出 Excel 清单

1. 「投递管理」→「Excel 导出」Tab
2. 可选筛选条件：模板、最低匹配分数、仅未投递
3. 点击「导出 Excel 清单」
4. 文件包含：公司、岗位、城市、薪资、匹配分、JD 摘要、发布时间、投递状态、岗位链接、平台
5. 匹配分数自动着色（绿/黄/红）

### 4.7 黑名单管理

- 进入「公司黑名单」→ 添加公司名称
- 加入黑名单的公司，其所有岗位将自动从匹配结果中过滤

---

## 五、目录结构

```
AI/
├── app/                              # 后端应用
│   ├── __init__.py                   # 应用工厂
│   ├── extensions.py                 # 扩展初始化
│   ├── config.py                     # (内嵌于 __init__.py)
│   ├── models/                       # 数据模型
│   │   ├── user.py                   # 用户
│   │   ├── resume.py                 # 简历 + 子表 + 优化记录
│   │   ├── template.py               # 求职诉求模板
│   │   ├── job.py                    # 岗位 + 匹配记录 + 黑名单
│   │   └── application.py            # 投递记录
│   ├── routes/                       # API 路由
│   │   ├── auth.py                   # 认证
│   │   ├── resume.py                 # 简历管理
│   │   ├── template.py               # 模板管理
│   │   ├── job.py                    # 岗位 + 黑名单 + 匹配
│   │   ├── application.py            # 投递辅助
│   │   └── system.py                 # 系统配置
│   ├── services/                     # 业务服务
│   │   ├── ai_service.py             # DeepSeek 封装 + Token 容错
│   │   ├── resume_parser.py          # PDF/Word 解析
│   │   ├── resume_optimizer.py       # 五维度 AI 优化
│   │   ├── pdf_generator.py          # PDF 生成
│   │   ├── job_platform.py           # 招聘平台适配层
│   │   ├── job_matcher.py            # 双层匹配引擎
│   │   ├── application_assistant.py  # 投递话术生成
│   │   └── excel_export.py           # Excel 导出
│   └── utils/                        # 工具
│       ├── token_manager.py          # Token 分片/截断
│       ├── decorators.py             # JWT 装饰器
│       └── responses.py              # 统一响应
├── static/                           # 前端静态资源
│   ├── index.html                    # SPA 入口
│   ├── css/app.css                   # 自定义样式
│   └── js/
│       ├── api.js                    # API 封装
│       ├── app.js                    # 主应用
│       └── components/               # 7 个页面组件
├── data/                             # 本地数据（自动创建）
│   ├── app.db                        # SQLite 数据库
│   ├── resumes/                      # 上传的简历
│   ├── optimized/                    # AI 优化后 PDF
│   ├── exports/                      # Excel 导出
│   └── logs/                         # 日志
├── config.example.yaml               # 配置模板
├── config.yaml                       # 实际配置（首次运行自动创建）
├── requirements.txt                  # Python 依赖
├── run.py                            # 启动入口
└── README.md                         # 本文档
```

---

## 六、API 接口概览

所有接口返回统一 JSON 格式：`{code, success, message, data}`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/register` | 用户注册 |
| POST | `/api/auth/login` | 用户登录 |
| GET | `/api/auth/me` | 获取当前用户 |
| PUT | `/api/auth/me` | 更新用户信息 |
| PUT | `/api/auth/password` | 重置密码 |
| GET | `/api/resume` | 简历列表 |
| POST | `/api/resume` | 创建空简历 |
| POST | `/api/resume/upload` | 上传并解析简历 |
| GET | `/api/resume/:id` | 简历详情 |
| PUT | `/api/resume/:id` | 更新简历 |
| DELETE | `/api/resume/:id` | 删除简历 |
| POST | `/api/resume/:id/reparse` | 重新 AI 解析 |
| POST | `/api/resume/:id/optimize` | 生成 AI 优化建议 |
| POST | `/api/resume/:id/optimize/:logId/apply` | 应用优化建议 |
| POST | `/api/resume/:id/export-pdf` | 生成 PDF |
| GET | `/api/resume/:id/download-pdf` | 下载 PDF |
| GET | `/api/template` | 模板列表 |
| POST | `/api/template` | 创建模板 |
| PUT | `/api/template/:id` | 更新模板 |
| DELETE | `/api/template/:id` | 删除模板 |
| POST | `/api/template/:id/set-default` | 设为默认 |
| GET | `/api/job` | 岗位列表 |
| POST | `/api/job/fetch-match` | 一键拉取并匹配 |
| GET | `/api/job/match-records` | 匹配记录 |
| GET | `/api/job/new-reminders` | 新岗位提醒 |
| GET | `/api/job/blacklist` | 黑名单列表 |
| POST | `/api/job/blacklist` | 加入黑名单 |
| DELETE | `/api/job/blacklist/:id` | 移出黑名单 |
| GET | `/api/application` | 投递记录列表 |
| POST | `/api/application` | 创建投递记录 |
| PUT | `/api/application/:id` | 更新状态 |
| POST | `/api/application/:id/mark-applied` | 标记已投 |
| POST | `/api/application/:jobId/generate-script` | 生成话术 |
| POST | `/api/application/batch-generate-scripts` | 批量生成话术 |
| POST | `/api/application/export-excel` | 导出 Excel |
| GET | `/api/application/stats` | 投递统计 |
| GET | `/api/system/health` | 健康检查 |
| GET | `/api/system/config` | 配置状态 |
| POST | `/api/system/ai/test` | 测试 DeepSeek 连接 |

---

## 七、招聘平台 API 接入说明

PRD 中要求对接 BOSS直聘、智联招聘、前程无忧、实习僧。**实际情况**：

- 这些平台大多不提供公开的岗位搜索 API
- 系统默认走 **Mock 演示模式**，使用本地生成的演示数据展示完整流程
- 如你拥有某平台的开放 API 授权，可在 `config.yaml` 中启用：

```yaml
job_platforms:
  zhilian:
    enabled: true
    base_url: "https://api.zhaopin.com/v1"
    api_key: "你的API Key"
  mock_mode: false   # 关闭 Mock 模式
```

并在 `app/services/job_platform.py` 对应适配器中实现 `fetch_jobs` 方法的真实 API 调用逻辑。

**严格遵守 PRD 约束**：仅查询公开岗位数据，不做爬虫、模拟登录、自动投递，规避平台风控。

---

## 八、安全与隐私

1. **本地存储**：所有数据存储在 `data/` 目录，绝不上传任何云端
2. **多用户隔离**：每条数据都带 `user_id`，查询时强制过滤
3. **密码安全**：使用 werkzeug PBKDF2-SHA256 哈希，不存储明文
4. **JWT 鉴权**：所有业务接口需携带 Bearer Token
5. **合规**：仅查询公开岗位数据，无爬虫、无模拟登录、无自动投递

---

## 九、常见问题

### Q1：启动时报 `ModuleNotFoundError`

重新安装依赖：
```bash
pip install -r requirements.txt
```

### Q2：AI 功能报错「DeepSeek API 连接失败」

1. 检查 `config.yaml` 中 `api_key` 是否填写正确
2. 在「系统设置」页面点击「测试连接」
3. 确认网络能访问 `https://api.deepseek.com`

### Q3：PDF 生成中文显示为方块

系统会自动尝试注册 Windows / macOS / Linux 常见中文字体。如仍异常，请确认系统存在以下任一字体：
- Windows: `C:\Windows\Fonts\simhei.ttf` 或 `msyh.ttc`
- macOS: `/System/Library/Fonts/PingFang.ttc`
- Linux: 安装 `fonts-wqy-zenhei`

### Q4：上传简历解析失败

1. 确认文件为标准 PDF 或 `.docx` 格式（扫描版 PDF 不支持）
2. 即使 AI 解析失败，文件仍会保留，可手动编辑补全信息
3. 在简历详情页点击「重解析」可重试

### Q5：端口被占用

修改 `config.yaml`：
```yaml
server:
  port: 5001   # 改为其他端口
```

### Q6：如何备份数据

直接复制整个 `data/` 目录即可。

---

## 十、增值能力（可选）

PRD 第 7 节提到的 Codex/Chatbox AI 工作流配置文件未在本版本实现。如需开发，建议参考以下思路：

1. **单岗位 JD 简历优化工作流**：导出当前简历 JSON + JD，封装为可导入 prompt 模板
2. **求职诉求解析工作流**：将自然语言描述转为结构化筛选条件 JSON
3. **JD 核心要求提取工作流**：从 JD 文本抽取技能、年限、学历等关键字段

可后续按需开发独立的 `.json` 配置文件，导入到 Chatbox 或 Codex 中使用。

---

## 十一、开发与扩展

### 新增招聘平台适配器

1. 在 `app/services/job_platform.py` 中继承 `BasePlatformAdapter`
2. 实现 `fetch_jobs` 方法，返回 `List[JobRawItem]`
3. 在 `PlatformManager.__init__` 中注册

### 新增 AI 优化维度

1. 在 `app/services/resume_optimizer.py` 的 `SYSTEM_PROMPT` 中追加维度
2. 在 `ResumeOptimizationLog` 模型中新增字段
3. 在前端 `resume.js` 的优化建议 Tab 中添加展示

### 修改前端主题色

编辑 `static/css/app.css`，修改 `PRIMARY_COLOR` 等变量。

---

**祝求职顺利！**
