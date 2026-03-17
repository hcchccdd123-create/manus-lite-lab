# IMPLEMENTATION_PLAN.md

## 1. 当前目标
在现有基线上持续稳定：
- 会话隔离流式对话
- Think 独立展示
- 草稿态 + 延迟入历史
- 可部署到 OpenCloudOS
- 收口为 Chat-only + 自动联网搜索

## 2. 分阶段执行（状态）

### Phase 0 - 基线可运行（已完成）
输入：项目目录与初始脚手架。
输出：前后端本地启动成功。
DoD：
- 后端 `uvicorn` 可启动
- 前端 `vite` 可启动
- `GET /api/v1/health` 可用

### Phase 1 - 后端聊天闭环（已完成）
输入：FastAPI + SQLite。
输出：会话、消息、流式聊天闭环。
DoD：
- 会话 CRUD 可用
- `/chat/stream` 可用
- 消息持久化可回放

### Phase 2 - 前端基础会话体验（已完成）
输入：Vue3 + Pinia。
输出：会话列表、消息区、输入发送。
DoD：
- 可发起会话聊天
- 流式消息可实时渲染
- 左栏 loading 与会话状态同步
- 删除按钮在 `conversation-item` hover 时可见

### Phase 3 - Think 与持久化（已完成）
输入：SSE 多事件流。
输出：ThinkPanel（缩略 + 居中放大）+ IndexedDB 持久化。
DoD：
- `message.thinking` 可实时展示
- think 可缩略展示与放大查看
- 刷新后会话/消息/think 可恢复
- message-scroll 自动滚底 + 手动接管 + 一键恢复可用

### Phase 4 - 草稿态与历史展示规则（已完成）
输入：现有会话交互。
输出：更接近 Manus 风格的会话创建行为。
DoD：
- 刷新默认草稿态
- `+ New` 不立即创建历史项
- 首发后 pending 会话仅在首条流内容到达时 reveal
- 标题取首问前 20 字

### Phase 5 - 稳定性与部署（进行中）
输入：本地可用版本。
输出：OpenCloudOS 可持续部署版本。
DoD：
- 部署脚本可执行
- systemd 服务可运行
- 生产环境变量模板完整
- 默认 Provider 切换为 GLM（`glm-4.7`）
- 输入区支持 Deep Thinking 开关并透传 `enable_thinking`
- 前端移除 Runtime / Web Search 控制面，仅保留 chat + Deep Thinking
- Think 缩略浮层（`70x70`）与居中放大交互稳定（含 Genie 风格开合动画）
- 全局业务滚动条样式统一且不污染第三方组件
- 支持联网搜索的模型自动获得 Web Search 能力；不支持的模型命中时效问题时返回标准提示，避免幻觉
- thinking loop guard 覆盖 GLM/Ollama，支持超时与重复止损并回传 `termination_reason`
- 回答末尾推荐 3 个追问（问候语/极短输入自动跳过）

## 3. 联调执行清单
1. 启动后端：`cd llm-python && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
2. 启动前端：`cd web-vue3-vite && npm run dev`
3. 验证 `GET /api/v1/health`
4. 草稿态发送首问，确认“首条流内容后才入左栏”
5. 并发测试：A 流式中切到 B 并发发送
6. 验证删除流程：hover 删除 -> 弹窗确认 -> 列表与本地数据同步
7. GLM 时效问题验证自动联网能力可用
8. Ollama/Codex 提问“今天股市/今天天气”时，后端应返回“不支持联网搜索”标准提示
9. thinking 压测触发 guard 时，`message.end.termination_reason` 与前端状态标签一致

## 4. 测试矩阵

### 单元测试
- SSE 解析（LF/CRLF 边界）
- think 解析状态机
- pending/reveal 状态机
- 联网意图识别（命中/漏判）与非联网 provider 防幻觉

### 集成测试
- 会话创建与消息落库
- 流式事件顺序
- 摘要触发与快照写入
- provider 错误映射
- 支持联网搜索的 provider 自动注入 Web Search tools
- 不支持联网搜索的 provider 命中时效问题时返回提示并结束

### 手工冒烟
- 草稿态居中输入
- 并发会话不串流
- Think 缩略展示与居中放大
- 刷新恢复与删除回退
- 删除按钮在整条 `conversation-item` hover 时可见
- Think 缩略模块不遮挡输入框/发送按钮
- 消息区底部留白在 100% / 125% / 150% 缩放下可读
- message-scroll 手动上滚后显示恢复按钮，点击后滚底并恢复自动滚动
- Deep Thinking 开关状态变化后，stream payload `enable_thinking` 同步
- 移动端输入框左侧 Think 入口可用
- 滚动条 hover/active 反馈与跨浏览器一致性
- 不再显示 Runtime / Web Search 控制按钮
- 不支持联网搜索的提示按普通 assistant 消息展示
- 触发 `thinking_timeout` / `thinking_guard_triggered` 时，顶部终止标签显示正确

## 5. 回归清单
- 草稿态入口（刷新 + New）
- 左栏 loading 与流状态一致
- 首条流内容 reveal 规则
- 删除弹窗视觉统一与行为正确
- IndexedDB 数据一致性
- 默认新会话 provider/model 为 `glm` / `glm-4.7`
- 缩略 Think 定位：`top:-50px; left:30px`
- 缩略 Think 外透明区不拦截 pointer 事件
- `message-scroll` `padding-bottom: 80px` 生效
- `message-scroll` 自动滚底暂停/恢复逻辑正确
- 业务滚动条蓝色细条 + hover 加亮；第三方组件不被污染
- 非联网 provider 的时效问题不会返回编造的“实时数据”

## 6. OpenCloudOS 部署步骤（后端）
1. 上传代码到目标目录（示例：`/opt/manus-lite-chat/app`）
2. 创建并激活虚拟环境（示例：`/opt/manus-lite-chat/venv`）
3. 安装依赖并配置 `.env`
4. 执行部署脚本：`scripts/deploy_opencloudos_backend.sh`
5. 用 systemd 管理服务并验证健康检查

## 7. 关键环境变量
- `DB_URL`
- `DEFAULT_PROVIDER`
- `GLM_MODEL`
- `DEFAULT_MODEL_OLLAMA`
- `OLLAMA_BASE_URL`
- `GLM_API_KEY` / `GLM_BASE_URL`
- `CODEX_API_KEY` / `CODEX_BASE_URL`
- `MEMORY_WINDOW_SIZE`
- `SUMMARY_TRIGGER_MESSAGES`
- `ENABLE_PROVIDER_FALLBACK`
- `APP_TIMEZONE`
- `THINKING_LOOP_MAX_SECONDS`

---
Last updated from codebase on 2026-03-06
