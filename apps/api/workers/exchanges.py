PAYMENTS_EXCHANGE = "payments"
ISSUER_EXCHANGE = "issuer"

# Dead letter exchanges -- failed messages route here, then to per-queue DLQs
PAYMENTS_DLX = "payments.dlx"
ISSUER_DLX = "issuer.dlx"
