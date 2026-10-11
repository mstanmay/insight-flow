import React from 'react';
import { useWorkspace } from '../../context/WorkspaceContext';

/**
 * Toast Container component for reactive system notifications
 */
export default function ToastContainer() {
  const { toasts, removeToast } = useWorkspace();

  if (!toasts || toasts.length === 0) return null;

  const typeStyles = {
    success: 'bg-emerald-950/90 text-emerald-200 border-emerald-500/40 shadow-emerald-950/50',
    info: 'bg-indigo-950/90 text-indigo-200 border-indigo-500/40 shadow-indigo-950/50',
    warning: 'bg-amber-950/90 text-amber-200 border-amber-500/40 shadow-amber-950/50',
    error: 'bg-rose-950/90 text-rose-200 border-rose-500/40 shadow-rose-950/50',
  };

  const typeIcons = {
    success: 'check_circle',
    info: 'info',
    warning: 'warning',
    error: 'error',
  };

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col gap-2 pointer-events-none">
      {toasts.map((toast) => {
        const style = typeStyles[toast.type] || typeStyles.success;
        const icon = typeIcons[toast.type] || 'check_circle';

        return (
          <div
            key={toast.id}
            onClick={() => removeToast(toast.id)}
            className={`pointer-events-auto cursor-pointer toast-anim flex items-center gap-3 px-4 py-3 rounded-xl border shadow-xl backdrop-blur-xl text-xs font-medium transition-all ${style}`}
          >
            <span className="material-symbols-outlined text-base">{icon}</span>
            <span>{toast.message}</span>
          </div>
        );
      })}
    </div>
  );
}
