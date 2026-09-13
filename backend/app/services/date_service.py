import re
from datetime import UTC, date, datetime, timedelta
from typing import Final

WEEKDAY_NUMBERS: Final[dict[str, int]] = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}

MONTH_NAMES: Final[tuple[str, ...]] = (
    "january",
    "february",
    "march",
    "april",
    "may",
    "june",
    "july",
    "august",
    "september",
    "october",
    "november",
    "december",
    "jan",
    "feb",
    "mar",
    "apr",
    "jun",
    "jul",
    "aug",
    "sep",
    "sept",
    "oct",
    "nov",
    "dec",
)

MONTH_PATTERN: Final[str] = "|".join(MONTH_NAMES)
WEEKDAY_PATTERN: Final[str] = "|".join(WEEKDAY_NUMBERS.keys())


def extract_date_reference(text: str) -> str | None:
    """Extract a user-supplied travel date deterministically from free text.

    Carefully orders patterns so phrases like 'day after tomorrow' are never
    incorrectly matched by 'tomorrow'. Case-insensitive and whitespace-normalized.
    """
    if not text:
        return None

    normalized = " ".join(text.strip().lower().split())
    if not normalized:
        return None

    # 0. Conversational correction with negation: "I meant tomorrow, not Friday", "tomorrow instead of Friday"
    correction_match = re.search(r"^(.*?)(?:,\s*not\b|\s+instead\s+of\b)", normalized)
    if correction_match:
        preferred_part = correction_match.group(1).strip()
        extracted = extract_date_reference(preferred_part)
        if extracted:
            return extracted

    # 1. Multi-word relative date references (longest first)
    if re.search(r"\bday after tomorrow\b", normalized):
        return "day after tomorrow"

    if re.search(r"\btomorrow\b", normalized):
        return "tomorrow"

    if re.search(r"\btoday\b", normalized):
        return "today"

    match = re.search(r"\bin\s+(\d+)\s+days?\b", normalized)
    if match:
        return f"in {match.group(1)} days"

    if re.search(r"\bin\s+(?:a|1)\s+week\b", normalized):
        return "in a week"

    # 2. Weekday & Weekend relative references
    match = re.search(r"\b(this|next)\s+weekend\b", normalized)
    if match:
        return match.group(0)

    match = re.search(rf"\b(this|next)\s+({WEEKDAY_PATTERN})\b", normalized)
    if match:
        return match.group(0)

    # 3. Numeric ISO date: YYYY-MM-DD
    match = re.search(r"\b(\d{4}-\d{1,2}-\d{1,2})\b", normalized)
    if match:
        return match.group(1)

    # 4. Numeric Slash/Hyphen date: DD/MM/YYYY or DD-MM-YYYY
    match = re.search(r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{4})\b", normalized)
    if match:
        return match.group(1)

    # 5. Month & Day formats with optional ordinals (e.g., '25 July', '25th September', 'September 25th')
    match = re.search(
        rf"\b(?:\d{{1,2}}(?:st|nd|rd|th)?\s+(?:{MONTH_PATTERN})|(?:{MONTH_PATTERN})\s+\d{{1,2}}(?:st|nd|rd|th)?)\b",
        normalized,
    )
    if match:
        return match.group(0)

    # 6. Standalone weekday references (e.g., 'Friday', 'for Saturday', 'Saturday instead')
    match = re.search(rf"\b({WEEKDAY_PATTERN})\b", normalized)
    if match:
        return match.group(1)

    return None


def resolve_calendar_date(
    value: str | None,
    *,
    reference_date: date | None = None,
) -> date | None:
    """Resolve natural-language and formatted date expressions to a datetime.date.

    reference_date is injectable for deterministic unit testing.
    In production, defaults to the current UTC date.
    """
    if value is None:
        return None

    normalized = value.strip().lower()
    if not normalized:
        return None

    current_date = (
        reference_date
        if reference_date is not None
        else datetime.now(UTC).date()
    )

    if normalized == "today":
        return current_date

    if normalized == "tomorrow":
        return current_date + timedelta(days=1)

    if normalized == "day after tomorrow":
        return current_date + timedelta(days=2)

    if normalized in {"in a week", "in 1 week"}:
        return current_date + timedelta(days=7)

    if normalized.startswith("in "):
        parts = normalized.split()
        if (
            len(parts) == 3
            and parts[1].isdigit()
            and parts[2] in {"day", "days"}
        ):
            return current_date + timedelta(days=int(parts[1]))

    if normalized.startswith("this "):
        target_name = normalized.removeprefix("this ").strip()
        target_weekday = (
            5
            if target_name == "weekend"
            else WEEKDAY_NUMBERS.get(target_name)
        )
        if target_weekday is not None:
            days_ahead = (target_weekday - current_date.weekday()) % 7
            return current_date + timedelta(days=days_ahead)

    if normalized.startswith("next "):
        target_name = normalized.removeprefix("next ").strip()
        target_weekday = (
            5
            if target_name == "weekend"
            else WEEKDAY_NUMBERS.get(target_name)
        )
        if target_weekday is not None:
            days_ahead = (target_weekday - current_date.weekday()) % 7
            days_ahead += 7
            return current_date + timedelta(days=days_ahead)

    # Standalone weekday references: e.g. "friday", "for friday", "on saturday"
    clean_weekday = normalized.removeprefix("for ").removeprefix("on ").strip()
    target_weekday = WEEKDAY_NUMBERS.get(clean_weekday)
    if target_weekday is not None:
        days_ahead = (target_weekday - current_date.weekday()) % 7
        if days_ahead == 0:
            days_ahead = 7
        return current_date + timedelta(days=days_ahead)

    # Standard explicit formats
    explicit_formats = (
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%d-%m-%Y",
    )
    for fmt in explicit_formats:
        try:
            parsed_dt = datetime.strptime(normalized, fmt).replace(tzinfo=UTC)
            return parsed_dt.date()
        except ValueError:
            continue

    # Month & Day formats with optional ordinals (e.g. "25th September", "September 25th")
    cleaned_ordinals = re.sub(r"(\d{1,2})(?:st|nd|rd|th)", r"\1", normalized)
    month_day_formats = (
        "%d %B",
        "%B %d",
        "%d %b",
        "%b %d",
    )
    for fmt in month_day_formats:
        try:
            # Parse with explicit year appended to avoid Python 3.15 deprecation
            augmented_input = f"{cleaned_ordinals} {current_date.year}"
            augmented_fmt = f"{fmt} %Y"
            parsed_dt = datetime.strptime(augmented_input, augmented_fmt).replace(tzinfo=UTC)
            candidate = parsed_dt.date()

            # If date has already passed in the current reference year, rollover to next year
            if candidate < current_date:
                candidate = date(
                    current_date.year + 1,
                    candidate.month,
                    candidate.day,
                )
            return candidate
        except ValueError:
            continue

    return None
