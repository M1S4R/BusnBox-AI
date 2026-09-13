import React from 'react';

export default function SuggestionChips({ suggestions, onSelect }) {
  if (!suggestions || suggestions.length === 0) return null;

  // Prefer 3-5 contextual suggestions (cap at 5 max to prevent UI clutter)
  const displaySuggestions = suggestions.slice(0, 5);

  return (
    <div className="chat-suggestions-area" role="group" aria-label="Suggested follow-up responses">
      {displaySuggestions.map((sug) => {
        const label = typeof sug === 'string' ? sug : sug.label;
        const msg = typeof sug === 'object' && sug.message ? sug.message : label;
        const id = (typeof sug === 'object' && sug.id) ? sug.id : label;
        return (
          <button
            key={id}
            type="button"
            className="suggestion-chip"
            onClick={() => onSelect(msg)}
            aria-label={`Ask: ${label}`}
          >
            {label}
          </button>
        );
      })}
    </div>
  );
}
