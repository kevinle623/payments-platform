"use client";

import { Suspense } from "react";
import { LoadingSkeleton } from "@/components/common/loading-skeleton";
import { BillsListScreen } from "@/components/bills";

export default function BillsPage() {
  return (
    <Suspense
      fallback={
        <div className="space-y-4">
          <LoadingSkeleton variant="card" />
          <LoadingSkeleton variant="table" />
        </div>
      }
    >
      <BillsListScreen />
    </Suspense>
  );
}
