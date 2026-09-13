import React, { useState, useRef } from 'react';
import { Send } from 'lucide-react';

export default function ChatInput({
  onSend,
  disabled,
  placeholder = 'Ask BnB anything — Where are you travelling? (e.g. Chennai to Bangalore tomorrow)',
}) {
  const [text, setText] = useState('');
  const inputRef = useRef(null);

  const handleSubmit = (e) => {
    if (e) e.preventDefault();
    const trimmed = text.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setText('');
    inputRef.current?.focus();
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="chat-input-area">
      <form className="chat-input-form" onSubmit={handleSubmit}>
        <input
          ref={inputRef}
          id="chat-input-field"
          type="text"
          className="chat-text-input"
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled}
          autoComplete="off"
          aria-label="Ask BnB chat message input"
        />
        <button
          id="chat-send-btn"
          type="submit"
          className="send-btn"
          disabled={disabled || !text.trim()}
          title="Send message"
          aria-label="Send message"
        >
          <Send size={16} />
        </button>
      </form>
    </div>
  );
}
