# FRONTEND_GUIDELINES.md

## 1. 设计语言
- 风格：暗色极简、对话优先
- 参考：主流会话产品（左侧线程栏 + 右侧内容区）
- 原则：减少噪声、突出消息内容与输入动作

## 2. 视觉 Token

### 颜色（当前实现主色）
- `--bg: #090b10`
- `--panel: #0f1117`
- `--panel-soft: #171a22`
- `--panel-elev: #1a1f2b`
- `--border: #262b36`
- `--text: #e6e9ef`
- `--muted: #99a1b3`
- `--accent: #5b8cff`
- `--accent-2: #7aa2ff`

### 字体
- `'SF Pro Text', 'Segoe UI', 'Inter', sans-serif`
- 代码字体：`'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace`

### 圆角
- 小组件：8px~10px
- 气泡/输入区：12px~14px
- 容器：14px+

### 间距
- 基础 spacing：4 / 8 / 10 / 12 / 14 / 18 px

## 3. 布局规范
1. 左栏固定宽度（当前 280px）
2. 右侧主区自适应
3. 仅允许以下区域滚动：
   - 左侧会话列表 `.conversation-list`
   - 右侧消息区 `.message-scroll`
4. 页面 body 禁止滚动（`overflow: hidden`）

## 4. 组件规范

### Sidebar
- 包含品牌区、Threads 标题、New 按钮、会话列表
- 不展示无关模块（例如 Automations / Skills）

### ConversationItem
- 显示标题、时间、可选 loading 小圆点
- active 与 hover 状态明确

### ChatPanel
- 顶部标题 + streaming 状态
- 中部消息流
- 可选 ThinkPanel
- 底部 Composer

### Composer
- 输入框内嵌发送按钮（右下角）
- 发送按钮为圆形，中心上箭头图标
- Enter 发送，Shift+Enter 换行

### ThinkPanel / ThinkModal
- Think 固定高度滚动区
- 支持折叠/展开
- 支持弹窗放大

## 5. 交互规范
1. 会话隔离：每个会话独立流式状态
2. loading 绑定会话流状态，不全局共享
3. 流式中切换会话不打断原会话
4. Think 与正文分离渲染
5. Markdown 渲染必须经过安全净化

## 6. 响应式
- 断点：980px
- 小屏下改为上下分区（左栏在上，聊天区在下）

## 7. 禁止项
- 原生默认样式按钮直接上线
- 随机色值、无 token 命名的硬编码
- 全页面可滚动导致左右区域滚动冲突
- 把 think 内容直接混入正文造成阅读干扰

---
Last updated from codebase on 2026-03-05
