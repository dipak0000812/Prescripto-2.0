import React, { useState, useRef } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { uploadPrescriptionApi } from '../api/prescriptions';
import { generateUUID } from '../api/client';
import {
  UploadCloud,
  FileText,
  AlertCircle,
  Loader2,
  CheckCircle2,
  ShieldCheck,
  X,
  FileCheck,
  Sparkles,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';

export const UploadPrescriptionPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { session } = useAuth();
  const { t, language } = useLanguage();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const initialPatientRef = searchParams.get('patient_ref') || session?.patient_id || 'PAT-1001';

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [patientExternalId, setPatientExternalId] = useState<string>(initialPatientRef);
  const [idempotencyKey, setIdempotencyKey] = useState<string>(generateUUID());
  const [showAdvanced, setShowAdvanced] = useState<boolean>(false);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [isDragOver, setIsDragOver] = useState<boolean>(false);

  const validateAndSetFile = (file: File) => {
    setError(null);

    // Max 20 MB
    if (file.size > 20971520) {
      setError(`File size (${(file.size / 1024 / 1024).toFixed(1)} MB) exceeds maximum 20 MB limit.`);
      return;
    }

    // MIME / Extension
    const validExtensions = ['jpg', 'jpeg', 'png', 'tiff', 'tif', 'pdf'];
    const ext = file.name.split('.').pop()?.toLowerCase();
    if (!ext || !validExtensions.includes(ext)) {
      setError('Please upload a valid image (JPEG, PNG, TIFF) or scanned PDF document.');
      return;
    }

    setSelectedFile(file);

    if (file.type.startsWith('image/')) {
      const url = URL.createObjectURL(file);
      setPreviewUrl(url);
    } else {
      setPreviewUrl(null);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) {
      setError('Please select a prescription document to upload.');
      return;
    }

    setIsUploading(true);
    setError(null);

    try {
      const result = await uploadPrescriptionApi(
        selectedFile,
        patientExternalId.trim() || undefined,
        idempotencyKey.trim()
      );

      // Successfully enqueued -> Navigate to analysis tracker
      navigate(`/analyses/${result.analysis_id}`, {
        state: { newUpload: true, prescriptionId: result.prescription_id },
      });
    } catch (err: any) {
      setError(err?.message || 'Failed to process prescription.');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-in fade-in duration-150">
      {/* Title */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2.5">
          <UploadCloud className="w-6 h-6 text-teal-600" />
          {t('upload.title', 'Upload & Verify Prescription')}
        </h1>
        <p className="text-xs text-slate-500 mt-1">
          {t('upload.subtitle', 'Scan or upload a doctor\'s prescription for instant handwriting digitization, medication verification, and allergy checks.')}
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Form */}
        <div className="lg:col-span-2">
          <form onSubmit={handleSubmit} className="bg-white border border-slate-200 rounded-2xl p-6 sm:p-8 shadow-xs space-y-5">
            {error && (
              <div className="p-3.5 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-800 flex items-start gap-2.5">
                <AlertCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
                <div className="leading-relaxed">{error}</div>
              </div>
            )}

            {/* Dropzone */}
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
                {language === 'hi' ? 'पर्चे का फ़ोटो या फ़ाइल' : 'Prescription Photo or Scan'}
              </label>

              {!selectedFile ? (
                <div
                  onDragOver={(e) => {
                    e.preventDefault();
                    setIsDragOver(true);
                  }}
                  onDragLeave={() => setIsDragOver(false)}
                  onDrop={handleDrop}
                  onClick={() => fileInputRef.current?.click()}
                  className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition flex flex-col items-center justify-center ${
                    isDragOver
                      ? 'border-teal-500 bg-teal-50/50'
                      : 'border-slate-300 hover:border-teal-500 bg-slate-50 hover:bg-slate-100/60'
                  }`}
                >
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".jpg,.jpeg,.png,.tiff,.tif,.pdf"
                    className="hidden"
                    onChange={handleFileChange}
                  />
                  <div className="w-12 h-12 rounded-xl bg-teal-50 text-teal-700 flex items-center justify-center mb-3 border border-teal-200">
                    <UploadCloud className="w-6 h-6" />
                  </div>
                  <div className="text-xs font-semibold text-slate-900">
                    {t('upload.dropzone', 'Click to select a photo or drag and drop prescription file')}
                  </div>
                  <div className="text-[11px] text-slate-500 mt-1">
                    {t('upload.hint', 'Supports JPEG, PNG, TIFF, or scanned PDF • Maximum size: 20 MB')}
                  </div>
                </div>
              ) : (
                <div className="p-4 bg-teal-50 border border-teal-200 rounded-xl flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-teal-600 text-white font-bold flex items-center justify-center shadow-2xs">
                      <FileCheck className="w-5 h-5" />
                    </div>
                    <div>
                      <div className="text-xs font-bold text-slate-900 truncate max-w-xs">
                        {selectedFile.name}
                      </div>
                      <div className="text-[11px] text-teal-800 font-medium">
                        {(selectedFile.size / 1024).toFixed(1)} KB &bull; Ready for verification
                      </div>
                    </div>
                  </div>

                  <button
                    type="button"
                    onClick={() => {
                      setSelectedFile(null);
                      setPreviewUrl(null);
                    }}
                    className="p-1.5 hover:bg-teal-100 text-teal-700 rounded-lg transition"
                    title="Remove file"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              )}
            </div>

            {/* Patient ID Assignment */}
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5 flex items-center justify-between">
                <span>Assign to Patient</span>
                <span className="text-teal-700 font-medium text-[11px]">Links to medical history</span>
              </label>
              <input
                type="text"
                value={patientExternalId}
                onChange={(e) => setPatientExternalId(e.target.value)}
                placeholder="e.g. PAT-1001 or Patient Name"
                className="w-full px-3.5 py-2.5 text-xs bg-white border border-slate-300 rounded-xl text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-teal-600/20 focus:border-teal-600 transition font-medium"
              />
              <div className="flex items-center gap-1.5 mt-2 text-xs flex-wrap">
                <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider flex items-center gap-1">
                  <Sparkles className="w-3 h-3 text-amber-600" /> Quick Select:
                </span>
                <button
                  type="button"
                  onClick={() => setPatientExternalId('PAT-1001')}
                  className="px-2 py-0.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 text-[11px] font-medium transition"
                >
                  PAT-1001 (Rahul Verma)
                </button>
                <button
                  type="button"
                  onClick={() => setPatientExternalId('PAT-1002')}
                  className="px-2 py-0.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 text-[11px] font-medium transition"
                >
                  PAT-1002 (Pooja Sharma)
                </button>
              </div>
            </div>

            {/* Optional Advanced Settings (Collapsible) */}
            <div className="pt-2 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setShowAdvanced(!showAdvanced)}
                className="flex items-center justify-between w-full text-xs font-medium text-slate-600 hover:text-slate-900 py-1 transition"
              >
                <span>Submission Options</span>
                {showAdvanced ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
              </button>

              {showAdvanced && (
                <div className="mt-2.5 p-3 bg-slate-50 rounded-xl border border-slate-200 space-y-2 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="font-medium text-slate-700 text-[11px]">Submission Token:</span>
                    <button
                      type="button"
                      onClick={() => setIdempotencyKey(generateUUID())}
                      className="text-teal-700 hover:underline text-[11px] font-medium"
                    >
                      Regenerate
                    </button>
                  </div>
                  <input
                    type="text"
                    value={idempotencyKey}
                    onChange={(e) => setIdempotencyKey(e.target.value)}
                    className="w-full px-2.5 py-1.5 font-mono text-[11px] bg-white border border-slate-300 rounded-lg text-slate-700"
                  />
                  <p className="text-[11px] text-slate-500">
                    Prevents accidental double-submissions when retrying uploads.
                  </p>
                </div>
              )}
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isUploading || !selectedFile}
              className="w-full py-3 px-4 bg-teal-600 hover:bg-teal-700 text-white text-xs font-semibold rounded-xl shadow-xs transition disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {isUploading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Scanning & Verifying Prescription...</span>
                </>
              ) : (
                <>
                  <UploadCloud className="w-4 h-4" />
                  <span>Verify Prescription & Check Safety</span>
                </>
              )}
            </button>
          </form>
        </div>

        {/* Sidebar Info & Preview */}
        <div className="space-y-6">
          {/* Preview card */}
          {previewUrl && (
            <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs">
              <h4 className="text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
                Document Preview
              </h4>
              <div className="rounded-lg overflow-hidden border border-slate-200 max-h-64 flex items-center justify-center bg-slate-50">
                <img
                  src={previewUrl}
                  alt="Selected preview"
                  className="max-h-64 object-contain"
                />
              </div>
            </div>
          )}

          {/* Clinical Best Practices */}
          <div className="bg-white border border-slate-200 rounded-xl p-5 text-xs text-slate-600 space-y-3 shadow-xs">
            <h4 className="font-bold text-slate-900 flex items-center gap-2 text-xs">
              <ShieldCheck className="w-4 h-4 text-teal-600" />
              Scanning Recommendations
            </h4>
            <ul className="space-y-2 text-[11px] text-slate-600">
              <li className="flex items-start gap-2">
                <span className="w-4 h-4 rounded-full bg-teal-50 text-teal-800 border border-teal-200 font-bold text-[10px] flex items-center justify-center shrink-0 mt-0.5">1</span>
                <span><strong className="text-slate-800">Clear Lighting:</strong> Ensure all handwritten lines, dosages, and doctor notes are well illuminated without glare.</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="w-4 h-4 rounded-full bg-teal-50 text-teal-800 border border-teal-200 font-bold text-[10px] flex items-center justify-center shrink-0 mt-0.5">2</span>
                <span><strong className="text-slate-800">Drug Verification:</strong> Extracted medications are checked against the CDSCO Drug Master database.</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="w-4 h-4 rounded-full bg-teal-50 text-teal-800 border border-teal-200 font-bold text-[10px] flex items-center justify-center shrink-0 mt-0.5">3</span>
                <span><strong className="text-slate-800">Allergy Safeguard:</strong> Automatically cross-references patient's documented allergies for adverse contraindications.</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="w-4 h-4 rounded-full bg-teal-50 text-teal-800 border border-teal-200 font-bold text-[10px] flex items-center justify-center shrink-0 mt-0.5">4</span>
                <span><strong className="text-slate-800">Doctor Sign-Off:</strong> Results requiring review are routed to qualified doctors for final clinical approval.</span>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default UploadPrescriptionPage;
