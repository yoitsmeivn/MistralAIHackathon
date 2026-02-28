# Learnings - Voice Agent Scaffold

## Environment
- Node v25.1.0, pnpm 10.27.0
- Fresh repo with just README.md
- macOS (darwin)

## Fastify Patterns (from Context7)
- Use generic route typing: `server.post<{ Body: BodyType, Reply: ReplyType }>('/path', ...)`
- Fastify v5 syntax with typed routes
- CORS via @fastify/cors plugin

## Next.js Patterns (from Context7)
- App Router with 'use client' directive for client components
- Server Components can fetch data directly
- Client components receive data as props, have access to state/effects

## Architecture Decisions
- pnpm workspaces monorepo
- packages/shared: types + utils (consumed by everything)
- packages/agents: agent loop logic (consumed by API service)
- services/api: Fastify backend
- apps/web: Next.js frontend
- In-memory session storage for hackathon simplicity
- All integrations via HTTP fetch (no SDKs)

## Foundation Layer Execution (Task 1)
- Root workspace files created: package.json scripts, pnpm-workspace.yaml, strict NodeNext tsconfig base, .env.example, .gitignore
- Shared package scaffolded as `@canard/shared` with API/message/STT contracts and utils (`generateId`, `formatTimestamp`, `delay`)
- Agents package scaffolded as `@canard/agents` with typed config/state/tool contracts, ToolRegistry, memory helpers, and Mistral-compatible raw fetch loop
- `callLlm` reads env vars at call-time to support test-time env mocking

## API Service Scaffold (Task)
- Created `services/api` Fastify app with CORS enabled globally and `PORT` defaulting to 3001.
- Added `POST /api/agent/text` route wired to `runAgentTurn` with in-memory `SessionStore` (`Map<string, ConversationState>`).
- Added `POST /api/agent/tts` route wired to raw ElevenLabs fetch and returns `audio/mpeg` buffer.
- Added `GET /health` route returning `{ status: "ok", timestamp }`.
- NodeNext relative imports in service source use `.js` extensions for runtime compatibility.
