from sqlalchemy.ext.asyncio import AsyncSession

from app.issuer.auth import repository as auth_repository
from app.issuer.cards import repository as cards_repository
from app.ledger import service as ledger_service
from app.outbox import service as outbox_service
from app.outbox.models import OutboxEventType
from shared.logger import get_logger

logger = get_logger(__name__)


async def clear_hold(
    session: AsyncSession,
    idempotency_key: str,
    amount: int,
) -> None:
    """
    Clear the issuer hold placed at authorization time.
    Called after acquiring settlement so both sides land in the same transaction.

    Lookup chain: idempotency_key -> IssuerAuthorization -> card_id -> Card -> ledger accounts
    """
    issuer_auth = await auth_repository.get_by_idempotency_key(session, idempotency_key)

    if issuer_auth is None:
        logger.debug(
            "clear_hold: no issuer authorization found | idempotency_key=%s -- skipping",
            idempotency_key,
        )
        return

    if issuer_auth.card_id is None:
        logger.debug(
            "clear_hold: authorization has no card_id | idempotency_key=%s -- skipping",
            idempotency_key,
        )
        return

    card = await cards_repository.get_card(session, issuer_auth.card_id)
    if card is None:
        logger.warning(
            "clear_hold: card not found | card_id=%s idempotency_key=%s -- skipping",
            issuer_auth.card_id,
            idempotency_key,
        )
        return

    await ledger_service.record_clear_hold(
        session,
        pending_hold_account_id=card.pending_hold_account_id,
        available_balance_account_id=card.available_balance_account_id,
        amount=amount,
        description=f"settlement clear hold for authorization {issuer_auth.id}",
    )

    await outbox_service.publish_event(
        session,
        event_type=OutboxEventType.HOLD_CLEARED,
        payload={
            "card_id": str(card.id),
            "authorization_id": str(issuer_auth.id),
            "amount": amount,
        },
    )

    logger.info(
        "hold cleared | card_id=%s authorization_id=%s amount=%d",
        card.id,
        issuer_auth.id,
        amount,
    )
