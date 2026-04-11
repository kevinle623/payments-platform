"use client";

import Link from "next/link";
import { ChevronLeft } from "lucide-react";
import { useParams } from "next/navigation";
import { EmptyState } from "@/components/common/empty-state";
import { ErrorState } from "@/components/common/error-state";
import { LoadingSkeleton } from "@/components/common/loading-skeleton";
import { PaymentDetailHeader } from "@/components/payments/payment-detail-header";
import { PaymentDetailTabs } from "@/components/payments/payment-detail-tabs";
import { PaymentOverviewPanel } from "@/components/payments/payment-overview-panel";
import { PaymentTimelinePanel } from "@/components/payments/payment-timeline-panel";
import { usePayment } from "@/lib/hooks/use-payments";
import { getFirstParamValue } from "@/lib/utils/params";

export function PaymentDetailScreen() {
  const params = useParams<{ id: string }>();
  const paymentId = getFirstParamValue(params.id);
  const { data, error, isLoading, mutate } = usePayment(paymentId);

  if (isLoading) {
    return (
      <div className="space-y-4">
        <LoadingSkeleton variant="card" />
        <LoadingSkeleton variant="table" />
      </div>
    );
  }

  if (error) {
    return <ErrorState error={error} onRetry={() => void mutate()} />;
  }

  if (!data) {
    return (
      <EmptyState
        title="Payment not found"
        description="No payment data was returned for this ID."
      />
    );
  }

  return (
    <div className="space-y-5">
      <Link
        href="/payments"
        className="inline-flex items-center gap-1.5 text-sm text-foreground-muted transition-colors hover:text-foreground"
      >
        <ChevronLeft className="h-4 w-4" />
        Back to payments
      </Link>

      <PaymentDetailHeader payment={data.payment} />

      <div className="grid gap-5 lg:grid-cols-2">
        <div className="space-y-4">
          <PaymentOverviewPanel payment={data.payment} />
          <PaymentTimelinePanel events={data.outbox_events} />
        </div>

        <PaymentDetailTabs detail={data} />
      </div>
    </div>
  );
}
