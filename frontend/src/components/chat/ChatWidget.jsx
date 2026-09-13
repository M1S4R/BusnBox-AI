import React from 'react';
import { useChat } from '../../context/ChatContext';
import MessageList from './MessageList';
import SuggestionChips from './SuggestionChips';
import ChatInput from './ChatInput';
import { Sparkles, Bot } from 'lucide-react';

export default function ChatWidget() {
  const { messages, isLoading, sendMessage, rateResponse } = useChat();

  // Find the latest suggestions from the most recent assistant message
  const lastAssistantWithSuggestions = [...messages]
    .reverse()
    .find((m) => m.role === 'assistant' && Array.isArray(m.suggestions) && m.suggestions.length > 0);

  const activeSuggestions = lastAssistantWithSuggestions
    ? lastAssistantWithSuggestions.suggestions
    : [];

  return (
    <div className="chat-widget-container">
      {/* Widget Top Bar */}
      <div className="chat-header">
        <div className="chat-header-info">
          <div className="chat-avatar">
            <Bot size={20} />
          </div>
          <div>
            <div className="chat-title">Ask BnB</div>
            <div className="chat-subtitle">
              <span className="status-dot" />
              <span>AI Travel Concierge • Online</span>
            </div>
          </div>
        </div>
      </div>

      {/* Messages */}
      <MessageList
        messages={messages}
        isLoading={isLoading}
        onRate={rateResponse}
      />

      {/* Suggestion Chips */}
      {!isLoading && (
        <SuggestionChips
          suggestions={activeSuggestions}
          onSelect={(suggestionText) => sendMessage(suggestionText)}
        />
      )}

      {/* Chat Input */}
      <ChatInput
        onSend={sendMessage}
        disabled={isLoading}
      />
    </div>
  );
}
