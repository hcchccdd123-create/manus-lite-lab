# TECH_STACK.md

## 1. 运行环境

### 本地开发
- OS: macOS（当前开发机）
- Node.js: 18+
- Python: 3.11+

### 目标部署
- OS: OpenCloudOS（后端服务部署目标）

## 2. 前端技术栈（`web-vue3-vite`）

### 核心框架
- Vue `3.5.29`
- Vite `6.4.1`
- TypeScript `5.9.3`
- Pinia `3.0.4`
- Vue Router `4.6.4`

### UI 与渲染
- Element Plus `2.13.3`（确认弹窗等组件）
- markdown-it `14.1.1`
- DOMPurify `3.3.1`

### 本地持久化
- idb `8.0.3`

### 开发依赖（关键）
- @vitejs/plugin-vue `5.2.4`
- vue-tsc `2.2.12`
- @types/dompurify `3.2.0`
- @types/markdown-it `14.1.2`
- @types/node `22.19.13`

### 命令
- `npm run dev`
- `npm run build`
- `npm run preview`

## 3. 后端技术栈（`llm-python`）

### Python 与 Web
- Python `>=3.11`
- FastAPI `0.135.1`
- Uvicorn `0.41.0`
- Pydantic `2.12.5`
- pydantic-settings `2.13.1`

### 数据与网络
- SQLAlchemy `2.0.48`
- greenlet `3.3.2`
- asyncpg `0.31.0`
- chromadb `1.5.5`
- httpx `0.28.1`
- sse-starlette `3.3.2`
- tenacity `9.1.4`

### RAG 与文档
- llama-index `0.14.18`
- pypdf `6.9.1`

### 测试
- pytest `9.0.2`
- pytest-asyncio `1.3.0`

## 4. 模型与 Provider
- 本地推理：Ollama
- Ollama Base URL: `http://127.0.0.1:11434`
- 默认模型：`glm-4.7`
- Provider 抽象：`ollama` / `glm` / `codex`
- Thinking: GLM / Ollama 路径均可通过请求参数控制，未传时后端默认开启
- Web Search: 当前通过 GLM tools（`web_search`）自动提供给支持模型，由模型自行决定是否调用

## 5. Runtime 形态
- 当前版本仅保留 Chat 模式
- Agent Runtime 暂不纳入本轮交付

## 5.1 当前可用运行时保护
- 时区上下文注入：`APP_TIMEZONE`（默认 `Asia/Shanghai`）
- thinking 止损：`THINKING_LOOP_MAX_CHARS` / `THINKING_LOOP_REPEAT_THRESHOLD` / `THINKING_LOOP_MAX_SECONDS`
- 终止可观测：`message.end` 返回 `termination_reason`
- 时效问题防幻觉：不支持联网搜索的模型命中实时问题时，由后端直接返回标准提示

## 6. 存储与数据
- 后端主数据库：PostgreSQL（本地开发当前使用 `postgresql+asyncpg`）
- 向量检索：ChromaDB HTTP Server（本机独立进程）
- 前端持久化：IndexedDB（`conversations` / `messages` / `think_states`）

## 7. 版本约束规则
- 文档必须记录明确版本，不写 “latest/stable”。
- 升级依赖时，同步更新本文件与 lock 文件。
- 前端以 `package-lock.json` 为实际安装基准，后端以 `.venv` 实装版本为运行基准。

---
Last updated from codebase on 2026-03-06
