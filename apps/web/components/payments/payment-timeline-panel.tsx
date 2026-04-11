import { Timeline } from "@/components/common/timeline";
import type { OutboxEvent } from "@/lib/api/types";
import { buildPaymentTimelineItems } from "@/lib/utils/payment-detail";

interface PaymentTimelinePanelProps {
  events: OutboxEvent[];
}

export function PaymentTimelinePanel({ events }: PaymentTimelinePanelProps) {
  return <Timeline items={buildPaymentTimelineItems(events)} />;
}
