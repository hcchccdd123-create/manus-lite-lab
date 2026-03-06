# APP_FLOW.md

## 1. 页面与路由

### 页面清单
- 主页面（单页）
  - 左侧：会话列表 + `+ New`
  - 右侧：聊天区（消息流、Think 缩略/放大面板、输入框）

### 路由
- `/`（当前唯一路由）

## 2. 核心流程

### Flow A: 进入应用（初始化）
触发条件：打开页面或刷新页面。

步骤：
1. 从 IndexedDB 恢复 `conversations/messages/think_states`。
2. 调用后端会话列表同步（失败不阻塞本地展示）。
3. 进入草稿态：右侧空白，输入框居中，默认不自动选中历史会话。

成功结果：
- 用户可直接输入首问开始新会话。
- 历史会话可在左侧手动切换查看。

失败处理：
- 后端同步失败：仅 warning，保留本地数据可用。

### Flow B: 点击 `+ New`
触发条件：用户点击左侧 `+ New`。

步骤：
1. 切换到草稿态（`uiMode='draft'`）。
2. 清空右侧会话上下文展示。
3. 左侧不立即新增历史会话项。

成功结果：
- 用户看到干净输入界面，不污染历史列表。

### Flow C: 草稿态首发消息
触发条件：草稿态输入并发送第一条消息。

步骤：
1. 前端先创建后端会话（默认 `provider=glm`、`model=glm-4.7`），拿到 `session_id` 并存入 `pendingConversations`。
2. 建立 SSE（`POST /api/v1/chat/stream`）。
3. 收到第一条流内容事件（`message.delta` 或 `message.thinking`）后，才将该会话从 pending 提升到左侧历史列表。
4. 标题使用首问标准化文本前 20 字。

成功结果：
- 避免“空会话”提前出现在历史列表。

失败处理：
- 若流式失败且从未收到首条流内容：该 pending 会话不显示在左栏。

### Flow D: 流式消息处理
触发条件：SSE 已建立。

事件序列：
1. `message.start`：会话置为 streaming，左栏显示 loading。
2. `message.thinking`：追加 think 文本，缩略 Think（70x70）实时更新并自动滚底。
3. `message.delta`：追加 assistant 正文草稿。
4. `memory.updated`：更新摘要状态（可选事件）。
5. `message.end`：固化 assistant 消息、结束 loading，Think 保留缩略可回看状态。
6. `error`：结束当前会话流状态并记录错误。

成功结果：
- 消息区和 Think 区可持续增量更新。
- 左栏 loading 与会话状态一致。

### Flow D.1: 消息区自动滚底与手动接管
触发条件：消息区有新增输出（用户发送、assistant 流式增量、会话切换）。

步骤：
1. 默认开启 `message-scroll` 自动滚底，增量内容到达后自动贴底。
2. 用户手动上滚后，暂停自动滚底。
3. 暂停期间在消息区右下角显示“回到底部”圆形悬浮按钮。
4. 点击按钮后恢复自动滚底并立即滚动到底部。

成功结果：
- 用户可以自由回看历史内容，不被强制拉回。
- 需要追踪最新输出时可一键恢复跟底。

### Flow E: 会话切换与并发隔离
触发条件：A 会话流式过程中切换到 B。

步骤：
1. 切换 `activeConversationId`。
2. A 的 SSE 连接保持，不中断。
3. B 可独立发起新的 SSE。
4. 回切 A 时继续看到 A 的增量输出。

成功结果：
- 多会话流式完全隔离，不串流。

### Flow F: 删除会话
触发条件：悬停会话项（`conversation-item`），点击删除按钮。

步骤：
1. 打开 Element Plus 确认弹窗。
2. 确认后调用 `DELETE /api/v1/conversations/{id}`（软删）。
3. 前端同步删除内存态与 IndexedDB 数据。
4. 若删除当前会话，自动回草稿态。

成功结果：
- 左栏、右侧、IndexedDB 三处状态一致。

### Flow F.1: 深度思考开关
触发条件：用户在输入框右下区域点击 Deep Thinking 按钮。

步骤：
1. 切换前端开关状态（开/关）。
2. 发送请求时将状态写入 `enable_thinking`。
3. 后端按 provider 路由：GLM/Ollama 使用该参数，其他 provider 安全降级。

成功结果：
- 用户可按需控制是否开启深度思考输出。
- 前后端参数一致，状态不丢失。

### Flow G: Think 缩略与放大
触发条件：当前会话存在 think 内容。

桌面端步骤：
1. 在输入区容器左上方显示缩略 Think：`top:-50px; left:30px`。
2. 缩略模块逻辑视图保持 `400x400`，通过等比缩放显示为 `70x70`。
3. 点击缩略模块后，同一 Think 视图提升到 chat-panel 最高层级并上下左右居中（无遮罩层）。
4. 展开/收缩动画参考 macOS Genie Effect（神奇灯）风格。
5. 放大视图首次打开自动滚动到底部；thinking 进行中默认持续自动滚底。
6. 用户手动滚动后暂停自动滚底，点击底部“回到底部”悬浮按钮恢复自动滚底。
7. 关闭放大视图后回到缩略模块初始位置。

移动端步骤（`<=980px`）：
1. 隐藏缩略模块。
2. 在输入框左侧显示 Think 放大入口按钮。
3. 点击入口按钮打开/关闭 Think 放大视图。

成功结果：
- 保持 think 快速预览能力，同时不遮挡输入与消息阅读。

### Flow H: Agent Runtime 推理循环（新增规划）
触发条件：用户发送需要工具协作的复杂问题，且本轮开启 Agent Runtime。

步骤：
1. 前端发起流式请求并声明 Agent 模式（建议字段：`runtime_mode=agent`）。
2. 后端进入 Agent Loop，先返回 `thinking`（可选）。
3. 当模型返回 `tool_call` 时，后端执行对应工具并产出 `tool_result`。
4. 工具结果注入上下文，模型继续下一轮推理。
5. 循环直到模型返回 `final_answer` 或达到最大步数。
6. 前端按步骤渲染 Agent 过程卡片，并在结束时展示最终答案。

成功结果：
- 用户可感知“模型思考 -> 调工具 -> 继续推理 -> 最终回答”的完整链路。
- 工具调用失败时也能看到可追踪的错误结果，而非静默失败。

失败处理：
- 工具超时/参数错误：显示 `tool_result(error)` 并由后端决定继续或终止。
- 达到步数上限：显示标准终止原因（例如 `step_limit_reached`）。

## 3. 决策点
- 当前是否为草稿态。
- 是否已有 active 会话。
- 流式首条内容是否到达（决定是否 reveal pending）。
- SSE 事件类型分支（start/thinking/delta/end/error）。
- 本地是否已有该会话历史消息缓存。
- 当前是否移动端（决定缩略模块或输入区入口按钮）。
- 当前是否开启 Agent Runtime（chat 模式 vs agent 模式）。
- Agent 当前 step_type（thinking/tool_call/tool_result/final_answer）。
- 是否达到 `max_steps` / 超时阈值（决定继续或终止）。

## 4. 异常分支
- CORS/网络失败：请求报错，保留当前 UI，不崩溃。
- provider 不可用：`/health` 返回 provider false。
- 会话不存在：聊天接口 404。
- SSE 中断：当前会话置 error/done，不自动续传（用户可重发）。
- 缩略层误拦截点击：视为 P1 回归，必须修复 pointer-events 命中区。
- Agent 工具不可用：回传结构化错误，UI 需展示并保留最终会话可读性。

---
Last updated from codebase on 2026-03-06
