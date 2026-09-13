# Troubleshooting & Integration FAQ

This document covers common integration questions and resolution steps.

---

## 1. Common Error Codes

### `INVALID_REQUEST` (`400 Bad Request`)
- **Cause**: Empty message string or JSON body failed validation.
- **Fix**: Ensure `{ "message": "..." }` is provided and is a non-empty string.

### `UNAUTHORIZED` (`401 Unauthorized`)
- **Cause**: `BUSNBOX_API_KEY` is configured on the backend, but the incoming request omitted or had an invalid `X-BusNBox-Key` or `Authorization: Bearer` header.
- **Fix**: Check `busnbox.api-key` in Spring Boot `application.yml` matches `BUSNBOX_API_KEY` in BusNBox `.env`.

### `AI_PROVIDER_UNAVAILABLE` (`503 Service Unavailable`)
- **Cause**: Gemini API key is missing, invalid, or rate-limited.
- **Fix**: Verify `GEMINI_API_KEY` in `.env`. Check that the key has quota in Google Cloud / Google AI Studio.

### `INVENTORY_UNAVAILABLE` (`503 Service Unavailable`)
- **Cause**: `INVENTORY_PROVIDER` is set to `company`, but `INVENTORY_API_BASE_URL` cannot be reached or timed out.
- **Fix**: Verify connectivity between BusNBox and your company inventory API. For local testing, switch to `INVENTORY_PROVIDER=mock`.

### `TIMEOUT` (`408 Request Timeout`)
- **Cause**: Gemini or the inventory API took longer than `REQUEST_TIMEOUT_SECONDS` (default: 30s) or `BUSNBOX_TIMEOUT` in Spring Boot.
- **Fix**: Increase timeout in `application.yml` (`busnbox.timeout: 15s`).

---

## 2. Multi-turn Context Questions

### Question: Why did BusNBox ask for the travel date again?
- **Cause**: The client sent a different `conversation_id` or omitted `conversation_id`.
- **Fix**: Ensure your Spring Boot gateway forwards the same `conversation_id` throughout a multi-turn conversation.

### Question: How do we reset context when the user wants to start over?
- **Answer**: Either issue a new `conversation_id` from the client or send a message containing `"New Search"` / `"start over"`.
