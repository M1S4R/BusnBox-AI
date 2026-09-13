# BusNBox AI — Public API Reference

## Base URL
Default: `http://localhost:8000`

All public endpoints are versioned under `/api/v1`. Legacy endpoints under `/api` are maintained for backwards compatibility.

---

## 1. Endpoints

### 1.1 `POST /api/v1/chat`
Processes conversational search and travel questions.

#### Headers
- `Content-Type: application/json`
- `X-BusNBox-Key: <token>` *(Optional: required only if `BUSNBOX_API_KEY` is configured)*

#### Request Body
```json
{
  "message": "Find buses from Chennai to Bangalore tomorrow",
  "conversation_id": "session-4291-xyz",
  "tenant_key": "busnbox"
}
```

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `message` | `string` | **Yes** | User's natural language input (1–2000 chars). |
| `conversation_id` | `string` | No | Unique ID to maintain multi-turn context across messages. |
| `tenant_key` | `string` | No | Tenant identifier (default: `"busnbox"`). |

#### Success Response (`200 OK`)
```json
{
  "success": true,
  "response_id": "c92842e4-9fd4-4d82-b7ca-45e3f53835c2",
  "conversation_id": "session-4291-xyz",
  "answer_source": "inventory",
  "response_time_ms": 342.15,
  "reply": "I found 12 buses from Chennai to Bangalore for tomorrow.",
  "intent": "search_bus",
  "parameters": {
    "source": "Chennai",
    "destination": "Bangalore",
    "travel_date": "tomorrow",
    "filters": {}
  },
  "trips": [
    {
      "id": "mock-trip-001",
      "source": "Chennai",
      "destination": "Bangalore",
      "departure_time": "2026-09-14T05:30:00",
      "arrival_time": "2026-09-14T11:45:00",
      "operator": {
        "id": "operator-001",
        "name": "BusNBox Demo Travels"
      },
      "bus": {
        "id": "bus-001",
        "name": "Morning Star",
        "bus_type": "AC Sleeper",
        "registration_number": "TN-01-BNB-1001",
        "amenities": ["Charging Point", "Blanket", "Water Bottle"],
        "total_seats": 36
      },
      "price": "649.00",
      "available_seats": 24,
      "boarding_point": "Chennai",
      "dropping_point": "Bangalore",
      "booking_url": null
    }
  ],
  "recommendations": [
    {
      "id": "cheapest-mock-trip-003",
      "type": "cheapest",
      "trip_id": "mock-trip-003",
      "title": "Cheapest option",
      "reason": "Southern Roadways has the lowest available fare at ₹499.",
      "operator": "Southern Roadways"
    }
  ],
  "suggestions": [
    {
      "id": "only-ac",
      "label": "Only AC",
      "message": "Show only AC buses",
      "action": "apply_filter"
    },
    {
      "id": "cheapest-first",
      "label": "Cheapest first",
      "message": "Sort by cheapest",
      "action": "sort"
    }
  ],
  "sources": [],
  "grounding_confidence": null
}
```

---

### 1.2 `GET /api/v1/health`
Liveness probe to check if the FastAPI process is running.

#### Response (`200 OK`)
```json
{
  "success": true,
  "status": "healthy",
  "service": "BusNBox AI Backend",
  "version": "0.1.0"
}
```

---

### 1.3 `GET /api/v1/ready`
Readiness probe verifying that internal providers are configured.

#### Response (`200 OK`)
```json
{
  "success": true,
  "status": "ready",
  "service": "BusNBox AI Backend",
  "version": "0.1.0",
  "checks": {
    "ai_provider": "gemini",
    "inventory_provider": "mock",
    "service": "operational"
  }
}
```

---

## 2. Standardized Error Contract

All non-200 responses return a machine-readable JSON structure with standard error codes:

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

### Error Codes
| Code | HTTP Status | Description |
| :--- | :--- | :--- |
| `INVALID_REQUEST` | 400 | Request body is empty, malformed, or failed schema validation. |
| `UNAUTHORIZED` | 401 | Service API key was missing or invalid. |
| `TIMEOUT` | 408 | Upstream LLM or inventory service exceeded request deadline. |
| `AI_PROVIDER_UNAVAILABLE` | 503 | Gemini API is unreachable, exhausted, or failing. |
| `INVENTORY_UNAVAILABLE` | 503 | Company inventory API or mock provider is down. |
| `KNOWLEDGE_BASE_UNAVAILABLE` | 503 | RAG / FAQ retrieval encountered an unrecoverable fault. |
| `INTERNAL_ERROR` | 500 | Unhandled server exception (sanitized, no internal paths exposed). |
