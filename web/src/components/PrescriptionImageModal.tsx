import React, { useState } from 'react';
import { X, ZoomIn, ZoomOut, RotateCw, RefreshCw, AlertCircle, FileText, ExternalLink } from 'lucide-react';
import { getPrescriptionApi } from '../api/prescriptions';
import { Button } from './ui/Button';

interface PrescriptionImageModalProps {
  prescriptionId: string;
  initialImageUrl: string | null;
  mimeType?: string;
  isOpen: boolean;
  onClose: () => void;
}

export const PrescriptionImageModal: React.FC<PrescriptionImageModalProps> = ({
  prescriptionId,
  initialImageUrl,
  mimeType = 'image/jpeg',
  isOpen,
  onClose,
}) => {
  const [imageUrl, setImageUrl] = useState<string | null>(initialImageUrl);
  const [zoom, setZoom] = useState<number>(1);
  const [rotation, setRotation] = useState<number>(0);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [loadError, setLoadError] = useState<boolean>(false);

  if (!isOpen) return null;

  const handleRefreshUrl = async () => {
    setIsRefreshing(true);
    setLoadError(false);
    try {
      const detail = await getPrescriptionApi(prescriptionId);
      setImageUrl(detail.image_url);
    } catch {
      setLoadError(true);
    } finally {
      setIsRefreshing(false);
    }
  };

  const isPdf = mimeType.toLowerCase().includes('pdf');

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-stone-900/40 backdrop-blur-xs p-4 animate-in fade-in">
      <div className="bg-white rounded-2xl shadow-xl border border-stone-200 w-full max-w-5xl h-[88vh] flex flex-col overflow-hidden animate-in zoom-in-95 duration-150 text-left">
        {/* Header */}
        <div className="px-6 py-4 border-b border-stone-200 flex items-center justify-between bg-white">
          <div>
            <h3 className="text-base font-extrabold text-[#1C252E] flex items-center gap-2">
              <FileText className="w-4 h-4 text-[#0F5147]" />
              Prescription Document Inspector
            </h3>
            <p className="text-xs text-stone-500 font-mono mt-0.5">
              ID: {prescriptionId} &bull; MIME: {mimeType}
            </p>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleRefreshUrl}
              disabled={isRefreshing}
              leftIcon={<RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin text-[#0F5147]' : ''}`} />}
              className="min-h-[36px] text-xs"
            >
              Refresh Link
            </Button>

            {imageUrl && (
              <a
                href={imageUrl}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-stone-700 bg-stone-50 border border-stone-200 rounded-xl hover:bg-stone-100 transition min-h-[36px]"
                title="Open in new window"
              >
                <ExternalLink className="w-3.5 h-3.5 text-[#0F5147]" />
                <span>Open Raw</span>
              </a>
            )}

            <button
              onClick={onClose}
              className="p-1.5 text-stone-400 hover:text-stone-700 hover:bg-stone-100 rounded-xl transition"
              title="Close inspector"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Toolbar */}
        {!isPdf && (
          <div className="px-6 py-2.5 border-b border-stone-200 bg-[#FAF9F6] flex items-center justify-between text-xs text-stone-600">
            <div className="flex items-center gap-2">
              <button
                onClick={() => setZoom((z) => Math.min(z + 0.25, 3))}
                className="p-1.5 hover:bg-stone-200 rounded-lg text-stone-700 transition"
                title="Zoom in"
              >
                <ZoomIn className="w-4 h-4" />
              </button>
              <button
                onClick={() => setZoom((z) => Math.max(z - 0.25, 0.5))}
                className="p-1.5 hover:bg-stone-200 rounded-lg text-stone-700 transition"
                title="Zoom out"
              >
                <ZoomOut className="w-4 h-4" />
              </button>
              <span className="font-mono text-[11px] text-stone-700 font-semibold px-2">
                {Math.round(zoom * 100)}%
              </span>
              <button
                onClick={() => setRotation((r) => (r + 90) % 360)}
                className="p-1.5 hover:bg-stone-200 rounded-lg text-stone-700 transition"
                title="Rotate 90 degrees"
              >
                <RotateCw className="w-4 h-4" />
              </button>
              <button
                onClick={() => {
                  setZoom(1);
                  setRotation(0);
                }}
                className="px-2 py-1 text-[11px] text-stone-600 hover:text-stone-900 rounded transition font-medium"
              >
                Reset
              </button>
            </div>
            <div className="text-[11px] text-stone-500">
              Drag to pan &bull; Scroll to inspect fine handwritten text
            </div>
          </div>
        )}

        {/* Viewport */}
        <div className="flex-1 bg-stone-100/70 p-6 overflow-auto flex items-center justify-center relative">
          {loadError || !imageUrl ? (
            <div className="text-center p-8 bg-white border border-stone-200 rounded-2xl max-w-md space-y-3 shadow-2xs">
              <AlertCircle className="w-10 h-10 text-[#BE123C] mx-auto" />
              <div className="text-sm font-bold text-[#1C252E]">Scan Preview Unavailable</div>
              <p className="text-xs text-stone-600 leading-relaxed">
                The image storage link has expired or the file is stored under local disk fallback. Click
                &quot;Refresh Link&quot; to generate a fresh link.
              </p>
              <Button
                variant="primary"
                size="sm"
                onClick={handleRefreshUrl}
                disabled={isRefreshing}
                className="min-h-[40px] bg-[#0F5147] hover:bg-[#0A3831]"
              >
                Generate Link
              </Button>
            </div>
          ) : isPdf ? (
            <iframe
              src={imageUrl}
              title="PDF Prescription View"
              className="w-full h-full rounded-xl border border-stone-200 bg-white"
            />
          ) : (
            <div className="transition-transform duration-200 ease-out origin-center flex items-center justify-center">
              <img
                src={imageUrl}
                alt="Prescription scan"
                onError={() => setLoadError(true)}
                style={{
                  transform: `scale(${zoom}) rotate(${rotation}deg)`,
                  maxWidth: '100%',
                  maxHeight: '100%',
                }}
                className="rounded-xl shadow-md border border-stone-200 select-none cursor-grab active:cursor-grabbing object-contain"
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default PrescriptionImageModal;
