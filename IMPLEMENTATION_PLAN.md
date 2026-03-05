# IMPLEMENTATION_PLAN.md

## 1. 目标
从当前代码基线出发，持续迭代为“会话隔离、可持久化、具备 think 展示”的稳定会话应用。

## 2. 分阶段实施路线

### Phase 0：基线确认（已完成）
输入：现有前后端仓库
输出：可运行的本地联调环境
DoD：
- 后端 `uvicorn` 可启动
- 前端 `vite` 可启动
- health 接口可用

### Phase 1：后端核心闭环（已完成）
输入：FastAPI + SQLite
输出：会话/消息/流式/摘要闭环
DoD：
- 会话 CRUD 可用
- `/chat` 与 `/chat/stream` 可用
- `messages` 与 `provider_call_logs` 持久化

### Phase 2：前端核心闭环（已完成）
输入：Vue3 + Pinia
输出：会话列表、消息流、输入发送
DoD：
- 可创建会话并发消息
- 流式事件能实时渲染
- 左栏 loading 可跟随流状态

### Phase 3：Think + 持久化（进行中）
输入：SSE delta 文本
输出：think 分离展示 + IndexedDB 恢复
DoD：
- think 可滚动、折叠、弹窗
- 刷新后会话与消息可恢复
- think 状态可恢复

### Phase 4：草稿态交互（待完成）
输入：当前会话页面
输出：刷新默认空白态 + New 不立即建会话
DoD：
- 刷新不自动打开历史会话
- New 仅进入草稿态
- 首次发送后才创建会话
- 标题自动取首问前 20 字

### Phase 5：部署与稳定性（进行中）
输入：本地可运行系统
输出：OpenCloudOS 可部署版本
DoD：
- 部署脚本可执行
- systemd 服务可拉起
- `.env.prod.example` 与运行参数完整

## 3. 前后端联调步骤（标准流程）
1. 启动后端：`llm-python`
2. 启动前端：`web-vue3-vite`
3. 验证 `/health`
4. 前端创建会话并发起流式聊天
5. 检查左栏 loading、右侧增量输出
6. 切换会话验证并发隔离
7. 刷新页面验证持久化恢复

## 4. 测试矩阵

### 4.1 单元测试
- SSE 事件解析（含 `\r\n\r\n` 边界）
- think 标签跨 chunk 拆分
- store 会话隔离与状态更新

### 4.2 集成测试
- 会话创建 + 聊天
- 流式输出完整事件序列
- 历史消息查询
- 记忆摘要触发

### 4.3 手工冒烟
- 发送一条消息能出流
- 左栏 loading 正确
- 切换会话不串流
- think 面板可查看

## 5. 回归清单
- 草稿态（刷新默认空白）
- 会话并发隔离
- think 展示与折叠/弹窗
- IndexedDB 恢复
- CORS 正常

## 6. OpenCloudOS 部署步骤（后端）
1. 上传代码至服务器目录（建议 `/opt/manus-lite-chat/app`）
2. 创建 venv（建议 `/opt/manus-lite-chat/venv`）
3. 执行部署脚本：`scripts/deploy_opencloudos_backend.sh`
4. 配置 `.env`（基于 `.env.prod.example`）
5. 启动 `uvicorn` 或 systemd 服务

## 7. 环境变量清单（关键）
- `DB_URL`
- `DEFAULT_PROVIDER`
- `DEFAULT_MODEL_OLLAMA`
- `OLLAMA_BASE_URL`
- `GLM_API_KEY` / `GLM_BASE_URL`
- `CODEX_API_KEY` / `CODEX_BASE_URL`
- `MEMORY_WINDOW_SIZE`
- `SUMMARY_TRIGGER_MESSAGES`
- `ENABLE_PROVIDER_FALLBACK`

## 8. 当前优先级建议
1. 完成草稿态交互（刷新空白 + New 延迟建会话）
2. 固化 thinking 开关策略并验证 qwen3.5:0.8b 输出
3. 增加前端自动化测试覆盖关键交互

---
Last updated from codebase on 2026-03-05
