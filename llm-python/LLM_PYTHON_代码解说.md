# llm-python 代码解说（Python 初学者版）

## 1. 这个项目在做什么

这是一个聊天后端服务，目标是：

- 支持会话聊天（每个会话一个 `session_id`）
- 保存历史消息（用户和助手消息）
- 支持多模型提供方（Ollama / GLM / Codex）
- 支持记忆机制（最近窗口 + 摘要落库）
- 提供 HTTP API 给前端调用

---

## 2. 先看哪几个目录

建议先熟悉这些路径：

- `app/main.py`：FastAPI 启动入口
- `app/api/routes/`：接口层（路由）
- `app/services/`：业务层（核心逻辑）
- `app/db/models.py`：数据库表结构
- `app/db/repositories/`：数据库读写封装
- `app/providers/`：不同模型的统一接入
- `app/memory/`：上下文拼装与摘要逻辑

---

## 3. 一次聊天请求怎么流转

以 `POST /api/v1/chat` 为例：

1. 路由接收请求（`app/api/routes/chat.py`）
2. 调用 `ChatService`（`app/services/chat_service.py`）
3. 先把用户消息写入 `messages` 表
4. 读取会话摘要 + 最近消息，拼成上下文
5. 通过 `ProviderRouter` 调模型
6. 把 AI 回复写回 `messages`
7. 判断是否触发摘要，必要时写入 `memory_snapshots`
8. 返回统一格式 JSON

---

## 4. 核心数据库表（重点）

定义在 `app/db/models.py`：

### `conversations`

会话主表，保存：

- `id`（会话 ID）
- `title`（会话标题）
- `provider` / `model`（默认模型配置）
- `status`（active/archived）
- `system_prompt`
- 时间字段（创建/更新/最后活跃）

### `messages`

消息表，保存每条消息：

- `role`（user/assistant/system/tool）
- `content`
- `sequence_no`（会话内顺序）
- `provider` / `model`（实际响应来源）
- token 统计字段

### `memory_snapshots`

记忆摘要表，保存：

- 当前摘要文本
- 已覆盖到哪条消息（`covered_until_sequence_no`）
- 摘要是由哪个 provider/model 生成的

### `provider_call_logs`

模型调用日志表，保存：

- 请求是否成功
- 延迟
- 错误码/错误信息（脱敏）

---

## 5. 多模型统一抽象怎么做

在 `app/providers/base.py` 定义统一接口与类型：

- `ChatRequest`
- `ChatResponse`
- `ChatChunk`
- `LLMProvider` 协议（`chat` / `stream_chat` / `health_check`）

具体实现：

- `ollama_provider.py`
- `glm_provider.py`
- `codex_provider.py`

路由选择由 `app/services/provider_router.py` 负责。

---

## 6. 记忆机制怎么实现

相关文件：

- `app/memory/context_builder.py`
- `app/memory/summarizer.py`
- `app/services/chat_service.py`

机制：

- 每次只带最近 N 条消息（避免上下文太大）
- 达到阈值后把“未摘要消息”压缩成摘要
- 摘要写入 `memory_snapshots`
- 下一轮请求把“摘要 + 最近窗口”一起喂给模型

这就是“低成本保留长期记忆”的核心思路。

---

## 7. API 快速索引

在 `app/api/routes/`：

- `health.py`
  - `GET /api/v1/health`
- `conversations.py`
  - `POST /api/v1/conversations`
  - `GET /api/v1/conversations`
  - `GET /api/v1/conversations/{session_id}`
  - `PATCH /api/v1/conversations/{session_id}`
  - `DELETE /api/v1/conversations/{session_id}`（软删除）
  - `GET /api/v1/conversations/{session_id}/messages`
- `chat.py`
  - `POST /api/v1/chat`
  - `POST /api/v1/chat/stream`（SSE）

---

## 8. 初学者建议的阅读顺序

1. `app/main.py`（知道项目如何启动）
2. `app/api/routes/chat.py`（看接口如何进 service）
3. `app/services/chat_service.py`（看核心业务闭环）
4. `app/db/models.py`（理解数据结构）
5. `app/providers/base.py`（理解抽象）
6. `app/services/provider_router.py`（理解多模型路由）

---

## 9. 常见问题（学习向）

### 为什么分层这么多？

因为要把职责拆开：

- route 只处理 HTTP
- service 处理业务流程
- repository 处理数据读写
- provider 处理外部模型调用

### 为什么不直接把全部历史都传给模型？

会很贵、很慢，还容易超过上下文限制。所以用“窗口 + 摘要”。

### SQLite 够吗？

当前阶段（单机/开发）够用；以后多用户再换 PostgreSQL。

---

## 10. 你可以立刻做的 3 个练习

1. 给 `conversations` 增加 `topic` 字段并打通接口返回
2. 给聊天接口增加一个参数并传到 provider（如 `temperature`）
3. 新增接口：返回某会话的最新摘要

这 3 个练习能帮你快速理解模型、业务层、数据库三者的关系。
