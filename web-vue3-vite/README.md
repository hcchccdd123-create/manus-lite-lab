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
- Think panel with markdown rendering, collapse, and modal zoom
- IndexedDB persistence for conversations, messages, and think states
