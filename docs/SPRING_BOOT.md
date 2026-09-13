# Spring Boot Integration Guide

This guide details how to integrate BusNBox AI into an enterprise **Spring Boot** microservice.

---

## 1. Architectural Role

Spring Boot acts as the **Company API Gateway** and **Security Boundary**:

```text
React Client
    │
    ▼ (Authenticated User Session)
Spring Boot Application
    │
    │ Validates user token / session
    │ Resolves or creates conversation_id
    │ Calls BusNBox AI
    ▼
BusNBox AI Service (/api/v1/chat)
```

**Why route through Spring Boot?**
1. **Security**: Browser clients never have access to Gemini API keys or internal service networks.
2. **Session Ownership**: Spring Boot links authenticated user accounts to conversation sessions.
3. **Audit & Analytics**: Log, throttle, or monitor queries according to company compliance.

---

## 2. Dependency Setup

Add Spring WebFlux (for non-blocking `WebClient`):

### Maven (`pom.xml`)
```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-webflux</artifactId>
</dependency>
```

### Gradle (`build.gradle`)
```groovy
implementation 'org.springframework.boot:spring-boot-starter-webflux'
```

---

## 3. Configuration (`application.yml`)

```yaml
busnbox:
  base-url: ${BUSNBOX_BASE_URL:http://localhost:8000}
  timeout: ${BUSNBOX_TIMEOUT:10s}
  api-key: ${BUSNBOX_API_KEY:}
```

---

## 4. WebClient Bean Configuration

```java
@Configuration
public class BusNBoxConfig {

    @Bean
    public WebClient.Builder webClientBuilder() {
        return WebClient.builder();
    }
}
```

---

## 5. Using the Reference Client

Use the pre-built reference client provided in [`examples/spring-boot/`](../examples/spring-boot/):
- `BusNBoxProperties.java`
- `BusNBoxClient.java`
- `BusNBoxRequest.java`
- `BusNBoxResponse.java`

Inject `BusNBoxClient` into any service or controller:

```java
@Service
public class TravelAssistantService {

    private final BusNBoxClient client;

    public TravelAssistantService(BusNBoxClient client) {
        this.client = client;
    }

    public Mono<BusNBoxResponse> processUserMessage(String userId, String message, String conversationId) {
        // Enforce company session or rate limits here
        return client.chat(message, conversationId);
    }
}
```

---

## 6. Error Handling

BusNBox AI returns structured error payloads for 4xx and 5xx responses:

```json
{
  "success": false,
  "error": {
    "code": "INVENTORY_UNAVAILABLE",
    "message": "Bus availability is temporarily unavailable."
  }
}
```

The reference `BusNBoxClient` captures these responses automatically without throwing unhandled exceptions, allowing your API layer to return graceful fallback messages to the frontend.
