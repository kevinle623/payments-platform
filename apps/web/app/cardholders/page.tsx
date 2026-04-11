"use client";

import { Suspense } from "react";
import { LoadingSkeleton } from "@/components/common/loading-skeleton";
import { CardholdersScreen } from "@/components/issuing";

export default function CardholdersPage() {
  return (
    <Suspense
      fallback={
        <div className="space-y-4">
          <LoadingSkeleton variant="card" />
          <LoadingSkeleton variant="table" />
        </div>
      }
    >
      <CardholdersScreen />
    </Suspense>
  );
}
