"""
Issuer risk consumer -- subscribes to auth events on the issuer exchange.

Routing keys: auth.approved, auth.declined
Queue: issuer.risk

Scores issuer-side risk patterns: velocity of declines, presence of decline reasons.
Future: feed signals into the fraud module.
"""

from shared.logger import get_logger
from workers.consumers.base import start
from workers.exchanges import ISSUER_EXCHANGE

logger = get_logger(__name__)

_QUEUE_NAME = "issuer.risk"
_ROUTING_KEYS = ["auth.approved", "auth.declined"]

# decline reasons that indicate elevated risk
_HIGH_RISK_DECLINE_REASONS = {"insufficient_funds", "velocity_exceeded"}


async def _handle(event_type: str, payload: dict) -> None:
    authorization_id = payload.get("authorization_id")
    card_id = payload.get("card_id")
    amount = payload.get("amount", 0)
    currency = payload.get("currency")

    if event_type == "auth.approved":
        logger.info(
            "issuer risk | event=auth.approved authorization_id=%s card_id=%s amount=%d currency=%s",
            authorization_id,
            card_id,
            amount,
            currency,
        )
    elif event_type == "auth.declined":
        decline_reason = payload.get("decline_reason")
        risk = "high" if decline_reason in _HIGH_RISK_DECLINE_REASONS else "low"
        logger.warning(
            "issuer risk | event=auth.declined authorization_id=%s card_id=%s amount=%d currency=%s decline_reason=%s risk=%s",
            authorization_id,
            card_id,
            amount,
            currency,
            decline_reason,
            risk,
        )
    else:
        logger.warning("risk consumer received unexpected event_type=%s", event_type)


if __name__ == "__main__":
    start(ISSUER_EXCHANGE, _QUEUE_NAME, _ROUTING_KEYS, _handle)
