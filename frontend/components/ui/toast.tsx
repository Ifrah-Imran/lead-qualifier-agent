"use client";

import { useEffect } from "react";
import { createPortal } from "react-dom";
import { CheckCircle2, X, XCircle } from "lucide-react";

export type ToastState = { message: string; tone: "success" | "error" } | null;

export function Toast({
  toast,
  onDismiss,
  durationMs = 5000,
}: {
  toast: ToastState;
  onDismiss: () => void;
  durationMs?: number;
}) {
  useEffect(() => {
    if (!toast) return;
    const timer = setTimeout(onDismiss, durationMs);
    return () => clearTimeout(timer);
  }, [toast, onDismiss, durationMs]);

  if (!toast) return null;

  const Icon = toast.tone === "success" ? CheckCircle2 : XCircle;

  return createPortal(
    <div className="fixed inset-x-0 top-4 z-[60] flex justify-center px-4">
      <div
        role="status"
        className="flex items-center gap-2.5 rounded-xl border border-border bg-card px-4 py-3 shadow-xl"
      >
        <Icon className={`h-4 w-4 shrink-0 ${toast.tone === "success" ? "text-success" : "text-destructive"}`} />
        <p className="text-sm font-medium text-foreground">{toast.message}</p>
        <button
          onClick={onDismiss}
          aria-label="Dismiss"
          className="ml-1 rounded-md p-0.5 text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
        >
          <X className="h-3.5 w-3.5" />
        </button>
      </div>
    </div>,
    document.body,
  );
}
