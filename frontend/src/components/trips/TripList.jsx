import React, { useState } from 'react';
import { useChat } from '../../context/ChatContext';
import TripCard from './TripCard';
import BookingModal from './BookingModal';
import { MapPin, Calendar, Filter, Bus } from 'lucide-react';

export default function TripList() {
  const { trips, recommendations, activeParameters, sendMessage, isLoading } = useChat();
  const [selectedTrip, setSelectedTrip] = useState(null);

  const hasRoute = Boolean(activeParameters.source && activeParameters.destination);
  const travelDate = activeParameters.travel_date;

  // Build recommendation lookup: trip_id -> tag/reason
  const recLookup = {};
  if (Array.isArray(recommendations)) {
    recommendations.forEach((rec) => {
      const id = rec.trip_id || rec.trip?.id;
      if (id) {
        recLookup[id] = rec.badge || rec.type || rec.reason || 'Recommended';
      }
    });
  }

  return (
    <div>
      {/* Active Search Context Summary Card */}
      {hasRoute && (
        <div className="search-summary-card">
          <div className="summary-route">
            <MapPin size={20} color="var(--primary-600)" />
            <span>{activeParameters.source}</span>
            <span style={{ color: 'var(--text-subtle)' }}>→</span>
            <span>{activeParameters.destination}</span>
          </div>

          <div className="summary-details">
            {travelDate && (
              <div className="summary-tag">
                <Calendar size={14} />
                <span>{travelDate}</span>
              </div>
            )}
            <div style={{ display: 'flex', gap: '0.4rem' }}>
              <button
                className="suggestion-chip"
                onClick={() => sendMessage('only AC')}
              >
                Only AC
              </button>
              <button
                className="suggestion-chip"
                onClick={() => sendMessage('cheapest')}
              >
                Cheapest
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Results Section */}
      <div className="results-header">
        <div className="results-count">
          Available Buses {trips.length > 0 && <span>({trips.length})</span>}
        </div>
      </div>

      {trips.length > 0 ? (
        <div className="trips-container">
          {trips.map((trip) => (
            <TripCard
              key={trip.id}
              trip={trip}
              isRecommended={Boolean(recLookup[trip.id])}
              recommendationLabel={recLookup[trip.id]}
              onBook={(t) => setSelectedTrip(t)}
            />
          ))}
        </div>
      ) : (
        <div className="empty-state">
          <div style={{ width: 56, height: 56, background: 'var(--primary-100)', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 1rem', color: 'var(--primary-700)' }}>
            <Bus size={28} />
          </div>
          <h3 style={{ fontSize: '1.25rem', marginBottom: '0.5rem' }}>
            {hasRoute ? 'No buses match your exact criteria' : 'Ready to find your journey'}
          </h3>
          <p style={{ color: 'var(--text-muted)', maxWidth: 450, margin: '0 auto 1.5rem', fontSize: '0.9rem' }}>
            {hasRoute
              ? 'Try removing filters or asking Ask BnB for alternative travel dates.'
              : 'Type your route into Ask BnB (e.g. "I want to travel from Chennai to Bangalore tomorrow") to see live buses.'}
          </p>
          {!hasRoute && (
            <button
              className="book-btn"
              style={{ width: 'auto', margin: '0 auto', display: 'inline-block' }}
              onClick={() => sendMessage('Find buses from Chennai to Bangalore tomorrow')}
            >
              Search Chennai to Bangalore
            </button>
          )}
        </div>
      )}

      {/* Booking Modal */}
      {selectedTrip && (
        <BookingModal trip={selectedTrip} onClose={() => setSelectedTrip(null)} />
      )}
    </div>
  );
}
