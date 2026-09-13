# BusNBox AI — Agent Instructions

## Project Overview

BusNBox AI is an AI-powered travel and bus-assistance system.

The project is approximately 90% complete.

The existing project contains an established backend architecture and may contain
partial, incomplete, or missing frontend implementation.

The primary objective is to understand and preserve the existing architecture,
then complete the remaining work without unnecessarily rewriting working code.

---

# IMPORTANT OPERATING RULE

DO NOT immediately start coding.

The first task is RESEARCH and PROJECT AUDITING.

Before modifying any source code, thoroughly inspect the entire repository and
produce a detailed technical assessment.

Do not assume that a component is missing simply because it is not immediately
visible.

Do not replace existing implementations until you understand how they work.

Do not perform large refactors during the research phase.

---

# PHASE 1 — RESEARCH / AUDIT

During the research phase, inspect the complete repository.

You must inspect:

- Backend
- Frontend
- API routes
- Services
- AI layer
- LLM providers
- RAG system
- Database-related code
- Inventory integration
- Conversation management
- Chat logic
- Intent extraction
- Query refinement
- Recommendation system
- Authentication if present
- Configuration
- Environment configuration
- Tests
- Documentation
- Docker/container configuration if present
- CI/CD configuration if present
- Git branches and recent history
- Package/dependency configuration
- Static assets
- Frontend components
- Frontend API integration
- Error handling
- Logging
- Deployment configuration

Search the repository rather than relying only on directory names.

---

# SECURITY RULES

NEVER expose, print, copy, or report:

- API keys
- Gemini keys
- passwords
- database passwords
- access tokens
- JWT secrets
- OAuth secrets
- private credentials
- Cloudflare credentials
- .env secret values

You may inspect configuration structure and variable names, but redact secret
values in the final report.

Do not commit secrets.

Do not modify .env files unless explicitly instructed later.

---

# GIT SAFETY

Before making changes:

1. Check current branch.
2. Check git status.
3. Inspect available branches.
4. Inspect recent commits.
5. Determine which branch appears to contain the active development work.

During PHASE 1:

DO NOT:
- commit
- push
- reset
- rebase
- delete branches
- overwrite working code

The research phase must be read-only whenever possible.

---

# BACKEND TECHNOLOGY

The existing backend is expected to use technologies such as:

- Python
- FastAPI
- Pydantic
- Gemini / Google GenAI
- RAG
- MariaDB / database integration
- REST APIs
- pytest

However, DO NOT assume the exact implementation.

Verify everything from the repository.

---

# AI ARCHITECTURE

Pay special attention to the AI architecture.

Identify and document:

- AIService
- BaseLLMProvider
- GeminiProvider
- ProviderFactory
- IntentExtractor
- RAGService
- KnowledgeBaseService
- QueryRefinementService
- ConversationService
- RecommendationService
- SuggestionService
- ChatResponseService
- ToolDispatcher
- InventoryTool
- InventoryService

Determine:

1. Which components actually exist.
2. Which components are currently used.
3. Which components are legacy.
4. Which components are partially implemented.
5. Which components have tests.
6. Which components are currently broken.
7. Which components are unnecessarily duplicated.

---

# CHAT FLOW AUDIT

Trace the complete request lifecycle.

Document the actual flow:

User message
    ↓
API route
    ↓
FAQ detection
    ↓
conversation context
    ↓
AI / intent extraction
    ↓
parameter extraction
    ↓
deterministic validation
    ↓
query refinement
    ↓
conversation context update
    ↓
RAG or inventory search
    ↓
recommendation
    ↓
response generation
    ↓
frontend response

Do not assume this flow is correct.

Verify it from the source code.

Identify exactly where the actual implementation differs from the intended
architecture.

---

# DATE HANDLING AUDIT

Pay special attention to travel-date handling.

Test and inspect support for:

- today
- tomorrow
- day after tomorrow
- in N days
- this Monday
- next Monday
- this weekend
- next weekend
- DD/MM/YYYY
- DD-MM-YYYY
- YYYY-MM-DD
- month/day formats

Determine whether Gemini can incorrectly invent a date.

Determine whether deterministic backend date extraction overrides Gemini.

Determine whether conversation context preserves dates between messages.

Example conversation that MUST be understood:

User:
"I want to travel from Chennai to Bangalore"

Assistant:
"When would you like to travel?"

User:
"tomorrow"

Expected behavior:

source = Chennai
destination = Bangalore
travel_date = tomorrow
resolved date = actual next day
inventory search executes

The system must NOT repeatedly ask for the date.

---

# RAG AUDIT

Determine:

- How RAG retrieves knowledge.
- What knowledge sources exist.
- How documents are loaded.
- How chunks are created.
- How embeddings/retrieval work.
- Which LLM provider RAG uses.
- Whether RAG still contains legacy Ollama logic.
- Whether Gemini is used correctly.
- How grounding is handled.
- How sources are returned.
- What tests exist.

Identify any remaining Ollama-specific code if Gemini is now the intended
provider.

---

# FRONTEND AUDIT

The frontend is important.

Determine:

1. Whether a frontend already exists.
2. Which framework is used.
3. Whether it is React/Vite/Next/etc.
4. Existing folder structure.
5. Existing components.
6. Existing pages.
7. Existing styling system.
8. API integration.
9. Chat UI implementation.
10. Bus search UI.
11. Trip cards.
12. Recommendations.
13. Loading states.
14. Error states.
15. Responsive/mobile behavior.
16. Environment configuration.
17. Whether the frontend is incomplete or completely missing.

If the frontend is missing, DO NOT immediately create it during PHASE 1.

Instead document:

- what frontend needs to be built
- recommended structure
- required API integrations
- required screens/components
- backend endpoints available for integration

---

# EXISTING DESIGN DIRECTION

The intended BusNBox AI assistant interface should feel like a modern travel
assistant.

The AI assistant UI should support:

- floating AI/chat launcher
- rounded chat panel
- BusNBox/BNB AI branding
- green visual identity
- rounded suggestion chips
- trip cards
- clean message bubbles
- bottom message input
- responsive mobile layout

Do not invent a completely different product direction.

If an existing frontend/design is present, inspect it and preserve it unless
there is a clear reason to change it.

---

# TESTING

Run the existing test suite where possible.

Record:

- total tests
- passed
- failed
- skipped
- errors
- warnings

Do not modify tests merely to make them pass.

If tests fail, determine whether:

- implementation is wrong
- test is outdated
- dependency is missing
- environment is incorrect
- external service is unavailable

---

# API AUDIT

Document all important API endpoints.

For each endpoint report:

- HTTP method
- path
- purpose
- request schema
- response schema
- authentication requirements
- dependencies
- current status
- test coverage

Pay particular attention to:

- /api/chat
- /api/health
- inventory endpoints
- AI endpoints
- debugging endpoints
- authentication endpoints

---

# DATABASE AUDIT

If database code exists, inspect:

- models
- schemas
- migrations
- connection handling
- repositories
- services
- queries
- configuration

Determine whether the AI backend directly accesses the database or communicates
through another service/API.

Do not change the database during the research phase.

---

# DEPLOYMENT AUDIT

Determine how the project is currently expected to run.

Inspect:

- local development commands
- environment variables
- Docker
- Docker Compose
- Cloudflare configuration
- ports
- frontend/backend communication
- production configuration
- CORS
- build commands

Document any differences between development and production.

---

# CODE QUALITY AUDIT

Look for:

- dead code
- duplicate classes
- duplicate functions
- unused imports
- legacy implementations
- TODOs
- FIXME comments
- inconsistent naming
- circular dependencies
- unnecessary complexity
- hardcoded values
- error handling problems
- security problems
- race conditions
- state management problems

Do not fix them yet.

Report them.

---

# REQUIRED RESEARCH REPORT

At the end of PHASE 1, produce ONE structured report.

Use exactly this structure:

## 1. Executive Summary

Explain what BusNBox currently contains and how complete it actually is.

## 2. Current Architecture

Show the architecture as a diagram.

Example:

Frontend
   ↓
FastAPI
   ↓
Chat API
   ↓
AIService
   ↓
Gemini
   ↓
Intent / Parameters
   ↓
Conversation + Refinement
   ↓
Inventory
   ↓
Recommendations
   ↓
Response

Use the ACTUAL architecture discovered in the repository.

## 3. Repository Structure

Show the important folders/files and explain their purpose.

## 4. Backend Status

For every major backend component:

| Component | Exists | Working | Tested | Notes |
|-----------|--------|---------|--------|-------|

## 5. AI Architecture

Explain the complete AI/LLM architecture.

## 6. Chat Flow

Explain the complete request lifecycle.

## 7. Date Handling

Explain exactly how date extraction, validation, context persistence and
resolution currently work.

Include any bugs discovered.

## 8. RAG

Explain the RAG implementation and identify legacy or broken pieces.

## 9. API Endpoints

Provide a table of important endpoints.

## 10. Frontend Status

Clearly state:

- frontend exists / does not exist
- framework
- completion level
- existing components
- missing components
- API integration status

## 11. Testing Results

Report actual test results.

## 12. Known Bugs

Rank bugs:

### Critical
### High
### Medium
### Low

## 13. Missing Features

List features required to finish the project.

## 14. Technical Debt

List technical debt that should be addressed.

## 15. Security Issues

List security issues without exposing secrets.

## 16. Recommended Development Order

Give a logical implementation sequence.

Example:

1. Fix blocking backend bugs
2. Stabilize chat flow
3. Complete booking/action flow
4. Complete RAG
5. Build frontend
6. Integrate frontend/backend
7. E2E testing
8. Production hardening

Use the actual project state to determine the order.

## 17. Frontend Development Plan

If frontend is missing/incomplete, provide a detailed frontend implementation
plan including:

- framework
- folder structure
- pages
- components
- state management
- API client
- chat interface
- trip cards
- recommendation UI
- responsive design
- loading/error states
- environment configuration

## 18. Final Completion Estimate

Give an honest estimate:

Backend: XX%
Frontend: XX%
Integration: XX%
Testing: XX%
Overall: XX%

Explain how you arrived at the estimate.

---

# MOST IMPORTANT

PHASE 1 IS RESEARCH ONLY.

DO NOT start implementing the recommendations.

DO NOT rewrite the project.

DO NOT create a new architecture simply because you prefer it.

Understand the existing system first.

After producing the report, STOP.

Wait for further instructions.
