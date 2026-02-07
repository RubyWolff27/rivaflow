import { useState, useEffect, useRef } from 'react';
import { Search, Plus, CheckCircle, AlertCircle } from 'lucide-react';
import { gymsApi } from '../api/client';

interface Gym {
  id: number;
  name: string;
  city?: string;
  state?: string;
  country: string;
  head_coach?: string;
  verified: boolean;
}

interface GymSelectorProps {
  value: string;
  onChange: (value: string, isCustom: boolean) => void;
  onCreateGym?: (gymName: string) => void;
  onGymSelected?: (gym: Gym) => void;
}

export default function GymSelector({ value, onChange, onCreateGym, onGymSelected }: GymSelectorProps) {
  const [gyms, setGyms] = useState<Gym[]>([]);
  const [searchQuery, setSearchQuery] = useState(value || '');
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [showCustomInput, setShowCustomInput] = useState(false);
  const [customGymName, setCustomGymName] = useState('');
  const wrapperRef = useRef<HTMLDivElement>(null);

  // Sync searchQuery with value prop when it changes (e.g., from profile default)
  useEffect(() => {
    if (value && value !== searchQuery) {
      setSearchQuery(value);
    }
  }, [value]);

  useEffect(() => {
    let cancelled = false;
    const doSearch = async () => {
      if (searchQuery.length >= 2) {
        setLoading(true);
        try {
          const response = await gymsApi.search(searchQuery, true);
          if (!cancelled) setGyms(response.data.gyms || []);
        } catch (error) {
          if (!cancelled) {
            console.error('Error searching gyms:', error);
            setGyms([]);
          }
        } finally {
          if (!cancelled) setLoading(false);
        }
      } else if (searchQuery.length === 0) {
        setLoading(true);
        try {
          const response = await gymsApi.list(true);
          if (!cancelled) setGyms(response.data.gyms || []);
        } catch (error) {
          if (!cancelled) {
            console.error('Error loading gyms:', error);
            setGyms([]);
          }
        } finally {
          if (!cancelled) setLoading(false);
        }
      }
    };
    doSearch();
    return () => { cancelled = true; };
  }, [searchQuery]);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const loadGyms = async () => {
    setLoading(true);
    try {
      const response = await gymsApi.list(true); // Only verified gyms
      setGyms(response.data.gyms || []);
    } catch (error) {
      console.error('Error loading gyms:', error);
      setGyms([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectGym = (gym: Gym) => {
    const gymName = [gym.name, gym.city, gym.state, gym.country]
      .filter(Boolean)
      .join(', ');
    setSearchQuery(gymName);
    onChange(gymName, false);

    // Notify parent with full gym object (for head coach auto-population)
    if (onGymSelected) {
      onGymSelected(gym);
    }

    setIsOpen(false);
  };

  const handleAddCustomGym = () => {
    if (!customGymName.trim()) return;

    onChange(customGymName.trim(), true);
    setSearchQuery(customGymName.trim());

    // Notify parent component to trigger verification flow
    if (onCreateGym) {
      onCreateGym(customGymName.trim());
    }

    setShowCustomInput(false);
    setCustomGymName('');
    setIsOpen(false);
  };

  const filteredGyms = gyms.filter(gym =>
    gym.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    gym.city?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    gym.state?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div ref={wrapperRef} className="relative">
      {/* Search Input */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5" style={{ color: 'var(--muted)' }} />
        <input
          type="text"
          className="input pl-10"
          value={searchQuery}
          onChange={(e) => {
            setSearchQuery(e.target.value);
            setIsOpen(true);
          }}
          onFocus={() => {
            setIsOpen(true);
            if (!searchQuery) loadGyms();
          }}
          placeholder="Search for your gym..."
          aria-label="Search gyms"
        />
      </div>

      {/* Dropdown */}
      {isOpen && (
        <div
          className="absolute z-50 mt-2 w-full rounded-[14px] shadow-lg max-h-80 overflow-y-auto"
          style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}
          role="listbox"
        >
          {loading ? (
            <div className="p-4 text-center text-sm" style={{ color: 'var(--muted)' }}>
              Loading gyms...
            </div>
          ) : filteredGyms.length > 0 ? (
            <>
              {filteredGyms.map((gym) => (
                <button
                  key={gym.id}
                  onClick={() => handleSelectGym(gym)}
                  className="w-full text-left px-4 py-3 hover:bg-[var(--surfaceElev)] transition-colors flex items-start justify-between"
                  role="option"
                  aria-selected={searchQuery === gym.name}
                >
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-sm" style={{ color: 'var(--text)' }}>
                        {gym.name}
                      </span>
                      {gym.verified && (
                        <CheckCircle className="w-4 h-4" style={{ color: 'var(--success)' }} />
                      )}
                    </div>
                    {(gym.city || gym.state || gym.country) && (
                      <span className="text-xs" style={{ color: 'var(--muted)' }}>
                        {[gym.city, gym.state, gym.country].filter(Boolean).join(', ')}
                      </span>
                    )}
                  </div>
                </button>
              ))}
              <div className="border-t" style={{ borderColor: 'var(--border)' }} />
            </>
          ) : searchQuery.length >= 2 ? (
            <div className="p-4 text-center text-sm" style={{ color: 'var(--muted)' }}>
              No gyms found matching "{searchQuery}"
            </div>
          ) : null}

          {/* Add Custom Gym Option */}
          {!showCustomInput ? (
            <button
              onClick={() => setShowCustomInput(true)}
              className="w-full text-left px-4 py-3 hover:bg-[var(--surfaceElev)] transition-colors flex items-center gap-2"
              style={{ color: 'var(--primary)' }}
            >
              <Plus className="w-4 h-4" />
              <span className="text-sm font-medium">Add a new gym</span>
            </button>
          ) : (
            <div className="p-4 border-t" style={{ borderColor: 'var(--border)' }}>
              <div className="flex items-start gap-2 mb-2">
                <AlertCircle className="w-4 h-4 mt-0.5" style={{ color: 'var(--warning)' }} />
                <p className="text-xs" style={{ color: 'var(--muted)' }}>
                  New gyms will be submitted for verification by our team
                </p>
              </div>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={customGymName}
                  onChange={(e) => setCustomGymName(e.target.value)}
                  placeholder="Enter gym name"
                  className="input flex-1 text-sm"
                  autoFocus
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') handleAddCustomGym();
                    if (e.key === 'Escape') setShowCustomInput(false);
                  }}
                  aria-label="New gym name"
                />
                <button
                  onClick={handleAddCustomGym}
                  disabled={!customGymName.trim()}
                  className="px-3 py-2 rounded-lg text-xs font-medium transition-colors"
                  style={{
                    backgroundColor: customGymName.trim() ? 'var(--primary)' : 'var(--surfaceElev)',
                    color: customGymName.trim() ? '#FFFFFF' : 'var(--muted)',
                    cursor: customGymName.trim() ? 'pointer' : 'not-allowed',
                  }}
                >
                  Add
                </button>
                <button
                  onClick={() => setShowCustomInput(false)}
                  className="px-3 py-2 rounded-lg text-xs font-medium transition-colors"
                  style={{ backgroundColor: 'var(--surfaceElev)', color: 'var(--text)' }}
                >
                  Cancel
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
