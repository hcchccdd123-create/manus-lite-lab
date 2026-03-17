# BACKEND_STRUCTURE.md

## 1. 分层结构
后端目录：`llm-python/app/`

- `api/`：FastAPI 路由与请求响应模型
- `services/`：核心业务流程（聊天、会话、provider 路由、agent loop 编排）
- `db/`：SQLAlchemy 模型、会话管理、仓储层
- `providers/`：`ollama/glm/codex` 统一抽象与实现
- `memory/`：上下文拼装、摘要策略与摘要执行
- `tools/`：工具实现与参数 schema 校验（当前含 `get_current_datetime`）

## 2. 数据库结构（SQLite）

### 2.1 `conversations`
字段：
- `id` (TEXT, PK)
- `title` (TEXT)
- `status` (`active` / `archived`)
- `provider` (`ollama` / `glm` / `codex`)
- `model` (TEXT)
- `system_prompt` (TEXT, nullable)
- `memory_mode` (TEXT)
- `memory_window_size` (INTEGER)
- `summary_message_count` (INTEGER)
- `created_at` / `updated_at` / `last_active_at` (DATETIME)

索引：
- `idx_conversations_last_active_at`
- `idx_conversations_status`

### 2.2 `messages`
字段：
- `id` (TEXT, PK)
- `conversation_id` (TEXT, FK -> `conversations.id`)
- `role` (`system/user/assistant/tool`)
- `content` (TEXT)
- `sequence_no` (INTEGER)
- `provider` / `model` (nullable)
- `prompt_tokens` / `completion_tokens` / `total_tokens` (nullable)
- `request_id` (TEXT, nullable)
- `created_at` (DATETIME)

约束与索引：
- unique(`conversation_id`, `sequence_no`)
- `idx_messages_conversation_created`
- `idx_messages_conversation_sequence`

### 2.3 `memory_snapshots`
字段：
- `id` (TEXT, PK)
- `conversation_id` (TEXT, FK)
- `summary_text` (TEXT)
- `covered_until_sequence_no` (INTEGER)
- `source_message_count` (INTEGER)
- `summarizer_provider` / `summarizer_model` (TEXT)
- `created_at` / `updated_at` (DATETIME)

索引：
- `idx_memory_conversation_updated`

### 2.4 `provider_call_logs`
字段：
- `id` (TEXT, PK)
- `request_id` (TEXT)
- `conversation_id` (TEXT)
- `provider` / `model` (TEXT)
- `success` (INTEGER)
- `latency_ms` (INTEGER)
- `error_code` / `error_message` (nullable)
- `created_at` (DATETIME)

### 2.5 `agent_steps`（规划）
字段：
- `id` (TEXT, PK)
- `conversation_id` (TEXT, FK -> `conversations.id`)
- `message_id` (TEXT, nullable)
- `step_no` (INTEGER)
- `step_type` (`thinking` / `tool_call` / `tool_result` / `final_answer`)
- `tool_name` (TEXT, nullable)
- `tool_args_json` (TEXT, nullable)
- `tool_result_json` (TEXT, nullable)
- `status` (`running` / `success` / `error` / `terminated`)
- `error_code` / `error_message` (nullable)
- `latency_ms` (INTEGER, nullable)
- `created_at` (DATETIME)

索引：
- `idx_agent_steps_conversation_step`
- `idx_agent_steps_created_at`

## 3. API 合约

### 会话
- `POST /api/v1/conversations`
- `GET /api/v1/conversations`
- `GET /api/v1/conversations/{session_id}`
- `PATCH /api/v1/conversations/{session_id}`
- `DELETE /api/v1/conversations/{session_id}`（软删）
- `GET /api/v1/conversations/{session_id}/messages`

### 聊天
- `POST /api/v1/chat/stream`

请求关键字段（已支持）：
- `enable_thinking`：可选；GLM/Ollama 未传时默认开启
- 其余聊天请求字段保持会话、provider、model 与生成参数

### 健康检查
- `GET /api/v1/health`

统一 envelope：
```json
{
  "request_id": "req_xxx",
  "data": {},
  "error": null
}
```

## 4. SSE 事件协议（`/api/v1/chat/stream`）
- `message.start`
- `message.thinking`
- `message.delta`
- `memory.updated`（可选）
- `message.end`（包含 `termination_reason`，如 `thinking_timeout` / `thinking_guard_triggered`）
- `error`

## 5. Provider 抽象与策略
- 抽象类型：`ChatRequest` / `ChatResponse` / `ChatChunk`。
- 可选 provider：`ollama` / `glm` / `codex`。
- 默认 provider：`glm`。
- 默认模型：`glm-4.7`。
- Thinking 参数：`enable_thinking`，GLM/Ollama 路径可用，未传时默认开启。
- Web Search：当前仅 GLM 通过 `tools` 透传 `web_search`，默认自动提供给支持模型，由模型自行决定是否调用。

## 5.1 实时问题防幻觉策略（已实现）
- 支持联网搜索的模型默认自动获得 Web Search 能力。
- 不支持联网搜索的模型命中天气/新闻/行情等时效问题时，后端直接返回标准提示文案，不让模型自由编造。
- 提示文案通过正常 SSE 消息流输出，不额外引入错误事件语义。

## 7. 记忆策略
- 模式：`window_summary`。
- 上下文：`system_prompt + latest_summary + 最近窗口消息`。
- 达阈值触发增量摘要，写入 `memory_snapshots`。
- 摘要失败不影响主聊天流程。

## 7.1 Thinking Guard（已实现）
- 防护维度：
  - 字符上限：`THINKING_LOOP_MAX_CHARS`
  - 重复检测：`THINKING_LOOP_REPEAT_WINDOW` + `THINKING_LOOP_REPEAT_THRESHOLD`
  - 时长上限：`THINKING_LOOP_MAX_SECONDS`
- 生效范围：GLM / Ollama。
- 触发后行为：提前结束流式循环，返回 `termination_reason` 并输出当前可用结果。

## 8. 异常与边界
- 会话不存在：返回 404。
- provider 错误统一映射（auth/rate-limit/timeout/unavailable）。
- SSE 失败通过 `error` 事件回传。
- 当前版本不做自动流式重连。

## 9. CORS 与本地联调
允许源：
- `http://localhost:5173`
- `http://127.0.0.1:5173`

---
Last updated from codebase on 2026-03-06
