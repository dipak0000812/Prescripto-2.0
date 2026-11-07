import React, { useState, useEffect, useRef } from 'react';
import {
  X,
  ZoomIn,
  ZoomOut,
  RotateCw,
  RefreshCw,
  AlertCircle,
  FileText,
  ExternalLink,
  Quote,
  Crosshair,
} from 'lucide-react';
import { getPrescriptionApi } from '../api/prescriptions';
import { Button } from './ui/Button';

export interface PrescriptionImageModalProps {
  prescriptionId: string;
  initialImageUrl: string | null;
  mimeType?: string;
  isOpen: boolean;
  onClose: () => void;
  highlightBox?: [number, number, number, number] | null;
  quotedText?: string | null;
  medicineName?: string | null;
}

export function calculateHighlightBoxStyle(
  box: [number, number, number, number] | null | undefined,
  imageNaturalWidth: number = 1000,
  imageNaturalHeight: number = 1000
): { left: string; top: string; width: string; height: string } | null {
  if (!box || box.length !== 4) return null;

  const [ymin, xmin, ymax, xmax] = box;
  const isNormalized = ymin <= 1 && xmin <= 1 && ymax <= 1 && xmax <= 1;

  if (isNormalized) {
    return {
      left: `${(xmin * 100).toFixed(2)}%`,
      top: `${(ymin * 100).toFixed(2)}%`,
      width: `${((xmax - xmin) * 100).toFixed(2)}%`,
      height: `${((ymax - ymin) * 100).toFixed(2)}%`,
    };
  }

  const leftPct = (xmin / imageNaturalWidth) * 100;
  const topPct = (ymin / imageNaturalHeight) * 100;
  const widthPct = ((xmax - xmin) / imageNaturalWidth) * 100;
  const heightPct = ((ymax - ymin) / imageNaturalHeight) * 100;

  return {
    left: `${leftPct.toFixed(2)}%`,
    top: `${topPct.toFixed(2)}%`,
    width: `${widthPct.toFixed(2)}%`,
    height: `${heightPct.toFixed(2)}%`,
  };
}

export function handleInspectorKeyboard(
  key: string,
  state: { zoom: number; rotation: number; pan: { x: number; y: number } }
): {
  newZoom: number;
  newRotation: number;
  newPan: { x: number; y: number };
  closeModal: boolean;
} {
  let newZoom = state.zoom;
  let newRotation = state.rotation;
  let newPan = { ...state.pan };
  let closeModal = false;

  switch (key) {
    case 'Escape':
      closeModal = true;
      break;
    case '+':
    case '=':
      newZoom = Math.min(state.zoom + 0.25, 4);
      break;
    case '-':
    case '_':
      newZoom = Math.max(state.zoom - 0.25, 0.5);
      break;
    case 'r':
    case 'R':
      newRotation = (state.rotation + 90) % 360;
      break;
    case '0':
      newZoom = 1;
      newRotation = 0;
      newPan = { x: 0, y: 0 };
      break;
    case 'ArrowLeft':
      newPan.x += 30;
      break;
    case 'ArrowRight':
      newPan.x -= 30;
      break;
    case 'ArrowUp':
      newPan.y += 30;
      break;
    case 'ArrowDown':
      newPan.y -= 30;
      break;
  }

  return { newZoom, newRotation, newPan, closeModal };
}

export const PrescriptionImageModal: React.FC<PrescriptionImageModalProps> = ({
  prescriptionId,
  initialImageUrl,
  mimeType = 'image/jpeg',
  isOpen,
  onClose,
  highlightBox,
  quotedText,
  medicineName,
}) => {
  const [imageUrl, setImageUrl] = useState<string | null>(initialImageUrl);
  const [zoom, setZoom] = useState<number>(1);
  const [rotation, setRotation] = useState<number>(0);
  const [pan, setPan] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [loadError, setLoadError] = useState<boolean>(false);

  // Dragging state
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const dragStartRef = useRef<{ startX: number; startY: number; initPanX: number; initPanY: number }>({
    startX: 0,
    startY: 0,
    initPanX: 0,
    initPanY: 0,
  });

  const imageRef = useRef<HTMLImageElement>(null);
  const [imageNaturalDims, setImageNaturalDims] = useState<{ width: number; height: number }>({
    width: 1000,
    height: 1000,
  });

  // Keyboard accessibility
  useEffect(() => {
    if (!isOpen) return;

    const onKeyDown = (e: KeyboardEvent) => {
      // Don't intercept if user is typing in an input
      if (['INPUT', 'TEXTAREA'].includes((e.target as HTMLElement)?.tagName)) return;

      const res = handleInspectorKeyboard(e.key, { zoom, rotation, pan });
      if (res.closeModal) {
        onClose();
        return;
      }
      setZoom(res.newZoom);
      setRotation(res.newRotation);
      setPan(res.newPan);
    };

    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [isOpen, zoom, rotation, pan, onClose]);

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

  const handleMouseDown = (e: React.MouseEvent) => {
    if (e.button !== 0) return; // Left click only
    setIsDragging(true);
    dragStartRef.current = {
      startX: e.clientX,
      startY: e.clientY,
      initPanX: pan.x,
      initPanY: pan.y,
    };
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging) return;
    const dx = e.clientX - dragStartRef.current.startX;
    const dy = e.clientY - dragStartRef.current.startY;
    setPan({
      x: dragStartRef.current.initPanX + dx,
      y: dragStartRef.current.initPanY + dy,
    });
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  const isPdf = mimeType.toLowerCase().includes('pdf');
  const boxStyle = calculateHighlightBoxStyle(
    highlightBox,
    imageNaturalDims.width,
    imageNaturalDims.height
  );

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="Prescription Image Inspector"
      className="fixed inset-0 z-50 flex items-center justify-center bg-stone-900/40 backdrop-blur-xs p-4 animate-in fade-in"
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
    >
      <div className="bg-white rounded-2xl shadow-xl border border-stone-200 w-full max-w-5xl h-[90vh] flex flex-col overflow-hidden animate-in zoom-in-95 duration-150 text-left">
        {/* Header */}
        <div className="px-6 py-3.5 border-b border-stone-200 flex items-center justify-between bg-white shrink-0">
          <div>
            <h3 className="text-base font-extrabold text-[#1C252E] flex items-center gap-2">
              <FileText className="w-4 h-4 text-[#0F5147]" />
              Prescription Document Inspector
            </h3>
            <p className="text-xs text-stone-500 font-mono mt-0.5">
              ID: {prescriptionId} &bull; MIME: {mimeType}
              {medicineName && <span className="ml-2 font-bold text-[#0F5147]">&bull; {medicineName}</span>}
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
                title="Open raw image in new tab"
              >
                <ExternalLink className="w-3.5 h-3.5 text-[#0F5147]" />
                <span>Open Raw</span>
              </a>
            )}

            <button
              onClick={onClose}
              className="p-1.5 text-stone-400 hover:text-stone-700 hover:bg-stone-100 rounded-xl transition"
              title="Close inspector (Esc)"
              aria-label="Close inspector"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Toolbar */}
        {!isPdf && (
          <div className="px-6 py-2 border-b border-stone-200 bg-[#FAF9F6] flex items-center justify-between text-xs text-stone-600 shrink-0">
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => setZoom((z) => Math.min(z + 0.25, 4))}
                className="p-1.5 hover:bg-stone-200 rounded-lg text-stone-700 transition"
                title="Zoom in (+)"
              >
                <ZoomIn className="w-4 h-4" />
              </button>
              <button
                type="button"
                onClick={() => setZoom((z) => Math.max(z - 0.25, 0.5))}
                className="p-1.5 hover:bg-stone-200 rounded-lg text-stone-700 transition"
                title="Zoom out (-)"
              >
                <ZoomOut className="w-4 h-4" />
              </button>
              <span className="font-mono text-[11px] text-stone-700 font-semibold px-2">
                {Math.round(zoom * 100)}%
              </span>
              <button
                type="button"
                onClick={() => setRotation((r) => (r + 90) % 360)}
                className="p-1.5 hover:bg-stone-200 rounded-lg text-stone-700 transition"
                title="Rotate 90 degrees (r)"
              >
                <RotateCw className="w-4 h-4" />
              </button>
              <button
                type="button"
                onClick={() => {
                  setZoom(1);
                  setRotation(0);
                  setPan({ x: 0, y: 0 });
                }}
                className="px-2 py-1 text-[11px] text-stone-600 hover:text-stone-900 rounded transition font-medium"
                title="Reset zoom and rotation (0)"
              >
                Reset
              </button>
            </div>
            <div className="hidden sm:block text-[11px] text-stone-500">
              Drag to pan &bull; Arrow keys &bull; +/- to zoom &bull; Esc to close
            </div>
          </div>
        )}

        {/* Viewport */}
        <div
          className="flex-1 bg-stone-100/70 p-4 sm:p-6 overflow-hidden flex items-center justify-center relative select-none"
          onMouseDown={handleMouseDown}
        >
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
            <div
              style={{
                transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom}) rotate(${rotation}deg)`,
                cursor: isDragging ? 'grabbing' : 'grab',
                transition: isDragging ? 'none' : 'transform 150ms ease-out',
              }}
              className="relative max-w-full max-h-full inline-block origin-center"
            >
              <img
                ref={imageRef}
                src={imageUrl}
                alt="Prescription scan"
                onLoad={(e) => {
                  const target = e.currentTarget;
                  setImageNaturalDims({
                    width: target.naturalWidth || 1000,
                    height: target.naturalHeight || 1000,
                  });
                }}
                onError={() => setLoadError(true)}
                draggable={false}
                className="rounded-xl shadow-md border border-stone-200 object-contain pointer-events-none max-h-[60vh] sm:max-h-[65vh]"
              />

              {/* Bounding box highlight if available */}
              {boxStyle && (
                <div
                  style={boxStyle}
                  className="absolute border-2 border-emerald-500 bg-emerald-500/20 rounded shadow-md pointer-events-none animate-pulse flex items-start justify-end p-1"
                >
                  <span className="bg-emerald-700 text-white text-[10px] font-bold px-1.5 py-0.5 rounded shadow">
                    {medicineName || 'Detected Item'}
                  </span>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Quoted Text Callout Panel */}
        {quotedText && (
          <div className="p-4 bg-[#FAF9F6] border-t border-stone-200 shrink-0">
            <div className="max-w-4xl mx-auto flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs">
              <div className="flex items-start gap-2.5">
                <div className="p-2 bg-[#E6F0EE] text-[#0F5147] rounded-xl shrink-0 mt-0.5 border border-[#9DC1BB]">
                  <Quote className="w-4 h-4" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-extrabold text-[#1C252E]">Quoted Prescription Text</span>
                    {medicineName && (
                      <span className="bg-stone-200 text-stone-800 text-[10px] font-bold px-2 py-0.5 rounded-full">
                        {medicineName}
                      </span>
                    )}
                  </div>
                  <blockquote className="mt-1 text-sm font-semibold text-[#1C252E] italic bg-white px-3 py-1.5 rounded-lg border border-stone-200 inline-block">
                    &ldquo;{quotedText}&rdquo;
                  </blockquote>
                </div>
              </div>

              <div className="flex items-center gap-1.5 text-stone-500 text-[11px] self-end sm:self-center">
                {boxStyle ? (
                  <span className="inline-flex items-center gap-1 text-emerald-700 font-medium">
                    <Crosshair className="w-3.5 h-3.5" />
                    Highlighted region shown in green box
                  </span>
                ) : (
                  <span className="text-stone-500">
                    Text extracted directly from document scan
                  </span>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default PrescriptionImageModal;
