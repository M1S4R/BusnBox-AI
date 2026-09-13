import React from 'react';
import FeedbackButtons from './FeedbackButtons';
import { BookOpen, CheckCircle2, ShieldAlert } from 'lucide-react';

export default function MessageBubble({ message, onRate }) {
  const isUser = message.role === 'user';
  const isError = message.isError;

  return (
    <div
      className={`message-bubble ${isUser ? 'user-message' : 'assistant-message'}`}
      style={isError ? { background: '#fee2e2', color: '#991b1b', border: '1px solid #fecaca' } : {}}
    >
      <div style={{ whiteSpace: 'pre-line' }}>{message.text}</div>

      {/* Sources & Grounding */}
      {message.sources && message.sources.length > 0 && (
        <div style={{ marginTop: '0.6rem', borderTop: '1px solid var(--border-light)', paddingTop: '0.4rem' }}>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '0.3rem', marginBottom: '0.25rem' }}>
            <BookOpen size={12} />
            <span>Grounding Sources:</span>
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.3rem' }}>
            {message.sources.map((src, i) => (
              <span key={i} className="grounding-tag">
                {src.title || src.id}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Confidence Indicator */}
      {message.groundingConfidence !== undefined && message.groundingConfidence !== null && (
        <div style={{ fontSize: '0.7rem', color: 'var(--primary-700)', marginTop: '0.3rem', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
          <CheckCircle2 size={11} />
          <span>Confidence: {Math.round(message.groundingConfidence * 100)}%</span>
        </div>
      )}

      {/* Feedback Buttons for Assistant */}
      {!isUser && !isError && message.responseId && (
        <FeedbackButtons
          messageId={message.id}
          responseId={message.responseId}
          currentRating={message.userRating}
          onRate={onRate}
        />
      )}
    </div>
  );
}
