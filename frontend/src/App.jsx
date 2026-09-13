import React from 'react';
import { ChatProvider } from './context/ChatContext';
import Header from './components/layout/Header';
import HeroSection from './components/layout/HeroSection';
import TripList from './components/trips/TripList';
import ChatWidget from './components/chat/ChatWidget';

function AppContent() {
  return (
    <div className="app-layout">
      <Header />
      <main className="main-content">
        <section className="search-and-results">
          <HeroSection />
          <TripList />
        </section>
        <aside className="assistant-sidebar">
          <ChatWidget />
        </aside>
      </main>
    </div>
  );
}

export default function App() {
  return (
    <ChatProvider>
      <AppContent />
    </ChatProvider>
  );
}
