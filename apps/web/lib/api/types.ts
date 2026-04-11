// Shared resource types mirroring backend Pydantic DTOs.
// Field names match the FastAPI response shapes exactly.

export type Currency = string;

// ---------------- Payments ----------------

export type PaymentStatus =
  | "pending"
  | "succeeded"
  | "failed"
  | "refunded"
  | "disputed";

export interface PaymentRecord {
  id: string;
  processor_payment_id: string | null;
  status: PaymentStatus;
  amount: number;
  currency: Currency;
  idempotency_key: string;
  created_at: string;
  updated_at: string;
}

export interface LedgerEntry {
  id: string;
  account_id: string;
  amount: number; // positive = debit, negative = credit
  currency: Currency;
  created_at: string;
}

export interface LedgerTransaction {
  id: string;
  description: string;
  entries: LedgerEntry[];
  created_at: string;
}

export type OutboxEventType =
  | "payment.authorized"
  | "payment.settled"
  | "payment.refunded"
  | "bill.scheduled"
  | "bill.executed"
  | "bill.failed"
  | "reconciliation.mismatch"
  | "card.issued"
  | "auth.approved"
  | "auth.declined"
  | "hold.created"
  | "hold.cleared";

export type OutboxEventStatus = "pending" | "published" | "failed";

export interface OutboxEvent {
  id: string;
  event_type: OutboxEventType;
  payload: Record<string, unknown>;
  status: OutboxEventStatus;
  created_at: string;
  published_at: string | null;
}

export type IssuerAuthDecision = "approved" | "declined" | "expired";

export interface IssuerAuthorization {
  id: string;
  idempotency_key: string;
  card_id: string | null;
  decision: IssuerAuthDecision;
  decline_reason: string | null;
  amount: number;
  currency: Currency;
  created_at: string;
}

export interface PaymentDetailResponse {
  payment: PaymentRecord;
  ledger_transactions: LedgerTransaction[];
  outbox_events: OutboxEvent[];
  issuer_authorization: IssuerAuthorization | null;
}

// ---------------- Issuer ----------------

export interface Cardholder {
  id: string;
  name: string;
  email: string;
  status: "active" | "suspended" | "closed";
  created_at: string;
}

export interface CreateCardholderInput {
  name: string;
  email: string;
}

export interface Card {
  id: string;
  cardholder_id: string;
  available_balance_account_id: string;
  pending_hold_account_id: string;
  last_four: string | null;
  credit_limit: number;
  currency: Currency;
  status: "active" | "frozen" | "closed";
  created_at: string;
  updated_at: string;
}

export interface CreateCardInput {
  cardholder_id: string;
  credit_limit: number;
  currency: Currency;
  last_four?: string | null;
}

export interface CardBalance {
  card_id: string;
  credit_limit: number;
  available_credit: number;
  pending_holds: number;
  currency: Currency;
}

export interface CardAuthorization {
  id: string;
  idempotency_key: string;
  card_id: string | null;
  decision: IssuerAuthDecision;
  decline_reason: string | null;
  amount: number;
  currency: Currency;
  created_at: string;
}

// ---------------- Payees ----------------

export type PayeeType = "utility" | "credit_card" | "mortgage" | "other";

export interface Payee {
  id: string;
  name: string;
  payee_type: PayeeType;
  account_number: string;
  routing_number: string;
  currency: Currency;
  created_at: string;
}

export interface CreatePayeeInput {
  name: string;
  payee_type: PayeeType;
  account_number: string;
  routing_number: string;
  currency: Currency;
}

// ---------------- Bills ----------------

export type BillFrequency = "one_time" | "weekly" | "biweekly" | "monthly";
export type BillStatus = "active" | "paused" | "completed" | "failed";
export type BillPaymentStatus = "pending" | "succeeded" | "failed";

export interface Bill {
  id: string;
  payee_id: string;
  card_id: string | null;
  amount: number;
  currency: Currency;
  frequency: BillFrequency;
  next_due_date: string;
  status: BillStatus;
  created_at: string;
  updated_at: string;
}

export interface BillPayment {
  id: string;
  bill_id: string;
  payment_id: string | null;
  status: BillPaymentStatus;
  executed_at: string;
}

export interface BillDetail {
  bill: Bill;
  payments: BillPayment[];
}

export interface BillExecutionResponse {
  bill: Bill;
  bill_payment: BillPayment;
}

export interface CreateBillInput {
  payee_id: string;
  card_id?: string | null;
  amount: number;
  currency: Currency;
  frequency: BillFrequency;
  next_due_date: string;
}

export interface UpdateBillInput {
  card_id?: string | null;
  amount?: number;
  status?: BillStatus;
  frequency?: BillFrequency;
  next_due_date?: string;
}

// ---------------- Fraud ----------------

export type RiskLevel = "low" | "high";

export interface FraudSignal {
  id: string;
  payment_id: string;
  risk_level: RiskLevel;
  amount: number;
  currency: Currency;
  flagged_at: string;
}

// ---------------- Reconciliation ----------------

export interface ReconciliationRun {
  id: string;
  started_at: string;
  completed_at: string | null;
  checked: number;
  mismatches: number;
}

export interface ReconciliationDiscrepancy {
  id: string;
  run_id: string;
  payment_id: string;
  processor_payment_id: string;
  our_status: string;
  stripe_status: string;
  detected_at: string;
}

// ---------------- Reporting ----------------

export interface ReportingSummaryRow {
  date: string;
  event_type: string;
  currency: Currency;
  total_amount: number;
  count: number;
}
