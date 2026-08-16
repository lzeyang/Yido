# Yido

Yido 是一款面向个人用户的本地任务管理应用，聚焦于“单人使用、离线可用、隐私优先、轻量高效”的日常待办管理场景。

它适合学生、上班族和普通个人用户，用来管理学习任务、工作待办、生活安排和重复性事务。

## 项目定位

- 个人用户场景，不面向团队协作
- 本地优先，数据保存在用户设备
- 无需云同步、不依赖第三方账号
- 简洁美观、交互轻盈、适合长期日常使用

## 主要功能

- 创建、编辑、删除、完成任务
- 任务标签、优先级和截止时间管理
- 今日、待办、已过期、已完成、全部视图
- 搜索与筛选（关键词、标签、状态、优先级）
- 本地提醒与通知
- 本地备份与恢复
- 主题、默认视图、提醒设置等个性化配置

## 技术栈

- 前端：React + TypeScript
- 桌面壳：Tauri
- 本地数据库：SQLite
- 状态管理：Zustand
- 样式：Tailwind CSS
- 路由：React Router
- 测试：Vitest + Testing Library

## 项目结构

```text
.
├── PRD.md                 # 产品需求文档
├── README.md              # 项目说明
├── todo.json              # 旧版 CLI 数据样例
├── claude.py              # 旧版脚本参考
├── claude2.py             # 旧版任务 CLI
├── deepseek.py            # 旧版脚本参考
├── deepseek2.py           # 旧版脚本参考
├── gpt.py                 # 旧版脚本参考
├── gpt2.py                # 旧版脚本参考
├── src/                   # 应用代码目录（规划中）
│   ├── components/
│   ├── features/
│   ├── hooks/
│   ├── lib/
│   ├── services/
│   ├── stores/
│   ├── types/
│   └── utils/
└── .gitignore             # Git 忽略规则（建议补充）
```

## 设计原则

- 简洁：界面不堆砌复杂功能
- 本地优先：所有数据尽量保存在本地
- 稳定：优先保证长期可用与低故障率
- 亲和：适合非技术用户快速上手

## 运行方式（后续实施）

当前项目处于规划与需求明确阶段，后续将按以下方向落地：

1. 初始化 Tauri + React + TypeScript 项目
2. 配置 SQLite 数据库与表结构
3. 实现任务 CRUD 与筛选逻辑
4. 完成今日视图与任务列表页面
5. 实现设置与备份导入导出
6. 添加本地通知与交互反馈

## Git 初始化建议

最合适的 Git 起点是当前项目根目录，也就是：

```bash
cd /d d:\ds_test
git init
git branch -M main
```

这样做的好处是：

- 整个项目文档、代码和后续结构都在同一仓库下
- 便于后续按功能模块提交
- 避免把 PRD、src 目录和历史脚本分散到不同仓库

建议在第一次提交前添加一个 .gitignore 文件，避免将开发缓存、构建产物和临时文件一并提交。

## 推荐提交顺序

```bash
git add .
git commit -m "feat: initialize Yido project and PRD"
```

如果需要连接远程仓库，再执行：

```bash
git remote add origin <你的仓库地址>
git push -u origin main
```

## 备注

这是一个本地优先的个人应用项目，后续可优先建立清晰的功能模块和数据层，再逐步实现前端界面和桌面应用封装。
