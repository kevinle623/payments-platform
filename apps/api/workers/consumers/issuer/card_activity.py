"""
Card activity consumer -- subscribes to card lifecycle events on the issuer exchange.

Routing keys: card.issued, hold.created, hold.cleared
Queue: issuer.card_activity

Logs card lifecycle events. Future: write to a card activity feed table.
"""

from shared.logger import get_logger
from workers.consumers.base import start
from workers.exchanges import ISSUER_EXCHANGE

logger = get_logger(__name__)

_QUEUE_NAME = "issuer.card_activity"
_ROUTING_KEYS = ["card.issued", "hold.created", "hold.cleared"]


async def _handle(event_type: str, payload: dict) -> None:
    if event_type == "card.issued":
        logger.info(
            "card activity | event=card.issued card_id=%s cardholder_id=%s credit_limit=%s currency=%s",
            payload.get("card_id"),
            payload.get("cardholder_id"),
            payload.get("credit_limit"),
            payload.get("currency"),
        )
    elif event_type == "hold.created":
        logger.info(
            "card activity | event=hold.created amount=%s available_balance_account_id=%s pending_hold_account_id=%s",
            payload.get("amount"),
            payload.get("available_balance_account_id"),
            payload.get("pending_hold_account_id"),
        )
    elif event_type == "hold.cleared":
        logger.info(
            "card activity | event=hold.cleared card_id=%s authorization_id=%s amount=%s",
            payload.get("card_id"),
            payload.get("authorization_id"),
            payload.get("amount"),
        )
    else:
        logger.warning(
            "card_activity consumer received unexpected event_type=%s", event_type
        )


if __name__ == "__main__":
    start(ISSUER_EXCHANGE, _QUEUE_NAME, _ROUTING_KEYS, _handle)
