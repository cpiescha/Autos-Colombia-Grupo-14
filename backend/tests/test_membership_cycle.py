from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.services.membership_cycle import MembershipCycleService


BOGOTA = ZoneInfo("America/Bogota")


def test_advance_payment_extends_from_current_cutoff():
    current_cutoff = datetime(2026, 12, 20, 0, 0, tzinfo=BOGOTA)
    paid_at = datetime(2026, 12, 5, 10, 30, tzinfo=BOGOTA)

    cycle = MembershipCycleService.calculate(current_cutoff, paid_at)

    assert cycle.previous_cutoff == current_cutoff
    assert cycle.coverage_start == current_cutoff
    assert cycle.new_cutoff == current_cutoff + timedelta(days=30)


def test_overdue_payment_preserves_original_cycle():
    current_cutoff = datetime(2026, 10, 20, 0, 0, tzinfo=BOGOTA)
    paid_at = datetime(2026, 11, 5, 9, 15, tzinfo=BOGOTA)

    cycle = MembershipCycleService.calculate(current_cutoff, paid_at)

    assert cycle.previous_cutoff == current_cutoff
    assert cycle.coverage_start == current_cutoff
    assert cycle.new_cutoff == current_cutoff + timedelta(days=30)


def test_payment_on_cutoff_day_extends_from_current_cutoff():
    current_cutoff = datetime(2026, 11, 20, 0, 0, tzinfo=BOGOTA)
    paid_at = datetime(2026, 11, 20, 16, 45, tzinfo=BOGOTA)

    cycle = MembershipCycleService.calculate(current_cutoff, paid_at)

    assert cycle.previous_cutoff == current_cutoff
    assert cycle.coverage_start == current_cutoff
    assert cycle.new_cutoff == current_cutoff + timedelta(days=30)


def test_first_payment_starts_cycle_from_payment_date():
    paid_at = datetime(2026, 11, 7, 14, 20, tzinfo=BOGOTA)

    cycle = MembershipCycleService.calculate(None, paid_at)

    assert cycle.previous_cutoff is None
    assert cycle.coverage_start == paid_at
    assert cycle.new_cutoff == paid_at + timedelta(days=30)
