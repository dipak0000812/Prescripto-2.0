"""
Prescripto AI 2.0 — Medicine Schedule & iCalendar Generator.
Generates local reminder times from Indian prescription frequencies,
computes due dates across timezones, and generates RFC 5545 iCalendar feeds with alarms.
"""
from __future__ import annotations

import re
import uuid
from datetime import datetime, date, time as dtime, timedelta, timezone
from typing import List, Optional, Tuple
from zoneinfo import ZoneInfo


DEFAULT_TIMEZONE = "Asia/Kolkata"


def parse_duration_days(duration_text: Optional[str]) -> Optional[int]:
    """Parses duration string into integer days. Returns None for SOS / PRN / indefinite."""
    if not duration_text:
        return None
    d = duration_text.strip().lower()
    if any(k in d for k in ("sos", "prn", "as needed", "needed", "ongoing", "continuous")):
        return None
    # match '5 days', 'x 5 d', 'for 7 days', '10'
    m_day = re.search(r"\b(\d+)\s*(?:d|day|days)?\b", d)
    m_week = re.search(r"\b(\d+)\s*(?:w|wk|wks|week|weeks)\b", d)
    m_month = re.search(r"\b(\d+)\s*(?:m|mo|mos|month|months)\b", d)

    if m_week:
        return int(m_week.group(1)) * 7
    if m_month:
        return int(m_month.group(1)) * 30
    if m_day:
        return int(m_day.group(1))
    return None


def generate_default_times(
    frequency_text: Optional[str], instructions_text: Optional[str] = None
) -> List[str]:
    """
    Generates recommended HH:MM local times based on prescription frequency and food timing.
    SOS / PRN returns empty list (no scheduled alarms).
    """
    text = f"{frequency_text or ''} {instructions_text or ''}".lower().strip()

    # SOS / as needed has no scheduled alarms
    if any(k in text for k in ("sos", "prn", "as needed", "when required", "if needed")):
        return []

    # Food timing shift
    is_after_food = any(k in text for k in ("after food", "after meals", "pc", "post cibum", "post meal"))
    is_before_food = any(k in text for k in ("before food", "before meals", "ac", "ante cibum", "empty stomach"))

    # Base morning, afternoon, night times
    m_hour, m_min = (8, 30) if is_after_food else ((7, 30) if is_before_food else (8, 0))
    a_hour, a_min = (14, 30) if is_after_food else ((13, 30) if is_before_food else (14, 0))
    e_hour, e_min = (18, 30) if is_after_food else (18, 0)
    n_hour, n_min = (21, 30) if is_after_food else ((20, 30) if is_before_food else (21, 0))

    fmt = lambda h, m: f"{h:02d}:{m:02d}"

    # Interval frequencies (e.g. q6h, q8h, q12h, q4h)
    if "q4h" in text or "every 4 hours" in text:
        return ["06:00", "10:00", "14:00", "18:00", "22:00", "02:00"]
    if "q6h" in text or "every 6 hours" in text:
        return ["06:00", "12:00", "18:00", "00:00"]
    if "q8h" in text or "every 8 hours" in text:
        return ["08:00", "16:00", "00:00"]
    if "q12h" in text or "every 12 hours" in text:
        return ["08:00", "20:00"]

    # Pattern matches (e.g. 1-0-1, 1-1-1, 1-0-0, 0-0-1)
    if "1-1-1-1" in text or "qid" in text or "4 times" in text:
        return ["08:00", "12:00", "16:00", "20:00"]
    if "1-1-1" in text or "tds" in text or "tid" in text or "thrice" in text or "3 times" in text:
        return [fmt(m_hour, m_min), fmt(a_hour, a_min), fmt(n_hour, n_min)]
    if "1-0-1" in text or "bd" in text or "bid" in text or "twice" in text or "2 times" in text:
        return [fmt(m_hour, m_min), fmt(n_hour, n_min)]
    if "1-0-0" in text or "morning" in text:
        return [fmt(m_hour, m_min)]
    if "0-1-0" in text or "afternoon" in text or "noon" in text:
        return [fmt(a_hour, a_min)]
    if "0-0-1" in text or "hs" in text or "bedtime" in text or "at night" in text:
        return ["21:30"]

    # OD (once daily) defaults to morning unless bedtime is indicated
    if "od" in text or "once daily" in text or "daily" in text:
        if "night" in text or "bedtime" in text:
            return ["21:30"]
        return [fmt(m_hour, m_min)]

    # Default fallback: twice daily (morning & night)
    return [fmt(m_hour, m_min), fmt(n_hour, n_min)]


def get_timezone(tz_str: str = DEFAULT_TIMEZONE) -> timezone:
    """Returns timezone, providing built-in fixed offset for Asia/Kolkata/UTC on Windows without tzdata."""
    if tz_str in ("Asia/Kolkata", "IST", "Asia/Calcutta"):
        return timezone(timedelta(hours=5, minutes=30), name="Asia/Kolkata")
    if tz_str in ("UTC", "Z"):
        return timezone.utc
    try:
        from zoneinfo import ZoneInfo
        return ZoneInfo(tz_str)
    except Exception:
        return timezone(timedelta(hours=5, minutes=30), name="Asia/Kolkata")


def compute_due_dates_utc(
    local_times: List[str],
    start_date: datetime,
    end_date: Optional[datetime],
    tz_str: str = DEFAULT_TIMEZONE,
    days_ahead: int = 14,
) -> List[datetime]:
    """
    Computes list of timezone-aware UTC datetimes for scheduled local times.
    Generates dates from max(start_date, today) up to min(end_date, today + days_ahead).
    """
    if not local_times:
        return []

    tz = get_timezone(tz_str)

    now_tz = datetime.now(tz)
    start_tz = start_date.astimezone(tz) if start_date.tzinfo else start_date.replace(tzinfo=tz)

    start_day = max(now_tz.date(), start_tz.date())
    max_day = now_tz.date() + timedelta(days=days_ahead)
    if end_date:
        end_tz = end_date.astimezone(tz) if end_date.tzinfo else end_date.replace(tzinfo=tz)
        max_day = min(max_day, end_tz.date())

    results: List[datetime] = []
    current_day = start_day

    while current_day <= max_day:
        for t_str in sorted(local_times):
            parts = t_str.strip().split(":")
            if len(parts) != 2:
                continue
            try:
                hour = int(parts[0])
                minute = int(parts[1])
            except ValueError:
                continue

            dt_local = datetime(
                year=current_day.year,
                month=current_day.month,
                day=current_day.day,
                hour=hour,
                minute=minute,
                tzinfo=tz,
            )
            # Only include if not in the past
            if dt_local >= now_tz - timedelta(minutes=15):
                results.append(dt_local.astimezone(timezone.utc))

        current_day += timedelta(days=1)

    return sorted(results)


def generate_ics_calendar(
    medicine_name: str,
    dosage_text: Optional[str],
    events: List[Tuple[uuid.UUID, datetime]],
    tz_str: str = DEFAULT_TIMEZONE,
) -> str:
    """
    Generates standard RFC 5545 iCalendar content with alarms (VALARM).
    events: List of (event_id, due_at_utc)
    """
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Prescripto//Prescripto 2.0 Medication Reminders//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:Prescripto - {medicine_name}",
        f"X-WR-TIMEZONE:{tz_str}",
    ]

    for event_id, due_utc in events:
        start_str = due_utc.strftime("%Y%m%dT%H%M%SZ")
        end_dt = due_utc + timedelta(minutes=15)
        end_str = end_dt.strftime("%Y%m%dT%H%M%SZ")
        summary = f"Take {medicine_name}"
        if dosage_text:
            summary += f" ({dosage_text})"
        desc = f"Scheduled dose for {medicine_name}. Prescribed via Prescripto 2.0."

        lines.extend([
            "BEGIN:VEVENT",
            f"UID:prescripto-{event_id}@prescripto.local",
            f"DTSTAMP:{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}",
            f"DTSTART:{start_str}",
            f"DTEND:{end_str}",
            f"SUMMARY:{summary}",
            f"DESCRIPTION:{desc}",
            "STATUS:CONFIRMED",
            "BEGIN:VALARM",
            "TRIGGER:-PT0M",
            "ACTION:DISPLAY",
            f"DESCRIPTION:Time for your medicine: {medicine_name}",
            "END:VALARM",
            "END:VEVENT",
        ])

    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"
