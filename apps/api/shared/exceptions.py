class PaymentsError(Exception):
    """Base domain exception."""


class LedgerImbalanceError(PaymentsError):
    """Raised when ledger entries do not sum to zero."""


class PaymentNotFoundError(PaymentsError):
    """Raised when a payment record cannot be found."""


class IdempotencyConflictError(PaymentsError):
    """Raised when an idempotency key is reused with different parameters."""


class ProcessorError(PaymentsError):
    """Raised when the payment processor returns an error."""


class PaymentDeclinedException(PaymentsError):
    """Raised when the issuer declines a payment authorization."""
