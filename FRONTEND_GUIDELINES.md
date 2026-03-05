# FRONTEND_GUIDELINES.md

## 1. 设计语言
- 暗色极简、对话优先、弱装饰。
- 参考主流会话产品信息密度，但避免照搬无关功能。
- 优先保证可读性、状态可见性、滚动行为可控性。

## 2. 视觉 Token（当前实现）

### 颜色
- `--bg: #090b10`
- `--panel: #0f1117`
- `--panel-soft: #171a22`
- `--panel-elev: #1a1f2b`
- `--border: #262b36`
- `--border-soft: #202531`
- `--text: #e6e9ef`
- `--muted: #99a1b3`
- `--accent: #5b8cff`
- `--accent-2: #7aa2ff`
- `--danger: #f06a6a`

### 字体
- 正文：`'SF Pro Text', 'Segoe UI', 'Inter', sans-serif`
- 等宽：`'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace`

### 圆角与间距
- 圆角：8 / 10 / 12 / 14 px
- 间距：4 / 8 / 10 / 12 / 14 / 18 px

## 3. 布局与滚动规范
- 左栏固定宽度：`280px`。
- 右侧主区自适应。
- 允许滚动区域仅有：
  - `.conversation-list`
  - `.message-scroll`
  - `.think-mini-scroll`（缩略 Think 内部）
  - `.think-dock-content`（放大 Think 内容区）
- 禁止 `body` 滚动（`overflow: hidden`）。
- `message-scroll` 必须包含 `padding-bottom: 80px` 基础留白。

## 4. 组件规范

### Sidebar
- 展示品牌、Threads 标题、`+ New`、会话列表。
- 不显示 Automations/Skills 等当前范围外模块。

### ConversationItem
- 标题、更新时间、streaming spinner。
- 删除按钮位于标题行最右侧，在 `conversation-item` hover/focus-within 或按钮 focus 时显示。

### ChatPanel
- 顶部会话标题与 streaming 状态。
- 草稿态：右侧空白 + 输入框垂直居中。
- 会话态：消息区 + 底部输入框 + 缩略 Think 浮层（桌面）。
- 消息区支持自动滚底；用户手动上滚后暂停，并显示“恢复自动滚底”圆形悬浮按钮。

### Composer
- 输入框内右下角圆形发送按钮（上箭头图标）。
- 发送按钮左侧提供“深度思考”开关按钮（高亮表示开启）。
- Enter 发送，Shift+Enter 换行。

### ThinkPanel
- Think 基准内容尺寸：`400x400`。
- 缩略态视觉尺寸：`70x70`（通过 `scale(0.175)` 等比缩小）。
- 桌面定位：相对输入区容器绝对定位 `top:-50px; left:30px`。
- 仅保留“放大居中面板 / 回缩略”，不再提供展开/收起。
- 流式输出期间 Think 内容自动滚动到底部。
- 点击缩略后，Think 同一内容视图提升到 chat-panel 最高层级并上下左右居中（无遮罩层）。
- 开合动画参考 macOS Genie Effect（神奇灯）视觉风格。
- 放大面板首次打开必须滚动到底部。
- thinking 未结束时放大面板持续自动滚底；用户手动滚动后暂停自动滚底。
- 放大面板底部悬浮“回到底部”按钮，点击后恢复自动滚底。

## 5. 关键交互规范
- 默认新会话使用 `provider=glm`、`model=glm-4.7`。
- `+ New` 只进入草稿态，不立即创建历史会话项。
- 首发后 pending 会话仅在收到第一条流内容时进入左栏。
- 标题规则：首问 `trim + 压缩空白 + 前 20 字`。
- 多会话并发流式隔离：切换会话不影响其他会话连接。
- 删除会话使用 Element Plus 确认弹窗，样式必须覆盖为暗色体系。
- 缩略 Think 外透明区不可拦截指针事件，不得影响输入框点击与输入。
- 移动端（`<=980px`）隐藏缩略 Think，输入框左侧显示放大入口（仅有 think 内容时显示）。
- `message-scroll` 默认自动滚底；用户手动上滚后暂停自动滚底。
- 暂停期间消息区右下角显示恢复按钮，点击后恢复自动滚底并滚到底部。
- Deep Thinking 开关状态要透传到 `/api/v1/chat/stream` 的 `enable_thinking` 字段。

## 6. 滚动条规范
- 覆盖业务滚动容器：会话列表、消息区、think 缩略内容、think 放大区内容、业务 markdown code block。
- 风格：高对比蓝色（基于 `--accent` / `--accent-2`）。
- 交互：默认细条，hover/focus 加亮，active 再增强。
- 范围控制：仅作用在业务容器，避免无差别污染第三方组件滚动条。

## 7. Markdown 与安全
- assistant 正文与 think 文本都走 Markdown 渲染。
- 渲染前做 DOMPurify 净化，禁止脚本注入。

## 8. 响应式
- 断点：`max-width: 980px`。
- 小屏改为上下布局（上：左栏，下：聊天区）。

## 9. 禁止项
- 未样式化的原生按钮直接上线。
- 与 token 无关的随机色值扩散。
- 全页面滚动导致左栏/右栏双滚动冲突。
- 将 think 文本直接混排进 assistant 正文。

---
Last updated from codebase on 2026-03-06
