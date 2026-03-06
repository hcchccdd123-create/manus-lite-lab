# Manus Lite Web (Vue3 + Vite)

## Run locally

```bash
cd /Users/cong/work/manus-lite-lab/web-vue3-vite
cp .env.example .env
npm install
npm run dev
```

Default backend URL is `http://127.0.0.1:8000`.

## Features

- Minimal split layout (left conversations, right chat panel)
- Session-isolated concurrent streaming
- Session-level loading indicator in sidebar
- Think panel with markdown rendering, mini preview, and centered zoom panel
- IndexedDB persistence for conversations, messages, and think states
- Draft mode + delayed reveal into conversation history
- Auto-follow message scrolling with manual pause/resume

## Next milestone (Agent Runtime UI)

- Add Chat/Agent runtime switch in composer area
- Visualize step events: `thinking`, `tool_call`, `tool_result`, `final_answer`
- Persist agent step events in local storage for refresh replay
