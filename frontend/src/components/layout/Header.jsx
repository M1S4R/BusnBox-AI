import React from 'react';
import { useChat } from '../../context/ChatContext';
import { Bus, RotateCcw, Sparkles } from 'lucide-react';

export default function Header() {
  const { conversationId, resetConversation } = useChat();

  const handleNewSearch = () => {
    resetConversation();
    setTimeout(() => {
      document.getElementById('chat-input-field')?.focus();
    }, 50);
  };

  return (
    <header className="app-header">
      <div className="brand-container">
        <div className="brand-icon">
          <Bus size={22} />
        </div>
        <div>
          <h1 className="brand-title">
            BusN<span>Box</span>
          </h1>
        </div>
        <span className="brand-badge">
          <Sparkles size={12} style={{ display: 'inline', marginRight: 3 }} />
          AI Travel
        </span>
      </div>

      <div className="header-actions">
        {conversationId && (
          <div
            style={{
              fontSize: '0.75rem',
              color: 'var(--text-muted)',
              background: 'var(--bg-subtle)',
              padding: '0.3rem 0.7rem',
              borderRadius: 'var(--radius-full)',
              display: 'flex',
              alignItems: 'center',
              gap: '0.4rem',
            }}
          >
            <span className="status-dot" />
            <span>Session: {conversationId.slice(0, 8)}...</span>
          </div>
        )}

        <button
          id="new-search-btn"
          className="reset-btn"
          onClick={handleNewSearch}
          title="Clear context and start a new search"
          aria-label="Start a new search and clear context"
        >
          <RotateCcw size={14} />
          <span>New Search</span>
        </button>
      </div>
    </header>
  );
}
