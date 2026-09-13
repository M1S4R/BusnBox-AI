import React, { useEffect, useRef } from 'react';
import MessageBubble from './MessageBubble';

export default function MessageList({ messages, isLoading, onRate }) {
  const bottomRef = useRef(null);

  useEffect(() => {
    if (typeof bottomRef.current?.scrollIntoView === 'function') {
      bottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isLoading]);

  return (
    <div className="messages-scroll">
      {messages.map((msg) => (
        <MessageBubble key={msg.id} message={msg} onRate={onRate} />
      ))}

      {isLoading && (
        <div className="typing-indicator" role="status" aria-live="polite">
          <div className="typing-dot" />
          <div className="typing-dot" />
          <div className="typing-dot" />
          <span className="typing-label">Finding buses...</span>
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  );
}
