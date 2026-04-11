export type StatusVariant =
  | "neutral"
  | "info"
  | "success"
  | "warning"
  | "danger"
  | "muted";

export type StatusDomain =
  | "payment"
  | "bill"
  | "auth"
  | "fraud"
  | "reconciliation"
  | "outbox";

interface StatusMeta {
  label: string;
  variant: StatusVariant;
}

const PAYMENT_STATUS: Record<string, StatusMeta> = {
  pending: { label: "Pending", variant: "info" },
  succeeded: { label: "Succeeded", variant: "success" },
  failed: { label: "Failed", variant: "danger" },
  refunded: { label: "Refunded", variant: "muted" },
  disputed: { label: "Disputed", variant: "warning" },
};

const BILL_STATUS: Record<string, StatusMeta> = {
  active: { label: "Active", variant: "success" },
  paused: { label: "Paused", variant: "warning" },
  completed: { label: "Completed", variant: "muted" },
  failed: { label: "Failed", variant: "danger" },
  pending: { label: "Pending", variant: "warning" },
  succeeded: { label: "Succeeded", variant: "success" },
};

const AUTH_STATUS: Record<string, StatusMeta> = {
  approved: { label: "Approved", variant: "success" },
  declined: { label: "Declined", variant: "danger" },
  expired: { label: "Expired", variant: "muted" },
};

const FRAUD_STATUS: Record<string, StatusMeta> = {
  low: { label: "Low", variant: "muted" },
  medium: { label: "Medium", variant: "warning" },
  high: { label: "High", variant: "danger" },
};

const RECON_STATUS: Record<string, StatusMeta> = {
  running: { label: "Running", variant: "info" },
  completed: { label: "Completed", variant: "success" },
  failed: { label: "Failed", variant: "danger" },
};

const OUTBOX_STATUS: Record<string, StatusMeta> = {
  pending: { label: "Pending", variant: "warning" },
  published: { label: "Published", variant: "success" },
  failed: { label: "Failed", variant: "danger" },
};

const REGISTRY: Record<StatusDomain, Record<string, StatusMeta>> = {
  payment: PAYMENT_STATUS,
  bill: BILL_STATUS,
  auth: AUTH_STATUS,
  fraud: FRAUD_STATUS,
  reconciliation: RECON_STATUS,
  outbox: OUTBOX_STATUS,
};

export function getStatusMeta(
  domain: StatusDomain,
  status: string | null | undefined,
): StatusMeta {
  if (!status) return { label: "Unknown", variant: "neutral" };
  const key = status.toLowerCase();
  return REGISTRY[domain][key] ?? { label: status, variant: "neutral" };
}
