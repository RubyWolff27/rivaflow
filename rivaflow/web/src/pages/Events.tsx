import { useState, useEffect, useCallback } from 'react';
import { Calendar, MapPin, Trophy, Scale, Plus, Edit2, Trash2, ChevronDown, ChevronUp, Clock } from 'lucide-react';
import { eventsApi, weightLogsApi } from '../api/client';
import { logger } from '../utils/logger';
import type { CompEvent, WeightLog } from '../types';
import { useToast } from '../contexts/ToastContext';
import ConfirmDialog from '../components/ConfirmDialog';
import PrepChecklist from '../components/events/PrepChecklist';

/* ------------------------------------------------------------------ */
/*  Helpers                                                            */
/* ------------------------------------------------------------------ */

function daysUntil(dateStr: string): number {
  const target = new Date(dateStr + 'T00:00:00');
  const now = new Date();
  now.setHours(0, 0, 0, 0);
  return Math.ceil((target.getTime() - now.getTime()) / 86_400_000);
}

function fmtDate(dateStr: string): string {
  return new Date(dateStr + 'T00:00:00').toLocaleDateString('en-AU', {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  });
}

/* ------------------------------------------------------------------ */
/*  Weight Sparkline (CSS-only bar chart)                              */
/* ------------------------------------------------------------------ */

function WeightChart({ logs }: { logs: WeightLog[] }) {
  if (logs.length === 0) {
    return (
      <p className="text-sm" style={{ color: 'var(--muted)' }}>
        No weight data yet. Start logging to see your trend.
      </p>
    );
  }

  // Show last 14 entries, oldest first
  const display = [...logs].reverse().slice(-14);
  const weights = display.map((l) => l.weight);
  const min = Math.min(...weights);
  const max = Math.max(...weights);
  const range = max - min || 1;

  return (
    <div>
      <div className="flex items-end gap-1" style={{ height: 80 }}>
        {display.map((l, i) => {
          const pct = ((l.weight - min) / range) * 100;
          const h = Math.max(pct, 8); // min 8% so bars are always visible
          return (
            <div
              key={i}
              title={`${l.logged_date}: ${l.weight} kg`}
              className="flex-1 rounded-t transition-all"
              style={{
                height: `${h}%`,
                backgroundColor: 'var(--accent)',
                opacity: 0.6 + (i / display.length) * 0.4,
                minWidth: 6,
              }}
            />
          );
        })}
      </div>
      <div className="flex justify-between mt-1">
        <span className="text-xs" style={{ color: 'var(--muted)' }}>
          {display[0]?.logged_date}
        </span>
        <span className="text-xs" style={{ color: 'var(--muted)' }}>
          {display[display.length - 1]?.logged_date}
        </span>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Event Form                                                         */
/* ------------------------------------------------------------------ */

const EMPTY_FORM = {
  name: '',
  event_type: 'competition',
  event_date: '',
  location: '',
  weight_class: '',
  target_weight: '' as string | number,
  division: '',
  notes: '',
  status: 'upcoming',
};

function EventForm({
  initial,
  onSubmit,
  onCancel,
}: {
  initial?: Partial<CompEvent>;
  onSubmit: (data: Record<string, unknown>) => Promise<void>;
  onCancel: () => void;
}) {
  const [form, setForm] = useState({ ...EMPTY_FORM, ...initial });
  const [saving, setSaving] = useState(false);

  const handle = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await onSubmit({
        ...form,
        target_weight: form.target_weight ? Number(form.target_weight) : undefined,
      });
    } finally {
      setSaving(false);
    }
  };

  const inputStyle = {
    backgroundColor: 'var(--surface)',
    color: 'var(--text)',
    border: '1px solid var(--border)',
  };

  return (
    <form onSubmit={handle} className="space-y-4">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium mb-1" style={{ color: 'var(--text)' }}>
            Event Name *
          </label>
          <input
            required
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            className="w-full px-3 py-2 rounded-lg text-sm"
            style={inputStyle}
            placeholder="e.g. IBJJF Sydney Open"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1" style={{ color: 'var(--text)' }}>
            Date *
          </label>
          <input
            required
            type="date"
            value={form.event_date}
            onChange={(e) => setForm({ ...form, event_date: e.target.value })}
            className="w-full px-3 py-2 rounded-lg text-sm"
            style={inputStyle}
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1" style={{ color: 'var(--text)' }}>
            Type
          </label>
          <select
            value={form.event_type}
            onChange={(e) => setForm({ ...form, event_type: e.target.value })}
            className="w-full px-3 py-2 rounded-lg text-sm"
            style={inputStyle}
          >
            <option value="competition">Competition</option>
            <option value="seminar">Seminar</option>
            <option value="grading">Grading</option>
            <option value="camp">Training Camp</option>
            <option value="other">Other</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium mb-1" style={{ color: 'var(--text)' }}>
            Location
          </label>
          <input
            value={form.location || ''}
            onChange={(e) => setForm({ ...form, location: e.target.value })}
            className="w-full px-3 py-2 rounded-lg text-sm"
            style={inputStyle}
            placeholder="e.g. Sydney Olympic Park"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1" style={{ color: 'var(--text)' }}>
            Weight Class
          </label>
          <input
            value={form.weight_class || ''}
            onChange={(e) => setForm({ ...form, weight_class: e.target.value })}
            className="w-full px-3 py-2 rounded-lg text-sm"
            style={inputStyle}
            placeholder="e.g. Middleweight"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1" style={{ color: 'var(--text)' }}>
            Target Weight (kg)
          </label>
          <input
            type="number"
            step="0.1"
            value={form.target_weight || ''}
            onChange={(e) => setForm({ ...form, target_weight: e.target.value })}
            className="w-full px-3 py-2 rounded-lg text-sm"
            style={inputStyle}
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1" style={{ color: 'var(--text)' }}>
            Division
          </label>
          <input
            value={form.division || ''}
            onChange={(e) => setForm({ ...form, division: e.target.value })}
            className="w-full px-3 py-2 rounded-lg text-sm"
            style={inputStyle}
            placeholder="e.g. Adult Blue Belt"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1" style={{ color: 'var(--text)' }}>
            Status
          </label>
          <select
            value={form.status}
            onChange={(e) => setForm({ ...form, status: e.target.value })}
            className="w-full px-3 py-2 rounded-lg text-sm"
            style={inputStyle}
          >
            <option value="upcoming">Upcoming</option>
            <option value="registered">Registered</option>
            <option value="completed">Completed</option>
            <option value="cancelled">Cancelled</option>
          </select>
        </div>
      </div>
      <div>
        <label className="block text-sm font-medium mb-1" style={{ color: 'var(--text)' }}>
          Notes
        </label>
        <textarea
          value={form.notes || ''}
          onChange={(e) => setForm({ ...form, notes: e.target.value })}
          className="w-full px-3 py-2 rounded-lg text-sm"
          style={inputStyle}
          rows={3}
          placeholder="Game plan, goals, travel notes..."
        />
      </div>
      <div className="flex gap-3 justify-end">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 rounded-lg text-sm font-medium"
          style={{ color: 'var(--muted)', border: '1px solid var(--border)' }}
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={saving}
          className="px-4 py-2 rounded-lg text-sm font-medium"
          style={{ backgroundColor: 'var(--accent)', color: '#FFFFFF', opacity: saving ? 0.6 : 1 }}
        >
          {saving ? 'Saving...' : initial?.id ? 'Update Event' : 'Create Event'}
        </button>
      </div>
    </form>
  );
}

/* ------------------------------------------------------------------ */
/*  Weight Log Quick Form                                              */
/* ------------------------------------------------------------------ */

function WeightLogForm({ onSubmit }: { onSubmit: () => void }) {
  const [weight, setWeight] = useState('');
  const [saving, setSaving] = useState(false);

  const handle = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!weight) return;
    setSaving(true);
    try {
      await weightLogsApi.create({ weight: Number(weight) });
      setWeight('');
      onSubmit();
    } finally {
      setSaving(false);
    }
  };

  return (
    <form onSubmit={handle} className="flex items-end gap-2">
      <div className="flex-1">
        <label className="block text-xs font-medium mb-1" style={{ color: 'var(--muted)' }}>
          Quick Weight Log (kg)
        </label>
        <input
          type="number"
          step="0.1"
          required
          value={weight}
          onChange={(e) => setWeight(e.target.value)}
          className="w-full px-3 py-2 rounded-lg text-sm"
          style={{ backgroundColor: 'var(--surface)', color: 'var(--text)', border: '1px solid var(--border)' }}
          placeholder="e.g. 82.5"
        />
      </div>
      <button
        type="submit"
        disabled={saving}
        className="px-4 py-2 rounded-lg text-sm font-medium"
        style={{ backgroundColor: 'var(--accent)', color: '#FFFFFF', opacity: saving ? 0.6 : 1 }}
      >
        <Scale className="w-4 h-4" />
      </button>
    </form>
  );
}

/* ------------------------------------------------------------------ */
/*  Main Events Page                                                   */
/* ------------------------------------------------------------------ */

export default function Events() {
  const [events, setEvents] = useState<CompEvent[]>([]);
  const [weightLogs, setWeightLogs] = useState<WeightLog[]>([]);
  const [nextEvent, setNextEvent] = useState<{
    event: CompEvent | null;
    days_until: number | null;
    current_weight: number | null;
  }>({ event: null, days_until: null, current_weight: null });
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingEvent, setEditingEvent] = useState<CompEvent | null>(null);
  const [showPast, setShowPast] = useState(false);
  const [deleteConfirmId, setDeleteConfirmId] = useState<number | null>(null);
  const toast = useToast();

  const fetchAll = useCallback(async () => {
    try {
      const [evRes, nextRes, wlRes] = await Promise.all([
        eventsApi.list(),
        eventsApi.getNext(),
        weightLogsApi.list(),
      ]);
      setEvents(evRes.data.events);
      setNextEvent(nextRes.data);
      setWeightLogs(wlRes.data.logs);
    } catch (err) {
      logger.error('Failed to load events data', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    const doLoad = async () => {
      try {
        const [evRes, nextRes, wlRes] = await Promise.all([
          eventsApi.list(),
          eventsApi.getNext(),
          weightLogsApi.list(),
        ]);
        if (!cancelled) {
          setEvents(evRes.data.events);
          setNextEvent(nextRes.data);
          setWeightLogs(wlRes.data.logs);
        }
      } catch (err) {
        if (!cancelled) logger.error('Failed to load events data', err);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    doLoad();
    return () => { cancelled = true; };
  }, [fetchAll]);

  const handleCreate = async (data: Record<string, unknown>) => {
    await eventsApi.create(data as Partial<CompEvent>);
    setShowForm(false);
    fetchAll();
  };

  const handleUpdate = async (data: Record<string, unknown>) => {
    if (!editingEvent) return;
    await eventsApi.update(editingEvent.id, data as Partial<CompEvent>);
    setEditingEvent(null);
    fetchAll();
  };

  const handleDelete = async (id: number) => {
    try {
      await eventsApi.delete(id);
      setDeleteConfirmId(null);
      fetchAll();
    } catch (err) {
      logger.error('Failed to delete event', err);
      toast.showToast('error', 'Failed to delete event');
    }
  };

  const upcoming = events.filter(
    (e) => e.status === 'upcoming' || e.status === 'registered'
  );
  const past = events.filter(
    (e) => e.status === 'completed' || e.status === 'cancelled'
  );

  if (loading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3].map((i) => (
          <div
            key={i}
            className="h-24 rounded-xl animate-pulse"
            style={{ backgroundColor: 'var(--surface)' }}
          />
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold" style={{ color: 'var(--text)' }}>
            Events & Competition Prep
          </h1>
          <p className="text-sm mt-1" style={{ color: 'var(--muted)' }}>
            Plan competitions, track your weight, and prepare for game day.
          </p>
        </div>
        <button
          onClick={() => {
            setEditingEvent(null);
            setShowForm(true);
          }}
          className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium"
          style={{ backgroundColor: 'var(--accent)', color: '#FFFFFF' }}
        >
          <Plus className="w-4 h-4" />
          New Event
        </button>
      </div>

      {/* Hero Countdown */}
      {nextEvent.event && nextEvent.days_until !== null && (
        <div
          className="rounded-xl p-6"
          style={{
            backgroundColor: 'var(--surface)',
            border: '1px solid var(--border)',
          }}
        >
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs uppercase font-semibold tracking-wide mb-1" style={{ color: 'var(--accent)' }}>
                Next Event
              </p>
              <h2 className="text-xl font-bold" style={{ color: 'var(--text)' }}>
                {nextEvent.event.name}
              </h2>
              <p className="text-sm mt-1" style={{ color: 'var(--muted)' }}>
                {fmtDate(nextEvent.event.event_date)}
                {nextEvent.event.location && (
                  <span className="ml-2">
                    <MapPin className="w-3 h-3 inline -mt-0.5" /> {nextEvent.event.location}
                  </span>
                )}
              </p>
              {nextEvent.event.division && (
                <p className="text-sm mt-1" style={{ color: 'var(--muted)' }}>
                  {nextEvent.event.division}
                  {nextEvent.event.weight_class && ` / ${nextEvent.event.weight_class}`}
                </p>
              )}
            </div>
            <div className="text-right">
              <div
                className="text-4xl font-black tabular-nums"
                style={{ color: nextEvent.days_until <= 7 ? 'var(--error, #ef4444)' : 'var(--accent)' }}
              >
                {nextEvent.days_until}
              </div>
              <div className="text-xs uppercase font-medium" style={{ color: 'var(--muted)' }}>
                {nextEvent.days_until === 1 ? 'day to go' : 'days to go'}
              </div>
              {nextEvent.event.target_weight && nextEvent.current_weight && (
                <div className="mt-2 text-xs" style={{ color: 'var(--muted)' }}>
                  <span style={{ color: 'var(--text)' }}>{nextEvent.current_weight} kg</span>
                  {' / '}
                  {nextEvent.event.target_weight} kg target
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Weight Section */}
      <div
        className="rounded-xl p-5"
        style={{
          backgroundColor: 'var(--surface)',
          border: '1px solid var(--border)',
        }}
      >
        <div className="flex items-center gap-2 mb-4">
          <Scale className="w-4 h-4" style={{ color: 'var(--accent)' }} />
          <h3 className="font-semibold" style={{ color: 'var(--text)' }}>
            Weight Tracker
          </h3>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
          <WeightChart logs={weightLogs} />
          <WeightLogForm onSubmit={fetchAll} />
        </div>
      </div>

      {/* Create / Edit Form */}
      {(showForm || editingEvent) && (
        <div
          className="rounded-xl p-5"
          style={{
            backgroundColor: 'var(--surface)',
            border: '1px solid var(--border)',
          }}
        >
          <h3 className="font-semibold mb-4" style={{ color: 'var(--text)' }}>
            {editingEvent ? 'Edit Event' : 'New Event'}
          </h3>
          <EventForm
            initial={editingEvent || undefined}
            onSubmit={editingEvent ? handleUpdate : handleCreate}
            onCancel={() => {
              setShowForm(false);
              setEditingEvent(null);
            }}
          />
        </div>
      )}

      {/* Upcoming Events */}
      <div>
        <h3 className="font-semibold mb-3" style={{ color: 'var(--text)' }}>
          Upcoming Events ({upcoming.length})
        </h3>
        {upcoming.length === 0 ? (
          <p className="text-sm" style={{ color: 'var(--muted)' }}>
            No upcoming events. Add one to start your competition prep.
          </p>
        ) : (
          <div className="space-y-3">
            {upcoming.map((ev) => {
              const d = daysUntil(ev.event_date);
              return (
                <div
                  key={ev.id}
                  className="rounded-xl p-4"
                  style={{
                    backgroundColor: 'var(--surface)',
                    border: '1px solid var(--border)',
                  }}
                >
                  <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div
                      className="w-12 h-12 rounded-lg flex flex-col items-center justify-center"
                      style={{
                        backgroundColor: d <= 7 ? 'rgba(239,68,68,0.15)' : 'rgba(var(--accent-rgb, 99,102,241), 0.15)',
                      }}
                    >
                      <span
                        className="text-lg font-bold leading-none"
                        style={{ color: d <= 7 ? 'var(--error, #ef4444)' : 'var(--accent)' }}
                      >
                        {d}
                      </span>
                      <span className="text-[9px] uppercase" style={{ color: 'var(--muted)' }}>
                        days
                      </span>
                    </div>
                    <div>
                      <p className="font-medium text-sm" style={{ color: 'var(--text)' }}>
                        {ev.name}
                      </p>
                      <p className="text-xs flex items-center gap-2" style={{ color: 'var(--muted)' }}>
                        <Calendar className="w-3 h-3" /> {fmtDate(ev.event_date)}
                        {ev.location && (
                          <>
                            <MapPin className="w-3 h-3 ml-1" /> {ev.location}
                          </>
                        )}
                      </p>
                      <div className="flex gap-2 mt-1">
                        {ev.event_type && (
                          <span
                            className="text-[10px] px-2 py-0.5 rounded-full font-medium"
                            style={{ backgroundColor: 'var(--surfaceElev, rgba(255,255,255,0.05))', color: 'var(--muted)' }}
                          >
                            {ev.event_type}
                          </span>
                        )}
                        {ev.weight_class && (
                          <span
                            className="text-[10px] px-2 py-0.5 rounded-full font-medium"
                            style={{ backgroundColor: 'var(--surfaceElev, rgba(255,255,255,0.05))', color: 'var(--muted)' }}
                          >
                            {ev.weight_class}
                          </span>
                        )}
                        {ev.status === 'registered' && (
                          <span
                            className="text-[10px] px-2 py-0.5 rounded-full font-medium"
                            style={{ backgroundColor: 'rgba(34,197,94,0.15)', color: '#22c55e' }}
                          >
                            Registered
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="flex gap-1">
                    <button
                      onClick={() => {
                        setShowForm(false);
                        setEditingEvent(ev);
                      }}
                      className="p-2 rounded-lg transition-colors"
                      style={{ color: 'var(--muted)' }}
                      aria-label="Edit event"
                    >
                      <Edit2 className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => setDeleteConfirmId(ev.id)}
                      className="p-2 rounded-lg transition-colors"
                      style={{ color: 'var(--muted)' }}
                      aria-label="Delete event"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
                <PrepChecklist eventId={ev.id} eventType={ev.event_type || 'other'} />
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Past Events */}
      {past.length > 0 && (
        <div>
          <button
            onClick={() => setShowPast(!showPast)}
            className="flex items-center gap-2 font-semibold mb-3"
            style={{ color: 'var(--text)' }}
          >
            Past Events ({past.length})
            {showPast ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>
          {showPast && (
            <div className="space-y-3">
              {past.map((ev) => (
                <div
                  key={ev.id}
                  className="rounded-xl p-4 flex items-center justify-between opacity-70"
                  style={{
                    backgroundColor: 'var(--surface)',
                    border: '1px solid var(--border)',
                  }}
                >
                  <div className="flex items-center gap-4">
                    <div
                      className="w-12 h-12 rounded-lg flex items-center justify-center"
                      style={{ backgroundColor: 'var(--surfaceElev, rgba(255,255,255,0.05))' }}
                    >
                      {ev.status === 'completed' ? (
                        <Trophy className="w-5 h-5" style={{ color: 'var(--accent)' }} />
                      ) : (
                        <Clock className="w-5 h-5" style={{ color: 'var(--muted)' }} />
                      )}
                    </div>
                    <div>
                      <p className="font-medium text-sm" style={{ color: 'var(--text)' }}>
                        {ev.name}
                      </p>
                      <p className="text-xs" style={{ color: 'var(--muted)' }}>
                        {fmtDate(ev.event_date)}
                        {ev.location && ` - ${ev.location}`}
                      </p>
                      <span
                        className="text-[10px] px-2 py-0.5 rounded-full font-medium inline-block mt-1"
                        style={{
                          backgroundColor: ev.status === 'completed'
                            ? 'rgba(34,197,94,0.15)'
                            : 'rgba(239,68,68,0.15)',
                          color: ev.status === 'completed' ? '#22c55e' : '#ef4444',
                        }}
                      >
                        {ev.status}
                      </span>
                    </div>
                  </div>
                  <div className="flex gap-1">
                    <button
                      onClick={() => {
                        setShowForm(false);
                        setEditingEvent(ev);
                      }}
                      className="p-2 rounded-lg transition-colors"
                      style={{ color: 'var(--muted)' }}
                      aria-label="Edit event"
                    >
                      <Edit2 className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => setDeleteConfirmId(ev.id)}
                      className="p-2 rounded-lg transition-colors"
                      style={{ color: 'var(--muted)' }}
                      aria-label="Delete event"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      <ConfirmDialog
        isOpen={deleteConfirmId !== null}
        onClose={() => setDeleteConfirmId(null)}
        onConfirm={() => deleteConfirmId && handleDelete(deleteConfirmId)}
        title="Delete Event"
        message="Are you sure you want to delete this event? This action cannot be undone."
        confirmText="Delete"
        variant="danger"
      />
    </div>
  );
}
