import { apiClient } from './client';

export async function sendChatMessage({
  message,
  conversationId = null,
  tenantKey = 'busnbox',
}) {
  const payload = {
    message,
    tenant_key: tenantKey,
  };

  if (conversationId) {
    payload.conversation_id = conversationId;
  }

  return await apiClient('/api/chat', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}
