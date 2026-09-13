import React, { createContext, useContext, useState, useEffect } from 'react';
import { sendChatMessage } from '../api/chat';
import { submitFeedback } from '../api/feedback';

const ChatContext = createContext(null);

const STORAGE_KEY_CONV_ID = 'bnb_conversation_id';
const STORAGE_KEY_MESSAGES = 'bnb_chat_messages';

const INITIAL_GREETING = {
  id: 'welcome-msg',
  role: 'assistant',
  text: "Hello! I'm Ask BnB, your AI bus travel assistant. Where would you like to travel?",
  timestamp: new Date().toISOString(),
  suggestions: [
    { id: 's1', label: 'Chennai to Bangalore tomorrow' },
    { id: 's2', label: 'Mumbai to Pune today' },
    { id: 's3', label: 'Delhi to Jaipur this weekend' },
  ],
};

export function ChatProvider({ children }) {
  const [conversationId, setConversationId] = useState(() => {
    return localStorage.getItem(STORAGE_KEY_CONV_ID) || null;
  });

  const [messages, setMessages] = useState(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY_MESSAGES);
      if (saved) {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed) && parsed.length > 0) return parsed;
      }
    } catch {
      // ignore parse error
    }
    return [INITIAL_GREETING];
  });

  const [trips, setTrips] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [activeParameters, setActiveParameters] = useState({
    source: null,
    destination: null,
    travel_date: null,
    filters: {},
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  // Sync to localStorage
  useEffect(() => {
    if (conversationId) {
      localStorage.setItem(STORAGE_KEY_CONV_ID, conversationId);
    } else {
      localStorage.removeItem(STORAGE_KEY_CONV_ID);
    }
  }, [conversationId]);

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY_MESSAGES, JSON.stringify(messages));
    } catch {
      // quota or serialization error
    }
  }, [messages]);

  const resetConversation = () => {
    setConversationId(null);
    localStorage.removeItem(STORAGE_KEY_CONV_ID);
    localStorage.removeItem(STORAGE_KEY_MESSAGES);
    setMessages([INITIAL_GREETING]);
    setTrips([]);
    setRecommendations([]);
    setActiveParameters({
      source: null,
      destination: null,
      travel_date: null,
      filters: {},
    });
    setError(null);
  };

  const sendMessage = async (text) => {
    if (!text || !text.trim() || isLoading) return;
    const cleanText = text.trim();
    setError(null);

    const userMsg = {
      id: `user-${Date.now()}`,
      role: 'user',
      text: cleanText,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);

    try {
      const response = await sendChatMessage({
        message: cleanText,
        conversationId: conversationId,
      });

      if (!response || typeof response !== 'object') {
        throw new Error('Invalid response received from server. Please try again.');
      }

      if (response.conversation_id && response.conversation_id !== conversationId) {
        setConversationId(response.conversation_id);
      }

      if (response.parameters) {
        setActiveParameters(response.parameters);
      }

      if (response.intent === 'clear_search') {
        setTrips([]);
        setRecommendations([]);
      } else if (response.intent === 'search_bus' && Array.isArray(response.trips)) {
        setTrips(response.trips);
      } else if (Array.isArray(response.trips) && response.trips.length > 0) {
        setTrips(response.trips);
      }

      if (response.intent !== 'clear_search' && Array.isArray(response.recommendations)) {
        setRecommendations(response.recommendations);
      }

      const assistantMsg = {
        id: response.response_id || `asst-${Date.now()}`,
        role: 'assistant',
        text: response.reply || 'I received your request but could not generate a response.',
        timestamp: new Date().toISOString(),
        responseId: response.response_id,
        intent: response.intent,
        parameters: response.parameters,
        trips: response.trips,
        recommendations: response.recommendations,
        suggestions: response.suggestions,
        sources: response.sources,
        groundingConfidence: response.grounding_confidence,
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      console.error('Chat error:', err);
      const errMsg = err.message || 'Something went wrong while processing your request.';
      setError(errMsg);

      const errorAsstMsg = {
        id: `err-${Date.now()}`,
        role: 'assistant',
        text: `⚠️ ${errMsg}`,
        timestamp: new Date().toISOString(),
        isError: true,
      };
      setMessages((prev) => [...prev, errorAsstMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const rateResponse = async (messageId, responseId, rating) => {
    try {
      await submitFeedback({
        messageId: responseId || messageId,
        conversationId: conversationId,
        rating,
      });

      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === messageId ? { ...msg, userRating: rating } : msg
        )
      );
    } catch (err) {
      console.error('Failed to submit feedback:', err);
    }
  };

  return (
    <ChatContext.Provider
      value={{
        conversationId,
        messages,
        trips,
        recommendations,
        activeParameters,
        isLoading,
        error,
        sendMessage,
        resetConversation,
        rateResponse,
      }}
    >
      {children}
    </ChatContext.Provider>
  );
}

export function useChat() {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error('useChat must be used within a ChatProvider');
  }
  return context;
}
