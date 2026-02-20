/** Client-side image compression using Canvas API. */

interface CompressOptions {
  maxWidth?: number;
  maxHeight?: number;
  quality?: number;
}

const SKIP_SIZE = 200 * 1024; // Skip compression for files under 200KB

/**
 * Compress an image file by resizing and re-encoding.
 * Skips GIFs (would lose animation) and small files (under 200KB).
 * Returns the original file if compression isn't beneficial.
 */
export async function compressImage(
  file: File,
  options: CompressOptions = {}
): Promise<File> {
  const { maxWidth = 1920, maxHeight = 1920, quality = 0.82 } = options;

  // Skip GIFs (lose animation) and small files
  if (file.type === 'image/gif' || file.size <= SKIP_SIZE) {
    return file;
  }

  const bitmap = await createImageBitmapCompat(file);
  const { width, height } = bitmap;

  // Skip if already within bounds
  if (width <= maxWidth && height <= maxHeight && file.size <= SKIP_SIZE * 5) {
    if ('close' in bitmap) (bitmap as ImageBitmap).close();
    return file;
  }

  // Calculate scaled dimensions maintaining aspect ratio
  let newWidth = width;
  let newHeight = height;
  if (newWidth > maxWidth) {
    newHeight = Math.round((newHeight * maxWidth) / newWidth);
    newWidth = maxWidth;
  }
  if (newHeight > maxHeight) {
    newWidth = Math.round((newWidth * maxHeight) / newHeight);
    newHeight = maxHeight;
  }

  // Draw to canvas
  const canvas = document.createElement('canvas');
  canvas.width = newWidth;
  canvas.height = newHeight;
  const ctx = canvas.getContext('2d');
  if (!ctx) {
    if ('close' in bitmap) (bitmap as ImageBitmap).close();
    return file;
  }
  ctx.drawImage(bitmap, 0, 0, newWidth, newHeight);
  if ('close' in bitmap) (bitmap as ImageBitmap).close();

  // Export as WebP if supported, else JPEG
  const outputType = file.type === 'image/png' ? 'image/png' : 'image/jpeg';
  const blob = await new Promise<Blob | null>((resolve) =>
    canvas.toBlob(resolve, outputType, quality)
  );

  if (!blob || blob.size >= file.size) {
    return file; // Compression didn't help
  }

  return new File([blob], file.name, { type: outputType, lastModified: Date.now() });
}

/** Fallback for browsers without createImageBitmap (older Safari). */
function createImageBitmapCompat(
  file: File
): Promise<ImageBitmap | HTMLImageElement> {
  if (typeof createImageBitmap === 'function') {
    return createImageBitmap(file);
  }
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = reject;
    img.src = URL.createObjectURL(file);
  });
}
