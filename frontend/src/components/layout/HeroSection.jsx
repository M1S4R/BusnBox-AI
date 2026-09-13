import React from 'react';
import { useChat } from '../../context/ChatContext';
import { Sparkles } from 'lucide-react';

const QUICK_ROUTES = [
  'Chennai to Bangalore tomorrow',
  'Chennai to Bangalore today',
  'Mumbai to Pune today',
  'Delhi to Jaipur this weekend',
];

export default function HeroSection() {
  const { sendMessage } = useChat();

  return (
    <div className="hero-banner">
      <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem', background: 'rgba(255,255,255,0.18)', padding: '0.25rem 0.75rem', borderRadius: 'var(--radius-full)', fontSize: '0.8rem', marginBottom: '1rem', fontWeight: 600 }}>
        <Sparkles size={14} color="#6ee7b7" />
        <span>Ask BnB Conversational Booking Assistant</span>
      </div>
      <h2 className="hero-title">Where would you like to travel?</h2>
      <p className="hero-subtitle">
        Search live inventory, filter by AC, operator, or sleeper, and ask anything in natural language.
      </p>

      <div className="hero-chips-bar">
        <span className="hero-chip-label">Quick Searches:</span>
        {QUICK_ROUTES.map((route) => (
          <button
            key={route}
            className="quick-chip"
            onClick={() => sendMessage(route)}
          >
            {route}
          </button>
        ))}
      </div>
    </div>
  );
}
