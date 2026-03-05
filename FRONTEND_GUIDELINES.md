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
  - `.think-content`（Think 内容区内部）
- 禁止 `body` 滚动（`overflow: hidden`）。

## 4. 组件规范

### Sidebar
- 展示品牌、Threads 标题、`+ New`、会话列表。
- 不显示 Automations/Skills 等当前范围外模块。

### ConversationItem
- 标题、更新时间、streaming spinner。
- 删除按钮位于标题行，仅 hover/active 显示。

### ChatPanel
- 顶部会话标题与 streaming 状态。
- 草稿态：右侧空白 + 输入框垂直居中。
- 会话态：ThinkPanel（可选）+ 消息区 + 底部输入框。

### Composer
- 输入框内右下角圆形发送按钮（上箭头图标）。
- Enter 发送，Shift+Enter 换行。

### ThinkPanel / ThinkModal
- Think 区固定高度、内部滚动。
- 流式中展开；完成后自动折叠。
- 支持弹窗放大查看 Markdown 内容。

## 5. 关键交互规范
- `+ New` 只进入草稿态，不立即创建历史会话项。
- 首发后 pending 会话仅在收到第一条流内容时进入左栏。
- 标题规则：首问 `trim + 压缩空白 + 前 20 字`。
- 多会话并发流式隔离：切换会话不影响其他会话连接。
- 删除会话使用 Element Plus 确认弹窗，样式必须覆盖为暗色体系。

## 6. Markdown 与安全
- assistant 正文与 think 文本都走 Markdown 渲染。
- 渲染前做 DOMPurify 净化，禁止脚本注入。

## 7. 响应式
- 断点：`max-width: 980px`。
- 小屏改为上下布局（上：左栏，下：聊天区）。

## 8. 禁止项
- 未样式化的原生按钮直接上线。
- 与 token 无关的随机色值扩散。
- 全页面滚动导致左栏/右栏双滚动冲突。
- 将 think 文本直接混排进 assistant 正文。

---
Last updated from codebase on 2026-03-05
