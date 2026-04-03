import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.issuer.cards import repository
from app.issuer.cards.schemas import CardBalanceResponse, CardDTO, CardholderDTO
from app.ledger import repository as ledger_repository
from app.ledger.models import LedgerAccount
from shared.enums.currency import Currency
from shared.exceptions import PaymentNotFoundError
from shared.logger import get_logger

logger = get_logger(__name__)


async def create_cardholder(
    session: AsyncSession,
    name: str,
    email: str,
) -> CardholderDTO:
    cardholder = await repository.create_cardholder(session, name=name, email=email)
    logger.info("cardholder created | cardholder_id=%s email=%s", cardholder.id, email)
    return cardholder


async def create_card(
    session: AsyncSession,
    cardholder_id: uuid.UUID,
    credit_limit: int,
    currency: Currency,
    last_four: str | None = None,
) -> CardDTO:
    # verify cardholder exists
    cardholder = await repository.get_cardholder(session, cardholder_id)
    if cardholder is None:
        raise PaymentNotFoundError(f"Cardholder not found: {cardholder_id}")

    # create the two dedicated ledger accounts for this card
    # available_balance_account: holds negative entries as credit is consumed by authorizations
    # pending_hold_account: holds positive entries for authorized-but-not-settled amounts
    available_balance_account = LedgerAccount(
        name=f"card:{cardholder_id}:available_balance",
        account_type="asset",
        currency=currency,
    )
    pending_hold_account = LedgerAccount(
        name=f"card:{cardholder_id}:pending_hold",
        account_type="liability",
        currency=currency,
    )
    session.add(available_balance_account)
    session.add(pending_hold_account)
    await session.flush()

    card = await repository.create_card(
        session,
        cardholder_id=cardholder_id,
        credit_limit=credit_limit,
        currency=currency,
        available_balance_account_id=available_balance_account.id,
        pending_hold_account_id=pending_hold_account.id,
        last_four=last_four,
    )

    logger.info(
        "card issued | card_id=%s cardholder_id=%s credit_limit=%d currency=%s",
        card.id,
        cardholder_id,
        credit_limit,
        currency,
    )
    return card


async def get_card_balance(
    session: AsyncSession,
    card_id: uuid.UUID,
) -> CardBalanceResponse:
    card = await repository.get_card(session, card_id)
    if card is None:
        raise PaymentNotFoundError(f"Card not found: {card_id}")

    currency = Currency(card.currency)

    available_balance = await ledger_repository.get_account_balance(
        session, card.available_balance_account_id, currency
    )
    pending_holds = await ledger_repository.get_account_balance(
        session, card.pending_hold_account_id, currency
    )

    # available credit = credit_limit + balance(available_balance_account)
    # the available_balance_account accumulates negative entries as holds are placed,
    # so this naturally reduces available credit without needing a separate calculation
    available_credit = card.credit_limit + available_balance.balance

    return CardBalanceResponse(
        card_id=card.id,
        credit_limit=card.credit_limit,
        available_credit=available_credit,
        pending_holds=pending_holds.balance,
        currency=card.currency,
    )
