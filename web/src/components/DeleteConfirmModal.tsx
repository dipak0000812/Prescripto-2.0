import React, { useState } from 'react';
import { Trash2, Loader2, AlertCircle } from 'lucide-react';
import { deletePrescriptionApi } from '../api/prescriptions';
import { Button } from './ui/Button';

interface DeleteConfirmModalProps {
  prescriptionId: string;
  isOpen: boolean;
  onClose: () => void;
  onDeleted: (jobId: string) => void;
}

export const DeleteConfirmModal: React.FC<DeleteConfirmModalProps> = ({
  prescriptionId,
  isOpen,
  onClose,
  onDeleted,
}) => {
  const [isDeleting, setIsDeleting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleConfirm = async () => {
    setIsDeleting(true);
    setError(null);
    try {
      const res = await deletePrescriptionApi(prescriptionId);
      onDeleted(res.deletion_job_id);
      onClose();
    } catch (err: any) {
      setError(err?.message || 'Could not request deletion. Please try again later.');
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-stone-900/40 backdrop-blur-xs p-4 animate-in fade-in">
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="delete-confirm-title"
        className="bg-white rounded-2xl shadow-xl border border-stone-200 max-w-lg w-full overflow-hidden animate-in zoom-in-95 duration-150 text-left"
      >
        <div className="p-6 sm:p-7">
          <div className="w-12 h-12 rounded-xl bg-[#FFE4E6] text-[#BE123C] border border-[#FDA4AF] flex items-center justify-center mb-4">
            <Trash2 className="w-6 h-6" aria-hidden="true" />
          </div>

          <h3 id="delete-confirm-title" className="text-base font-extrabold text-[#1C252E]">
            Delete prescription record?
          </h3>

          <p className="text-xs text-stone-600 mt-2 leading-relaxed">
            This will submit a permanent deletion request for the following prescription record:
          </p>
          <div className="my-2.5 p-2.5 rounded-xl bg-stone-50 font-mono text-xs text-stone-700 break-all border border-stone-200">
            {prescriptionId}
          </div>

          <div className="bg-[#FFE4E6]/60 border border-[#FDA4AF] rounded-xl p-3.5 text-xs text-[#881337] mt-4 space-y-1.5">
            <div className="font-semibold flex items-center gap-1.5">
              <AlertCircle className="w-3.5 h-3.5 text-[#BE123C] shrink-0" />
              <span>Irreversible Action</span>
            </div>
            <p className="text-[11px] leading-relaxed text-[#881337]">
              Confirm you are authorized to remove this record and have checked applicable clinical retention requirements.
            </p>
          </div>

          {error && (
            <div role="alert" className="mt-3 p-3 bg-[#FFE4E6] border border-[#FDA4AF] rounded-xl text-xs text-[#881337]">
              {error}
            </div>
          )}

          <div className="mt-6 flex items-center justify-end gap-3">
            <Button
              variant="outline"
              size="sm"
              onClick={onClose}
              disabled={isDeleting}
              className="min-h-[40px]"
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              size="sm"
              onClick={handleConfirm}
              disabled={isDeleting}
              isLoading={isDeleting}
              leftIcon={<Trash2 className="w-4 h-4" />}
              className="min-h-[40px]"
            >
              Request Deletion
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DeleteConfirmModal;
