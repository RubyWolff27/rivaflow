import { useState } from 'react';
import { Camera, Upload, X } from 'lucide-react';
import { photosApi } from '../api/client';

interface PhotoUploadProps {
  activityType: 'session' | 'readiness' | 'rest';
  activityId: number;
  activityDate: string;
  currentPhotoCount: number;
  onUploadSuccess: () => void;
}

export default function PhotoUpload({
  activityType,
  activityId,
  activityDate,
  currentPhotoCount,
  onUploadSuccess,
}: PhotoUploadProps) {
  const [uploading, setUploading] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [caption, setCaption] = useState('');
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  const maxPhotos = 3;
  const canUpload = currentPhotoCount < maxPhotos;

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validate file type
    const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
    if (!allowedTypes.includes(file.type)) {
      alert('Invalid file type. Please upload a JPG, PNG, GIF, or WebP image.');
      return;
    }

    // Validate file size (10MB)
    const maxSize = 10 * 1024 * 1024;
    if (file.size > maxSize) {
      alert('File too large. Maximum size is 10MB.');
      return;
    }

    setSelectedFile(file);
    setPreviewUrl(URL.createObjectURL(file));
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('activity_type', activityType);
      formData.append('activity_id', activityId.toString());
      formData.append('activity_date', activityDate);
      if (caption) {
        formData.append('caption', caption);
      }

      await photosApi.upload(formData);

      // Reset form
      setSelectedFile(null);
      setCaption('');
      setPreviewUrl(null);

      // Notify parent
      onUploadSuccess();
    } catch (error: any) {
      console.error('Error uploading photo:', error);
      alert(error.response?.data?.detail || 'Failed to upload photo');
    } finally {
      setUploading(false);
    }
  };

  const handleCancel = () => {
    setSelectedFile(null);
    setCaption('');
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
      setPreviewUrl(null);
    }
  };

  if (!canUpload) {
    return (
      <div className="text-center py-4 text-gray-500 dark:text-gray-400">
        Maximum {maxPhotos} photos reached for this activity
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {!selectedFile ? (
        <div>
          <label className="flex flex-col items-center justify-center w-full h-32 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg cursor-pointer hover:border-purple-500 dark:hover:border-purple-400 transition-colors">
            <div className="flex flex-col items-center justify-center pt-5 pb-6">
              <Camera className="w-8 h-8 mb-2 text-gray-400" />
              <p className="text-sm text-gray-600 dark:text-gray-400">
                <span className="font-semibold">Click to upload</span> or drag and drop
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-500">
                JPG, PNG, GIF, WebP (max 10MB)
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                {currentPhotoCount}/{maxPhotos} photos uploaded
              </p>
            </div>
            <input
              type="file"
              className="hidden"
              accept="image/jpeg,image/png,image/gif,image/webp"
              onChange={handleFileSelect}
            />
          </label>
        </div>
      ) : (
        <div className="space-y-4">
          {/* Preview */}
          <div className="relative">
            <img
              src={previewUrl || ''}
              alt="Preview"
              className="w-full h-64 object-cover rounded-lg"
            />
            <button
              onClick={handleCancel}
              className="absolute top-2 right-2 p-1 bg-red-500 text-white rounded-full hover:bg-red-600 transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Caption */}
          <div>
            <label className="label">Caption (optional)</label>
            <input
              type="text"
              className="input"
              value={caption}
              onChange={(e) => setCaption(e.target.value)}
              placeholder="Add a caption..."
              maxLength={200}
            />
          </div>

          {/* Upload button */}
          <button
            onClick={handleUpload}
            disabled={uploading}
            className="btn-primary w-full flex items-center justify-center gap-2"
          >
            <Upload className="w-4 h-4" />
            {uploading ? 'Uploading...' : 'Upload Photo'}
          </button>
        </div>
      )}
    </div>
  );
}
