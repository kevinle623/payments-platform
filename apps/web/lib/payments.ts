const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface AuthorizeResponse {
  id: string;
  processor_payment_id: string | null;
  client_secret: string | null;
  status: string;
  amount: number;
  currency: string;
  idempotency_key: string;
  created_at: string;
}

export async function authorizePayment(
  amount: number,
  currency: string
): Promise<AuthorizeResponse> {
  const res = await fetch(`${API_BASE}/payments/authorize`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      amount,
      currency,
      idempotency_key: crypto.randomUUID(),
      metadata: {},
    }),
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Authorization failed (${res.status})`);
  }

  return res.json();
}
