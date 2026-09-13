# Spring Boot Integration Reference for BusNBox AI

This directory provides a production-grade reference integration for Spring Boot applications communicating with the BusNBox AI module.

## Architecture

```text
React.js Frontend (Company)
       │
       ▼ REST (Internal API)
Spring Boot Gateway (Company)
       │
       ▼ REST (POST /api/v1/chat)
BusNBox AI Module (FastAPI)
```

---

## 1. Files Included

- `BusNBoxProperties.java`: Binds configuration properties under `busnbox.*` from `application.yml`.
- `BusNBoxRequest.java`: POJO representing the request payload (`message`, `conversation_id`, `tenant_key`).
- `BusNBoxResponse.java`: POJO representing the response model (`success`, `intent`, `parameters`, `trips`, `reply`, `error`).
- `BusNBoxClient.java`: Spring `WebClient` service wrapper handling request serialization, timeouts, and error code mapping.

---

## 2. Configuration (`application.yml`)

Add the following to your Spring Boot `application.yml` or `application.properties`:

```yaml
busnbox:
  base-url: ${BUSNBOX_BASE_URL:http://localhost:8000}
  timeout: ${BUSNBOX_TIMEOUT:10s}
  api-key: ${BUSNBOX_API_KEY:}
```

### Environment Variables
- `BUSNBOX_BASE_URL`: URL of your BusNBox FastAPI service (e.g. `http://busnbox-ai:8000` or `http://localhost:8000`).
- `BUSNBOX_TIMEOUT`: Maximum request duration (recommended: `10s` - `15s`).
- `BUSNBOX_API_KEY`: Optional service-to-service secret token matching `BUSNBOX_API_KEY` in BusNBox.

---

## 3. Example Spring MVC Controller

```java
package com.company.travel.controller;

import com.company.travel.busnbox.BusNBoxClient;
import com.company.travel.busnbox.BusNBoxResponse;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Mono;

import java.util.UUID;

@RestController
@RequestMapping("/api/assistant")
public class TravelAssistantController {

    private final BusNBoxClient busnboxClient;

    public TravelAssistantController(BusNBoxClient busnboxClient) {
        this.busnboxClient = busnboxClient;
    }

    @PostMapping("/chat")
    public Mono<ResponseEntity<BusNBoxResponse>> chat(
            @RequestParam(required = false) String conversationId,
            @RequestBody UserMessageRequest request) {

        // Company application manages or preserves conversationId
        String activeSessionId = (conversationId != null && !conversationId.isBlank())
                ? conversationId
                : UUID.randomUUID().toString();

        return busnboxClient.chat(request.getMessage(), activeSessionId)
                .map(response -> ResponseEntity.ok(response));
    }
}
```

---

## 4. Key Integration Rules

1. **Company application owns `conversation_id`**: Always pass the same `conversation_id` during follow-ups to maintain conversational state (route, date, filters).
2. **Never expose Gemini or internal BusNBox secrets to the browser**: All client requests from React go through the Spring Boot gateway.
3. **No direct database connection**: BusNBox does not require access to your MariaDB or PostgreSQL. It fetches availability through your company's inventory endpoint.
