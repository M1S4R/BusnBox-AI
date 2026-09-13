import { describe, it, expect, beforeEach, vi } from 'vitest';
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import App from '../App';
import * as chatApi from '../api/chat';
import * as feedbackApi from '../api/feedback';

describe('Frontend Chat Flow and State Persistence', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  it('renders initial welcome message and suggestion chips', () => {
    render(<App />);
    expect(screen.getByText(/Ask BnB, your AI bus travel assistant/i)).toBeDefined();
    expect(screen.getAllByText(/Chennai to Bangalore tomorrow/i).length).toBeGreaterThanOrEqual(1);
  });

  it('sends chat message and preserves conversation_id', async () => {
    vi.spyOn(chatApi, 'sendChatMessage').mockResolvedValueOnce({
      success: true,
      response_id: 'resp-123',
      answer_source: 'inventory',
      response_time_ms: 50,
      reply: 'When would you like to travel?',
      intent: 'search_bus',
      conversation_id: 'conv-abc-789',
      parameters: { source: 'Chennai', destination: 'Bangalore', travel_date: null },
      trips: [],
      recommendations: [],
      suggestions: [{ id: 's-tomorrow', label: 'Tomorrow' }],
    });

    render(<App />);

    const input = screen.getByPlaceholderText(/Ask BnB anything/i);
    fireEvent.change(input, { target: { value: 'I want to travel from Chennai to Bangalore' } });
    fireEvent.click(screen.getByTitle(/Send message/i));

    await waitFor(() => {
      expect(screen.getByText('When would you like to travel?')).toBeDefined();
    });

    // Check conversation_id stored in localStorage
    expect(localStorage.getItem('bnb_conversation_id')).toBe('conv-abc-789');
  });

  it('clicking suggestion chip sends message', async () => {
    const chatSpy = vi.spyOn(chatApi, 'sendChatMessage').mockResolvedValueOnce({
      success: true,
      response_id: 'resp-456',
      reply: 'Looking up buses...',
      intent: 'search_bus',
      conversation_id: 'conv-101',
      parameters: { source: 'Chennai', destination: 'Bangalore', travel_date: 'tomorrow' },
      trips: [
        {
          id: 'trip-001',
          source: 'Chennai',
          destination: 'Bangalore',
          departure_time: '2026-07-23T06:00:00',
          arrival_time: '2026-07-23T12:00:00',
          price: '649.00',
          available_seats: 12,
          operator: { name: 'BusNBox Demo Travels' },
          bus: { bus_type: 'AC Sleeper', amenities: ['WiFi', 'Blanket'] },
        },
      ],
      recommendations: [
        { trip_id: 'trip-001', badge: 'Cheapest', reason: 'Lowest price' },
      ],
      suggestions: [],
    });

    render(<App />);

    const chips = screen.getAllByText('Chennai to Bangalore tomorrow');
    fireEvent.click(chips[0]);

    await waitFor(() => {
      expect(chatSpy).toHaveBeenCalled();
    });

    await waitFor(() => {
      expect(screen.getByText('BusNBox Demo Travels')).toBeDefined();
    });

    expect(screen.getAllByText('Cheapest').length).toBeGreaterThanOrEqual(1);
  });

  it('resets conversation when clicking New Search', async () => {
    localStorage.setItem('bnb_conversation_id', 'existing-conv-id');
    render(<App />);

    const resetBtn = screen.getByTitle(/Clear context and start a new search/i);
    fireEvent.click(resetBtn);

    expect(localStorage.getItem('bnb_conversation_id')).toBeNull();
  });

  it('allows user to submit thumbs up feedback', async () => {
    const feedbackSpy = vi.spyOn(feedbackApi, 'submitFeedback').mockResolvedValueOnce({
      success: true,
      feedback_id: 'fb-001',
    });

    vi.spyOn(chatApi, 'sendChatMessage').mockResolvedValueOnce({
      success: true,
      response_id: 'resp-789',
      reply: 'Here are the details.',
      conversation_id: 'conv-fb',
      trips: [],
      recommendations: [],
      suggestions: [],
    });

    render(<App />);

    const input = screen.getByPlaceholderText(/Ask BnB anything/i);
    fireEvent.change(input, { target: { value: 'How can I cancel my ticket?' } });
    fireEvent.click(screen.getByTitle(/Send message/i));

    await waitFor(() => {
      expect(screen.getByText('Here are the details.')).toBeDefined();
    });

    const thumbsUpBtn = screen.getByTitle(/Thumbs up - accurate and helpful/i);
    fireEvent.click(thumbsUpBtn);

    await waitFor(() => {
      expect(feedbackSpy).toHaveBeenCalledWith(
        expect.objectContaining({
          messageId: 'resp-789',
          rating: 'up',
        })
      );
    });
  });

  it('handles backend error cleanly without crashing the UI', async () => {
    vi.spyOn(chatApi, 'sendChatMessage').mockRejectedValueOnce(
      new Error('Unable to connect to BusNBox backend server.')
    );

    render(<App />);

    const input = screen.getByPlaceholderText(/Ask BnB anything/i);
    fireEvent.change(input, { target: { value: 'Chennai to Bangalore' } });
    fireEvent.click(screen.getByTitle(/Send message/i));

    await waitFor(() => {
      expect(screen.getByText(/Unable to connect to BusNBox backend server/i)).toBeDefined();
    });

    // Input should be re-enabled after error
    expect(input.hasAttribute('disabled')).toBe(false);
  });
});
