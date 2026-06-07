SmartStudyCause/
├── README.md                               # 项目介绍、快速开始
├── .gitignore
├── docker-compose.yml                      # 一键启动后端+数据库+Redis
├── Makefile                                # 常用命令（lint, test, run）
│
├── backend/                                # Python后端服务
│   ├── pyproject.toml                      # 项目依赖管理（Poetry或setuptools）
│   ├── .env.example                        # 环境变量模板
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                         # FastAPI 应用入口
│   │   ├── config.py                       # 配置管理（Pydantic Settings）
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── v1/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── endpoints/
│   │   │   │   │   ├── analysis.py         # 试卷分析核心接口
│   │   │   │   │   ├── templates.py        # 模板上传/下载/删除
│   │   │   │   │   ├── reports.py          # 报告生成/分享/历史查询
│   │   │   │   │   └── users.py            # 用户登录、绑定
│   │   │   │   └── dependencies.py
│   │   │   └── deps/
│   │   ├── core/                           # 核心业务逻辑
│   │   │   ├── __init__.py
│   │   │   ├── ocr.py                      # PaddleOCR-VL 调用封装
│   │   │   ├── llm.py                      # Qwen-Learning 调用封装
│   │   │   ├── report_builder.py           # 基于模板填充报告（docx/xlsx）
│   │   │   ├── template_parser.py          # 模板变量提取与校验
│   │   │   └── schemas.py                  # Pydantic 模型（请求/响应）
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   ├── session.py                  # 数据库会话
│   │   │   ├── base.py
│   │   │   └── models/                     # SQLAlchemy ORM 模型
│   │   │       ├── user.py
│   │   │       ├── paper.py                # 原始试卷记录
│   │   │       ├── mistake.py              # 错题明细
│   │   │       ├── template.py             # 用户上传的模板
│   │   │       └── report.py               # 生成报告记录
│   │   ├── services/                       # 第三方服务集成
│   │   │   ├── __init__.py
│   │   │   ├── storage.py                  # 云存储（OSS/COS）
│   │   │   └── wechat.py                   # 微信登录/分享辅助
│   │   ├── utils/                          # 工具函数
│   │   │   ├── __init__.py
│   │   │   ├── image.py                    # 图片压缩、裁剪
│   │   │   ├── file.py                     # 文件类型检测
│   │   │   └── logger.py
│   │   └── tasks/                          # 异步任务（Celery 可选）
│   │       ├── __init__.py
│   │       └── analysis_tasks.py           # 长耗时分析任务
│   └── migrations/                         # Alembic 数据库迁移脚本
│
├── miniprogram/                            # 微信小程序
│   ├── app.js
│   ├── app.json
│   ├── app.wxss
│   ├── project.config.json
│   ├── sitemap.json
│   ├── pages/
│   │   ├── index/                          # 启动页（拍照/上传）
│   │   ├── analysis/                       # 分析中/结果预览
│   │   ├── report/                         # 报告详情与分享
│   │   ├── templates/                      # 我的模板
│   │   ├── history/                        # 历史报告列表
│   │   └── user/                           # 个人中心
│   ├── components/
│   │   ├── camera-view/                    # 自定义相机
│   │   ├── mistake-item/                   # 错题条目
│   │   ├── loading/                        # 加载动画
│   │   └── share-button/                   # 一键分享组件
│   ├── utils/
│   │   ├── request.js                      # 封装 wx.request
│   │   ├── auth.js                         # 登录与 token 管理
│   │   └── helper.js
│   └── services/
│       ├── api.js                          # 后端接口定义
│       └── storage.js                      # 本地缓存
│
├── ai_tests/                               # AI 模型调试脚本
│   ├── test_ocr.py                         # 测试 PaddleOCR-VL
│   ├── test_llm.py                         # 测试 Qwen-Learning 提示词
│   └── cost_estimate.py                    # 成本估算
│
├── docs/                                   # 项目文档
│   ├── api.md                              # API 文档
│   ├── template_guide.md                   # 模板制作指南
│   ├── deployment.md                       # 生产部署
│   └── prompts/                            # 提示词工程记录
│       └── qwen_system.txt
│
└── scripts/                                # 运维/辅助脚本
    ├── backup_db.sh
    └── init_tables.py