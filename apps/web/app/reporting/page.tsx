"use client";

import { Suspense } from "react";
import { LoadingSkeleton } from "@/components/common/loading-skeleton";
import { ReportingScreen } from "@/components/observability";

export default function ReportingPage() {
  return (
    <Suspense
      fallback={
        <div className="space-y-4">
          <LoadingSkeleton variant="card" />
          <LoadingSkeleton variant="table" />
        </div>
      }
    >
      <ReportingScreen />
    </Suspense>
  );
}
