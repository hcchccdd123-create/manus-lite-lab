# BACKEND_STRUCTURE.md

## 1. 架构概览
后端位于 `llm-python/`，分层为：
- API 路由层（FastAPI）
- Service 业务层
- Repository 数据访问层
- Provider 抽象层（Ollama/GLM/Codex）
- Memory 层（上下文构建与摘要）

## 2. 数据库结构（SQLite）

### 2.1 conversations
- `id` TEXT PK
- `title` VARCHAR(255)
- `status` VARCHAR(32) (`active`/`archived`)
- `provider` VARCHAR(32)
- `model` VARCHAR(128)
- `system_prompt` TEXT NULL
- `memory_mode` VARCHAR(32)
- `memory_window_size` INTEGER
- `summary_message_count` INTEGER
- `created_at` DATETIME
- `updated_at` DATETIME
- `last_active_at` DATETIME

索引：
- `idx_conversations_last_active_at`
- `idx_conversations_status`

### 2.2 messages
- `id` TEXT PK
- `conversation_id` FK -> conversations.id
- `role` VARCHAR(32)
- `content` TEXT
- `sequence_no` INTEGER
- `provider` VARCHAR(32) NULL
- `model` VARCHAR(128) NULL
- `prompt_tokens` INTEGER NULL
- `completion_tokens` INTEGER NULL
- `total_tokens` INTEGER NULL
- `request_id` VARCHAR(64) NULL
- `created_at` DATETIME

约束：
- unique(`conversation_id`, `sequence_no`)

索引：
- `idx_messages_conversation_created`
- `idx_messages_conversation_sequence`

### 2.3 memory_snapshots
- `id` TEXT PK
- `conversation_id` FK
- `summary_text` TEXT
- `covered_until_sequence_no` INTEGER
- `source_message_count` INTEGER
- `summarizer_provider` VARCHAR(32)
- `summarizer_model` VARCHAR(128)
- `created_at` DATETIME
- `updated_at` DATETIME

索引：
- `idx_memory_conversation_updated`

### 2.4 provider_call_logs
- `id` TEXT PK
- `request_id` VARCHAR(64)
- `conversation_id` VARCHAR(64)
- `provider` VARCHAR(32)
- `model` VARCHAR(128)
- `success` INTEGER
- `latency_ms` INTEGER
- `error_code` VARCHAR(64) NULL
- `error_message` VARCHAR(255) NULL
- `created_at` DATETIME

## 3. API 合约

### 3.1 Health
- `GET /api/v1/health`

### 3.2 Conversations
- `POST /api/v1/conversations`
- `GET /api/v1/conversations`
- `GET /api/v1/conversations/{session_id}`
- `PATCH /api/v1/conversations/{session_id}`
- `DELETE /api/v1/conversations/{session_id}`（软删 -> archived）
- `GET /api/v1/conversations/{session_id}/messages`

### 3.3 Chat
- `POST /api/v1/chat`
- `POST /api/v1/chat/stream`

统一响应 envelope：
- `request_id`
- `data`
- `error`

## 4. SSE 事件合约（chat/stream）
- `message.start`
- `message.delta`
- `message.end`
- `memory.updated`（摘要更新时）
- `error`

## 5. Provider 策略
- 统一抽象 `ChatRequest / ChatResponse / ChatChunk`
- provider 实现：`ollama`, `glm`, `codex`
- 默认 provider：`ollama`
- 默认模型：`qwen3.5:0.8b`
- 可选 fallback（配置开关）

## 6. Thinking 说明
- 本地验证：`qwen3.5:0.8b` 具备 `thinking` capability
- 当前前端按 `<think>...</think>` 做解析与展示
- 启用策略文档约定：默认仅 Ollama 开启（实现按代码状态推进）

## 7. 异常与边界
- provider auth/rate-limit/timeout/unavailable 统一异常映射
- 会话不存在返回 404
- SSE 失败通过 `error` 事件回传
- 当前版本不提供自动流式重连

## 8. CORS
- 后端允许本地前端源：
  - `http://localhost:5173`
  - `http://127.0.0.1:5173`

---
Last updated from codebase on 2026-03-05
