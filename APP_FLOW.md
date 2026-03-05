# APP_FLOW.md

## 1. 页面与路由

### 页面清单
1. 主页面（单页）
   - 左侧：会话列表与新建入口
   - 右侧：聊天区（消息流 + Think 面板 + 输入框）

### 路由
- `/`（当前唯一路由）

## 2. 核心流程

### 流程 A：页面初始化
触发：用户打开应用

步骤：
1. 前端从 IndexedDB 恢复会话、消息、think 状态
2. 前端请求后端会话列表进行同步
3. 用户可在左侧选择历史会话查看消息

成功结果：
- 左侧显示会话列表
- 右侧显示当前选中会话内容（若有）

失败处理：
- 后端同步失败仅 warning，不阻断本地已恢复内容

### 流程 B：新建并开始对话
触发：用户点击 New 或在可输入状态发送消息

步骤（现行实现）：
1. 创建会话（`POST /api/v1/conversations`）
2. 设置 activeConversation
3. 发送流式聊天（`POST /api/v1/chat/stream`）

成功结果：
- 左侧新增会话项
- 右侧显示流式回复

失败处理：
- 创建失败：提示错误，不进入流式
- 流式失败：会话结束 loading 并标记错误

### 流程 C：流式消息处理
触发：SSE 已建立

事件序列：
1. `message.start` -> 会话 isStreaming=true（左侧 loading）
2. `message.delta` -> 追加 assistant 草稿文本；解析 think 片段
3. `message.end` -> 固化 assistant 消息；isStreaming=false
4. `error` -> 会话流状态 error，结束 loading

成功结果：
- 右侧消息区实时滚动
- 左侧 loading 与会话状态一致

失败处理：
- 事件解析异常则丢弃单条事件，连接不中断

### 流程 D：会话切换与并发隔离
触发：用户点击左侧不同会话

步骤：
1. activeConversationId 切换
2. 若本地无消息则拉取后端历史
3. 已在流式中的其它会话连接保持

成功结果：
- 切换后显示对应会话消息
- 非当前会话继续后台流式

失败处理：
- 拉历史失败仅提示，不影响其它会话

### 流程 E：Think 展示
触发：delta 或 end 文本含 `<think>...</think>`

步骤：
1. 前端解析 think 与 normal 文本
2. think 持续写入 ThinkPanel（滚动）
3. 结束后自动折叠，可点击放大弹窗

成功结果：
- think 与正文分离显示
- think 支持 Markdown

失败处理：
- 无 think 标签时仅展示正文

## 3. 决策点
1. 是否存在 active 会话
2. 是否需要创建新会话
3. SSE 事件类型分支
4. think 解析模式（normal/think）
5. 本地消息是否命中缓存，决定是否请求后端

## 4. 异常分支
- CORS/网络错误：fetch 失败，流程短路并提示
- 后端 4xx/5xx：按接口错误展示
- provider 不可用：`/health` 可见状态 false
- SSE 中断：当前会话进入 done/error，不自动重连

---
Last updated from codebase on 2026-03-05
