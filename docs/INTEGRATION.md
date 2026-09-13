# BusNBox AI — 5-Minute Integration Guide

Follow this guide to connect your company's Spring Boot backend and React frontend to BusNBox AI in under 5 minutes.

---

## Step 1: Start BusNBox AI

### Option A: Local Python
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Add your GEMINI_API_KEY to .env
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### Option B: Docker
```bash
docker build -t busnbox-ai .
docker run -p 8000:8000 -e GEMINI_API_KEY="your-gemini-key" busnbox-ai
```

---

## Step 2: Verify Health
```bash
curl http://localhost:8000/api/v1/health
# Response: {"success":true,"status":"healthy","service":"BusNBox AI Backend","version":"0.1.0"}
```

---

## Step 3: Configure Spring Boot

In your Spring Boot application's `application.yml`:

```yaml
busnbox:
  base-url: http://localhost:8000
  timeout: 10s
```

Copy the 4 reference client files from `examples/spring-boot/` into your project:
- `BusNBoxProperties.java`
- `BusNBoxClient.java`
- `BusNBoxRequest.java`
- `BusNBoxResponse.java`

---

## Step 4: Expose Gateway Endpoint in Spring Boot

```java
@RestController
@RequestMapping("/api/assistant")
public class ChatController {

    private final BusNBoxClient client;

    public ChatController(BusNBoxClient client) {
        this.client = client;
    }

    @PostMapping("/chat")
    public Mono<BusNBoxResponse> handleChat(
            @RequestParam(required = false) String conversationId,
            @RequestBody MessagePayload payload) {
        
        String sessionId = conversationId != null ? conversationId : UUID.randomUUID().toString();
        return client.chat(payload.getMessage(), sessionId);
    }
}
```

---

## Step 5: Test from React or Curl

### Initial Search
```bash
curl -X POST http://localhost:8080/api/assistant/chat?conversationId=my-test-session \
     -H "Content-Type: application/json" \
     -d '{"message": "Chennai to Bangalore tomorrow"}'
```

### Follow-up (Retains Route and Date)
```bash
curl -X POST http://localhost:8080/api/assistant/chat?conversationId=my-test-session \
     -H "Content-Type: application/json" \
     -d '{"message": "only AC"}'
```

You are now integrated!
