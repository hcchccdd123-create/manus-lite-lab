# llm-python 代码解说（Python 初学者版，2026-03 现状）

## 1. 这个后端现在做什么

`llm-python` 是一个本地优先的 AI Chat 后端，核心能力包括：

- 会话聊天（每个会话一个 `session_id`）
- 历史消息持久化（`user/assistant/system/tool`）
- 多模型 Provider 抽象（`ollama / glm / codex`）
- 记忆策略（最近窗口 + 摘要快照）
- SSE 流式输出（`message.start/thinking/delta/end/error`）
- 自动 Web Search + 后端意图拦截（防止编造实时信息）
- Thinking 稳定性保护（重复/长度/时长三重 guard）
- 答案末尾推荐追问（由模型基于回答内容动态生成）

---

## 2. 目录速览（建议先看）

- `app/main.py`：FastAPI 启动入口
- `app/api/routes/`：接口层
- `app/services/chat_service.py`：聊天核心编排（最重要）
- `app/services/provider_router.py`：Provider 路由与调用日志
- `app/services/thinking_loop_guard.py`：thinking 重复检测和止损
- `app/providers/`：各模型实现
- `app/memory/`：记忆上下文拼装 + 摘要
- `app/tools/datetime_tool.py`：时间工具（`get_current_datetime`）
- `app/core/config.py`：配置项定义（`.env` 对应）

---

## 3. 一次流式聊天请求完整流转（重点）

以 `POST /api/v1/chat/stream` 为例：

1. 路由接收请求（`app/api/routes/chat.py`）
2. 参数反序列化（`ChatRequestIn`，含 `enable_thinking`）
3. 进入 `ChatService.stream_message(...)`
4. 写入用户消息到 `messages`
5. 执行“是否需要联网”的后端能力判断与意图识别
   - 支持联网搜索的模型默认自动获得 Web Search 能力
   - 不支持联网搜索且命中时效问题：直接返回标准提示（不让模型编造）
6. 读取摘要 + 最近消息，构建上下文
7. 注入运行时 system 信息（当前时区时间、时间问题回答规则等）
8. 构建 `ChatRequest`，通过 `ProviderRouter` 调用对应 Provider
9. 边读 chunk 边 SSE 输出（thinking/delta）
10. `ThinkingLoopGuard` 在流中实时检测：
   - 超长
   - 重复
   - 超时
11. 结束后落库 assistant 消息，并在 `message.end` 返回：
   - `text`
   - `thinking`
   - `termination_reason`（如 `thinking_timeout`）
12. 最终文本会追加“推荐追问”块（如符合条件）

---

## 4. 核心表结构（为什么这样设计）

定义在 `app/db/models.py`：

### `conversations`
- 每个会话一条
- 保存默认 provider/model、标题、状态、记忆参数、活跃时间

### `messages`
- 每条消息一条
- `sequence_no` 保证会话内顺序
- `role` 区分 user/assistant/system/tool

### `memory_snapshots`
- 保存摘要文本和“已覆盖到哪条消息”
- 让上下文不依赖全量历史，降低 token 成本

### `provider_call_logs`
- 记录模型调用成功率、延迟、错误
- 便于排查“模型慢/模型挂/模型限流”

---

## 5. Provider 抽象：为什么这么做

在 `app/providers/base.py` 定义统一数据结构：

- `ChatRequest`
  - 现在支持 `tools` 字段（用于 GLM `web_search`）
- `ChatResponse`
- `ChatChunk`
- `LLMProvider` 协议：`chat` / `stream_chat` / `health_check`

好处：

- 上层 `ChatService` 不关心底层是 GLM 还是 Ollama
- 业务只拼一次请求，Provider 负责适配具体 API 格式

---

## 6. 你最近新增的关键能力（代码对应）

### 6.1 自动 Web Search + 后端意图拦截

相关文件：

- `app/services/chat_service.py`（意图识别 + 非联网 provider 拦截）
- `app/providers/glm_provider.py`（透传 `tools.web_search`）

逻辑要点：

- 支持联网搜索的模型默认自动可用
- 后端识别“实时问题”（天气/新闻/行情等）
- 若当前模型不支持联网，直接返回提示：
  - “当前所选模型不支持联网搜索”
- 防止模型凭记忆“编出今天行情”

### 6.2 Thinking 默认开启 + 三重止损

相关文件：

- `app/services/chat_service.py`
- `app/services/thinking_loop_guard.py`
- `app/core/config.py`

逻辑要点：

- `enable_thinking` 未传时，GLM/Ollama 默认开启
- Guard 维度：
  - `THINKING_LOOP_MAX_CHARS`
  - `THINKING_LOOP_REPEAT_WINDOW` + `THINKING_LOOP_REPEAT_THRESHOLD`
  - `THINKING_LOOP_MAX_SECONDS`
- 触发后会提前终止无效推理，并回传 `termination_reason`

### 6.3 动态推荐追问（不再死模板）

相关文件：

- `app/services/chat_service.py`

逻辑要点：

- 主回答生成后，再调用一次模型生成 3 个追问（JSON 格式）
- 追问内容基于“用户问题 + 主回答”动态生成
- 失败时回退到兜底模板
- 问候语/极短输入不追加追问

---

## 7. 记忆系统（window + summary）怎么协作

核心文件：

- `app/memory/context_builder.py`
- `app/memory/summarizer.py`
- `app/services/chat_service.py`

流程：

1. 每轮只取最近窗口消息（避免超上下文）
2. 超过阈值后把“未摘要区间”做增量摘要
3. 摘要写入 `memory_snapshots`
4. 下轮上下文 = `system_prompt + summary + recent_messages`

这样既保留长期语义，又可控成本。

---

## 8. API 快速索引（当前可用）

- `GET /api/v1/health`
- `POST /api/v1/conversations`
- `GET /api/v1/conversations`
- `GET /api/v1/conversations/{session_id}`
- `PATCH /api/v1/conversations/{session_id}`
- `DELETE /api/v1/conversations/{session_id}`（软删）
- `GET /api/v1/conversations/{session_id}/messages`
- `POST /api/v1/chat/stream`

`/chat/stream` 常用参数：

- `enable_thinking`: 是否开启 thinking（GLM/Ollama 默认 true）

---

## 9. 新同学阅读顺序（推荐）

1. `app/main.py`（入口）
2. `app/api/routes/chat.py`（HTTP -> Service）
3. `app/services/chat_service.py`（主流程）
4. `app/providers/base.py` + `app/providers/glm_provider.py`（Provider 适配）
5. `app/services/provider_router.py`（路由和日志）
6. `app/services/thinking_loop_guard.py`（止损机制）
7. `app/memory/`（上下文和摘要）
8. `app/db/models.py`（数据结构）

---

## 10. 常见问题（按当前代码回答）

### Q1：为什么“今天股市行情”有时会被拦截？

因为系统判断这是时效问题，而当前模型不支持联网搜索，所以会强制拦截，避免幻觉。

### Q2：为什么会出现“thinking 自动终止”？

因为触发了 guard（超时/重复/过长），系统主动止损，保护响应时延和稳定性。

### Q3：为什么推荐追问有时没有？

问候语或极短输入会被过滤，不追加追问是故意设计。

---

## 11. 三个实战练习（适合继续深入）

1. 给时效意图识别增加“白名单/黑名单配置化”（从代码常量改为 `.env` 或独立配置）
2. 为 `termination_reason` 增加统计接口（看哪类终止最常见）
3. 给追问生成加缓存（相同问答短时间内复用，降低二次调用成本）
