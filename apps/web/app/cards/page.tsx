"use client";

import { Suspense } from "react";
import { LoadingSkeleton } from "@/components/common/loading-skeleton";
import { CardsListScreen } from "@/components/issuing";

export default function CardsPage() {
  return (
    <Suspense
      fallback={
        <div className="space-y-4">
          <LoadingSkeleton variant="card" />
          <LoadingSkeleton variant="table" />
        </div>
      }
    >
      <CardsListScreen />
    </Suspense>
  );
}
