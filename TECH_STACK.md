# TECH_STACK.md

## 1. 前端（web-vue3-vite）

### 运行时
- Node.js: >= 18（由 Vite 6 与 esbuild 依赖要求）
- 包管理器: npm（存在 `package-lock.json`）

### 核心依赖（当前 package.json）
- vue: ^3.5.13
- vite: ^6.2.0
- typescript: ^5.8.2
- pinia: ^3.0.3
- vue-router: ^4.5.1
- markdown-it: ^14.1.0
- dompurify: ^3.2.6
- idb: ^8.0.0
- @vitejs/plugin-vue: ^5.2.1
- vue-tsc: ^2.2.8

### 构建脚本
- `npm run dev`
- `npm run build`
- `npm run preview`

## 2. 后端（llm-python）

### Python
- Python: >= 3.11（`pyproject.toml`）

### 核心依赖（当前 pyproject.toml）
- fastapi >=0.115.0
- uvicorn[standard] >=0.30.0
- pydantic >=2.8.0
- pydantic-settings >=2.4.0
- sqlalchemy >=2.0.30
- greenlet >=3.0.0
- aiosqlite >=0.20.0
- httpx >=0.27.0
- sse-starlette >=2.1.0
- tenacity >=9.0.0

### 开发依赖
- pytest >=8.0.0
- pytest-asyncio >=0.24.0

## 3. 本地模型与推理服务
- Ollama endpoint: `http://127.0.0.1:11434`
- 默认模型（当前配置）: `qwen3.5:0.8b`
- 已验证模型能力：`qwen3.5:0.8b` 包含 `thinking`

## 4. Provider 组合
- Ollama（本地）
- GLM（OpenAI-compatible endpoint）
- Codex/OpenAI-compatible endpoint

## 5. 数据与存储
- 后端数据库：SQLite（`sqlite+aiosqlite:///./data/chat.db`）
- 前端持久化：IndexedDB（会话、消息、think_state）

## 6. 部署环境
- 本地开发：macOS
- 目标部署：OpenCloudOS（后端已提供部署脚本与 systemd 模板）

## 7. 约束
- 禁止使用“latest/stable”等模糊版本说明
- 新增依赖必须在本文件同步记录

---
Last updated from codebase on 2026-03-05
