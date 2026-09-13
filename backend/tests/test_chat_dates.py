from datetime import date

import pytest
from fastapi import HTTPException

from app.api.routes.chat import (
    resolve_travel_date,
)


REFERENCE_DATE = date(2026, 7, 22)  # Wednesday


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("today", date(2026, 7, 22)),
        ("tomorrow", date(2026, 7, 23)),
        (
            "day after tomorrow",
            date(2026, 7, 24),
        ),
        ("in 3 days", date(2026, 7, 25)),
        ("this Friday", date(2026, 7, 24)),
        ("next Friday", date(2026, 7, 31)),
        (
            "this weekend",
            date(2026, 7, 25),
        ),
        (
            "next weekend",
            date(2026, 8, 1),
        ),
        ("25 July", date(2026, 7, 25)),
        ("July 25", date(2026, 7, 25)),
        ("25/07/2026", date(2026, 7, 25)),
        ("25-07-2026", date(2026, 7, 25)),
        ("2026-07-25", date(2026, 7, 25)),
    ],
)
def test_resolve_travel_date(
    value: str,
    expected: date,
) -> None:
    assert (
        resolve_travel_date(
            value,
            reference_date=REFERENCE_DATE,
        )
        == expected
    )


def test_date_without_year_moves_to_next_year() -> None:
    assert resolve_travel_date(
        "10 July",
        reference_date=REFERENCE_DATE,
    ) == date(2027, 7, 10)


def test_empty_date_returns_none() -> None:
    assert (
        resolve_travel_date(
            "   ",
            reference_date=REFERENCE_DATE,
        )
        is None
    )


def test_invalid_date_raises_bad_request() -> None:
    with pytest.raises(HTTPException) as exc_info:
        resolve_travel_date(
            "someday maybe",
            reference_date=REFERENCE_DATE,
        )

    assert exc_info.value.status_code == 400