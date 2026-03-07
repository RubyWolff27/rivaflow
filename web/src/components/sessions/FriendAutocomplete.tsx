import { useState } from 'react';
import { X } from 'lucide-react';
import type { Friend } from '../../types';

interface FriendAutocompleteProps {
  label?: string;
  icon?: React.ReactNode;
  friends: Friend[];
  selected: string[];
  onAdd: (name: string) => void;
  onRemove: (name: string) => void;
  placeholder?: string;
  hint?: string;
}

export default function FriendAutocomplete({
  label,
  icon,
  friends,
  selected,
  onAdd,
  onRemove,
  placeholder = 'Type to search friends...',
  hint = 'Type to search friends, or enter any name and press Enter',
}: FriendAutocompleteProps) {
  const [input, setInput] = useState('');

  const addName = (name: string) => {
    const trimmed = name.trim();
    if (!trimmed || selected.includes(trimmed)) return;
    onAdd(trimmed);
    setInput('');
  };

  const query = input.trim().toLowerCase();
  const suggestions = query.length >= 1
    ? friends
        .filter(p => p.name && p.name.toLowerCase().includes(query) && !selected.includes(p.name))
        .slice(0, 6)
    : [];

  return (
    <div className="relative">
      {label && (
        <label className="label flex items-center gap-1.5">
          {icon}
          {label}
        </label>
      )}
      {selected.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mb-2">
          {selected.map((name, i) => (
            <span
              key={i}
              className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium"
              style={{ backgroundColor: 'rgba(59,130,246,0.1)', color: '#3B82F6' }}
            >
              {name}
              <button
                type="button"
                onClick={() => onRemove(name)}
                className="ml-0.5 hover:opacity-70"
              >
                <X className="w-3 h-3" />
              </button>
            </span>
          ))}
        </div>
      )}
      <input
        type="text"
        className="input text-sm"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={(e) => {
          if ((e.key === 'Enter' || e.key === ',') && input.trim()) {
            e.preventDefault();
            addName(input.replace(/,+$/, ''));
          }
        }}
        onBlur={() => {
          setTimeout(() => {
            if (input.trim()) {
              addName(input.replace(/,+$/, ''));
            }
          }, 200);
        }}
        placeholder={placeholder}
      />
      {suggestions.length > 0 && (
        <div
          className="absolute left-0 right-0 mt-1 rounded-lg overflow-hidden shadow-lg z-10"
          style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}
        >
          {suggestions.map((friend) => (
            <button
              key={friend.id}
              type="button"
              className="w-full text-left px-3 py-2 text-sm hover:bg-[var(--surfaceElev)] transition-colors"
              onMouseDown={(e) => {
                e.preventDefault();
                addName(friend.name);
              }}
            >
              <span className="font-medium text-[var(--text)]">{friend.name}</span>
              {friend.belt_rank && (
                <span className="text-xs text-[var(--muted)] ml-1.5">
                  ({friend.belt_rank} belt)
                </span>
              )}
            </button>
          ))}
        </div>
      )}
      {hint && <p className="text-xs text-[var(--muted)] mt-1">{hint}</p>}
    </div>
  );
}
