from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import require_administrator
from app.db.session import get_db
from app.models import Payment, UserAccount
from app.schemas.payment import AnnulPaymentRequest, PaymentResponse
from app.services.payment_annulment import PaymentAnnulmentService

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


@router.patch("/{payment_id}/anular", response_model=PaymentResponse)
def annul_payment(
    payment_id: int,
    body: AnnulPaymentRequest,
    account: UserAccount = Depends(require_administrator),
    db: Session = Depends(get_db),
) -> PaymentResponse:
    payment = PaymentAnnulmentService(db).annul(payment_id, account, body.motivo)
    return _response(payment)
