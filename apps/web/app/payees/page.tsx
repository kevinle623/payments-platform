"use client";

import { Suspense } from "react";
import { LoadingSkeleton } from "@/components/common/loading-skeleton";
import { PayeesScreen } from "@/components/bills";

export default function PayeesPage() {
  return (
    <Suspense
      fallback={
        <div className="space-y-4">
          <LoadingSkeleton variant="card" />
          <LoadingSkeleton variant="table" />
        </div>
      }
    >
      <PayeesScreen />
    </Suspense>
  );
}
