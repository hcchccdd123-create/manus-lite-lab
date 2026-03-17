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

## Current UI shape

- Composer keeps message input, send button, and Deep Thinking toggle
- Web search is handled automatically by the backend for supported models
- Current runtime is chat-only
