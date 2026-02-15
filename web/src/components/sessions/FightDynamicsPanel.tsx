import { ChevronDown, ChevronUp, Swords, Shield, Plus, Minus } from 'lucide-react';

interface FightDynamicsData {
  attacks_attempted: number;
  attacks_successful: number;
  defenses_attempted: number;
  defenses_successful: number;
}

interface FightDynamicsPanelProps {
  data: FightDynamicsData;
  expanded: boolean;
  onToggle: () => void;
  onIncrement: (field: keyof FightDynamicsData) => void;
  onDecrement: (field: keyof FightDynamicsData) => void;
  onChange: (field: keyof FightDynamicsData, value: number) => void;
}

export default function FightDynamicsPanel({
  data,
  expanded,
  onToggle,
  onIncrement,
  onDecrement,
  onChange,
}: FightDynamicsPanelProps) {
  return (
    <div className="border-t border-[var(--border)] pt-4">
      <button
        type="button"
        onClick={onToggle}
        className="flex items-center justify-between w-full text-left"
      >
        <div>
          <h3 className="font-semibold text-lg flex items-center gap-2">
            <Swords className="w-5 h-5" style={{ color: 'var(--accent)' }} />
            Fight Dynamics
            <span className="text-xs font-normal px-2 py-0.5 rounded-full" style={{ backgroundColor: 'var(--surfaceElev)', color: 'var(--muted)' }}>
              optional
            </span>
          </h3>
          <p className="text-xs mt-0.5" style={{ color: 'var(--muted)' }}>For comp prep — track attacks and defences</p>
        </div>
        {expanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
      </button>

      {expanded && (
        <div className="mt-4 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            {/* Attack Column */}
            <div className="p-3 rounded-lg" style={{ backgroundColor: 'rgba(255, 77, 45, 0.08)', border: '1px solid rgba(255, 77, 45, 0.2)' }}>
              <h4 className="text-sm font-semibold mb-3 flex items-center gap-1" style={{ color: 'var(--accent)' }}>
                <Swords className="w-4 h-4" />
                ATTACK
              </h4>
              <div className="space-y-3">
                <div>
                  <label className="text-xs font-medium mb-1 block" style={{ color: 'var(--muted)' }}>Attempted</label>
                  <div className="flex items-center gap-2">
                    <button type="button" onClick={() => onDecrement('attacks_attempted')} className="w-11 h-11 rounded-lg flex items-center justify-center font-bold" style={{ backgroundColor: 'var(--surfaceElev)', border: '1px solid var(--border)' }}>
                      <Minus className="w-4 h-4" />
                    </button>
                    <input
                      type="number"
                      className="input text-center font-bold text-lg flex-1"
                      value={data.attacks_attempted}
                      onChange={(e) => onChange('attacks_attempted', parseInt(e.target.value) || 0)}
                      min="0"
                    />
                    <button type="button" onClick={() => onIncrement('attacks_attempted')} className="w-11 h-11 rounded-lg flex items-center justify-center font-bold" style={{ backgroundColor: 'var(--accent)', color: '#fff' }}>
                      <Plus className="w-4 h-4" />
                    </button>
                  </div>
                </div>
                <div>
                  <label className="text-xs font-medium mb-1 block" style={{ color: 'var(--muted)' }}>Successful</label>
                  <div className="flex items-center gap-2">
                    <button type="button" onClick={() => onDecrement('attacks_successful')} className="w-11 h-11 rounded-lg flex items-center justify-center font-bold" style={{ backgroundColor: 'var(--surfaceElev)', border: '1px solid var(--border)' }}>
                      <Minus className="w-4 h-4" />
                    </button>
                    <input
                      type="number"
                      className="input text-center font-bold text-lg flex-1"
                      value={data.attacks_successful}
                      onChange={(e) => onChange('attacks_successful', parseInt(e.target.value) || 0)}
                      min="0"
                      max={data.attacks_attempted}
                    />
                    <button type="button" onClick={() => onIncrement('attacks_successful')} className="w-11 h-11 rounded-lg flex items-center justify-center font-bold" style={{ backgroundColor: 'var(--accent)', color: '#fff' }}>
                      <Plus className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
              {data.attacks_attempted > 0 && (
                <p className="text-xs font-semibold mt-2 text-center" style={{ color: 'var(--accent)' }}>
                  {Math.round((data.attacks_successful / data.attacks_attempted) * 100)}% success
                </p>
              )}
            </div>

            {/* Defence Column */}
            <div className="p-3 rounded-lg" style={{ backgroundColor: 'rgba(0, 149, 255, 0.08)', border: '1px solid rgba(0, 149, 255, 0.2)' }}>
              <h4 className="text-sm font-semibold mb-3 flex items-center gap-1" style={{ color: '#0095FF' }}>
                <Shield className="w-4 h-4" />
                DEFENCE
              </h4>
              <div className="space-y-3">
                <div>
                  <label className="text-xs font-medium mb-1 block" style={{ color: 'var(--muted)' }}>Attempted</label>
                  <div className="flex items-center gap-2">
                    <button type="button" onClick={() => onDecrement('defenses_attempted')} className="w-11 h-11 rounded-lg flex items-center justify-center font-bold" style={{ backgroundColor: 'var(--surfaceElev)', border: '1px solid var(--border)' }}>
                      <Minus className="w-4 h-4" />
                    </button>
                    <input
                      type="number"
                      className="input text-center font-bold text-lg flex-1"
                      value={data.defenses_attempted}
                      onChange={(e) => onChange('defenses_attempted', parseInt(e.target.value) || 0)}
                      min="0"
                    />
                    <button type="button" onClick={() => onIncrement('defenses_attempted')} className="w-11 h-11 rounded-lg flex items-center justify-center font-bold" style={{ backgroundColor: '#0095FF', color: '#fff' }}>
                      <Plus className="w-4 h-4" />
                    </button>
                  </div>
                </div>
                <div>
                  <label className="text-xs font-medium mb-1 block" style={{ color: 'var(--muted)' }}>Successful</label>
                  <div className="flex items-center gap-2">
                    <button type="button" onClick={() => onDecrement('defenses_successful')} className="w-11 h-11 rounded-lg flex items-center justify-center font-bold" style={{ backgroundColor: 'var(--surfaceElev)', border: '1px solid var(--border)' }}>
                      <Minus className="w-4 h-4" />
                    </button>
                    <input
                      type="number"
                      className="input text-center font-bold text-lg flex-1"
                      value={data.defenses_successful}
                      onChange={(e) => onChange('defenses_successful', parseInt(e.target.value) || 0)}
                      min="0"
                      max={data.defenses_attempted}
                    />
                    <button type="button" onClick={() => onIncrement('defenses_successful')} className="w-11 h-11 rounded-lg flex items-center justify-center font-bold" style={{ backgroundColor: '#0095FF', color: '#fff' }}>
                      <Plus className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
              {data.defenses_attempted > 0 && (
                <p className="text-xs font-semibold mt-2 text-center" style={{ color: '#0095FF' }}>
                  {Math.round((data.defenses_successful / data.defenses_attempted) * 100)}% success
                </p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
