import { useEffect } from "react";
import type { PendingAction } from "../types";

export function ConfirmationModal({
  pendingAction,
  isConfirming,
  onCancel,
  onConfirm,
}: {
  pendingAction: PendingAction | null;
  isConfirming: boolean;
  onCancel: () => void;
  onConfirm: () => void;
}) {
  useEffect(() => {
    if (!pendingAction) {
      return;
    }

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape" && !isConfirming) {
        onCancel();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isConfirming, onCancel, pendingAction]);

  if (!pendingAction) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/45 p-4 backdrop-blur-sm">
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="confirm-action-title"
        aria-busy={isConfirming}
        className="w-full max-w-lg rounded-3xl border border-slate-200 bg-white p-6 shadow-glow"
      >
        <div className="mb-5 flex items-start gap-4">
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-amber-50 text-amber-600">
            <span aria-hidden="true">!</span>
          </div>
          <div>
            <p className="font-mono text-xs font-medium uppercase tracking-[0.22em] text-blue-600">
              Confirm Action
            </p>
            <h2 id="confirm-action-title" className="mt-2 text-2xl font-semibold tracking-[-0.03em] text-ink">
              Review before execution
            </h2>
          </div>
        </div>

        <p className="text-sm leading-7 text-ink">{pendingAction.confirmation_message}</p>

        <div className="mt-5 rounded-2xl border border-slate-200 bg-slate-50 p-4">
          <p className="font-mono text-xs font-medium uppercase tracking-[0.16em] text-ink">Action</p>
          <p className="mt-2 text-sm font-semibold text-ink">{pendingAction.action_type.replace(/_/g, " ")}</p>
        </div>

        <div className="mt-6 flex flex-col-reverse gap-3 sm:flex-row">
          <button
            type="button"
            disabled={isConfirming}
            className="min-h-11 flex-1 rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-medium text-ink transition hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
            onClick={onCancel}
          >
            Cancel
          </button>
          <button
            type="button"
            disabled={isConfirming}
            className="min-h-11 flex-1 rounded-2xl bg-blue-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-blue-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:bg-slate-300"
            onClick={onConfirm}
          >
            {isConfirming ? "Confirming..." : "Confirm action"}
          </button>
        </div>
      </div>
    </div>
  );
}
