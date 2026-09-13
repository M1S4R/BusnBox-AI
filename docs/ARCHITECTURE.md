# BusNBox AI — Architecture Guide

## 1. System Overview

BusNBox AI is an **independently deployable AI travel-assistance module** designed to integrate with an enterprise company platform powered by **Spring Boot** and **React.js**.

BusNBox AI is **NOT** a standalone travel portal or booking engine. It acts as an intelligent conversational processing layer for travel inquiries.

```text
                    COMPANY ECOSYSTEM
        ┌───────────────────────────────────────┐
        │          React.js Frontend            │
        └───────────────────┬───────────────────┘
                            │ REST / Internal API
                            ▼
        ┌───────────────────────────────────────┐
        │       Spring Boot Backend Gateway     │
        └───────────────────┬───────────────────┘
                            │ REST (POST /api/v1/chat)
                            ▼
        ┌───────────────────────────────────────┐
        │        BusNBox AI Module (FastAPI)    │
        │                                       │
        │  • Intent Detection   • Route Engine  │
        │  • Date Engine        • Refinements   │
        │  • Conversation State • RAG / FAQ     │
        │  • Recommendations    • Gemini LLM    │
        └───────────────────┬───────────────────┘
                            │ HTTP
                            ▼
        ┌───────────────────────────────────────┐
        │       Company Inventory API           │
        └───────────────────┬───────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │          Company Database             │
        └───────────────────────────────────────┘
```

---

## 2. Ownership Boundaries

### What BusNBox AI Owns:
- Natural language query understanding and conversational multi-turn flow.
- Deterministic extraction and normalization of routes, dates, and filters.
- Travel search parameter refinement (sorting, budget constraints, operator/bus type preferences).
- Contextual recommendations and suggestion generation.
- Conversational state isolation keyed by `conversation_id`.
- Internal RAG and FAQ retrieval.
- Server-side Gemini model interactions.
- Normalized trip response formatting.

### What the Company Platform Owns:
- User accounts, authentication, and authorization.
- The company's primary React web and mobile applications.
- Spring Boot backend services and API gateways.
- Company databases (MariaDB, PostgreSQL, MySQL).
- Inventory scheduling, seat locking, reservations, ticketing, and booking confirmation.
- Payment processing (Razorpay, Stripe, payment gateways).
- Generation and lifecycle management of `conversation_id`.

---

## 3. Communication & Decoupling Principles

1. **No Direct Database Access**: BusNBox AI communicates with your inventory strictly via HTTP using the Inventory Adapter (`CompanyInventoryProvider`). BusNBox never queries the company database directly.
2. **Gemini is Internal**: Gemini API keys and prompts are encapsulated inside the BusNBox AI service. Neither the browser nor the Spring Boot gateway needs to interact directly with LLM APIs.
3. **Stateless Service with Memory Key**: BusNBox stores conversation memory in-memory keyed by `conversation_id`. When the company application starts a new search, it simply issues a new `conversation_id`.
4. **Resilient Fallbacks**: If external AI or inventory providers encounter downtime or rate limits, BusNBox returns clean, structured integration errors (`AI_PROVIDER_UNAVAILABLE`, `INVENTORY_UNAVAILABLE`, `TIMEOUT`) without crashing or exposing stack traces.
