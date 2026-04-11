import { EmptyState } from "@/components/common/empty-state";
import { JsonBlock } from "@/components/common/json-block";
import { StatusBadge } from "@/components/common/status-badge";
import type { OutboxEvent } from "@/lib/api/types";
import { formatDateTime, formatRelative } from "@/lib/utils/format";

interface PaymentOutboxEventsProps {
  events: OutboxEvent[];
}

export function PaymentOutboxEvents({ events }: PaymentOutboxEventsProps) {
  if (events.length === 0) {
    return (
      <EmptyState
        title="No outbox events"
        description="No events are attached to this payment yet."
      />
    );
  }

  return (
    <div className="space-y-2">
      {events.map((event) => (
        <details
          key={event.id}
          className="overflow-hidden rounded-lg border border-border bg-card"
        >
          <summary className="flex cursor-pointer flex-wrap items-center gap-2 px-3 py-2 text-sm marker:hidden">
            <span className="font-medium text-foreground">
              {event.event_type}
            </span>
            <StatusBadge domain="outbox" status={event.status} />
            <span
              className="ml-auto text-xs text-foreground-muted"
              title={formatDateTime(event.created_at)}
            >
              Created {formatRelative(event.created_at)}
            </span>
            <span
              className="text-xs text-foreground-subtle"
              title={
                event.published_at
                  ? formatDateTime(event.published_at)
                  : undefined
              }
            >
              Published{" "}
              {event.published_at
                ? formatRelative(event.published_at)
                : "Not yet"}
            </span>
          </summary>
          <div className="border-t border-border p-3">
            <JsonBlock value={event.payload} />
          </div>
        </details>
      ))}
    </div>
  );
}
