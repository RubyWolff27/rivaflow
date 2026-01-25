import { useState, useEffect } from 'react';
import { videosApi } from '../api/client';
import type { Video } from '../types';
import { Video as VideoIcon, ExternalLink } from 'lucide-react';

export default function Videos() {
  const [videos, setVideos] = useState<Video[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadVideos();
  }, []);

  const loadVideos = async () => {
    setLoading(true);
    try {
      const res = await videosApi.list();
      setVideos(res.data);
    } catch (error) {
      console.error('Error loading videos:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="text-center py-12">Loading...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <VideoIcon className="w-8 h-8 text-primary-600" />
        <h1 className="text-3xl font-bold">Video Library</h1>
      </div>

      <div className="card">
        <p className="text-gray-600 dark:text-gray-400 mb-4">
          Manage your instructional video library. Videos are linked to techniques and appear as recall cards during session logging.
        </p>
        <p className="text-sm text-gray-500 dark:text-gray-500">
          Tip: Use the CLI to add videos with timestamps: <code className="bg-gray-100 dark:bg-gray-800 px-2 py-1 rounded">rivaflow video add URL --title "Title" --technique "armbar"</code>
        </p>
      </div>

      {videos.length === 0 ? (
        <div className="card text-center py-12">
          <VideoIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-500 dark:text-gray-400 mb-4">No videos in your library yet</p>
          <p className="text-sm text-gray-400 dark:text-gray-500">
            Add videos using the CLI command above to build your instructional library
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {videos.map((video) => (
            <div key={video.id} className="card hover:shadow-md transition-shadow">
              <div className="flex justify-between items-start mb-3">
                <h3 className="font-semibold text-lg">{video.title || 'Untitled Video'}</h3>
                <a
                  href={video.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary-600 hover:text-primary-700"
                >
                  <ExternalLink className="w-5 h-5" />
                </a>
              </div>

              <div className="text-sm text-gray-600 dark:text-gray-400 space-y-1 mb-3">
                <p className="truncate">{video.url}</p>
                {video.technique_id && (
                  <p className="text-primary-600">Linked to technique</p>
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
