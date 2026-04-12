"use client";

import { SWRConfig } from "swr";
import type { ReactNode } from "react";
import { ToastProvider } from "@/components/common/toast-provider";

export function Providers({ children }: { children: ReactNode }) {
  return (
    <SWRConfig
      value={{
        revalidateOnFocus: true,
        dedupingInterval: 2000,
        errorRetryCount: 2,
        shouldRetryOnError: (err: unknown) => {
          // Don't retry 4xx client errors
          if (
            err &&
            typeof err === "object" &&
            "status" in err &&
            typeof (err as { status: number }).status === "number"
          ) {
            const status = (err as { status: number }).status;
            return status >= 500;
          }
          return true;
        },
      }}
    >
      <ToastProvider>{children}</ToastProvider>
    </SWRConfig>
  );
}
