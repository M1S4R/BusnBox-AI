# BUSNBOX AI

**AI travel-assistance module for integration with existing Spring Boot + React applications.**

BusNBox AI is an independently deployable microservice providing natural language bus search, conversational multi-turn refinement, deterministic date/route extraction, and FAQ/RAG assistance.

---

## What BusNBox Does
- **Natural Language Route Parsing**: Extracts origins and destinations from natural phrasing (`Chennai to Bangalore`, `buses from Chennai`, `Chennai -> Bangalore`, arrow notation, typo tolerance).
- **Deterministic Date Resolution**: Resolves relative expressions (`tomorrow`, `day after tomorrow`, `next Monday`, `in a week`, ordinals `25th September`) anchored to UTC without LLM hallucinations.
- **Conversational Multi-Turn Search**: Retains search state across follow-ups (`only AC`, `cheapest`, `show Volvo`, `remove Volvo`).
- **Route & Date Corrections**: Allows in-flight changes (`Wait, change Bangalore to Hyderabad`) without losing unrelated context.
- **Trip Ranking & Recommendations**: Labels top options (cheapest, earliest departure, best value).
- **RAG & FAQ Support**: Answers policy and booking FAQs directly with source attribution.
- **Standardized Public API**: Versioned REST contract (`/api/v1/chat`, `/api/v1/health`, `/api/v1/ready`).

---

## What BusNBox Does NOT Do
- **NO Booking or Ticketing**: Seat reservation, ticket generation, and PNR issuance are owned by the company platform.
- **NO Payments**: Payment gateways, Razorpay, Stripe, and checkout are strictly owned by the company platform.
- **NO User Authentication**: User login, accounts, and session tokens belong to the company application.
- **NO Direct Database Access**: BusNBox does not query the company database directly; it communicates through the Inventory Adapter via HTTP.

---

## Architecture

```text
React.js Frontend (Company)
       │
       ▼ (Internal API / User Session)
Spring Boot Backend (Company Gateway)
       │
       ▼ REST (POST /api/v1/chat)
BusNBox AI Module (FastAPI)
       │
 ┌─────┼─────────────┐
 ▼     ▼             ▼
NLP   RAG    Inventory Adapter
                     │ HTTP
                     ▼
             Company Inventory API
                     │
                     ▼
             Company Database
```

---

## Quick Start (5 Minutes)

### 1. Run with Docker
```bash
docker build -t busnbox-ai .
docker run -p 8000:8000 -e GEMINI_API_KEY="your-key-here" busnbox-ai
```

### 2. Run with Python
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Set GEMINI_API_KEY in .env
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### 3. Verify Health
```bash
curl http://localhost:8000/api/v1/health
# Response: {"success":true,"status":"healthy","service":"BusNBox AI Backend","version":"0.1.0"}
```

---

## API Contract

### Chat Request (`POST /api/v1/chat`)
```json
{
  "message": "Find buses from Chennai to Bangalore tomorrow",
  "conversation_id": "user-session-1234"
}
```

### Chat Response (`200 OK`)
```json
{
  "success": true,
  "response_id": "uuid-here",
  "conversation_id": "user-session-1234",
  "intent": "search_bus",
  "reply": "I found 12 buses from Chennai to Bangalore for tomorrow.",
  "parameters": {
    "source": "Chennai",
    "destination": "Bangalore",
    "travel_date": "tomorrow",
    "filters": {}
  },
  "trips": [...],
  "recommendations": [...],
  "suggestions": [...]
}
```

### Standardized Error Format (`4xx` / `5xx`)
```json
{
  "success": false,
  "error": {
    "code": "INVENTORY_UNAVAILABLE",
    "message": "Bus availability is temporarily unavailable."
  },
  "detail": "Bus availability is temporarily unavailable."
}
```

See [docs/API.md](docs/API.md) for full endpoint specifications.

---

## Spring Boot Integration

A reference client is provided in [`examples/spring-boot/`](examples/spring-boot/):
- `BusNBoxProperties.java`
- `BusNBoxClient.java`
- `BusNBoxRequest.java`
- `BusNBoxResponse.java`

Add to `application.yml`:
```yaml
busnbox:
  base-url: ${BUSNBOX_BASE_URL:http://localhost:8000}
  timeout: ${BUSNBOX_TIMEOUT:10s}
```

See [docs/SPRING_BOOT.md](docs/SPRING_BOOT.md) for complete setup instructions.

---

## React Integration

- **Option A (Custom UI)**: Call your Spring Boot gateway from your existing React components.
- **Option B (Reusable Components)**: Reuse pre-built components from `frontend/src/components/` (`ChatWidget`, `TripCard`, `ChatInput`, `MessageList`, `SuggestionChips`).

See [docs/REACT.md](docs/REACT.md) for details.

---

## Inventory Integration

BusNBox AI searches inventory through an abstract adapter interface:
- **`mock`**: Runs entirely in-memory for development and automated testing.
- **`company`**: Connects via HTTP REST to your company inventory API.

Configure in `.env`:
```env
INVENTORY_PROVIDER=company
INVENTORY_API_BASE_URL=https://inventory.yourcompany.com
INVENTORY_API_SEARCH_PATH=/api/trips/search
```

See [docs/INVENTORY.md](docs/INVENTORY.md) for data schemas and customization.

---

## Configuration

| Variable | Default | Description |
| :--- | :--- | :--- |
| `AI_PROVIDER` | `gemini` | AI LLM provider (`gemini` or `ollama`). |
| `GEMINI_API_KEY` | `""` | Google Gemini API key (server-side only). |
| `INVENTORY_PROVIDER` | `mock` | Inventory provider (`mock` or `company`). |
| `INVENTORY_API_BASE_URL` | `http://127.0.0.1:9000` | Base URL of company inventory API. |
| `BUSNBOX_API_KEY` | `""` | Optional service-to-service key for `/api/v1/chat`. |
| `REQUEST_TIMEOUT_SECONDS` | `30` | Upstream request timeout. |

---

## Deployment

Deployable as a single Docker container or cloud service (Kubernetes, AWS ECS, GCP Cloud Run).

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).

---

## Testing

Run the full automated test suite:

### Backend Tests
```bash
cd backend
PYTHONPATH=.:.venv/lib/python3.13/site-packages /usr/bin/python3.13 -m pytest tests
```

### Frontend Tests
```bash
cd frontend
npm test -- --run
npm run build
```

---

## Troubleshooting

See [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) for common error codes, diagnostic checklists, and resolution steps.

---

## Documentation Index
- [Architecture Guide](docs/ARCHITECTURE.md)
- [Public API Reference](docs/API.md)
- [5-Minute Integration Guide](docs/INTEGRATION.md)
- [Spring Boot Integration](docs/SPRING_BOOT.md)
- [React Frontend Integration](docs/REACT.md)
- [Inventory Adapter Guide](docs/INVENTORY.md)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [Troubleshooting & FAQ](docs/TROUBLESHOOTING.md)
- [Spring Boot Reference Client](examples/spring-boot/README.md)
