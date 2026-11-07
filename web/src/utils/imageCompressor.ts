/**
 * Client-side image validation, scaling, and compression utilities.
 * Conforms to Prescripto upload limits: max 20MB, JPEG/PNG/WebP, max 2500px long side.
 */

export const MAX_UPLOAD_BYTES = 20 * 1024 * 1024; // 20 MB
export const ALLOWED_MIME_TYPES = ['image/jpeg', 'image/png', 'image/webp', 'image/tiff'];
export const MAX_IMAGE_LONG_SIDE = 2500;
export const COMPRESSION_QUALITY = 0.85;

export interface ValidationResult {
  valid: boolean;
  error?: string;
}

/**
 * Validates file MIME type and size limits before processing or uploading.
 */
export function validateImageFile(file: File): ValidationResult {
  if (!file) {
    return { valid: false, error: 'No file selected.' };
  }

  const mime = (file.type || '').toLowerCase();

  if (mime === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf')) {
    return {
      valid: false,
      error: 'PDF uploads are not supported. Upload a JPEG, PNG or WebP image.',
    };
  }

  if (file.size > MAX_UPLOAD_BYTES) {
    const sizeMb = (file.size / (1024 * 1024)).toFixed(1);
    return {
      valid: false,
      error: `File size (${sizeMb} MB) exceeds maximum allowed limit of 20MB.`,
    };
  }

  const isAllowed = ALLOWED_MIME_TYPES.includes(mime) ||
    /\.(jpe?g|png|webp|tiff?)$/i.test(file.name);

  if (!isAllowed) {
    return {
      valid: false,
      error: `Unsupported file type (${file.type || 'unknown'}). Please upload a JPEG, PNG, or WebP photo.`,
    };
  }

  return { valid: true };
}

/**
 * Calculates new dimensions scaled to maxSide while preserving aspect ratio.
 */
export function calculateTargetDimensions(
  width: number,
  height: number,
  maxSide: number = MAX_IMAGE_LONG_SIDE
): { width: number; height: number } {
  if (width <= maxSide && height <= maxSide) {
    return { width, height };
  }

  if (width >= height) {
    const ratio = height / width;
    return {
      width: maxSide,
      height: Math.round(maxSide * ratio),
    };
  } else {
    const ratio = width / height;
    return {
      width: Math.round(maxSide * ratio),
      height: maxSide,
    };
  }
}

/**
 * Detects if current client is on a mobile device or tablet where native camera capture attribute works.
 */
export function isMobileDevice(): boolean {
  if (typeof navigator === 'undefined') return false;
  const userAgent = navigator.userAgent || '';
  const mobileRegex = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i;
  const isTouch = Boolean(navigator.maxTouchPoints && navigator.maxTouchPoints > 1);
  return mobileRegex.test(userAgent) || isTouch;
}

/**
 * Compresses large images client-side before upload to reduce network latency and payload size.
 * Resizes images so longest side is at most maxSide (default 2500px) and outputs JPEG (0.85).
 */
export async function compressImage(
  file: File,
  maxSide: number = MAX_IMAGE_LONG_SIDE,
  quality: number = COMPRESSION_QUALITY
): Promise<File> {
  // If running in a non-browser environment or SVG/small file, return original
  if (typeof window === 'undefined' || typeof document === 'undefined' || !file.type.startsWith('image/')) {
    return file;
  }

  return new Promise((resolve) => {
    const reader = new FileReader();
    reader.onerror = () => resolve(file);
    reader.onload = (event) => {
      const img = new Image();
      img.onerror = () => resolve(file);
      img.onload = () => {
        try {
          const { width, height } = calculateTargetDimensions(img.naturalWidth || img.width, img.naturalHeight || img.height, maxSide);

          // If no resize is needed and file size is already modest (< 2MB), keep original
          if (width === (img.naturalWidth || img.width) && height === (img.naturalHeight || img.height) && file.size < 2 * 1024 * 1024) {
            resolve(file);
            return;
          }

          const canvas = document.createElement('canvas');
          canvas.width = width;
          canvas.height = height;

          const ctx = canvas.getContext('2d');
          if (!ctx) {
            resolve(file);
            return;
          }

          // Use high quality image smoothing
          ctx.imageSmoothingEnabled = true;
          ctx.imageSmoothingQuality = 'high';
          ctx.drawImage(img, 0, 0, width, height);

          canvas.toBlob(
            (blob) => {
              if (!blob) {
                resolve(file);
                return;
              }

              // Only use compressed blob if it's actually smaller or if dimensions were scaled down
              if (blob.size < file.size || width < (img.naturalWidth || img.width)) {
                const newName = file.name.replace(/\.[^/.]+$/, '') + '.jpg';
                const compressedFile = new File([blob], newName, {
                  type: 'image/jpeg',
                  lastModified: Date.now(),
                });
                resolve(compressedFile);
              } else {
                resolve(file);
              }
            },
            'image/jpeg',
            quality
          );
        } catch {
          resolve(file);
        }
      };
      img.src = event.target?.result as string;
    };
    reader.readAsDataURL(file);
  });
}

