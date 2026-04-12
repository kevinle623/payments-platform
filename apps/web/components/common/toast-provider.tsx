"use client";

import { CheckCircle2, Info, X, AlertTriangle } from "lucide-react";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { cn } from "@/lib/utils/cn";

type ToastVariant = "success" | "error" | "info";

interface ToastInput {
  title: string;
  description?: string;
  variant?: ToastVariant;
  durationMs?: number;
}

interface ToastRecord {
  id: string;
  title: string;
  description?: string;
  variant: ToastVariant;
  durationMs: number;
}

interface ToastContextValue {
  pushToast: (input: ToastInput) => void;
}

const ToastContext = createContext<ToastContextValue | null>(null);

const VARIANT_CLASSES: Record<ToastVariant, string> = {
  success: "border-success-border bg-success-bg text-success",
  error: "border-danger-border bg-danger-bg text-danger",
  info: "border-info-border bg-info-bg text-info",
};

function ToastIcon({ variant }: { variant: ToastVariant }) {
  if (variant === "success") {
    return <CheckCircle2 className="h-4 w-4" />;
  }
  if (variant === "error") {
    return <AlertTriangle className="h-4 w-4" />;
  }
  return <Info className="h-4 w-4" />;
}

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastRecord[]>([]);
  const timeoutsRef = useRef<Map<string, number>>(new Map());

  const dismissToast = useCallback((id: string) => {
    const timeout = timeoutsRef.current.get(id);
    if (timeout) {
      window.clearTimeout(timeout);
      timeoutsRef.current.delete(id);
    }
    setToasts((prev) => prev.filter((toast) => toast.id !== id));
  }, []);

  const pushToast = useCallback(
    (input: ToastInput) => {
      const id =
        typeof crypto !== "undefined" && "randomUUID" in crypto
          ? crypto.randomUUID()
          : `${Date.now()}-${Math.random().toString(36).slice(2)}`;

      const record: ToastRecord = {
        id,
        title: input.title,
        description: input.description,
        variant: input.variant ?? "info",
        durationMs: input.durationMs ?? 4500,
      };

      setToasts((prev) => [...prev, record]);

      const timeout = window.setTimeout(() => {
        dismissToast(id);
      }, record.durationMs);
      timeoutsRef.current.set(id, timeout);
    },
    [dismissToast],
  );

  useEffect(() => {
    return () => {
      for (const timeout of timeoutsRef.current.values()) {
        window.clearTimeout(timeout);
      }
      timeoutsRef.current.clear();
    };
  }, []);

  const value = useMemo<ToastContextValue>(
    () => ({
      pushToast,
    }),
    [pushToast],
  );

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div className="pointer-events-none fixed right-4 top-16 z-50 flex w-[min(420px,calc(100vw-2rem))] flex-col gap-2">
        {toasts.map((toast) => (
          <div
            key={toast.id}
            role="status"
            aria-live="polite"
            className={cn(
              "pointer-events-auto rounded-lg border p-3 shadow-lg backdrop-blur",
              VARIANT_CLASSES[toast.variant],
            )}
          >
            <div className="flex items-start gap-2.5">
              <div className="mt-0.5 shrink-0">
                <ToastIcon variant={toast.variant} />
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-sm font-semibold text-foreground">
                  {toast.title}
                </p>
                {toast.description ? (
                  <p className="mt-0.5 text-xs text-foreground-muted">
                    {toast.description}
                  </p>
                ) : null}
              </div>
              <button
                type="button"
                onClick={() => dismissToast(toast.id)}
                className="rounded-md p-1 text-foreground-subtle transition-colors hover:bg-background/40 hover:text-foreground"
                aria-label="Dismiss notification"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error("useToast must be used within ToastProvider");
  }
  return context;
}
