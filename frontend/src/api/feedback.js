import { apiClient } from './client';

export async function submitFeedback({
  messageId,
  conversationId = null,
  rating, // 'up' | 'down'
  reason = null,
  comment = null,
  intent = null,
}) {
  const payload = {
    message_id: messageId,
    rating,
  };

  if (conversationId) payload.conversation_id = conversationId;
  if (reason) payload.reason = reason;
  if (comment) payload.comment = comment;
  if (intent) payload.intent = intent;

  return await apiClient('/api/feedback', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}
