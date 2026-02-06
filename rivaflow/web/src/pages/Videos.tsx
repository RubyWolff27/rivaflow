import { useState, useEffect } from 'react';
import { videosApi, techniquesApi } from '../api/client';
import type { Video, Technique } from '../types';
import { Video as VideoIcon, ExternalLink, Plus, X } from 'lucide-react';

interface VideoForm {
  url: string;
  title: string;
  technique_id: number | null;
  timestamps: { time: string; label: string }[];
}

export default function Videos() {
  const [videos, setVideos] = useState<Video[]>([]);
  const [techniques, setTechniques] = useState<Technique[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [formData, setFormData] = useState<VideoForm>({
    url: '',
    title: '',
    technique_id: null,
    timestamps: [],
  });

  useEffect(() => {
    loadData();
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
      alert('Failed to add video. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteVideo = async (id: number) => {
    if (!confirm('Are you sure you want to delete this video?')) return;

    try {
      await videosApi.delete(id);
      await loadData();
    } catch (error) {
      console.error('Error deleting video:', error);
      alert('Failed to delete video. Please try again.');
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
    return <div className="text-center py-12">Loading...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <VideoIcon className="w-8 h-8 text-primary-600" />
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
        <p className="text-gray-600 dark:text-gray-400">
          Manage your instructional video library. Videos are linked to techniques and appear as recall cards during session logging.
        </p>
      </div>

      {/* Add Video Form */}
      {showForm && (
        <div className="card bg-gray-50 dark:bg-gray-800 border-2 border-primary-200 dark:border-primary-800">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold">Add New Video</h2>
            <button
              onClick={() => setShowForm(false)}
              className="text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
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
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 bg-white dark:bg-gray-700"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Title (optional)</label>
              <input
                type="text"
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                placeholder="e.g., Armbar from Closed Guard"
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 bg-white dark:bg-gray-700"
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
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 bg-white dark:bg-gray-700"
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
                  className="text-sm text-primary-600 hover:text-primary-700 flex items-center gap-1"
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
                        className="w-24 px-2 py-1 border border-gray-300 dark:border-gray-600 rounded focus:ring-2 focus:ring-primary-500 bg-white dark:bg-gray-700 text-sm"
                      />
                      <input
                        type="text"
                        placeholder="Description"
                        value={ts.label}
                        onChange={(e) => updateTimestamp(idx, 'label', e.target.value)}
                        className="flex-1 px-2 py-1 border border-gray-300 dark:border-gray-600 rounded focus:ring-2 focus:ring-primary-500 bg-white dark:bg-gray-700 text-sm"
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
          <VideoIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-500 dark:text-gray-400 mb-4">No videos in your library yet</p>
          <p className="text-sm text-gray-400 dark:text-gray-500">
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
                    className="text-primary-600 hover:text-primary-700"
                  >
                    <ExternalLink className="w-5 h-5" />
                  </a>
                  <button
                    onClick={() => handleDeleteVideo(video.id)}
                    className="text-red-500 hover:text-red-700"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>
              </div>

              <div className="text-sm text-gray-600 dark:text-gray-400 space-y-1 mb-3">
                <p className="truncate">{video.url}</p>
                {video.technique_id && (
                  <p className="text-primary-600">
                    Linked to: {techniques.find((t) => t.id === video.technique_id)?.name || 'Unknown technique'}
                  </p>
                )}
              </div>

              {video.timestamps && video.timestamps.length > 0 && (
                <div className="border-t border-gray-200 dark:border-gray-700 pt-3 mt-3">
                  <p className="text-xs font-semibold text-gray-600 dark:text-gray-400 mb-2">
                    TIMESTAMPS
                  </p>
                  <div className="space-y-1">
                    {video.timestamps.map((ts, idx) => (
                      <div key={idx} className="text-sm flex gap-2">
                        <span className="text-primary-600 font-mono">{ts.time}</span>
                        <span className="text-gray-600 dark:text-gray-400">{ts.label}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
