# Decisions - Voice Agent Scaffold

## Package Structure
- `@canard/shared` - types and utilities
- `@canard/agents` - agent loop, tools, memory
- Scope prefix: `@canard/`

## Type Strategy
- Shared types define ALL API contracts (request/response bodies)
- Agent types define AgentConfig, ConversationState, Message
- Shared exports utility functions (generateId, etc.)

## Build Strategy
- Each package uses TypeScript compiler (tsc) for build
- Next.js handles its own build
- Root scripts orchestrate workspace builds
