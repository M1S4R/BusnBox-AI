# React Frontend Integration Guide

The existing frontend located in `frontend/` serves as a **production-ready reference implementation**.

Your company development team has two integration paths:

---

## Option A: Company Builds Its Own UI (Recommended for Existing Apps)

If your company already has an established design system and React application:

1. **Route through Spring Boot**:
   ```javascript
   // src/api/assistant.js
   export async function sendMessage(message, conversationId) {
     const response = await fetch('/api/assistant/chat', {
       method: 'POST',
       headers: { 'Content-Type': 'application/json' },
       body: JSON.stringify({ message, conversation_id: conversationId }),
     });
     return await response.json();
   }
   ```

2. **Handle the Standard Response**:
   - `reply`: Show in the assistant's speech bubble.
   - `trips`: Render inside your company's standard trip card / list component.
   - `suggestions`: Render as clickable quick-reply chips.
   - `recommendations`: Highlight top picks (cheapest, earliest, best value).

---

## Option B: Reuse BusNBox UI Components

You can import or copy specific components from `frontend/src/components/`:

| Component | Path | Description |
| :--- | :--- | :--- |
| `ChatWidget` | `src/components/chat/ChatWidget.jsx` | Floating launcher + rounded chat dialog modal. |
| `MessageList` | `src/components/chat/MessageList.jsx` | Chat message bubbles with typing indicator. |
| `ChatInput` | `src/components/chat/ChatInput.jsx` | Natural text composer with auto-focus & loading states. |
| `TripCard` | `src/components/trips/TripCard.jsx` | High-contrast bus card with badges, operator, duration & price. |
| `SuggestionChips` | `src/components/chat/SuggestionChips.jsx` | Contextual chip carousel. |

### Environment Configuration
The reference frontend reads:
```bash
VITE_API_BASE_URL=http://localhost:8000
```
In your production company setup, point this to your Spring Boot gateway (e.g. `https://api.yourcompany.com`).
