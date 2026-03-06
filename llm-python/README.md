# Manus Lite Chat Backend

## Quick start (dev)

```bash
cd /Users/cong/work/manus-lite-lab/llm-python
make install-dev
cp .env.example .env
make run
```

## Python virtual environment strategy

- Dev machine: use project-local venv `.venv/`
- Server (OpenCloudOS): use fixed path venv, recommended `/opt/manus-lite-chat/venv`
- Never use system Python site-packages for runtime dependencies
- Pin runtime by Python major/minor (`python3.11` preferred)
- Dependency install commands should always go through `.venv`, e.g. `make install-dev` or `.venv/bin/pip install ...`

## OpenCloudOS deployment (backend only)

1) Copy project to server, e.g. `/opt/manus-lite-chat/app`
2) Run deployment bootstrap script:

```bash
cd /opt/manus-lite-chat/app
bash scripts/deploy_opencloudos_backend.sh
```

3) Configure production env:

```bash
cp .env.prod.example .env
vim .env
```

4) (Optional but recommended) create systemd service using `deploy/manus-lite-chat.service`

5) Run service directly first for smoke test:

```bash
source /opt/manus-lite-chat/venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
```

## Notes

- SQLite database file default: `./data/chat.db`
- Default provider: GLM (`glm-4.7`)
- Configure `GLM_API_KEY` only in local `.env` or deployment secret manager; never hardcode or commit real keys.
- Default GLM base URL: `https://open.bigmodel.cn/api/paas/v4`
- Loop guard for thinking stream is enabled by default (`ENABLE_THINKING_LOOP_GUARD=true`)
- Stream endpoint: `POST /api/v1/chat/stream`
- API docs: `http://localhost:8000/docs`
- If you deploy frontend later, place build output in Nginx and reverse proxy `/api` to this service

## Next milestone (Agent Runtime)

- Product direction upgrades to local-first `Chat + Agent`.
- Agent loop target: `thinking -> tool_call -> tool_result -> final_answer`.
- Planned runtime safeguards:
  - `AGENT_ENABLED`
  - `AGENT_MAX_STEPS`
  - `AGENT_STEP_TIMEOUT_MS`
  - `TOOL_DEFAULT_TIMEOUT_MS`
- Suggested implementation order:
  1) add `agent` service layer and step models
  2) add tool registry and schema validation
  3) expose streaming events for step visualization
