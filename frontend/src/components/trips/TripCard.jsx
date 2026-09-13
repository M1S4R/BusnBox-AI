import React from 'react';
import { Clock, Wifi, Zap, Award, Sparkles } from 'lucide-react';

function formatTime(val) {
  if (!val) return '--:--';
  if (typeof val === 'string' && val.includes('T')) {
    const d = new Date(val);
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false });
  }
  return String(val).slice(0, 5);
}

function formatDuration(val) {
  if (!val) return 'Direct';
  if (Array.isArray(val) && val.length === 2) {
    return `${val[0]}h ${val[1]}m`;
  }
  if (typeof val === 'string' && val.trim()) {
    return val;
  }
  return 'Direct';
}

export default function TripCard({ trip, isRecommended, recommendationLabel, onBook }) {
  const operatorName = trip.operator?.name || trip.operator || 'Bus Operator';
  const busName = trip.bus?.name || trip.bus_name || '';
  const busType = trip.bus?.bus_type || trip.bus_type || 'Standard Express';
  const depTime = formatTime(trip.departure_time || trip.departure);
  const arrTime = formatTime(trip.arrival_time || trip.arrival);
  const durationText = formatDuration(trip.duration);
  const seats = trip.available_seats ?? trip.seats ?? 0;
  const amenities = trip.bus?.amenities || trip.amenities || [];
  const price = trip.price ? `₹${trip.price}` : '₹--';

  // Recommendation Badge style
  let badgeClass = 'rec-badge badge-cheapest';
  let badgeIcon = <Sparkles size={12} />;
  const lowerLabel = (recommendationLabel || '').toLowerCase();
  if (lowerLabel.includes('fast')) {
    badgeClass = 'rec-badge badge-fastest';
    badgeIcon = <Clock size={12} />;
  } else if (lowerLabel.includes('rate') || lowerLabel.includes('top')) {
    badgeClass = 'rec-badge badge-top-rated';
    badgeIcon = <Award size={12} />;
  }

  return (
    <div className={`trip-card ${isRecommended ? 'featured' : ''}`}>
      {isRecommended && recommendationLabel && (
        <div className="badge-row">
          <span className={badgeClass}>
            {badgeIcon}
            <span>{recommendationLabel}</span>
          </span>
        </div>
      )}

      <div className="trip-main-row">
        {/* Operator Info */}
        <div className="operator-info">
          <h4>{operatorName}</h4>
          <div className="bus-type-tag">
            {busType} {busName ? `• ${busName}` : ''}
          </div>
        </div>

        {/* Times & Route */}
        <div className="trip-times">
          <div className="time-box">
            <div className="time">{depTime}</div>
            <div className="city">{trip.source}</div>
          </div>

          <div className="duration-line">
            <div className="duration-text">
              <Clock size={11} style={{ display: 'inline', marginRight: 3 }} />
              {durationText}
            </div>
            <div className="line-bar" />
          </div>

          <div className="time-box">
            <div className="time">{arrTime}</div>
            <div className="city">{trip.destination}</div>
          </div>
        </div>

        {/* Pricing & Booking */}
        <div className="trip-pricing">
          <div className="price-tag">{price}</div>
          <div className="seats-pill">{seats} seats available</div>
          <button
            id={`book-btn-${trip.id}`}
            className="book-btn"
            onClick={() => onBook(trip)}
          >
            Book Now
          </button>
        </div>
      </div>

      {amenities.length > 0 && (
        <div className="trip-amenities">
          {amenities.map((amenity, idx) => (
            <span key={idx} className="amenity-chip">
              {amenity}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
