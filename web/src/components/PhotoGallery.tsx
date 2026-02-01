import { useState, useEffect } from 'react';
import { Trash2, X } from 'lucide-react';
import { photosApi } from '../api/client';
import ConfirmDialog from './ConfirmDialog';
import { useToast } from '../contexts/ToastContext';

interface Photo {
  id: number;
  file_name: string;
  caption?: string;
  url: string;
  created_at: string;
}

interface PhotoGalleryProps {
  activityType: 'session' | 'readiness' | 'rest';
  activityId: number;
  onPhotoCountChange?: (count: number) => void;
}

export default function PhotoGallery({
  activityType,
  activityId,
  onPhotoCountChange,
}: PhotoGalleryProps) {
  const [photos, setPhotos] = useState<Photo[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedPhoto, setSelectedPhoto] = useState<Photo | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [photoToDelete, setPhotoToDelete] = useState<number | null>(null);
  const toast = useToast();

  useEffect(() => {
    loadPhotos();
  }, [activityType, activityId]);

  const loadPhotos = async () => {
    setLoading(true);
    try {
      const response = await photosApi.getByActivity(activityType, activityId);
      // Handle both array response (from stub endpoint) and object response (from real endpoint)
      if (Array.isArray(response.data)) {
        setPhotos(response.data);
        onPhotoCountChange?.(response.data.length);
      } else if (response.data.photos) {
        setPhotos(response.data.photos);
        onPhotoCountChange?.(response.data.count);
      } else {
        // Handle error or unexpected response format gracefully
        setPhotos([]);
        onPhotoCountChange?.(0);
      }
    } catch (error) {
      console.error('Error loading photos:', error);
      // Gracefully handle errors - set empty photos instead of crashing
      setPhotos([]);
      onPhotoCountChange?.(0);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (photoId: number) => {
    setDeleting(true);
    try {
      await photosApi.delete(photoId);
      await loadPhotos();
      setSelectedPhoto(null);
      setPhotoToDelete(null);
      toast.success('Photo deleted successfully');
    } catch (error: any) {
      console.error('Error deleting photo:', error);
      toast.error(error.response?.data?.detail || 'Failed to delete photo');
    } finally {
      setDeleting(false);
    }
  };

  if (loading) {
    return <div className="text-center py-4">Loading photos...</div>;
  }

  if (photos.length === 0) {
    return null;
  }

  return (
    <>
      <div className="grid grid-cols-3 gap-2" role="list" aria-label="Photo gallery">
        {photos.map((photo) => (
          <div
            key={photo.id}
            className="relative aspect-square cursor-pointer group"
            onClick={() => setSelectedPhoto(photo)}
            role="listitem"
          >
            <img
              src={`/api${photo.url}`}
              alt={photo.caption || 'Activity photo'}
              className="w-full h-full object-cover rounded-lg"
            />
            <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-30 transition-all rounded-lg" />
            <button
              onClick={(e) => {
                e.stopPropagation();
                setPhotoToDelete(photo.id);
              }}
              disabled={deleting}
              className="absolute top-1 right-1 p-1 bg-red-500 text-white rounded-full opacity-0 group-hover:opacity-100 transition-opacity hover:bg-red-600"
              aria-label={`Delete photo ${photo.caption ? photo.caption : ''}`}
            >
              <Trash2 className="w-3 h-3" />
            </button>
          </div>
        ))}
      </div>

      {/* Lightbox */}
      {selectedPhoto && (
        <div
          className="fixed inset-0 bg-black bg-opacity-90 z-50 flex items-center justify-center p-4"
          onClick={() => setSelectedPhoto(null)}
          role="dialog"
          aria-modal="true"
          aria-label="Photo viewer"
        >
          <div className="relative max-w-4xl max-h-full">
            <button
              onClick={() => setSelectedPhoto(null)}
              className="absolute -top-10 right-0 text-white hover:text-gray-300"
              aria-label="Close photo viewer"
            >
              <X className="w-8 h-8" />
            </button>
            <img
              src={`/api${selectedPhoto.url}`}
              alt={selectedPhoto.caption || 'Activity photo'}
              className="max-w-full max-h-[80vh] object-contain"
              onClick={(e) => e.stopPropagation()}
            />
            {selectedPhoto.caption && (
              <p className="text-white text-center mt-4 text-lg">
                {selectedPhoto.caption}
              </p>
            )}
          </div>
        </div>
      )}

      {/* Delete Confirmation */}
      <ConfirmDialog
        isOpen={photoToDelete !== null}
        onClose={() => setPhotoToDelete(null)}
        onConfirm={() => photoToDelete && handleDelete(photoToDelete)}
        title="Delete Photo"
        message="Are you sure you want to delete this photo? This action cannot be undone."
        confirmText="Delete"
        cancelText="Cancel"
        variant="danger"
      />
    </>
  );
}
