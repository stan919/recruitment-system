# 职引未来 - 高校毕业生就业服务平台

## 项目简介
本项目旨在解决高校毕业生在求职初期面临的"信息过载但价值密度低"的痛点，通过可视化技术将复杂的招聘数据转化为直观的决策依据。

**最新版本**: v1.0.3  
**更新时间**: 2026-04-05

## 功能特性

### 核心功能
- 📊 **数据洞察**：企业画像、地域热力图、技能雷达图、学历分析
- 🔍 **智能搜索**：支持按专业、薪资、城市、学历、经验多条件筛选
- 💼 **职位详情**：完整的职位描述、公司信息、技能要求
- 📱 **响应式设计**：适配 PC 和移动端

### 用户系统
- 🔐 **注册登录**：支持用户名/邮箱登录，密码强度验证（至少 8 位）
- 👤 **个人中心**：简历管理、投递记录、账户设置
- 📄 **简历管理**：在线填写简历 + PDF/Word 附件上传（最大 10MB）
- 💬 **即时聊天**：求职者与企业 HR 实时沟通

### 企业后台
- 🏢 **企业管理**：公司信息管理、雇主品牌展示
- 📋 **投递管理**：查看投递列表、更新状态（待处理/面试/Offer/拒绝）
- 📊 **数据统计**：职位统计、转化率分析、处理时效
- 🔒 **权限控制**：企业管理员专属后台

### 管理员后台
- 👥 **用户管理**：用户列表、账号状态、激活/禁用
- 📝 **职位审核**：职位上架审核、批量审核、驳回原因
- 📈 **数据统计**：用户数、职位数、投递量统计
- 🔐 **内容安全**：敏感词管理、操作日志、数据导出
- 📊 **企业监管**：企业列表、职位监控

### 安全与优化
- 🔒 **XSS 防护**：使用 markupsafe 转义 HTML 字符
- 🛡️ **文件验证**：文件头校验 + 大小限制
- ⚡ **性能优化**：数据库连接池（pool_size=20）
- 📝 **审计日志**：企业操作记录、管理员操作追踪

## 技术栈
- **后端**: Python 3.14 + Flask
- **数据库**: MySQL 8.0 + SQLAlchemy ORM
- **前端**: HTML5 + CSS3 + JavaScript + ECharts
- **可视化**: Pyecharts + ECharts
- **认证**: Werkzeug 密码哈希 + Flask Session
- **文件处理**: werkzeug 安全文件名 + 文件头验证
- **API**: RESTful API + JSON
- **部署**: Gunicorn (生产环境)

## 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 配置环境变量
复制 `.env.example` 为 `.env`，修改配置：
```ini
SECRET_KEY=your-secret-key-here
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your-password
DB_NAME=job_navigation
PORT=5000
```

### 3. 初始化数据库
```bash
python init_admin.py        # 初始化超级管理员
python init_company_admin.py # 初始化企业管理员（可选）
```

### 4. 启动服务
```bash
python app.py
```

访问 http://localhost:5000

### 5. 默认账号
- **超级管理员**: admin / admin123456
- **普通用户**: 需自行注册

## 项目结构
```
积分单元/
├── app.py                    # Flask 主应用（所有路由和 API）
├── auth.py                   # 用户认证管理器
├── config.py                 # 配置文件
├── load_env.py              # 环境变量加载
├── setup_env.py             # 环境设置脚本
├── models_user.py           # 用户模型
├── models_job.py            # 职位模型
├── models_resume.py         # 简历和投递模型
├── models_company.py        # 公司和审计日志模型
├── models_chat.py           # 聊天消息模型
├── data_cleaner.py          # 数据清洗模块
├── visualizer.py            # 可视化图表生成
├── generate_mock_data.py    # 模拟数据生成
├── import_data.py           # 数据导入工具
├── run_production.py        # 生产环境启动脚本
├── comprehensive_test.py    # 综合功能测试脚本
├── templates/               # HTML 模板
│   ├── home.html           # 主页
│   ├── login.html          # 登录页
│   ├── register.html       # 注册页
│   ├── profile.html        # 个人中心
│   ├── applications.html   # 投递记录
│   ├── user_chat.html      # 用户聊天页
│   ├── company_chat.html   # 企业聊天页
│   ├── job_search.html     # 职位搜索
│   ├── job_detail.html     # 职位详情
│   ├── insights.html       # 数据洞察
│   ├── admin.html          # 管理员后台
│   ├── company.html        # 企业后台
│   └── company_settings.html # 企业设置
├── static/                  # 静态资源
│   ├── charts/            # 生成的图表 HTML
│   ├── css/               # 样式文件
│   └── js/                # JavaScript 文件
├── uploads/                 # 上传文件
│   └── resumes/           # 简历附件
├── logs/                    # 日志文件
├── .env                     # 环境变量配置
├── .env.example            # 环境变量示例
├── requirements.txt        # Python 依赖
└── README.md               # 本文档
```

## 数据文件说明

### `jobs_data_public.csv` 与 `jobs_data_30k.csv` 的区别

| 文件名 | 规模 | 字段数量 | 主要用途 |
|---|---:|---:|---|
| `jobs_data_public.csv` | 2,000 行 | 13 列 | 轻量演示、快速导入、开发调试 |
| `jobs_data_30k.csv` | 30,000 行 | 17 列 | 压测、统计分析、接近生产规模的数据验证 |

`jobs_data_30k.csv` 相比 `jobs_data_public.csv` 额外包含以下字段：
- `industry`
- `company_size`
- `is_campus`
- `publish_date`

如果你只是本地快速跑通功能，建议优先使用 `jobs_data_public.csv`；
如果要观察筛选、分页、统计、可视化在大数据量下的表现，使用 `jobs_data_30k.csv` 更合适。

## API 文档

### 认证相关
- `POST /api/login` - 用户登录
- `POST /api/register` - 用户注册
- `POST /api/logout` - 用户登出
- `GET /api/user` - 获取当前用户信息

### 职位相关
- `GET /api/jobs/search` - 职位搜索
- `GET /api/jobs/<id>` - 获取职位详情

### 简历相关
- `GET /api/resume` - 获取简历
- `POST /api/resume` - 保存简历
- `POST /api/resume/upload` - 上传简历附件
- `DELETE /api/resume/attachment` - 删除附件
- `POST /api/application/submit` - 提交申请
- `GET /api/applications` - 获取投递记录

### 企业后台
- `GET /api/company/dashboard` - 控制台统计
- `GET /api/company/applications` - 投递列表
- `GET /api/company/jobs` - 在招职位
- `PUT /api/company/application/<id>/status` - 更新申请状态
- `GET /api/company/settings` - 获取公司设置
- `PUT /api/company/settings` - 更新公司设置

### 管理员后台
- `GET /api/admin/check` - 检查管理员权限
- `GET /api/admin/dashboard` - 控制台统计
- `GET /api/admin/users` - 用户列表
- `GET /api/admin/jobs` - 职位列表
- `PUT /api/admin/jobs/<id>/audit` - 审核职位
- `GET /api/admin/companies` - 企业列表
- `GET /api/admin/logs` - 操作日志

### 聊天功能
- `GET /api/chat/conversations` - 会话列表
- `GET /api/chat/conversations/<id>` - 历史消息
- `POST /api/chat/conversations` - 创建会话
- `POST /api/chat/messages` - 发送消息

## 测试验证

### 运行全功能测试
```bash
python comprehensive_test.py
```

测试覆盖：
- ✅ 健康检查
- ✅ 页面加载（主页、登录、注册、数据洞察）
- ✅ 登录注册验证
- ✅ 职位搜索 API
- ✅ 密码强度验证（8 位以上）
- ✅ 会话态用户信息与登出流程

说明：历史上存在多个功能重复的脚本（`full_test.py`、`test_optimization.py`），当前已统一为 `comprehensive_test.py`，避免维护重复测试。

## 安全特性

### 已实现
- ✅ 密码哈希存储（Werkzeug）
- ✅ XSS 防护（markupsafe.escape）
- ✅ 文件上传验证（文件头 + 大小限制 10MB）
- ✅ SQL 注入防护（SQLAlchemy ORM 参数化）
- ✅ 速率限制（登录尝试 5 分钟 10 次）
- ✅ 手机号脱敏导出
- ✅ 审计日志记录

### 建议加强
- ⚠️ CSRF Token 保护（目前部分表单使用）
- ⚠️ 密码复杂度要求（建议增加特殊字符）
- ⚠️ 双因素认证（可选）
- ⚠️ IP 白名单（管理员后台）

## 性能优化

### 已实现
- ✅ 数据库连接池（pool_size=20, max_overflow=10）
- ✅ 单例模式（全局共享引擎）
- ✅ scoped_session 会话管理
- ✅ 延迟加载（模型文件）
- ✅ 分页查询（职位列表、投递记录）

### 后续计划
- 🔲 Redis 缓存热点数据
- 🔲 数据库索引优化
- 🔲 静态资源 CDN
- 🔲 异步任务队列（Celery）

## 常见问题

### Q: 数据库连接失败？
A: 检查 `.env` 文件配置，确保 MySQL 服务已启动

### Q: 文件上传失败？
A: 检查 `uploads` 目录权限，确保有写入权限

### Q: 图表不显示？
A: 检查浏览器控制台是否有 JavaScript 错误，清除缓存后重试

### Q: 如何重置管理员密码？
A: 重新运行 `python init_admin.py` 会覆盖原密码

## 项目总览总结

本项目已形成完整的求职平台主链路：普通用户可完成注册登录、职位搜索、简历上传、在线投递与消息沟通；企业端可进行岗位与投递处理；管理员端可完成用户与职位治理、内容安全和审计导出。当前代码以 `app.py` 为统一入口，测试以 `comprehensive_test.py` 为单一综合脚本，文档保持面向快速部署与核心能力说明。
