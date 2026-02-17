/** Matches HH:MM in 24-hour format (00:00 to 23:59). */
export const HH_MM_RE = /^([01]\d|2[0-3]):([0-5]\d)$/;

/** Max image file size in bytes (5MB). */
export const MAX_IMAGE_SIZE = 5 * 1024 * 1024;

/** Accepted image MIME types. */
export const ACCEPTED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/webp', 'image/gif'];

/**
 * Validate an image file for upload (type + size check).
 * Returns an error string or null if valid.
 */
export function validateImageFile(file: File, maxSize = MAX_IMAGE_SIZE): string | null {
  if (!ACCEPTED_IMAGE_TYPES.includes(file.type)) {
    return 'Please select a valid image (JPEG, PNG, WebP, or GIF)';
  }
  if (file.size > maxSize) {
    return `File size must be under ${Math.round(maxSize / 1024 / 1024)}MB`;
  }
  return null;
}
