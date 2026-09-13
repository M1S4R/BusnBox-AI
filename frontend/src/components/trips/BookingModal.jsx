import React from 'react';
import { X, CheckCircle, ExternalLink, ShieldCheck, AlertCircle } from 'lucide-react';

export default function BookingModal({ trip, onClose }) {
  if (!trip) return null;

  const operatorName = trip.operator?.name || trip.operator || 'Bus Operator';
  const busType = trip.bus?.bus_type || trip.bus_type || 'Standard Coach';
  const price = trip.price ? `₹${trip.price}` : '₹--';
  const seats = trip.available_seats ?? trip.seats ?? 0;

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <ShieldCheck size={24} color="var(--primary-600)" />
            <h3 style={{ fontSize: '1.25rem' }}>Booking Details</h3>
          </div>
          <button className="close-modal-btn" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        <div style={{ background: 'var(--bg-subtle)', padding: '1.25rem', borderRadius: 'var(--radius-md)', marginBottom: '1.25rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
            <span style={{ fontWeight: 700, fontSize: '1.1rem' }}>{operatorName}</span>
            <span style={{ fontWeight: 800, fontSize: '1.25rem', color: 'var(--primary-700)' }}>{price}</span>
          </div>
          <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: '0.5rem' }}>
            {busType} • {seats} seats left
          </div>
          <div style={{ fontSize: '0.85rem', color: 'var(--text-main)' }}>
            Route: <strong>{trip.source}</strong> → <strong>{trip.destination}</strong>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem', background: '#ecfdf5', border: '1px solid #a7f3d0', padding: '1rem', borderRadius: 'var(--radius-md)', marginBottom: '1.5rem', alignItems: 'flex-start' }}>
          <AlertCircle size={20} color="#059669" style={{ flexShrink: 0, marginTop: 2 }} />
          <div style={{ fontSize: '0.82rem', color: '#065f46', lineHeight: 1.45 }}>
            <strong>Operator Booking Handoff:</strong> BusNBox AI is a search and discovery platform. Seat reservation and checkout are completed directly through the operator reservation desk.
          </div>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end' }}>
          <button
            onClick={onClose}
            style={{
              padding: '0.65rem 1.25rem',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border-light)',
              background: 'white',
              cursor: 'pointer',
              fontWeight: 600,
            }}
          >
            Cancel
          </button>
          <button
            onClick={onClose}
            style={{
              padding: '0.65rem 1.4rem',
              borderRadius: 'var(--radius-md)',
              border: 'none',
              background: 'var(--primary-600)',
              color: 'white',
              cursor: 'pointer',
              fontWeight: 600,
              display: 'flex',
              alignItems: 'center',
              gap: '0.4rem',
            }}
          >
            <span>Proceed to Operator Desk</span>
            <ExternalLink size={15} />
          </button>
        </div>
      </div>
    </div>
  );
}
