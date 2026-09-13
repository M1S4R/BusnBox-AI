import React from 'react';
import { ThumbsUp, ThumbsDown } from 'lucide-react';

export default function FeedbackButtons({ messageId, responseId, currentRating, onRate }) {
  return (
    <div className="feedback-container">
      <span style={{ fontSize: '0.7rem', color: 'var(--text-subtle)' }}>Helpful?</span>
      <button
        type="button"
        className={`feedback-btn ${currentRating === 'up' ? 'active' : ''}`}
        onClick={() => onRate(messageId, responseId, 'up')}
        title="Thumbs up - accurate and helpful"
      >
        <ThumbsUp size={12} />
      </button>
      <button
        type="button"
        className={`feedback-btn ${currentRating === 'down' ? 'active' : ''}`}
        onClick={() => onRate(messageId, responseId, 'down')}
        title="Thumbs down - inaccurate or unhelpful"
      >
        <ThumbsDown size={12} />
      </button>
    </div>
  );
}
