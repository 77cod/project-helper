# project-helper

`project-helper` 是一个帮助用户快速读懂开源项目源码的 Web 应用。

## 功能

- 输入公开 GitHub 仓库地址，自动克隆并分析源码
- 生成小白友好的分析报告
- 展示项目历史，已分析项目自动缓存
- 通过 SSE 实时推送分析进度
- 基于源码的交互式问答，支持流式输出
- 前后端分离：FastAPI + Vue

## 技术栈

- 后端：FastAPI、SQLAlchemy、SQLite、LangChain、DeepSeek 兼容接入
- 前端：Vue 3、Vite、Markdown-it、highlight.js

## 启动后端

```bash
cd backend
python -m pip install --default-timeout=1000 -e .[dev]
python -m uvicorn app.main:app --reload --port 8000
```

可选环境变量：

```bash
PROJECT_HELPER_DEEPSEEK_API_KEY=your_key
PROJECT_HELPER_DEEPSEEK_BASE_URL=https://api.deepseek.com
PROJECT_HELPER_DEEPSEEK_MODEL=deepseek-chat
PROJECT_HELPER_DATABASE_URL=sqlite+aiosqlite:///./project-helper.db
PROJECT_HELPER_WORKSPACE_ROOT=./workspace
```

如果没有配置 DeepSeek Key，系统会退回到本地启发式分析与问答模式，依然可以运行和测试。

## 启动前端

```bash
cd frontend
npm install
npm run dev
```

默认请求 `http://127.0.0.1:8000`，如需修改：

```bash
set VITE_API_BASE_URL=http://127.0.0.1:8000
npm run dev
```

## 测试

后端：

```bash
python -m pytest backend/tests
```

前端：

```bash
cd frontend
npm test
npm run build
```
