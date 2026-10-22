import React, { useState } from 'react';
import { AlertTriangle, Trash2, X, Loader2, CheckCircle2 } from 'lucide-react';
import { deletePrescriptionApi } from '../api/prescriptions';

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
      setError(err?.message || 'Failed to initiate verifiable deletion.');
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4 animate-in fade-in">
      <div className="bg-white rounded-2xl shadow-xl border border-slate-200 max-w-lg w-full overflow-hidden animate-in zoom-in-95 duration-150">
        <div className="p-6 sm:p-8">
          <div className="w-12 h-12 rounded-xl bg-rose-50 text-rose-600 border border-rose-200 flex items-center justify-center mb-4">
            <Trash2 className="w-6 h-6" />
          </div>

          <h3 className="text-base font-bold text-slate-900">
            Request DPDPA 2023 Verifiable Deletion
          </h3>

          <p className="text-xs text-slate-600 mt-2 leading-relaxed">
            You are about to initiate statutory deletion for prescription document:
          </p>
          <div className="my-2 p-2.5 rounded-lg bg-slate-50 font-mono text-xs text-slate-700 break-all border border-slate-200">
            {prescriptionId}
          </div>

          <div className="bg-rose-50 border border-rose-200 rounded-xl p-4 text-xs text-rose-800 mt-4 space-y-2">
            <div className="font-semibold flex items-center gap-1.5 text-rose-900">
              <AlertTriangle className="w-4 h-4 text-rose-600" />
              Verifiable Erasure Lifecycle:
            </div>
            <p className="text-[11px] text-rose-700 leading-relaxed">
              1. Document status set to <code className="font-mono font-bold text-rose-800">DELETION_REQUESTED</code>.<br />
              2. Asynchronous job purges storage binaries and derived artifacts.<br />
              3. Cryptographic manifest is logged into the separately permissioned retention vault.<br />
              4. Global CDSCO medication master knowledge remains unaffected.
            </p>
          </div>

          {error && (
            <div className="mt-3 p-3 bg-rose-50 border border-rose-200 rounded-lg text-xs text-rose-700">
              {error}
            </div>
          )}

          <div className="mt-6 flex items-center justify-end gap-3">
            <button
              onClick={onClose}
              disabled={isDeleting}
              className="px-4 py-2 text-xs font-medium text-slate-700 hover:text-slate-900 hover:bg-slate-100 rounded-lg transition"
            >
              Cancel
            </button>
            <button
              onClick={handleConfirm}
              disabled={isDeleting}
              className="inline-flex items-center gap-2 px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white text-xs font-semibold rounded-lg shadow-xs disabled:opacity-50 transition"
            >
              {isDeleting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Initiating...
                </>
              ) : (
                <>
                  <Trash2 className="w-4 h-4" />
                  Confirm Deletion
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DeleteConfirmModal;
