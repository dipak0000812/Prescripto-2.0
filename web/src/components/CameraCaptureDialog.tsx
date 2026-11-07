import React, { useState, useEffect, useRef } from 'react';
import { Camera, RefreshCw, Check, X, AlertCircle, Upload } from 'lucide-react';
import { Button } from './ui/Button';

interface CameraCaptureDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onCapture: (file: File) => void;
  onFallbackToFilePicker: () => void;
}

export const CameraCaptureDialog: React.FC<CameraCaptureDialogProps> = ({
  isOpen,
  onClose,
  onCapture,
  onFallbackToFilePicker,
}) => {
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [capturedBlob, setCapturedBlob] = useState<Blob | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [isInitializing, setIsInitializing] = useState<boolean>(true);

  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  // Stop video stream helper
  const stopTracks = () => {
    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
      setStream(null);
    }
  };

  // Start camera on open
  useEffect(() => {
    if (!isOpen) {
      stopTracks();
      setCapturedBlob(null);
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
        setPreviewUrl(null);
      }
      setErrorMsg(null);
      return;
    }

    let isMounted = true;
    setIsInitializing(true);
    setErrorMsg(null);

    const startCamera = async () => {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        if (isMounted) {
          setErrorMsg('Camera access is not supported by your browser. Please choose an image from your files.');
          setIsInitializing(false);
        }
        return;
      }

      try {
        const mediaStream = await navigator.mediaDevices.getUserMedia({
          video: {
            facingMode: 'environment',
            width: { ideal: 1920 },
            height: { ideal: 1080 },
          },
          audio: false,
        });

        if (!isMounted) {
          mediaStream.getTracks().forEach((t) => t.stop());
          return;
        }

        setStream(mediaStream);
        if (videoRef.current) {
          videoRef.current.srcObject = mediaStream;
        }
      } catch (err: unknown) {
        if (!isMounted) return;
        const e = err as Error;
        if (e.name === 'NotAllowedError' || e.name === 'PermissionDeniedError') {
          setErrorMsg('Camera permission was denied. Please allow camera access in your browser settings, or select a file instead.');
        } else if (e.name === 'NotFoundError' || e.name === 'DevicesNotFoundError') {
          setErrorMsg('No camera was detected on this device. Please select a photo from your files.');
        } else {
          setErrorMsg(`Unable to access camera (${e.message || 'Error'}). Please upload a file.`);
        }
      } finally {
        if (isMounted) setIsInitializing(false);
      }
    };

    startCamera();

    return () => {
      isMounted = false;
      stopTracks();
    };
  }, [isOpen]);

  // Handle escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  // Capture frame to canvas
  const handleTakePhoto = () => {
    if (!videoRef.current || !canvasRef.current) return;
    const video = videoRef.current;
    const canvas = canvasRef.current;

    canvas.width = video.videoWidth || 1280;
    canvas.height = video.videoHeight || 720;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    canvas.toBlob(
      (blob) => {
        if (blob) {
          setCapturedBlob(blob);
          const url = URL.createObjectURL(blob);
          setPreviewUrl(url);
          // Pause camera while reviewing photo
          stopTracks();
        }
      },
      'image/jpeg',
      0.92
    );
  };

  // Retake photo: restart camera stream
  const handleRetake = async () => {
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
      setPreviewUrl(null);
    }
    setCapturedBlob(null);
    setIsInitializing(true);
    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment', width: { ideal: 1920 } },
        audio: false,
      });
      setStream(mediaStream);
      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
      }
    } catch (err: unknown) {
      const e = err as Error;
      setErrorMsg(e.message || 'Unable to re-initialize camera.');
    } finally {
      setIsInitializing(false);
    }
  };

  // Confirm and use captured photo
  const handleUsePhoto = () => {
    if (!capturedBlob) return;
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const photoFile = new File([capturedBlob], `prescription-camera-${timestamp}.jpg`, {
      type: 'image/jpeg',
      lastModified: Date.now(),
    });
    onCapture(photoFile);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4 animate-in fade-in">
      <div className="bg-white rounded-2xl shadow-2xl border border-stone-200 w-full max-w-2xl overflow-hidden flex flex-col text-left">
        {/* Header */}
        <div className="px-5 py-3.5 border-b border-stone-200 flex items-center justify-between bg-[#FAF9F6]">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-[#E6F0EE] text-[#0F5147] border border-[#9DC1BB] flex items-center justify-center font-bold">
              <Camera className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-[#1C252E]">Take Prescription Photo</h3>
              <p className="text-xs text-stone-500">Position the prescription clearly inside the frame</p>
            </div>
          </div>
          <button
            onClick={onClose}
            aria-label="Close camera dialog"
            className="p-1.5 rounded-lg text-stone-500 hover:text-[#1C252E] hover:bg-stone-200/50 transition-colors cursor-pointer min-h-[40px] min-w-[40px] flex items-center justify-center"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Viewport Area */}
        <div className="relative bg-black min-h-[360px] max-h-[60vh] flex items-center justify-center overflow-hidden">
          {errorMsg ? (
            <div className="p-6 text-center max-w-md">
              <AlertCircle className="w-12 h-12 text-amber-400 mx-auto mb-3" />
              <h4 className="text-sm font-bold text-white mb-2">Camera Unavailable</h4>
              <p className="text-xs text-stone-300 mb-5 leading-relaxed">{errorMsg}</p>
              <Button
                variant="primary"
                onClick={() => {
                  onClose();
                  onFallbackToFilePicker();
                }}
                className="inline-flex items-center gap-2"
              >
                <Upload className="w-4 h-4" />
                Choose File from Gallery Instead
              </Button>
            </div>
          ) : previewUrl ? (
            <img src={previewUrl} alt="Captured Prescription" className="max-h-[60vh] w-auto object-contain" />
          ) : (
            <>
              <video
                ref={videoRef}
                autoPlay
                playsInline
                muted
                className="w-full h-full object-cover max-h-[60vh]"
              />
              {/* Prescription viewfinder overlay guide */}
              <div className="absolute inset-6 border-2 border-dashed border-white/60 rounded-xl pointer-events-none flex flex-col justify-between p-3">
                <span className="text-[10px] text-white/80 bg-black/40 px-2 py-0.5 rounded self-start">
                  Align prescription edges
                </span>
                <span className="text-[10px] text-white/80 bg-black/40 px-2 py-0.5 rounded self-end">
                  Ensure doctor&apos;s handwriting is sharp
                </span>
              </div>
              {isInitializing && (
                <div className="absolute inset-0 bg-black/80 flex items-center justify-center text-white text-xs gap-2">
                  <RefreshCw className="w-4 h-4 animate-spin text-teal-400" />
                  Starting camera...
                </div>
              )}
            </>
          )}

          {/* Hidden Canvas for capture */}
          <canvas ref={canvasRef} className="hidden" />
        </div>

        {/* Footer Actions */}
        <div className="px-5 py-3.5 bg-stone-50 border-t border-stone-200 flex items-center justify-between">
          <Button
            variant="outline"
            onClick={() => {
              onClose();
              onFallbackToFilePicker();
            }}
            className="text-xs text-stone-600 inline-flex items-center gap-1.5"
          >
            <Upload className="w-3.5 h-3.5" />
            Upload File Instead
          </Button>

          <div className="flex items-center gap-2">
            {previewUrl ? (
              <>
                <Button variant="outline" onClick={handleRetake} className="inline-flex items-center gap-1.5 text-xs">
                  <RefreshCw className="w-3.5 h-3.5" />
                  Retake Photo
                </Button>
                <Button variant="primary" onClick={handleUsePhoto} className="inline-flex items-center gap-1.5 text-xs">
                  <Check className="w-3.5 h-3.5" />
                  Use This Photo
                </Button>
              </>
            ) : (
              <Button
                variant="primary"
                onClick={handleTakePhoto}
                disabled={isInitializing || Boolean(errorMsg)}
                className="inline-flex items-center gap-2 font-bold px-5"
              >
                <Camera className="w-4 h-4" />
                Capture
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

