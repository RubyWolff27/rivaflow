import { useState, useEffect } from 'react';
import { videosApi, techniquesApi } from '../api/client';
import type { Video, Technique } from '../types';
import { Video as VideoIcon, ExternalLink, Plus, X } from 'lucide-react';
import { useToast } from '../contexts/ToastContext';
import ConfirmDialog from '../components/ConfirmDialog';
import { CardSkeleton } from '../components/ui';

interface VideoForm {
  url: string;
  title: string;
  technique_id: number | null;
  timestamps: { time: string; label: string }[];
}

export default function Videos() {
  const toast = useToast();
  const [videos, setVideos] = useState<Video[]>([]);
  const [techniques, setTechniques] = useState<Technique[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [deleteConfirmId, setDeleteConfirmId] = useState<number | null>(null);
  const [formData, setFormData] = useState<VideoForm>({
    url: '',
    title: '',
    technique_id: null,
    timestamps: [],
  });

  useEffect(() => {
    let cancelled = false;
    const doLoad = async () => {
      setLoading(true);
      try {
        const [videosRes, techniquesRes] = await Promise.all([
          videosApi.list(),
          techniquesApi.list(),
        ]);
        if (!cancelled) {
          setVideos(videosRes.data);
          setTechniques(techniquesRes.data.techniques || []);
        }
      } catch (error) {
        if (!cancelled) console.error('Error loading data:', error);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    doLoad();
    return () => { cancelled = true; };
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [videosRes, techniquesRes] = await Promise.all([
        videosApi.list(),
        techniquesApi.list(),
      ]);
      setVideos(videosRes.data);
      setTechniques(techniquesRes.data.techniques || []);
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddVideo = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.url) return;

    setSubmitting(true);
    try {
      await videosApi.create({
        url: formData.url,
        title: formData.title || undefined,
        technique_id: formData.technique_id || undefined,
        timestamps: formData.timestamps.length > 0 ? formData.timestamps : undefined,
      });

      // Reset form and reload videos
      setFormData({ url: '', title: '', technique_id: null, timestamps: [] });
      setShowForm(false);
      await loadData();
    } catch (error) {
      console.error('Error adding video:', error);
      toast.showToast('error', 'Failed to add video. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteVideo = async (id: number) => {
    try {
      await videosApi.delete(id);
      setDeleteConfirmId(null);
      await loadData();
    } catch (error) {
      console.error('Error deleting video:', error);
      toast.showToast('error', 'Failed to delete video. Please try again.');
    }
  };

  const addTimestamp = () => {
    setFormData({
      ...formData,
      timestamps: [...formData.timestamps, { time: '', label: '' }],
    });
  };

  const removeTimestamp = (index: number) => {
    setFormData({
      ...formData,
      timestamps: formData.timestamps.filter((_, i) => i !== index),
    });
  };

  const updateTimestamp = (index: number, field: 'time' | 'label', value: string) => {
    const newTimestamps = [...formData.timestamps];
    newTimestamps[index][field] = value;
    setFormData({ ...formData, timestamps: newTimestamps });
  };

  if (loading) {
    return (
      <div className="space-y-4">
        {[1, 2].map((i) => (
          <CardSkeleton key={i} lines={3} />
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <VideoIcon className="w-8 h-8 text-[var(--accent)]" />
          <h1 className="text-3xl font-bold">Video Library</h1>
        </div>
        <button
          onClick={() => setShowForm(true)}
          className="btn btn-primary flex items-center gap-2"
        >
          <Plus className="w-5 h-5" />
          Add Video
        </button>
      </div>

      <div className="card">
        <p className="text-[var(--muted)]">
          Manage your instructional video library. Videos are linked to techniques and appear as recall cards during session logging.
        </p>
      </div>

      {/* Add Video Form */}
      {showForm && (
        <div className="card bg-[var(--surfaceElev)] border-2 border-primary-200">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold">Add New Video</h2>
            <button
              onClick={() => setShowForm(false)}
              className="text-[var(--muted)] hover:text-[var(--text)]"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          <form onSubmit={handleAddVideo} className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">
                Video URL <span className="text-red-500">*</span>
              </label>
              <input
                type="url"
                required
                value={formData.url}
                onChange={(e) => setFormData({ ...formData, url: e.target.value })}
                placeholder="https://youtube.com/watch?v=..."
                className="w-full px-3 py-2 border border-[var(--border)] rounded-lg focus:ring-2 focus:ring-primary-500 bg-[var(--surface)]"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Title (optional)</label>
              <input
                type="text"
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                placeholder="e.g., Armbar from Closed Guard"
                className="w-full px-3 py-2 border border-[var(--border)] rounded-lg focus:ring-2 focus:ring-primary-500 bg-[var(--surface)]"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Technique (optional)</label>
              <select
                value={formData.technique_id || ''}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    technique_id: e.target.value ? parseInt(e.target.value) : null,
                  })
                }
                className="w-full px-3 py-2 border border-[var(--border)] rounded-lg focus:ring-2 focus:ring-primary-500 bg-[var(--surface)]"
              >
                <option value="">Select a technique...</option>
                {techniques.map((technique) => (
                  <option key={technique.id} value={technique.id}>
                    {technique.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <div className="flex justify-between items-center mb-2">
                <label className="block text-sm font-medium">Timestamps (optional)</label>
                <button
                  type="button"
                  onClick={addTimestamp}
                  className="text-sm text-[var(--accent)] hover:opacity-80 flex items-center gap-1"
                >
                  <Plus className="w-4 h-4" />
                  Add Timestamp
                </button>
              </div>

              {formData.timestamps.length > 0 && (
                <div className="space-y-2">
                  {formData.timestamps.map((ts, idx) => (
                    <div key={idx} className="flex gap-2">
                      <input
                        type="text"
                        placeholder="0:00"
                        value={ts.time}
                        onChange={(e) => updateTimestamp(idx, 'time', e.target.value)}
                        className="w-24 px-2 py-1 border border-[var(--border)] rounded focus:ring-2 focus:ring-primary-500 bg-[var(--surface)] text-sm"
                      />
                      <input
                        type="text"
                        placeholder="Description"
                        value={ts.label}
                        onChange={(e) => updateTimestamp(idx, 'label', e.target.value)}
                        className="flex-1 px-2 py-1 border border-[var(--border)] rounded focus:ring-2 focus:ring-primary-500 bg-[var(--surface)] text-sm"
                      />
                      <button
                        type="button"
                        onClick={() => removeTimestamp(idx)}
                        className="text-red-500 hover:text-red-700"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="flex gap-3 pt-2">
              <button
                type="submit"
                disabled={submitting || !formData.url}
                className="btn btn-primary"
              >
                {submitting ? 'Adding...' : 'Add Video'}
              </button>
              <button
                type="button"
                onClick={() => setShowForm(false)}
                className="btn btn-secondary"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Videos List */}
      {videos.length === 0 ? (
        <div className="card text-center py-12">
          <VideoIcon className="w-12 h-12 text-[var(--muted)] mx-auto mb-4" />
          <p className="text-[var(--muted)] mb-4">No videos in your library yet</p>
          <p className="text-sm text-[var(--muted)]">
            Click the "Add Video" button above to get started
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {videos.map((video) => (
            <div key={video.id} className="card hover:shadow-md transition-shadow">
              <div className="flex justify-between items-start mb-3">
                <h3 className="font-semibold text-lg flex-1">{video.title || 'Untitled Video'}</h3>
                <div className="flex gap-2">
                  <a
                    href={video.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-[var(--accent)] hover:opacity-80"
                  >
                    <ExternalLink className="w-5 h-5" />
                  </a>
                  <button
                    onClick={() => setDeleteConfirmId(video.id)}
                    className="text-red-500 hover:text-red-700"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>
              </div>

              <div className="text-sm text-[var(--muted)] space-y-1 mb-3">
                <p className="truncate">{video.url}</p>
                {video.technique_id && (
                  <p className="text-[var(--accent)]">
                    Linked to: {techniques.find((t) => t.id === video.technique_id)?.name || 'Unknown technique'}
                  </p>
                )}
              </div>

              {video.timestamps && video.timestamps.length > 0 && (
                <div className="border-t border-[var(--border)] pt-3 mt-3">
                  <p className="text-xs font-semibold text-[var(--muted)] mb-2">
                    TIMESTAMPS
                  </p>
                  <div className="space-y-1">
                    {video.timestamps.map((ts, idx) => (
                      <div key={idx} className="text-sm flex gap-2">
                        <span className="text-[var(--accent)] font-mono">{ts.time}</span>
                        <span className="text-[var(--muted)]">{ts.label}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      <ConfirmDialog
        isOpen={deleteConfirmId !== null}
        onClose={() => setDeleteConfirmId(null)}
        onConfirm={() => deleteConfirmId && handleDeleteVideo(deleteConfirmId)}
        title="Delete Video"
        message="Are you sure you want to delete this video? This action cannot be undone."
        confirmText="Delete"
        variant="danger"
      />
    </div>
  );
}
