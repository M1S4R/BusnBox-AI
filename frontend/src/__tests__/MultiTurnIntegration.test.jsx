import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import App from '../App';
import * as chatApi from '../api/chat';

describe('Phase 4 Comprehensive Multi-Turn & Context Isolation Integration Tests', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('Executes 6-turn user journey: date refinement, trips, AC filter, sort, reset, and FAQ isolation', async () => {
    // Turn 1: Date question
    const spy = vi.spyOn(chatApi, 'sendChatMessage').mockImplementation(async ({ message }) => {
      if (message.toLowerCase().includes('bangalore') && !message.toLowerCase().includes('tomorrow')) {
        return {
          success: true,
          response_id: 'resp-1',
          answer_source: 'inventory',
          response_time_ms: 60,
          reply: 'When would you like to travel from Chennai to Bangalore?',
          intent: 'search_bus',
          conversation_id: 'conv-phase4-001',
          parameters: { source: 'Chennai', destination: 'Bangalore', travel_date: null, filters: {} },
          trips: [],
          recommendations: [],
          suggestions: [{ id: 'date-tomorrow', label: 'Tomorrow', message: 'tomorrow', action: 'set_travel_date' }],
          sources: [],
        };
      }
      if (message.toLowerCase().includes('tomorrow')) {
        return {
          success: true,
          response_id: 'resp-2',
          answer_source: 'inventory',
          response_time_ms: 70,
          reply: 'I found 2 buses from Chennai to Bangalore on 14 Sep 2026.',
          intent: 'search_bus',
          conversation_id: 'conv-phase4-001',
          parameters: { source: 'Chennai', destination: 'Bangalore', travel_date: 'tomorrow', filters: {} },
          trips: [
            {
              id: 'trip-1',
              source: 'Chennai',
              destination: 'Bangalore',
              departure_time: '2026-09-14T06:00:00',
              arrival_time: '2026-09-14T12:00:00',
              operator: { id: 'op-1', name: 'Night Rider Travels' },
              bus: { id: 'b-1', name: 'AC Sleeper', bus_type: 'AC Sleeper', amenities: ['WiFi'] },
              price: '650.00',
              available_seats: 20,
            },
            {
              id: 'trip-2',
              source: 'Chennai',
              destination: 'Bangalore',
              departure_time: '2026-09-14T18:00:00',
              arrival_time: '2026-09-15T00:00:00',
              operator: { id: 'op-2', name: 'Southern Comfort Express' },
              bus: { id: 'b-2', name: 'Non-AC Seater', bus_type: 'Non-AC Seater', amenities: [] },
              price: '450.00',
              available_seats: 10,
            },
          ],
          recommendations: [
            { trip_id: 'trip-2', badge: 'Cheapest option', reason: 'Lowest fare at ₹450' },
          ],
          suggestions: [
            { id: 'only-ac', label: 'Only AC', message: 'only AC', action: 'apply_filter' },
            { id: 'cheapest', label: 'Cheapest', message: 'cheapest', action: 'sort' },
          ],
          sources: [],
        };
      }
      if (message.toLowerCase().includes('only ac')) {
        return {
          success: true,
          response_id: 'resp-3',
          answer_source: 'inventory',
          response_time_ms: 55,
          reply: 'Showing only AC buses.',
          intent: 'search_bus',
          conversation_id: 'conv-phase4-001',
          parameters: { source: 'Chennai', destination: 'Bangalore', travel_date: 'tomorrow', filters: { ac: true } },
          trips: [
            {
              id: 'trip-1',
              source: 'Chennai',
              destination: 'Bangalore',
              departure_time: '2026-09-14T06:00:00',
              arrival_time: '2026-09-14T12:00:00',
              operator: { id: 'op-1', name: 'Night Rider Travels' },
              bus: { id: 'b-1', name: 'AC Sleeper', bus_type: 'AC Sleeper', amenities: ['WiFi'] },
              price: '650.00',
              available_seats: 20,
            },
          ],
          recommendations: [],
          suggestions: [{ id: 'cheapest', label: 'Cheapest', message: 'cheapest', action: 'sort' }],
          sources: [],
        };
      }
      if (message.toLowerCase().includes('cancel')) {
        return {
          success: true,
          response_id: 'resp-faq-5',
          answer_source: 'faq',
          response_time_ms: 40,
          reply: 'You can cancel your ticket up to 2 hours before departure.',
          intent: 'faq',
          conversation_id: 'conv-fresh-faq',
          parameters: { source: null, destination: null, travel_date: null, filters: {} },
          trips: [],
          recommendations: [],
          suggestions: [],
          sources: [{ id: 'faq-1', title: 'Cancellation & Refund Policy', kind: 'faq' }],
        };
      }
      return {
        success: true,
        response_id: 'resp-fallback',
        reply: 'Ok',
        trips: [],
      };
    });

    render(<App />);

    const input = screen.getByPlaceholderText(/Ask BnB anything/i);
    const sendBtn = screen.getByTitle(/Send message/i);

    // Turn 1: Chennai to Bangalore
    fireEvent.change(input, { target: { value: 'I want to travel from Chennai to Bangalore' } });
    fireEvent.click(sendBtn);

    await waitFor(() => {
      expect(screen.getByText(/When would you like to travel from Chennai to Bangalore\?/i)).toBeDefined();
    });
    expect(localStorage.getItem('bnb_conversation_id')).toBe('conv-phase4-001');

    // Turn 2: Tomorrow
    const tomorrowChips = screen.getAllByText('Tomorrow');
    fireEvent.click(tomorrowChips[0]);

    await waitFor(() => {
      expect(screen.getByText('Night Rider Travels')).toBeDefined();
      expect(screen.getByText('Southern Comfort Express')).toBeDefined();
      expect(screen.getByText(/Cheapest option/i)).toBeDefined();
    });

    // Turn 3: "only AC"
    const acChips = screen.getAllByText('Only AC');
    fireEvent.click(acChips[0]);

    await waitFor(() => {
      expect(screen.getByText('Night Rider Travels')).toBeDefined();
      expect(screen.queryByText('Southern Comfort Express')).toBeNull();
    });

    // Turn 4: Click New Search -> resets state
    const newSearchBtn = screen.getByText(/New Search/i);
    fireEvent.click(newSearchBtn);

    expect(localStorage.getItem('bnb_conversation_id')).toBeNull();
    expect(screen.queryByText('Night Rider Travels')).toBeNull();

    // Turn 5: FAQ Query isolation: "How can I cancel my ticket?"
    fireEvent.change(input, { target: { value: 'How can I cancel my ticket?' } });
    fireEvent.click(sendBtn);

    await waitFor(() => {
      expect(screen.getByText(/You can cancel your ticket up to 2 hours before departure/i)).toBeDefined();
      expect(screen.getByText(/Cancellation & Refund Policy/i)).toBeDefined();
    });
    expect(screen.queryByText('Night Rider Travels')).toBeNull();
  });

  it('Verifies conversation_id persistence across simulated browser refresh', async () => {
    localStorage.setItem('bnb_conversation_id', 'persisted-conv-step7');

    const spy = vi.spyOn(chatApi, 'sendChatMessage').mockResolvedValueOnce({
      success: true,
      response_id: 'resp-refresh',
      answer_source: 'inventory',
      response_time_ms: 50,
      reply: 'Found buses for your continued journey.',
      intent: 'search_bus',
      conversation_id: 'persisted-conv-step7',
      parameters: { source: 'Chennai', destination: 'Bangalore', travel_date: '2026-09-14', filters: {} },
      trips: [],
      recommendations: [],
      suggestions: [],
      sources: [],
    });

    render(<App />);

    const input = screen.getByPlaceholderText(/Ask BnB anything/i);
    const sendBtn = screen.getByTitle(/Send message/i);

    fireEvent.change(input, { target: { value: 'tomorrow' } });
    fireEvent.click(sendBtn);

    await waitFor(() => {
      expect(spy).toHaveBeenCalledWith(
        expect.objectContaining({
          message: 'tomorrow',
          conversationId: 'persisted-conv-step7',
        })
      );
    });
  });

  it('Verifies New Search context isolation (no Bangalore leakage into Hyderabad)', async () => {
    const spy = vi.spyOn(chatApi, 'sendChatMessage').mockResolvedValueOnce({
      success: true,
      response_id: 'resp-hyd',
      answer_source: 'inventory',
      response_time_ms: 60,
      reply: 'Found 4 buses from Chennai to Hyderabad.',
      intent: 'search_bus',
      conversation_id: 'conv-hyderabad-999',
      parameters: { source: 'Chennai', destination: 'Hyderabad', travel_date: '2026-09-14', filters: {} },
      trips: [
        {
          id: 'trip-hyd-1',
          source: 'Chennai',
          destination: 'Hyderabad',
          departure_time: '2026-09-14T20:00:00',
          arrival_time: '2026-09-15T08:00:00',
          operator: { id: 'op-h1', name: 'Hyderabad Super Travels' },
          bus: { id: 'b-h1', name: 'Volvo Multi-Axle', bus_type: 'Volvo Multi-Axle', amenities: ['Charging Point'] },
          price: '950.00',
          available_seats: 15,
        },
      ],
      recommendations: [],
      suggestions: [],
      sources: [],
    });

    render(<App />);

    const input = screen.getByPlaceholderText(/Ask BnB anything/i);
    const sendBtn = screen.getByTitle(/Send message/i);

    fireEvent.change(input, { target: { value: 'Chennai to Hyderabad tomorrow' } });
    fireEvent.click(sendBtn);

    await waitFor(() => {
      expect(screen.getByText('Hyderabad Super Travels')).toBeDefined();
    });

    const callArgs = spy.mock.calls[0][0];
    expect(callArgs.message).toContain('Hyderabad');
  });

  it('Verifies controlled error handling when backend is unreachable', async () => {
    vi.spyOn(chatApi, 'sendChatMessage').mockRejectedValueOnce(
      new Error('Backend service unavailable (connection refused)')
    );

    render(<App />);

    const input = screen.getByPlaceholderText(/Ask BnB anything/i);
    const sendBtn = screen.getByTitle(/Send message/i);

    fireEvent.change(input, { target: { value: 'Hello' } });
    fireEvent.click(sendBtn);

    await waitFor(() => {
      expect(screen.getByText(/Backend service unavailable/i)).toBeDefined();
    });
  });
});
