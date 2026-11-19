from dataclasses import dataclass
from datetime import datetime, timedelta


CYCLE_DURATION = timedelta(days=30)


@dataclass(frozen=True)
class MembershipCycle:
    previous_cutoff: datetime | None
    coverage_start: datetime
    new_cutoff: datetime


class MembershipCycleService:
    """Calculate membership coverage without shifting an established cycle."""

    @staticmethod
    def calculate(
        current_cutoff_date: datetime | None,
        paid_at: datetime,
    ) -> MembershipCycle:
        base_date = current_cutoff_date if current_cutoff_date is not None else paid_at
        return MembershipCycle(
            previous_cutoff=current_cutoff_date,
            coverage_start=base_date,
            new_cutoff=base_date + CYCLE_DURATION,
        )
