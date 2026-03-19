# llm-python 代码解说（Python 初学者版，2026-03 现状）

## 1. 这个后端现在做什么

`llm-python` 是一个本地优先的 AI Chat 后端，核心能力包括：

- 会话聊天（每个会话一个 `session_id`）
- 历史消息持久化（`user/assistant/system/tool`）
- 多模型 Provider 抽象（`ollama / glm / codex`）
- 记忆策略（最近窗口 + 摘要快照）
- SSE 流式输出（`message.start/thinking/delta/end/error`）
- 自动 Web Search + 后端意图拦截（防止编造实时信息）
- RAG 文档问答（Chroma 检索 + prompt 注入）
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
2. 参数反序列化（`ChatRequestIn`，含 `use_rag`、`enable_thinking`）
3. 进入 `ChatService.stream_message(...)`
4. 写入用户消息到 `messages`
5. 执行“是否需要联网”的后端能力判断与意图识别
   - 支持联网搜索的模型默认自动获得 Web Search 能力
   - 不支持联网搜索且命中时效问题：直接返回标准提示（不让模型编造）
6. 计算这一轮的 RAG 决策
   - `RAG_ENABLED` 是全局总开关
   - `use_rag` 是单次请求覆盖
   - 若 `use_rag` 不传，则走“意图识别”
7. 若命中 RAG，从 Chroma 检索相关文档 chunk
8. 读取摘要 + 最近消息，构建上下文
9. 注入运行时 system 信息（当前时区时间、时间问题回答规则、RAG 上下文等）
10. 构建 `ChatRequest`，通过 `ProviderRouter` 调用对应 Provider
11. 边读 chunk 边 SSE 输出（thinking/delta）
12. `ThinkingLoopGuard` 在流中实时检测：
   - 超长
   - 重复
   - 超时
13. 结束后落库 assistant 消息，并在 `message.end` 返回：
   - `text`
   - `thinking`
   - `termination_reason`（如 `thinking_timeout`）
14. 最终文本会追加“推荐追问”块（如符合条件）

---

## 4. 先把几个关键概念分清楚

很多初学者第一次看这段代码，会把几个开关混在一起。这里先拆清楚：

### 4.1 `RAG_ENABLED`

- 这是全局配置，定义在 `app/core/config.py`
- 它表示：系统层面允不允许走 RAG
- 可以把它理解为“总电源”

如果它是 `false`：

- 不管这次请求有没有传 `use_rag`
- 都不会真正发起文档检索

### 4.2 `use_rag`

- 这是接口请求体里的字段，定义在 `app/api/schemas.py`
- 它表示：这一次请求要不要覆盖默认行为

它有 3 种情况：

- `true`：这次强制走 RAG
- `false`：这次强制不走 RAG
- `null` / 不传：这次不指定，交给后端自动判断

可以把它理解为“本次临时开关”，不是总开关。

### 4.3 `enable_thinking`

- 这也是请求体字段
- 表示：这次请求要不要显式控制模型的 thinking 模式

当前代码里的策略是：

- 普通问答：如果不传，GLM/Ollama 默认开启 thinking
- 文档/RAG 问答：如果不传，默认关闭 thinking

这么做的原因很简单：

- 文档问答更像“查资料然后回答”
- 不需要太长的推理链
- 关闭 thinking 可以减少“思考流转半天但正文没出来”的情况

---

## 5. `POST /api/v1/chat/stream` 的一轮完整执行过程

下面这部分是最适合你拿着代码一起对照看的。

### 第一步：进入路由层

文件：`app/api/routes/chat.py`

路由函数做的事很少：

1. 接收前端 POST 请求
2. 把 JSON 解析成 `ChatRequestIn`
3. 创建 `ChatService`
4. 调用 `stream_message(...)`
5. 把 service 产出的事件包装成 SSE 返回给前端

也就是说，路由层基本不做业务判断，它只是“转发站”。

### 第二步：进入 `ChatService.stream_message(...)`

文件：`app/services/chat_service.py`

这是整个聊天流程的编排中心。你可以把它理解成“导演”：

- 它不直接生成模型回答
- 它负责决定什么时候查数据库、什么时候查 RAG、什么时候调模型、什么时候往前端推流

函数开头会先做几件基础工作：

1. 生成 `request_id`
2. 根据 `session_id` 查会话
3. 确定本轮实际使用的 `provider` 和 `model`
4. 把用户消息写入数据库

### 第三步：先做“联网搜索需求”判断

代码里有 `_is_network_query(...)`，它会识别：

- 天气
- 新闻
- 行情
- 最新、实时、today、latest 之类的时效性问题

如果问题本质上需要联网，而当前 provider 又不支持联网搜索：

- 系统不会让模型硬答
- 而是直接返回标准提示

这样做是为了减少“实时问题幻觉”。

### 第四步：计算这一轮 RAG 决策

这是你最近刚调通的关键链路。

代码里现在有一个 `RAGDecision` 数据结构，里面会统一保存：

- `enabled`：全局 RAG 是否开启
- `override`：本次请求有没有显式传 `use_rag`
- `intent_matched`：问题是否像文档问答
- `should_retrieve`：最终这轮要不要去检索

这样做的好处是：

- 判断逻辑集中
- 日志更清楚
- 不容易在多个函数里写出互相打架的条件

实际判断顺序是：

1. 先看全局 `RAG_ENABLED`
2. 再看 `use_rag`
3. 如果 `use_rag` 没传，再交给 `RAGIntentDetector`

### 第五步：如果命中 RAG，就去 Chroma 检索

这里要把两个存储分清楚：

- PostgreSQL / SQLite：存业务数据，比如会话、消息、知识库文档状态
- Chroma：存向量库里的 chunk 文本、embedding、metadata

检索发生在 `RAGRetriever` 里：

1. 先把用户问题做 embedding
2. 用 query embedding 去 Chroma 查相似 chunk
3. 拿回 `documents`、`metadatas`、`distances`
4. 过滤掉相似度不够的结果
5. 组装成 `RetrievedContext`

然后 `ChatService` 会把这些检索结果拼进 system prompt，让模型优先参考这些内容回答。

### 第六步：组装上下文

`_build_context_messages(...)` 会把这些东西合并起来：

- 会话自带的 `system_prompt`
- 当前时间信息
- 历史摘要 `summary`
- 最近窗口消息 `recent_messages`
- 这轮 RAG 命中的上下文

最终得到一个完整的 `messages` 列表，再发给 provider。

### 第七步：决定 thinking 默认值

这一步你前面已经踩过坑了，所以很值得记住。

当前逻辑不是“所有问题都默认开 thinking”，而是：

- 普通问题：默认开
- 文档/RAG 问题：默认关

因为文档问答更适合“短路径回答”，不需要先输出大量 thinking。

### 第八步：调模型并流式返回

然后 `ChatService` 会构造 `ChatRequest`，交给 `ProviderRouter`。

`ProviderRouter` 的作用是：

- 根据 provider 选中具体实现
- 统一记录调用日志
- 对上层暴露一致接口

所以不管你底层接的是 GLM、Ollama 还是别的模型，上层写法都差不多。

流式过程中，后端会不断 `yield` SSE 事件给前端：

- `message.start`
- `message.thinking`
- `message.delta`
- `message.end`

前端就是根据这些事件，一边收一边把内容显示出来。

### 第九步：thinking guard 实时止损

如果模型在 thinking 阶段：

- 太长
- 太重复
- 太久没结束

`ThinkingLoopGuard` 就会触发止损。

这是为了避免：

- 模型在 thinking 里绕圈
- 前端一直转圈没正文
- 响应时长失控

### 第十步：生成结束后的收尾动作

模型正文流结束后，还会做几件事：

1. 拼接终止提示（如果触发了 guard）
2. 追加“你可能还想问”
3. 如果命中了 RAG，再追加来源摘要
4. 把 assistant 最终消息写入数据库
5. 视情况更新摘要快照

这也是为什么前端最后看到的完整文本，通常比模型原始 delta 多一些后处理内容。

---

## 6. 核心表结构（为什么这样设计）

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

## 7. Provider 抽象：为什么这么做

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

## 8. 你最近新增的关键能力（代码对应）

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

### 8.2 Thinking 默认开启 + 三重止损

相关文件：

- `app/services/chat_service.py`
- `app/services/thinking_loop_guard.py`
- `app/core/config.py`

逻辑要点：

- `enable_thinking` 未传时，GLM/Ollama 在普通问答默认开启
- 若本轮被识别为文档/RAG 问答，则默认关闭 thinking
- Guard 维度：
  - `THINKING_LOOP_MAX_CHARS`
  - `THINKING_LOOP_REPEAT_WINDOW` + `THINKING_LOOP_REPEAT_THRESHOLD`
  - `THINKING_LOOP_MAX_SECONDS`
- 触发后会提前终止无效推理，并回传 `termination_reason`

### 8.3 RAG 文档问答

相关文件：

- `app/services/chat_service.py`
- `app/rag/intent_detector.py`
- `app/rag/retriever.py`
- `app/rag/ingestion_service.py`

逻辑要点：

- `RAG_ENABLED` 控制全局是否启用
- `use_rag` 只控制本次请求是否覆盖默认行为
- 文档问题会先做意图识别，再决定是否检索
- 检索结果会作为上下文注入模型
- 最终回答末尾会附带来源摘要

### 8.4 动态推荐追问（不再死模板）

相关文件：

- `app/services/chat_service.py`

逻辑要点：

- 主回答生成后，再调用一次模型生成 3 个追问（JSON 格式）
- 追问内容基于“用户问题 + 主回答”动态生成
- 失败时回退到兜底模板
- 问候语/极短输入不追加追问

---

## 9. 记忆系统（window + summary）怎么协作

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

## 10. API 快速索引（当前可用）

- `GET /api/v1/health`
- `POST /api/v1/conversations`
- `GET /api/v1/conversations`
- `GET /api/v1/conversations/{session_id}`
- `PATCH /api/v1/conversations/{session_id}`
- `DELETE /api/v1/conversations/{session_id}`（软删）
- `GET /api/v1/conversations/{session_id}/messages`
- `POST /api/v1/chat/stream`

`/chat/stream` 常用参数：

- `use_rag`: 单次请求的 RAG 覆盖开关（`true/false/null`）
- `enable_thinking`: 是否开启 thinking（GLM/Ollama 默认 true）

---

## 11. 新同学阅读顺序（推荐）

1. `app/main.py`（入口）
2. `app/api/routes/chat.py`（HTTP -> Service）
3. `app/services/chat_service.py`（主流程）
4. `app/providers/base.py` + `app/providers/glm_provider.py`（Provider 适配）
5. `app/services/provider_router.py`（路由和日志）
6. `app/services/thinking_loop_guard.py`（止损机制）
7. `app/memory/`（上下文和摘要）
8. `app/db/models.py`（数据结构）

---

## 12. 常见问题（按当前代码回答）

### Q1：为什么“今天股市行情”有时会被拦截？

因为系统判断这是时效问题，而当前模型不支持联网搜索，所以会强制拦截，避免幻觉。

### Q2：为什么会出现“thinking 自动终止”？

因为触发了 guard（超时/重复/过长），系统主动止损，保护响应时延和稳定性。

### Q3：为什么我明明没传 `use_rag`，却仍然走了文档检索？

因为 `use_rag=null` 的意思不是“关闭 RAG”，而是“不覆盖默认行为”。

此时后端会继续看：

- 全局 `RAG_ENABLED` 是否开启
- 当前问题是否像“文档问答”

如果这两者都满足，仍然会走 RAG。

### Q4：为什么推荐追问有时没有？

问候语或极短输入会被过滤，不追加追问是故意设计。

---

## 13. 三个实战练习（适合继续深入）

1. 给时效意图识别增加“白名单/黑名单配置化”（从代码常量改为 `.env` 或独立配置）
2. 为 `termination_reason` 增加统计接口（看哪类终止最常见）
3. 给追问生成加缓存（相同问答短时间内复用，降低二次调用成本）
