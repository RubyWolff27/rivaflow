import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { glossaryApi } from '../api/client';
import type { Movement } from '../types';
import { ArrowLeft, Award, Plus, Trash2, ExternalLink, Video as VideoIcon } from 'lucide-react';
import ConfirmDialog from '../components/ConfirmDialog';
import { useToast } from '../contexts/ToastContext';
import { CardSkeleton } from '../components/ui';

const CATEGORY_LABELS: Record<string, string> = {
  position: 'Position',
  submission: 'Submission',
  sweep: 'Sweep',
  pass: 'Guard Pass',
  takedown: 'Takedown',
  escape: 'Escape',
  movement: 'Movement',
  concept: 'Concept',
  defense: 'Defense',
};

const CATEGORY_STYLES: Record<string, React.CSSProperties> = {
  position: { backgroundColor: 'rgba(59,130,246,0.1)', color: 'var(--accent)' },
  submission: { backgroundColor: 'rgba(239,68,68,0.1)', color: 'var(--error)' },
  sweep: { backgroundColor: 'rgba(34,197,94,0.1)', color: 'var(--success)' },
  pass: { backgroundColor: 'rgba(168,85,247,0.1)', color: '#a855f7' },
  takedown: { backgroundColor: 'rgba(249,115,22,0.1)', color: '#f97316' },
  escape: { backgroundColor: 'rgba(234,179,8,0.1)', color: '#ca8a04' },
  movement: { backgroundColor: 'rgba(99,102,241,0.1)', color: '#6366f1' },
  concept: { backgroundColor: 'var(--surfaceElev)', color: 'var(--text)' },
  defense: { backgroundColor: 'rgba(236,72,153,0.1)', color: '#ec4899' },
};

export default function MovementDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [movement, setMovement] = useState<Movement | null>(null);
  const [loading, setLoading] = useState(true);
  const [showAddVideo, setShowAddVideo] = useState(false);
  const [videoToDelete, setVideoToDelete] = useState<number | null>(null);
  const toast = useToast();
  const [videoForm, setVideoForm] = useState({
    url: '',
    title: '',
    video_type: 'general',
  });

  useEffect(() => {
    let cancelled = false;
    const doLoad = async () => {
      if (!id) return;
      setLoading(true);
      try {
        const response = await glossaryApi.getById(parseInt(id), true);
        if (!cancelled) setMovement(response.data);
      } catch (error) {
        if (!cancelled) console.error('Error loading movement:', error);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    doLoad();
    return () => { cancelled = true; };
  }, [id]);

  const loadMovement = async () => {
    if (!id) return;
    setLoading(true);
    try {
      const response = await glossaryApi.getById(parseInt(id), true);
      setMovement(response.data);
    } catch (error) {
      console.error('Error loading movement:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddVideo = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id) return;

    try {
      await glossaryApi.addCustomVideo(parseInt(id), {
        url: videoForm.url,
        title: videoForm.title || undefined,
        video_type: videoForm.video_type,
      });
      setShowAddVideo(false);
      setVideoForm({ url: '', title: '', video_type: 'general' });
      await loadMovement();
      toast.success('Video link added successfully');
    } catch (error) {
      console.error('Error adding video:', error);
      toast.error('Failed to add video link.');
    }
  };

  const handleDeleteVideo = async () => {
    if (!id || !videoToDelete) return;

    try {
      await glossaryApi.deleteCustomVideo(parseInt(id), videoToDelete);
      await loadMovement();
      toast.success('Video link deleted successfully');
    } catch (error) {
      console.error('Error deleting video:', error);
      toast.error('Failed to delete video link.');
    } finally {
      setVideoToDelete(null);
    }
  };

  const extractYouTubeId = (url: string): string | null => {
    const patterns = [
      /(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\s]+)/,
      /youtube\.com\/embed\/([^&\s]+)/,
    ];
    for (const pattern of patterns) {
      const match = url.match(pattern);
      if (match) return match[1];
    }
    return null;
  };

  const renderVideo = (url: string, title?: string) => {
    const youtubeId = extractYouTubeId(url);
    if (youtubeId) {
      return (
        <div className="aspect-video w-full">
          <iframe
            className="w-full h-full rounded-lg"
            src={`https://www.youtube.com/embed/${youtubeId}`}
            title={title || 'YouTube video'}
            frameBorder="0"
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
            allowFullScreen
          />
        </div>
      );
    }
    return (
      <a
        href={url}
        target="_blank"
        rel="noopener noreferrer"
        className="flex items-center gap-2 text-[var(--accent)] hover:opacity-80"
      >
        <ExternalLink className="w-4 h-4" />
        {title || url}
      </a>
    );
  };

  if (loading) {
    return (
      <div className="max-w-5xl mx-auto space-y-4">
        <CardSkeleton lines={2} />
        <CardSkeleton lines={4} />
      </div>
    );
  }

  if (!movement) {
    return (
      <div className="text-center py-12">
        <p className="text-[var(--muted)] mb-4">Movement not found</p>
        <button onClick={() => navigate('/glossary')} className="btn-secondary">
          Back to Glossary
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button
          onClick={() => navigate('/glossary')}
          className="btn-secondary flex items-center gap-2"
        >
          <ArrowLeft className="w-4 h-4" />
          Back
        </button>
        <div className="flex-1">
          <h1 className="text-3xl font-bold">{movement.name}</h1>
          {movement.subcategory && (
            <p className="text-[var(--muted)] capitalize">
              {movement.subcategory}
            </p>
          )}
        </div>
      </div>

      {/* Movement Details Card */}
      <div className="card space-y-4">
        <div className="flex flex-wrap gap-2">
          <span className="px-3 py-1 rounded-full text-sm font-medium" style={CATEGORY_STYLES[movement.category]}>
            {CATEGORY_LABELS[movement.category] || movement.category}
          </span>
          {movement.points > 0 && (
            <span className="px-3 py-1 rounded-full text-sm font-medium flex items-center gap-1" style={{ backgroundColor: 'rgba(245,158,11,0.1)', color: '#d97706' }}>
              <Award className="w-4 h-4" />
              {movement.points} points
            </span>
          )}
          {movement.custom && (
            <span className="px-3 py-1 rounded-full text-sm font-medium" style={{ backgroundColor: 'rgba(59,130,246,0.1)', color: 'var(--accent)' }}>
              Custom
            </span>
          )}
        </div>

        {movement.description && (
          <div>
            <h3 className="text-sm font-semibold text-[var(--muted)] uppercase mb-1">Description</h3>
            <p className="text-[var(--text)]">{movement.description}</p>
          </div>
        )}

        <div className="grid grid-cols-2 gap-4">
          <div>
            <h3 className="text-sm font-semibold text-[var(--muted)] uppercase mb-1">Gi Applicable</h3>
            <p className="text-[var(--text)]">{movement.gi_applicable ? 'Yes' : 'No'}</p>
          </div>
          <div>
            <h3 className="text-sm font-semibold text-[var(--muted)] uppercase mb-1">No-Gi Applicable</h3>
            <p className="text-[var(--text)]">{movement.nogi_applicable ? 'Yes' : 'No'}</p>
          </div>
        </div>

        {movement.aliases && movement.aliases.length > 0 && (
          <div>
            <h3 className="text-sm font-semibold text-[var(--muted)] uppercase mb-1">Also Known As</h3>
            <p className="text-[var(--text)]">{movement.aliases.join(', ')}</p>
          </div>
        )}

        <div className="grid grid-cols-2 md:grid-cols-5 gap-2">
          <div className="text-center">
            <h3 className="text-xs font-semibold text-[var(--muted)] uppercase mb-1">White</h3>
            <p className={movement.ibjjf_legal_white ? 'text-green-600' : 'text-red-600'}>
              {movement.ibjjf_legal_white ? 'Legal' : 'Illegal'}
            </p>
          </div>
          <div className="text-center">
            <h3 className="text-xs font-semibold text-[var(--muted)] uppercase mb-1">Blue</h3>
            <p className={movement.ibjjf_legal_blue ? 'text-green-600' : 'text-red-600'}>
              {movement.ibjjf_legal_blue ? 'Legal' : 'Illegal'}
            </p>
          </div>
          <div className="text-center">
            <h3 className="text-xs font-semibold text-[var(--muted)] uppercase mb-1">Purple</h3>
            <p className={movement.ibjjf_legal_purple ? 'text-green-600' : 'text-red-600'}>
              {movement.ibjjf_legal_purple ? 'Legal' : 'Illegal'}
            </p>
          </div>
          <div className="text-center">
            <h3 className="text-xs font-semibold text-[var(--muted)] uppercase mb-1">Brown</h3>
            <p className={movement.ibjjf_legal_brown ? 'text-green-600' : 'text-red-600'}>
              {movement.ibjjf_legal_brown ? 'Legal' : 'Illegal'}
            </p>
          </div>
          <div className="text-center">
            <h3 className="text-xs font-semibold text-[var(--muted)] uppercase mb-1">Black</h3>
            <p className={movement.ibjjf_legal_black ? 'text-green-600' : 'text-red-600'}>
              {movement.ibjjf_legal_black ? 'Legal' : 'Illegal'}
            </p>
          </div>
        </div>
      </div>

      {/* Reference Videos */}
      {(movement.gi_video_url || movement.nogi_video_url) && (
        <div className="card space-y-4">
          <h2 className="text-xl font-bold flex items-center gap-2">
            <VideoIcon className="w-5 h-5" />
            Instructional Videos
          </h2>

          {movement.gi_video_url && (
            <div>
              <h3 className="text-sm font-semibold text-[var(--muted)] uppercase mb-2">Gi Version</h3>
              {renderVideo(movement.gi_video_url, `${movement.name} - Gi`)}
            </div>
          )}

          {movement.nogi_video_url && (
            <div>
              <h3 className="text-sm font-semibold text-[var(--muted)] uppercase mb-2">No-Gi Version</h3>
              {renderVideo(movement.nogi_video_url, `${movement.name} - No-Gi`)}
            </div>
          )}
        </div>
      )}

      {/* Custom Videos */}
      <div className="card space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-bold flex items-center gap-2">
            <VideoIcon className="w-5 h-5" />
            Your Custom Videos
          </h2>
          <button
            onClick={() => setShowAddVideo(!showAddVideo)}
            className="btn-primary flex items-center gap-2 text-sm"
          >
            <Plus className="w-4 h-4" />
            Add Video
          </button>
        </div>

        {/* Add Video Form */}
        {showAddVideo && (
          <form onSubmit={handleAddVideo} className="bg-[var(--surfaceElev)] p-4 rounded-lg space-y-3">
            <div>
              <label className="label">Video URL</label>
              <input
                type="url"
                className="input"
                value={videoForm.url}
                onChange={(e) => setVideoForm({ ...videoForm, url: e.target.value })}
                placeholder="https://youtube.com/watch?v=..."
                required
              />
            </div>
            <div>
              <label className="label">Title (optional)</label>
              <input
                type="text"
                className="input"
                value={videoForm.title}
                onChange={(e) => setVideoForm({ ...videoForm, title: e.target.value })}
                placeholder="e.g., John Danaher Breakdown"
              />
            </div>
            <div>
              <label className="label">Video Type</label>
              <select
                className="input"
                value={videoForm.video_type}
                onChange={(e) => setVideoForm({ ...videoForm, video_type: e.target.value })}
              >
                <option value="general">General</option>
                <option value="gi">Gi</option>
                <option value="nogi">No-Gi</option>
              </select>
            </div>
            <div className="flex gap-2">
              <button type="submit" className="btn-primary text-sm">Add Video</button>
              <button
                type="button"
                onClick={() => setShowAddVideo(false)}
                className="btn-secondary text-sm"
              >
                Cancel
              </button>
            </div>
          </form>
        )}

        {/* Custom Videos List */}
        {movement.custom_videos && movement.custom_videos.length > 0 ? (
          <div className="space-y-4">
            {movement.custom_videos.map((video) => (
              <div key={video.id} className="border border-[var(--border)] rounded-lg p-4 space-y-3">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      {video.title && (
                        <h4 className="font-semibold text-[var(--text)]">{video.title}</h4>
                      )}
                      <span className="px-2 py-0.5 rounded text-xs font-medium" style={
                        video.video_type === 'gi' ? { backgroundColor: 'rgba(59,130,246,0.1)', color: 'var(--accent)' } :
                        video.video_type === 'nogi' ? { backgroundColor: 'rgba(168,85,247,0.1)', color: '#a855f7' } :
                        { backgroundColor: 'var(--surfaceElev)', color: 'var(--text)' }
                      }>
                        {video.video_type === 'gi' ? 'Gi' : video.video_type === 'nogi' ? 'No-Gi' : 'General'}
                      </span>
                    </div>
                  </div>
                  <button
                    onClick={() => setVideoToDelete(video.id)}
                    className="text-[var(--error)] hover:opacity-80"
                    title="Delete video"
                    aria-label="Delete video"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
                {renderVideo(video.url, video.title)}
              </div>
            ))}
          </div>
        ) : (
          <p className="text-[var(--muted)] text-sm">
            No custom videos yet. Add your preferred instructional videos above.
          </p>
        )}
      </div>

      <ConfirmDialog
        isOpen={videoToDelete !== null}
        onClose={() => setVideoToDelete(null)}
        onConfirm={handleDeleteVideo}
        title="Delete Video Link"
        message="Are you sure you want to delete this video link? This action cannot be undone."
        confirmText="Delete"
        cancelText="Cancel"
        variant="danger"
      />
    </div>
  );
}
