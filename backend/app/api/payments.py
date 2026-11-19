from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_account, require_administrator
from app.db.session import get_db
from app.models import Payment, UserAccount
from app.schemas.payment import (
    AnnulPaymentRequest,
    PaymentReadResponse,
    PaymentResponse,
    RegisteredPaymentResponse,
    RegisterPaymentRequest,
)
from app.services.payment_annulment import PaymentAnnulmentService
from app.services.payment_queries import PaymentQueryService
from app.services.payment_registration import PaymentRegistrationService

router = APIRouter(prefix="/api/pagos", tags=["pagos"])


def _response(payment: Payment) -> PaymentResponse:
    return PaymentResponse(
        id=payment.id,
        estado=payment.status,
        valor=payment.amount,
        medio=payment.payment_method,
        fecha_corte_anterior=payment.previous_cutoff,
        anulado_en=payment.annulled_at,
        motivo_anulacion=payment.annulment_reason,
    )


def _read_response(payment: Payment) -> PaymentReadResponse:
    return PaymentReadResponse(
        id=payment.id,
        vehiculo_id=payment.vehicle_id,
        cliente_id=payment.client_id,
        mensualidad_id=payment.membership_id,
        estado=payment.status,
        valor=payment.amount,
        medio=payment.payment_method,
        fecha_pago=payment.paid_at,
        cobertura_desde=payment.coverage_start,
        fecha_corte=payment.coverage_end,
        fecha_corte_anterior=payment.previous_cutoff,
        responsable_id=payment.recorded_by,
        anulado_en=payment.annulled_at,
        anulado_por_id=payment.annulled_by,
        motivo_anulacion=payment.annulment_reason,
    )


@router.post(
    "",
    response_model=RegisteredPaymentResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_payment(
    body: RegisterPaymentRequest,
    account: UserAccount = Depends(get_current_account),
    db: Session = Depends(get_db),
) -> RegisteredPaymentResponse:
    payment = PaymentRegistrationService(db).register(
        vehicle_id=body.vehiculo_id,
        amount=body.valor,
        payment_method=body.medio,
        idempotency_key=body.clave_idempotencia,
        account=account,
        paid_at=body.fecha_pago,
    )
    return RegisteredPaymentResponse(
        id=payment.id,
        vehiculo_id=payment.vehicle_id,
        cliente_id=payment.client_id,
        mensualidad_id=payment.membership_id,
        estado=payment.status,
        valor=payment.amount,
        medio=payment.payment_method,
        fecha_pago=payment.paid_at,
        cobertura_desde=payment.coverage_start,
        fecha_corte=payment.coverage_end,
        fecha_corte_anterior=payment.previous_cutoff,
        responsable_id=payment.recorded_by,
    )


@router.get("", response_model=list[PaymentReadResponse])
def list_payments(
    account: UserAccount = Depends(get_current_account),
    db: Session = Depends(get_db),
) -> list[PaymentReadResponse]:
    payments = PaymentQueryService(db).list_payments(account)
    return [_read_response(payment) for payment in payments]


@router.get("/{payment_id}", response_model=PaymentReadResponse)
def get_payment(
    payment_id: int,
    account: UserAccount = Depends(get_current_account),
    db: Session = Depends(get_db),
) -> PaymentReadResponse:
    payment = PaymentQueryService(db).get_payment(payment_id, account)
    return _read_response(payment)


@router.patch("/{payment_id}/anular", response_model=PaymentResponse)
def annul_payment(
    payment_id: int,
    body: AnnulPaymentRequest,
    account: UserAccount = Depends(require_administrator),
    db: Session = Depends(get_db),
) -> PaymentResponse:
    payment = PaymentAnnulmentService(db).annul(payment_id, account, body.motivo)
    return _response(payment)
