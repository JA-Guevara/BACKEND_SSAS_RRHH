from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

from ssas.suscripciones.application.reconciliation import derived_status
from ssas.suscripciones.infrastructure.http import router as subscriptions_router
from ssas.suscripciones.infrastructure.http.router import _claim_stripe_event, _map_status
from ssas.main import app


def subscription(**overrides):
    values = {
        "estado": "ACTIVA",
        "periodo_prueba_hasta": None,
        "fecha_fin": None,
        "cancelar_al_fin_periodo": False,
        "updated_at": datetime.now(UTC),
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_maps_stripe_statuses() -> None:
    assert _map_status("active") == "ACTIVA"
    assert _map_status("trialing") == "PRUEBA"
    assert _map_status("past_due") == "PAGO_FALLIDO"
    assert _map_status("canceled") == "CANCELADA"


@pytest.mark.asyncio
async def test_stripe_webhook_needs_signature_not_user_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(subscriptions_router, "_stripe_ready", lambda **_kwargs: None)

    def reject_signature(*_args):
        raise ValueError("invalid signature")

    monkeypatch.setattr(subscriptions_router.stripe.Webhook, "construct_event", reject_signature)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        webhook_response = await client.post(
            "/api/v1/webhooks/stripe",
            content=b"{}",
            headers={"Stripe-Signature": "invalid"},
        )
        protected_response = await client.get("/api/v1/suscripcion")

    assert webhook_response.status_code == 400
    assert webhook_response.json()["detail"] == "Firma Stripe inválida"
    assert protected_response.status_code == 401


def test_expired_trial_becomes_expired() -> None:
    today = datetime.now(UTC).date()
    item = subscription(estado="PRUEBA", periodo_prueba_hasta=today - timedelta(days=1))
    assert derived_status(item, today=today, now=datetime.now(UTC), grace_days=3) == "VENCIDA"


def test_failed_payment_is_suspended_after_grace_period() -> None:
    item = subscription(
        estado="PAGO_FALLIDO",
        updated_at=datetime.now(UTC) - timedelta(days=4),
    )
    assert derived_status(item, today=datetime.now(UTC).date(), now=datetime.now(UTC), grace_days=3) == "SUSPENDIDA"


def test_future_active_subscription_is_unchanged() -> None:
    today = datetime.now(UTC).date()
    item = subscription(fecha_fin=today + timedelta(days=30))
    assert derived_status(item, today=today, now=datetime.now(UTC), grace_days=3) == "ACTIVA"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("previous_status", "inserted", "expected_attempts", "duplicate"),
    [
        ("PROCESANDO", True, 1, False),
        ("PROCESADO", False, 1, True),
        ("FALLIDO", False, 2, False),
        ("PROCESANDO", False, 2, False),
    ],
)
async def test_stripe_event_claim_only_skips_processed_events(
    previous_status: str, inserted: bool, expected_attempts: int, duplicate: bool
) -> None:
    log = SimpleNamespace(
        estado_procesamiento=previous_status,
        intentos=1,
        fecha_procesamiento=datetime.now(UTC),
        error="fallo anterior",
    )
    session = SimpleNamespace(execute=AsyncMock(side_effect=[
        SimpleNamespace(rowcount=int(inserted)),
        SimpleNamespace(scalar_one=lambda: log),
    ]))

    result = await _claim_stripe_event(session, {"id": "evt_test", "type": "invoice.paid"})

    assert (result is None) is duplicate
    assert log.intentos == expected_attempts
    if not duplicate:
        assert log.estado_procesamiento == "PROCESANDO"
        assert log.fecha_procesamiento is None
        assert log.error is None
    assert session.execute.await_count == 2


@pytest.mark.asyncio
async def test_failed_stripe_webhook_can_succeed_on_retry(monkeypatch: pytest.MonkeyPatch) -> None:
    event = {
        "id": "evt_retry",
        "type": "checkout.session.completed",
        "data": {"object": {
            "metadata": {"empresa_id": "company-a", "plan_id": "plan-a"},
            "customer": "cus_test",
            "subscription": "sub_test",
        }},
    }
    log = SimpleNamespace(estado_procesamiento="PROCESANDO", error=None, fecha_procesamiento=None)
    item = SimpleNamespace(
        id="subscription-a", empresa_id="company-a", plan_id="old-plan",
        stripe_customer_id=None, stripe_subscription_id=None, estado="PENDIENTE"
    )

    @asynccontextmanager
    async def nested():
        yield

    session = SimpleNamespace(begin_nested=nested, commit=AsyncMock())
    request = SimpleNamespace(body=AsyncMock(return_value=b"payload"))
    target = AsyncMock(side_effect=[RuntimeError("temporary failure"), item])
    sync_modules = AsyncMock()
    audit = AsyncMock()

    async def claim(_session, _event):
        if log.estado_procesamiento == "FALLIDO":
            log.estado_procesamiento = "PROCESANDO"
            log.error = None
        return log

    monkeypatch.setattr(subscriptions_router, "_stripe_ready", lambda **_kwargs: None)
    monkeypatch.setattr(
        subscriptions_router.stripe,
        "Webhook",
        SimpleNamespace(construct_event=lambda *_args: event),
        raising=False,
    )
    monkeypatch.setattr(subscriptions_router, "_claim_stripe_event", claim)
    monkeypatch.setattr(subscriptions_router, "_target_subscription", target)
    monkeypatch.setattr(subscriptions_router, "_sync_modules", sync_modules)
    monkeypatch.setattr(subscriptions_router, "_audit", audit)

    with pytest.raises(RuntimeError, match="temporary failure"):
        await subscriptions_router.stripe_webhook(request, "signature", session)
    assert log.estado_procesamiento == "FALLIDO"
    session.commit.assert_awaited_once()

    result = await subscriptions_router.stripe_webhook(request, "signature", session)
    assert result == {"received": True}
    assert log.estado_procesamiento == "PROCESADO"
    assert log.error is None
    assert item.plan_id == "plan-a"
    assert item.estado == "ACTIVA"
    sync_modules.assert_awaited_once()
    audit.assert_awaited_once()
