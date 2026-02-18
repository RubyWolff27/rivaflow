import { useState, useEffect } from 'react';
import { usePageTitle } from '../hooks/usePageTitle';
import { videosApi, glossaryApi } from '../api/client';
import { logger } from '../utils/logger';
import type { Video, Movement } from '../types';
import { Video as VideoIcon, ExternalLink, Plus, X } from 'lucide-react';
import { useToast } from '../contexts/ToastContext';
import ConfirmDialog from '../components/ConfirmDialog';
import { CardSkeleton, EmptyState } from '../components/ui';

interface VideoForm {
  url: string;
  title: string;
  movement_id: number | null;
  video_type: string;
}

export default function Videos() {
  usePageTitle('Videos');
  const toast = useToast();
  const [videos, setVideos] = useState<Video[]>([]);
  const [movements, setMovements] = useState<Movement[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [deleteConfirmId, setDeleteConfirmId] = useState<number | null>(null);
  const [movementSearch, setMovementSearch] = useState('');
  const [formData, setFormData] = useState<VideoForm>({
    url: '',
    title: '',
    movement_id: null,
    video_type: 'general',
  });

  useEffect(() => {
    let cancelled = false;
    const doLoad = async () => {
      setLoading(true);
      try {
        const [videosRes, movementsRes] = await Promise.all([
          videosApi.list(),
          glossaryApi.list(),
        ]);
        if (!cancelled) {
          const vData = videosRes.data as Video[] | { videos: Video[] };
          setVideos(Array.isArray(vData) ? vData : vData?.videos || []);
          const mData = movementsRes.data as Movement[] | { movements: Movement[] };
          setMovements(Array.isArray(mData) ? mData : mData?.movements || []);
        }
      } catch (error) {
        if (!cancelled) {
          logger.error('Error loading data:', error);
          toast.error('Failed to load videos');
        }
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
      const [videosRes, movementsRes] = await Promise.all([
        videosApi.list(),
        glossaryApi.list(),
      ]);
      const vData = videosRes.data as Video[] | { videos: Video[] };
      setVideos(Array.isArray(vData) ? vData : vData?.videos || []);
      const mData = movementsRes.data as Movement[] | { movements: Movement[] };
      setMovements(Array.isArray(mData) ? mData : mData?.movements || []);
    } catch (error) {
      logger.error('Error loading data:', error);
      toast.error('Failed to load videos');
    } finally {
      setLoading(false);
    }
  };

  const handleAddVideo = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.url || !formData.movement_id) return;

    setSubmitting(true);
    try {
      await videosApi.create({
        url: formData.url,
        title: formData.title || undefined,
        movement_id: formData.movement_id,
        video_type: formData.video_type,
      });

      setFormData({ url: '', title: '', movement_id: null, video_type: 'general' });
      setMovementSearch('');
      setShowForm(false);
      await loadData();
      toast.success('Video added successfully!');
    } catch (error) {
      logger.error('Error adding video:', error);
      toast.error('Failed to add video. Please try again.');
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
      logger.error('Error deleting video:', error);
      toast.error('Failed to delete video. Please try again.');
    }
  };

  const filteredMovements = movementSearch
    ? movements.filter((m) =>
        m.name.toLowerCase().includes(movementSearch.toLowerCase())
      ).slice(0, 20)
    : movements.slice(0, 20);

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
          Manage your instructional video library. Videos are linked to glossary movements and appear as recall cards during session logging.
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
              <label className="block text-sm font-medium mb-1">
                Movement <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={movementSearch}
                onChange={(e) => {
                  setMovementSearch(e.target.value);
                  if (!e.target.value) setFormData({ ...formData, movement_id: null });
                }}
                placeholder="Search movements..."
                className="w-full px-3 py-2 border border-[var(--border)] rounded-lg focus:ring-2 focus:ring-primary-500 bg-[var(--surface)]"
              />
              {movementSearch && !formData.movement_id && (
                <div className="mt-1 max-h-40 overflow-y-auto border border-[var(--border)] rounded-lg bg-[var(--surface)]">
                  {filteredMovements.map((m) => (
                    <button
                      key={m.id}
                      type="button"
                      onClick={() => {
                        setFormData({ ...formData, movement_id: m.id });
                        setMovementSearch(m.name);
                      }}
                      className="w-full text-left px-3 py-2 hover:bg-[var(--surfaceElev)] text-sm"
                    >
                      <span className="font-medium">{m.name}</span>
                      <span className="text-[var(--muted)] ml-2">{m.category}</span>
                    </button>
                  ))}
                </div>
              )}
              {formData.movement_id && (
                <p className="text-sm text-[var(--accent)] mt-1">
                  Selected: {movementSearch}
                </p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Video Type</label>
              <select
                value={formData.video_type}
                onChange={(e) => setFormData({ ...formData, video_type: e.target.value })}
                className="w-full px-3 py-2 border border-[var(--border)] rounded-lg focus:ring-2 focus:ring-primary-500 bg-[var(--surface)]"
              >
                <option value="general">General</option>
                <option value="gi">Gi</option>
                <option value="nogi">No-Gi</option>
              </select>
            </div>

            <div className="flex gap-3 pt-2">
              <button
                type="submit"
                disabled={submitting || !formData.url || !formData.movement_id}
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
        <EmptyState
          icon={VideoIcon}
          title="No videos in your library yet"
          description="Click the &quot;Add Video&quot; button above to get started."
        />
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
                {video.movement_name && (
                  <p className="text-[var(--accent)]">
                    Linked to: {video.movement_name}
                  </p>
                )}
                {video.video_type && video.video_type !== 'general' && (
                  <span className="inline-block px-2 py-0.5 text-xs rounded bg-[var(--surfaceElev)]">
                    {video.video_type}
                  </span>
                )}
              </div>
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
