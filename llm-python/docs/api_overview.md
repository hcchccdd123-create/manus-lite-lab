# API 概览

当前后端默认对外提供流式聊天接口：

- 路径：`POST /api/v1/chat/stream`
- 作用：接收用户消息并返回流式回答
- 典型场景：网页聊天、知识库问答、问题排查

默认聊天模型提供商是 `glm`，后端会根据会话配置决定实际模型和参数。

## 请求体常用字段

```json
{
  "session_id": "conv_xxx",
  "message": "文档里 chat 接口路径是什么？",
  "provider": "glm",
  "model": "glm-4.7",
  "use_rag": null,
  "enable_thinking": null
}
```

- `session_id`：会话 ID，表示这条消息属于哪个会话
- `message`：用户输入的文本
- `provider` / `model`：可选，不传时使用当前会话默认值
- `use_rag`：单次请求的 RAG 覆盖开关
  - `true`：这次强制走 RAG
  - `false`：这次强制不走 RAG
  - `null` 或不传：由后端根据全局配置和意图自动判断
- `enable_thinking`：单次请求的 thinking 开关
  - `true`：强制开启
  - `false`：强制关闭
  - `null` 或不传：由后端决定；普通问答默认跟随 provider，文档/RAG 问答默认关闭

## 当前流式接口的整体流程

1. 路由层接收 `POST /api/v1/chat/stream` 请求。
2. `ChatRequestIn` 把 JSON 反序列化成 Python 对象。
3. `ChatService.stream_message(...)` 先把用户消息写入数据库。
4. 后端判断这是不是“需要联网搜索”的时效问题。
   - 如果当前 provider 不支持联网搜索，就直接返回提示，不继续调用模型。
5. 后端计算本轮 RAG 决策：
   - 先看全局 `RAG_ENABLED`
   - 再看本次请求有没有显式传 `use_rag`
   - 最后看消息内容是否像“文档问答”
6. 如果命中 RAG，就从 Chroma 检索相关 chunk，把检索结果拼进 system prompt。
7. 后端读取最近消息和摘要快照，构造最终上下文。
8. 按当前请求是否是 RAG 问答，决定默认要不要开启 thinking。
9. 通过 `ProviderRouter` 调用实际模型，边生成边用 SSE 往前端推送事件。
10. 如果 thinking 重复、过长或超时，`ThinkingLoopGuard` 会提前止损。
11. 生成结束后，后端会补充“你可能还想问”追问建议，并把最终回答入库。

## SSE 事件说明

前端会收到一系列流式事件，常见有：

- `message.start`：一轮回答开始
- `message.thinking`：模型思考内容片段
- `message.delta`：正文内容片段
- `memory.updated`：摘要快照更新
- `message.end`：这一轮结束，带完整文本和结束原因
- `error`：处理过程中发生异常

## 一个适合入门者的理解方式

可以把这条接口分成 4 层：

- 接口层：收请求、返回 SSE
- 编排层：`ChatService` 决定走不走 RAG、thinking、web search
- 模型层：`ProviderRouter` 和具体 provider 真正调用模型
- 数据层：消息、摘要、知识库文档状态持久化

如果你在学习这套项目，最推荐的阅读顺序是：

1. `app/api/routes/chat.py`
2. `app/api/schemas.py`
3. `app/services/chat_service.py`
4. `app/services/provider_router.py`
5. `app/providers/glm_provider.py`
