import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.issuer.auth import repository
from app.issuer.auth.models import IssuerAuthDecision
from app.issuer.auth.schemas import IssuerAuthorizationDTO
from app.issuer.cards import repository as cards_repository
from app.issuer.cards.models import CardStatus
from app.issuer.controls import service as controls_service
from app.ledger import service as ledger_service
from app.outbox import service as outbox_service
from app.outbox.models import OutboxEventType
from shared.enums.currency import Currency
from shared.logger import get_logger

logger = get_logger(__name__)


async def evaluate(
    session: AsyncSession,
    idempotency_key: str,
    amount: int,
    currency: str,
    metadata: dict,
    card_id: uuid.UUID | None = None,
) -> IssuerAuthorizationDTO:
    # idempotency -- if we already evaluated this request, return the existing decision
    existing = await repository.get_by_idempotency_key(session, idempotency_key)
    if existing:
        logger.info(
            "issuer auth idempotency hit | idempotency_key=%s decision=%s",
            idempotency_key,
            existing.decision,
        )
        return existing

    decision = IssuerAuthDecision.APPROVED
    decline_reason = None
    card = None

    if card_id is not None:
        card = await cards_repository.get_card(session, card_id)

        if card is None:
            decision = IssuerAuthDecision.DECLINED
            decline_reason = "card_not_found"
        elif card.status != CardStatus.ACTIVE:
            decision = IssuerAuthDecision.DECLINED
            decline_reason = "card_inactive"
        else:
            # compute available credit for the balance check
            balance = await ledger_service.get_balance(
                session, card.available_balance_account_id, Currency(card.currency)
            )
            available_credit = card.credit_limit + balance.balance

            decline_reason = await controls_service.check_controls(
                session,
                card_id=card_id,
                available_credit=available_credit,
                amount=amount,
                metadata=metadata,
            )
            if decline_reason:
                decision = IssuerAuthDecision.DECLINED

    record = await repository.create(
        session,
        idempotency_key=idempotency_key,
        card_id=card_id,
        decision=decision,
        decline_reason=decline_reason,
        amount=amount,
        currency=currency,
    )

    logger.info(
        "issuer auth decision | idempotency_key=%s decision=%s amount=%d currency=%s card_id=%s",
        idempotency_key,
        decision,
        amount,
        currency,
        card_id,
    )

    # write hold to card ledger if approved with a card
    if decision == IssuerAuthDecision.APPROVED and card is not None:
        await ledger_service.record_hold(
            session,
            available_balance_account_id=card.available_balance_account_id,
            pending_hold_account_id=card.pending_hold_account_id,
            amount=amount,
            description=f"hold for authorization {record.id}",
        )

    event_type = (
        OutboxEventType.AUTH_APPROVED
        if decision == IssuerAuthDecision.APPROVED
        else OutboxEventType.AUTH_DECLINED
    )
    payload: dict = {
        "authorization_id": str(record.id),
        "card_id": str(card_id) if card_id is not None else None,
        "amount": amount,
        "currency": currency,
        "idempotency_key": idempotency_key,
    }
    if decision == IssuerAuthDecision.DECLINED:
        payload["decline_reason"] = decline_reason
    await outbox_service.publish_event(session, event_type=event_type, payload=payload)

    return record


async def get_by_idempotency_key(
    session: AsyncSession,
    idempotency_key: str,
) -> IssuerAuthorizationDTO | None:
    return await repository.get_by_idempotency_key(session, idempotency_key)


async def list_card_authorizations(
    session: AsyncSession,
    card_id: uuid.UUID,
    limit: int = 100,
    offset: int = 0,
) -> list[IssuerAuthorizationDTO]:
    return await repository.list_by_card_id(
        session=session,
        card_id=card_id,
        limit=limit,
        offset=offset,
    )
