import React, { useState, useRef, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { uploadPrescriptionApi } from '../api/prescriptions';
import { generateUUID } from '../api/client';
import {
  Camera,
  Image as ImageIcon,
  RotateCcw,
  CheckCircle2,
  AlertTriangle,
  X,
  ArrowRight,
  ShieldCheck,
  RefreshCw,
  FileText,
  ChevronDown,
  ChevronUp,
  FileCheck,
  Clock,
  Sparkles,
  User as UserIcon,
  Search,
  UserPlus,
} from 'lucide-react';
import { Button } from '../components/ui/Button';
import { AlertBanner } from '../components/ui/AlertBanner';
import { StatusChip } from '../components/ui/StatusChip';
import { SegmentedControl } from '../components/ui/SegmentedControl';
import { Checkbox } from '../components/ui/Checkbox';
import { CameraCaptureDialog } from '../components/CameraCaptureDialog';
import { compressImage, validateImageFile, isMobileDevice } from '../utils/imageCompressor';
import { searchPatientsApi, createPatientApi, PatientSummary } from '../api/patients';

export const UploadPrescriptionPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { session } = useAuth();
  const { t } = useLanguage();

  const cameraInputRef = useRef<HTMLInputElement>(null);
  const galleryInputRef = useRef<HTMLInputElement>(null);

  const initialPatientRef = searchParams.get('patient_ref') || session?.patient_id || '';
  const isPatientUser = Boolean(session?.is_patient || session?.patient_id || session?.role === 'OPERATOR');

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [patientExternalId, setPatientExternalId] = useState<string>(initialPatientRef);
  const [idempotencyKey, setIdempotencyKey] = useState<string>(generateUUID());
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [consentChecked, setConsentChecked] = useState<boolean>(false);
  const [consentError, setConsentError] = useState<boolean>(false);
  const [showPatientRef, setShowPatientRef] = useState<boolean>(Boolean(initialPatientRef));

  // Camera Dialog & Image Compression states
  const [isCameraDialogOpen, setIsCameraDialogOpen] = useState<boolean>(false);
  const [isCompressing, setIsCompressing] = useState<boolean>(false);

  // Reviewer / Doctor Patient Intake Linking State
  const [patientMode, setPatientMode] = useState<'existing' | 'new' | 'walkin'>(
    initialPatientRef ? 'existing' : isPatientUser ? 'existing' : 'walkin'
  );
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [patientSearchResults, setPatientSearchResults] = useState<PatientSummary[]>([]);
  const [selectedPatient, setSelectedPatient] = useState<PatientSummary | null>(null);
  const [isSearchingPatient, setIsSearchingPatient] = useState<boolean>(false);

  // Quick Create Patient Modal/Form State
  const [newPatientName, setNewPatientName] = useState<string>('');
  const [newPatientPhone, setNewPatientPhone] = useState<string>('');
  const [newPatientAge, setNewPatientAge] = useState<string>('');
  const [newPatientGender, setNewPatientGender] = useState<string>('OTHER');
  const [isCreatingPatient, setIsCreatingPatient] = useState<boolean>(false);
  const [patientCreateError, setPatientCreateError] = useState<string | null>(null);

  // Uploading & waiting state
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [uploadProgressStep, setUploadProgressStep] = useState<1 | 2 | 3>(1);
  const [error, setError] = useState<string | null>(null);
  const [isDragOver, setIsDragOver] = useState<boolean>(false);
  const [showTips, setShowTips] = useState<boolean>(false);

  // Clean up blob URL on unmount or file change
  useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
    };
  }, [previewUrl]);

  // Debounced Patient Search for Doctor / Reviewer upload
  useEffect(() => {
    if (!searchQuery.trim() || isPatientUser) {
      setPatientSearchResults([]);
      return;
    }
    const timer = setTimeout(async () => {
      setIsSearchingPatient(true);
      try {
        const results = await searchPatientsApi(searchQuery.trim());
        setPatientSearchResults(results);
      } catch {
        setPatientSearchResults([]);
      } finally {
        setIsSearchingPatient(false);
      }
    }, 250);
    return () => clearTimeout(timer);
  }, [searchQuery, isPatientUser]);

  // Gentle progression for the friendly waiting screen while reading
  useEffect(() => {
    let timer1: any;
    let timer2: any;
    if (isUploading) {
      setUploadProgressStep(1);
      timer1 = setTimeout(() => {
        setUploadProgressStep(2);
      }, 3500);
      timer2 = setTimeout(() => {
        setUploadProgressStep(3);
      }, 10000);
    }
    return () => {
      if (timer1) clearTimeout(timer1);
      if (timer2) clearTimeout(timer2);
    };
  }, [isUploading]);

  const validateAndSetFile = async (file: File) => {
    setError(null);
    setConsentError(false);

    // 1. Client-side MIME and size validation (matching backend)
    const valResult = validateImageFile(file);
    if (!valResult.valid) {
      setError(valResult.error || 'Invalid file selected.');
      return;
    }

    setIsCompressing(true);
    try {
      // 2. Client-side compression for photos > 2500px long side
      const processedFile = await compressImage(file);

      if (selectedFile !== processedFile) {
        setIdempotencyKey(generateUUID());
      }
      setSelectedFile(processedFile);

      const url = URL.createObjectURL(processedFile);
      setPreviewUrl(url);
    } catch {
      // Fallback to original file if compression fails
      setSelectedFile(file);
      const url = URL.createObjectURL(file);
      setPreviewUrl(url);
    } finally {
      setIsCompressing(false);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      validateAndSetFile(e.target.files[0]);
    }
    e.target.value = '';
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleRemoveFile = () => {
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setSelectedFile(null);
    setPreviewUrl(null);
    setError(null);
    setConsentChecked(false);
    setConsentError(false);
    setIdempotencyKey(generateUUID());
  };

  const handleTakePhotoClick = () => {
    if (isMobileDevice()) {
      cameraInputRef.current?.click();
    } else {
      setIsCameraDialogOpen(true);
    }
  };

  const handleCreatePatientSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newPatientName.trim() || !newPatientPhone.trim()) {
      setPatientCreateError('Patient name and phone number are required.');
      return;
    }
    setIsCreatingPatient(true);
    setPatientCreateError(null);
    try {
      const created = await createPatientApi({
        name: newPatientName.trim(),
        phone_number: newPatientPhone.trim(),
        age: newPatientAge ? parseInt(newPatientAge, 10) : undefined,
        gender: newPatientGender,
      });
      setSelectedPatient(created);
      setPatientExternalId(created.patient_id);
      setPatientMode('existing');
      setNewPatientName('');
      setNewPatientPhone('');
      setNewPatientAge('');
    } catch (err: any) {
      setPatientCreateError(err?.response?.data?.detail || err?.message || 'Could not register patient.');
    } finally {
      setIsCreatingPatient(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) {
      setError('Please take a photo or select an image first.');
      return;
    }

    if (!consentChecked) {
      setConsentError(true);
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

      // Successfully enqueued -> navigate to analysis review screen
      navigate(`/analyses/${result.analysis_id}`, {
        state: { newUpload: true, prescriptionId: result.prescription_id },
      });
    } catch (err: any) {
      // Retain the selected file so user doesn't lose it upon recoverable error!
      const errorMsg =
        err?.response?.data?.detail ||
        err?.message ||
        'Could not upload prescription. Please check your internet connection and try again.';
      setError(errorMsg);
      setIsUploading(false);
    }
  };

  // =========================================================================
  // VIEW: FRIENDLY WAITING SCREEN (While reading the prescription)
  // =========================================================================
  if (isUploading) {
    return (
      <div className="max-w-xl mx-auto py-8 sm:py-12 px-4 animate-in fade-in duration-200">
        <div className="bg-white border border-stone-200 rounded-2xl p-6 sm:p-8 shadow-xs text-center space-y-6">
          {/* Gentle Animated Progress Ring */}
          <div className="relative w-20 h-20 mx-auto flex items-center justify-center">
            <div className="absolute inset-0 rounded-full border-4 border-[#E6F0EE]" />
            <div className="absolute inset-0 rounded-full border-4 border-[#0F5147] border-t-transparent animate-spin" />
            <Clock className="w-8 h-8 text-[#0F5147]" aria-hidden="true" />
          </div>

          <div className="space-y-2">
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-[#E6F0EE] text-[#0F5147] border border-[#9DC1BB]">
              <Sparkles className="w-3.5 h-3.5" aria-hidden="true" />
              <span>Step 2 of 3</span>
            </span>

            <h1 className="text-xl sm:text-2xl font-extrabold text-[#1C252E] tracking-tight">
              {t('upload.waiting_title', 'Reading your prescription… about 20 seconds')}
            </h1>

            <p className="text-sm text-stone-600 max-w-md mx-auto leading-relaxed">
              {t('upload.waiting_sub', 'Please keep this screen open. We are organizing your medicines.')}
            </p>
          </div>

          {/* Step-by-Step Progress Cards */}
          <div className="space-y-2.5 text-left pt-2">
            {/* Step 1 */}
            <div
              className={`p-3.5 rounded-xl border flex items-center gap-3 transition ${
                uploadProgressStep >= 1
                  ? 'bg-[#ECFDF5] border-[#A7F3D0] text-[#065F46]'
                  : 'bg-stone-50 border-stone-200 text-stone-500'
              }`}
            >
              {uploadProgressStep > 1 ? (
                <CheckCircle2 className="w-5 h-5 text-[#047857] shrink-0" aria-hidden="true" />
              ) : (
                <RefreshCw className="w-5 h-5 text-[#0F5147] animate-spin shrink-0" aria-hidden="true" />
              )}
              <span className="text-sm font-semibold">
                {t('upload.step1_progress', '1. Uploading prescription photo securely')}
              </span>
            </div>

            {/* Step 2 */}
            <div
              className={`p-3.5 rounded-xl border flex items-center gap-3 transition ${
                uploadProgressStep >= 2
                  ? uploadProgressStep > 2
                    ? 'bg-[#ECFDF5] border-[#A7F3D0] text-[#065F46]'
                    : 'bg-[#E6F0EE] border-[#9DC1BB] text-[#0F5147]'
                  : 'bg-stone-50 border-stone-200 text-stone-400'
              }`}
            >
              {uploadProgressStep > 2 ? (
                <CheckCircle2 className="w-5 h-5 text-[#047857] shrink-0" aria-hidden="true" />
              ) : uploadProgressStep === 2 ? (
                <RefreshCw className="w-5 h-5 text-[#0F5147] animate-spin shrink-0" aria-hidden="true" />
              ) : (
                <div className="w-5 h-5 rounded-full border-2 border-stone-300 shrink-0" />
              )}
              <span className="text-sm font-semibold">
                {t('upload.step2_progress', '2. Checking handwriting and image clarity')}
              </span>
            </div>

            {/* Step 3 */}
            <div
              className={`p-3.5 rounded-xl border flex items-center gap-3 transition ${
                uploadProgressStep >= 3
                  ? 'bg-[#E6F0EE] border-[#9DC1BB] text-[#0F5147]'
                  : 'bg-stone-50 border-stone-200 text-stone-400'
              }`}
            >
              {uploadProgressStep === 3 ? (
                <RefreshCw className="w-5 h-5 text-[#0F5147] animate-spin shrink-0" aria-hidden="true" />
              ) : (
                <div className="w-5 h-5 rounded-full border-2 border-stone-300 shrink-0" />
              )}
              <span className="text-sm font-semibold">
                {t('upload.step3_progress', '3. Organizing medicines and daily timings')}
              </span>
            </div>
          </div>

          {/* Reassurance note in plain words */}
          <div className="pt-2 border-t border-stone-100">
            <p className="text-xs text-stone-500 leading-relaxed">
              {t('upload.waiting_reassurance', 'We are carefully reading every line. Almost ready!')}
            </p>
          </div>
        </div>
      </div>
    );
  }

  // =========================================================================
  // VIEW: MAIN UPLOAD SCREEN
  // =========================================================================
  return (
    <div className="max-w-2xl mx-auto space-y-6 pb-12 animate-in fade-in duration-150">
      {/* Hidden file inputs for Camera and Gallery */}
      <input
        ref={cameraInputRef}
        type="file"
        accept="image/*"
        capture="environment"
        className="sr-only"
        onChange={handleFileChange}
        aria-hidden="true"
      />
      <input
        ref={galleryInputRef}
        type="file"
        accept="image/jpeg,image/png,image/tiff,.tif,.tiff"
        className="sr-only"
        onChange={handleFileChange}
        aria-hidden="true"
      />

      {/* Screen Header with Step Indicator */}
      <div className="text-left space-y-1.5">
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-[#E6F0EE] text-[#0F5147] border border-[#9DC1BB]">
          <ShieldCheck className="w-3.5 h-3.5 text-[#0F5147]" aria-hidden="true" />
          <span>{t('upload.step_badge', 'Step 1 of 3')}</span>
        </div>

        <h1 className="text-2xl sm:text-3xl font-extrabold text-[#1C252E] tracking-tight">
          {t('upload.title', 'Upload Prescription')}
        </h1>

        <p className="text-sm sm:text-base text-stone-600 leading-relaxed">
          {t('upload.subtitle', 'Take a photo or choose from gallery. We will explain your medicines simply.')}
        </p>
      </div>

      {/* Error Alert with Plain Words + Retry */}
      {error && (
        <AlertBanner
          type="error"
          title={t('upload.error_title', 'We could not read this photo')}
          badgeLabel="Problem"
          action={
            <button
              type="button"
              onClick={() => setError(null)}
              className="text-xs font-semibold text-[#BE123C] hover:underline flex items-center gap-1 cursor-pointer mt-1"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>{t('upload.try_again_btn', 'Try again')}</span>
            </button>
          }
        >
          {error}
        </AlertBanner>
      )}

      {/* MAIN UPLOAD / PREVIEW CONTAINER */}
      <form onSubmit={handleSubmit} className="space-y-6">
        {!selectedFile ? (
          /* ================= STATE A: NO FILE SELECTED YET ================= */
          <div className="space-y-4">
            {/* HUGE BUTTON 1: Take a Photo (Mobile Camera First / Desktop Modal) */}
            <button
              type="button"
              onClick={handleTakePhotoClick}
              className="w-full flex items-center gap-4 p-5 sm:p-6 bg-[#E6F0EE] hover:bg-[#D8E9E5] border-2 border-[#0F5147] rounded-2xl text-left cursor-pointer transition min-h-[96px] shadow-2xs group focus-visible:ring-2 focus-visible:ring-[#0F5147]"
              aria-label="Take a photo of your prescription with your camera"
            >
              <div className="w-14 h-14 sm:w-16 sm:h-16 rounded-2xl bg-[#0F5147] text-white flex items-center justify-center shrink-0 shadow-2xs group-hover:scale-105 transition">
                <Camera className="w-7 h-7 sm:w-8 sm:h-8" aria-hidden="true" />
              </div>
              <div className="min-w-0 flex-1">
                <span className="block text-lg sm:text-xl font-extrabold text-[#0F5147] leading-tight">
                  {t('upload.take_photo', 'Take a photo')}
                </span>
                <span className="block text-xs sm:text-sm text-stone-600 mt-0.5">
                  {t('upload.take_photo_sub', 'Use your camera to snap the prescription')}
                </span>
              </div>
              <ArrowRight className="w-5 h-5 text-[#0F5147] shrink-0" aria-hidden="true" />
            </button>

            {/* HUGE BUTTON 2: Choose from Gallery / Files */}
            <button
              type="button"
              onClick={() => galleryInputRef.current?.click()}
              className="w-full flex items-center gap-4 p-5 sm:p-6 bg-white hover:bg-[#F4F2EC] border-2 border-stone-300 rounded-2xl text-left cursor-pointer transition min-h-[96px] shadow-2xs group focus-visible:ring-2 focus-visible:ring-[#0F5147]"
              aria-label="Upload or choose from gallery"
            >
              <div className="w-14 h-14 sm:w-16 sm:h-16 rounded-2xl bg-[#F4F2EC] text-[#1C252E] border border-stone-200 flex items-center justify-center shrink-0 shadow-2xs group-hover:scale-105 transition">
                <ImageIcon className="w-7 h-7 sm:w-8 sm:h-8 text-stone-700" aria-hidden="true" />
              </div>
              <div className="min-w-0 flex-1">
                <span className="block text-lg sm:text-xl font-bold text-[#1C252E] leading-tight">
                  {t('upload.choose_gallery', 'Upload or choose from gallery')}
                </span>
                <span className="block text-xs sm:text-sm text-stone-600 mt-0.5">
                  {t('upload.choose_gallery_sub', 'Pick a saved photo or scan from your phone or computer')}
                </span>
              </div>
              <ArrowRight className="w-5 h-5 text-stone-400 shrink-0" aria-hidden="true" />
            </button>

            {/* Optional Desktop Drag & Drop Area */}
            <div
              onDragOver={(e) => {
                e.preventDefault();
                setIsDragOver(true);
              }}
              onDragLeave={() => setIsDragOver(false)}
              onDrop={handleDrop}
              onClick={() => galleryInputRef.current?.click()}
              className={`hidden sm:flex border border-dashed rounded-xl p-4 text-center items-center justify-center gap-2 cursor-pointer transition text-xs font-medium text-stone-500 ${
                isDragOver ? 'border-[#0F5147] bg-[#E6F0EE]/50 text-[#0F5147]' : 'border-stone-300 bg-stone-50/50 hover:bg-stone-100/60'
              }`}
            >
              <FileCheck className="w-4 h-4 text-stone-400" aria-hidden="true" />
              <span>{t('upload.or_drop', 'Or drag and drop your photo here on computer')}</span>
            </div>

            {/* PHOTO TIPS: Short Expandable Disclosure */}
            <div className="bg-white border border-stone-200 rounded-2xl p-4 sm:p-5 shadow-2xs text-left">
              <button
                type="button"
                onClick={() => setShowTips((prev) => !prev)}
                className="w-full flex items-center justify-between text-left cursor-pointer min-h-[40px]"
                aria-expanded={showTips}
              >
                <div className="flex items-center gap-2 font-bold text-sm text-[#1C252E]">
                  <ShieldCheck className="w-4 h-4 text-[#0F5147]" aria-hidden="true" />
                  <span>{t('upload.tips_title', 'Tips for a clear reading')}</span>
                </div>
                <div className="flex items-center gap-1 text-xs text-stone-500 font-medium">
                  <span>{showTips ? 'Hide tips' : 'Show tips'}</span>
                  <ChevronDown className={`w-4 h-4 transition-transform duration-200 ${showTips ? 'rotate-180' : ''}`} />
                </div>
              </button>

              {showTips && (
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs sm:text-sm pt-4 mt-2 border-t border-stone-100 animate-in fade-in-50 duration-150">
                  <div className="p-3 bg-[#FAF9F6] border border-stone-200 rounded-xl space-y-1">
                    <div className="font-bold text-[#1C252E] flex items-center gap-1.5">
                      <span className="w-5 h-5 rounded-full bg-[#E6F0EE] text-[#0F5147] text-xs flex items-center justify-center font-bold">1</span>
                      <span>{t('upload.tip_flat', 'Keep page flat')}</span>
                    </div>
                    <p className="text-stone-600 leading-relaxed text-xs">
                      {t('upload.tip_flat_desc', 'Lay the paper flat on a table so text is not folded.')}
                    </p>
                  </div>

                  <div className="p-3 bg-[#FAF9F6] border border-stone-200 rounded-xl space-y-1">
                    <div className="font-bold text-[#1C252E] flex items-center gap-1.5">
                      <span className="w-5 h-5 rounded-full bg-[#E6F0EE] text-[#0F5147] text-xs flex items-center justify-center font-bold">2</span>
                      <span>{t('upload.tip_light', 'Good lighting')}</span>
                    </div>
                    <p className="text-stone-600 leading-relaxed text-xs">
                      {t('upload.tip_light_desc', 'Take photo in bright light without harsh shadows or flash glare.')}
                    </p>
                  </div>

                  <div className="p-3 bg-[#FAF9F6] border border-stone-200 rounded-xl space-y-1">
                    <div className="font-bold text-[#1C252E] flex items-center gap-1.5">
                      <span className="w-5 h-5 rounded-full bg-[#E6F0EE] text-[#0F5147] text-xs flex items-center justify-center font-bold">3</span>
                      <span>{t('upload.tip_full', 'Show entire slip')}</span>
                    </div>
                    <p className="text-stone-600 leading-relaxed text-xs">
                      {t('upload.tip_full_desc', 'Include doctor name, all medicines, and date in frame.')}
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>
        ) : (
          /* ================= STATE B: FILE SELECTED / PREVIEW ================= */
          <div className="space-y-5">
            {/* Prescription Preview Card */}
            <div className="bg-white border border-stone-200 rounded-2xl p-5 shadow-2xs space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-stone-100">
                <StatusChip variant="success" label={t('upload.photo_ready', 'Prescription photo ready')} />
                <span className="text-xs text-stone-500 font-mono">
                  {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
                </span>
              </div>

              {/* Photo Display */}
              {previewUrl ? (
                <div className="relative rounded-xl overflow-hidden border border-stone-200 bg-[#FAF9F6] max-h-80 flex items-center justify-center p-2">
                  <img
                    src={previewUrl}
                    alt="Prescription document preview"
                    className="max-h-72 object-contain rounded-lg shadow-2xs"
                  />
                </div>
              ) : (
                <div className="p-8 bg-[#FAF9F6] rounded-xl border border-stone-200 text-center">
                  <FileText className="w-10 h-10 text-stone-400 mx-auto mb-2" />
                  <p className="text-sm font-bold text-[#1C252E]">{selectedFile.name}</p>
                </div>
              )}

              {/* Retake and Remove Actions (Touch Target >= 48px) */}
              <div className="flex flex-wrap items-center gap-3 pt-1">
                <Button
                  type="button"
                  variant="outline"
                  size="md"
                  onClick={handleTakePhotoClick}
                  leftIcon={<RotateCcw className="w-4 h-4 text-[#0F5147]" />}
                  className="flex-1 min-h-[48px] text-sm"
                >
                  {t('upload.retake_photo', 'Retake photo')}
                </Button>

                <Button
                  type="button"
                  variant="ghost"
                  size="md"
                  onClick={handleRemoveFile}
                  leftIcon={<X className="w-4 h-4 text-stone-500" />}
                  className="min-h-[48px] text-sm text-stone-600 hover:text-[#BE123C]"
                >
                  {t('upload.remove_photo', 'Remove')}
                </Button>
              </div>
            </div>

            {/* PLAIN-WORDS SAFETY CONSENT CHECKBOX ROW */}
            <div className="bg-white border border-stone-200 rounded-2xl p-4 sm:p-5 shadow-2xs text-left">
              <Checkbox
                checked={consentChecked}
                onChange={(e) => {
                  setConsentChecked(e.target.checked);
                  if (e.target.checked) setConsentError(false);
                }}
                label={t(
                  'upload.consent_label',
                  'This is a computer reading of my prescription. Please check it with your doctor or chemist before taking any medicine.'
                )}
                description="We will organize your dose timings clearly. Never start or change medication without consulting a healthcare professional."
                errorMessage={
                  consentError
                    ? t('upload.consent_error', 'Please check the box above to confirm before continuing.')
                    : undefined
                }
              />
            </div>

            {/* PATIENT LINKING SECTION */}
            {isPatientUser ? (
              /* State for logged-in Patient */
              <div className="bg-[#E6F0EE]/50 border border-[#9DC1BB] rounded-xl p-3.5 flex items-center justify-between text-left">
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-lg bg-[#0F5147] text-white flex items-center justify-center shrink-0">
                    <UserIcon className="w-4 h-4" />
                  </div>
                  <div>
                    <p className="text-xs font-bold text-[#0F5147]">Linked to Your Health Timeline</p>
                    <p className="text-xs text-stone-600">{session?.patient_name || session?.username} ({session?.patient_id || 'PAT-CURRENT'})</p>
                  </div>
                </div>
                <StatusChip variant="success" label="Auto-Linked" />
              </div>
            ) : (
              /* State for Reviewer / Doctor / Admin */
              <div className="bg-white border border-stone-200 rounded-xl p-4 sm:p-5 shadow-2xs text-left space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <label className="text-xs font-bold text-stone-700 uppercase tracking-wider flex items-center gap-1.5">
                    <UserIcon className="w-4 h-4 text-[#0F5147]" />
                    <span>Patient Record</span>
                  </label>

                  <div className="w-full sm:w-auto">
                    <SegmentedControl
                      size="sm"
                      value={patientMode}
                      onChange={(val) => {
                        setPatientMode(val);
                        if (val === 'walkin') {
                          setSelectedPatient(null);
                          setPatientExternalId('');
                        } else if (val === 'existing' && selectedPatient) {
                          setPatientExternalId(selectedPatient.patient_id);
                        }
                      }}
                      options={[
                        { value: 'existing', label: 'Select Patient' },
                        { value: 'new', label: '+ New Patient' },
                        { value: 'walkin', label: 'Walk-in' },
                      ]}
                    />
                  </div>
                </div>

                {patientMode === 'existing' && (
                  <div className="space-y-2">
                    {selectedPatient ? (
                      <div className="p-3 bg-[#E6F0EE]/60 border border-[#9DC1BB] rounded-xl flex items-center justify-between">
                        <div>
                          <span className="text-sm font-bold text-[#0F5147] block">{selectedPatient.name}</span>
                          <span className="text-xs text-stone-600 block">ID: {selectedPatient.patient_id} • Phone: {selectedPatient.phone_number}</span>
                        </div>
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            setSelectedPatient(null);
                            setPatientExternalId('');
                          }}
                          className="text-xs text-stone-500 hover:text-[#BE123C]"
                        >
                          Change
                        </Button>
                      </div>
                    ) : (
                      <div className="relative">
                        <div className="relative flex items-center">
                          <Search className="w-4 h-4 text-stone-400 absolute left-3 pointer-events-none" />
                          <input
                            type="text"
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            placeholder="Search patient by name, phone, or PAT-ID..."
                            className="w-full pl-9 pr-3.5 py-2.5 text-sm bg-white border border-stone-300 rounded-xl text-[#1C252E] placeholder:text-stone-400 focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-[#0F5147]"
                          />
                          {isSearchingPatient && <RefreshCw className="w-4 h-4 text-[#0F5147] animate-spin absolute right-3" />}
                        </div>

                        {patientSearchResults.length > 0 && (
                          <div className="absolute top-full left-0 right-0 mt-1 max-h-48 overflow-y-auto bg-white border border-stone-200 rounded-xl shadow-lg z-20 divide-y divide-stone-100">
                            {patientSearchResults.map((pat) => (
                              <button
                                key={pat.id}
                                type="button"
                                onClick={() => {
                                  setSelectedPatient(pat);
                                  setPatientExternalId(pat.patient_id);
                                  setSearchQuery('');
                                  setPatientSearchResults([]);
                                }}
                                className="w-full px-3.5 py-2.5 text-left hover:bg-stone-50 flex items-center justify-between text-xs cursor-pointer transition"
                              >
                                <div>
                                  <span className="font-bold text-stone-900 block">{pat.name}</span>
                                  <span className="text-stone-500 block">{pat.patient_id} • {pat.phone_number}</span>
                                </div>
                                <span className="text-[10px] font-semibold text-teal-700 bg-teal-50 px-2 py-0.5 rounded-full">Select</span>
                              </button>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )}

                {patientMode === 'new' && (
                  <div className="p-3.5 bg-stone-50 border border-stone-200 rounded-xl space-y-3">
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                      <div>
                        <label className="text-[11px] font-bold text-stone-600 block mb-1">Full Name *</label>
                        <input
                          type="text"
                          value={newPatientName}
                          onChange={(e) => setNewPatientName(e.target.value)}
                          placeholder="e.g. Ramesh Kumar"
                          className="w-full px-3 py-1.5 text-xs bg-white border border-stone-300 rounded-lg text-stone-900 focus-visible:ring-1 focus-visible:ring-[#0F5147]"
                        />
                      </div>
                      <div>
                        <label className="text-[11px] font-bold text-stone-600 block mb-1">Phone Number *</label>
                        <input
                          type="tel"
                          value={newPatientPhone}
                          onChange={(e) => setNewPatientPhone(e.target.value)}
                          placeholder="e.g. 9876543210"
                          className="w-full px-3 py-1.5 text-xs bg-white border border-stone-300 rounded-lg text-stone-900 focus-visible:ring-1 focus-visible:ring-[#0F5147]"
                        />
                      </div>
                      <div>
                        <label className="text-[11px] font-bold text-stone-600 block mb-1">Age</label>
                        <input
                          type="number"
                          value={newPatientAge}
                          onChange={(e) => setNewPatientAge(e.target.value)}
                          placeholder="e.g. 42"
                          className="w-full px-3 py-1.5 text-xs bg-white border border-stone-300 rounded-lg text-stone-900 focus-visible:ring-1 focus-visible:ring-[#0F5147]"
                        />
                      </div>
                      <div>
                        <label className="text-[11px] font-bold text-stone-600 block mb-1">Gender</label>
                        <select
                          value={newPatientGender}
                          onChange={(e) => setNewPatientGender(e.target.value)}
                          className="w-full px-3 py-1.5 text-xs bg-white border border-stone-300 rounded-lg text-stone-900 focus-visible:ring-1 focus-visible:ring-[#0F5147]"
                        >
                          <option value="MALE">Male</option>
                          <option value="FEMALE">Female</option>
                          <option value="OTHER">Other</option>
                        </select>
                      </div>
                    </div>
                    {patientCreateError && <p className="text-xs text-[#BE123C] font-semibold">{patientCreateError}</p>}
                    <Button
                      type="button"
                      variant="primary"
                      size="sm"
                      onClick={handleCreatePatientSubmit}
                      disabled={isCreatingPatient}
                      className="w-full inline-flex items-center justify-center gap-1.5 text-xs"
                    >
                      <UserPlus className="w-3.5 h-3.5" />
                      {isCreatingPatient ? 'Registering...' : 'Register & Link Patient'}
                    </Button>
                  </div>
                )}

                {patientMode === 'walkin' && (
                  <div className="p-3 bg-stone-50 border border-stone-200 rounded-xl flex items-center justify-between text-xs text-stone-600">
                    <span>Prescription will be recorded as a Walk-in (unregistered) patient.</span>
                    <StatusChip variant="neutral" label="Walk-in" />
                  </div>
                )}
              </div>
            )}

            {/* PRIMARY ACTION: One Obvious Button (Max 2 Actions Visible) */}
            <div className="pt-2">
              <Button
                type="submit"
                variant="primary"
                size="lg"
                disabled={isCompressing}
                className="w-full min-h-[56px] text-base sm:text-lg font-bold bg-[#0F5147] hover:bg-[#0A3831]"
                rightIcon={<ArrowRight className="w-5 h-5 sm:w-6 sm:h-6 text-white" />}
              >
                {isCompressing ? 'Preparing Image...' : t('upload.submit_btn', 'Upload & Read My Prescription')}
              </Button>
            </div>
          </div>
        )}
      </form>

      {/* Camera Capture Dialog for Desktop */}
      <CameraCaptureDialog
        isOpen={isCameraDialogOpen}
        onClose={() => setIsCameraDialogOpen(false)}
        onCapture={(file) => validateAndSetFile(file)}
        onFallbackToFilePicker={() => galleryInputRef.current?.click()}
      />
    </div>
  );
};

export default UploadPrescriptionPage;
