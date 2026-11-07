"""
Unit tests for Prescripto 2.0 Medicine Schedule & iCalendar Generator.
"""
import uuid
from datetime import datetime, timezone, timedelta
from prescripto.domain.reminder.generator import (
    generate_default_times,
    parse_duration_days,
    compute_due_dates_utc,
    generate_ics_calendar,
)


def test_generate_default_times_presets():
    # 1-0-1: Morning and night
    assert generate_default_times("1-0-1") == ["08:00", "21:00"]

    # 1-1-1 / TDS: Morning, afternoon, night
    assert generate_default_times("1-1-1") == ["08:00", "14:00", "21:00"]
    assert generate_default_times("TDS") == ["08:00", "14:00", "21:00"]

    # 1-0-0: Morning only
    assert generate_default_times("1-0-0") == ["08:00"]

    # 0-0-1 / HS / Bedtime: Night
    assert generate_default_times("0-0-1") == ["21:30"]
    assert generate_default_times("HS") == ["21:30"]

    # 1-1-1-1 / QID
    assert generate_default_times("QID") == ["08:00", "12:00", "16:00", "20:00"]


def test_generate_default_times_intervals():
    # q6h: 4 times spaced by 6 hours
    assert generate_default_times("q6h") == ["06:00", "12:00", "18:00", "00:00"]

    # q8h: 3 times spaced by 8 hours
    assert generate_default_times("q8h") == ["08:00", "16:00", "00:00"]

    # q12h: 2 times
    assert generate_default_times("q12h") == ["08:00", "20:00"]


def test_food_timing_shifts():
    # After food shifts morning/afternoon/night later by 30 mins
    assert generate_default_times("1-1-1", "after food") == ["08:30", "14:30", "21:30"]
    assert generate_default_times("BD", "pc") == ["08:30", "21:30"]

    # Before food shifts earlier by 30 mins
    assert generate_default_times("1-0-1", "before food") == ["07:30", "20:30"]
    assert generate_default_times("OD", "empty stomach") == ["07:30"]


def test_sos_as_needed_produces_no_scheduled_alarms():
    assert generate_default_times("SOS") == []
    assert generate_default_times("PRN for pain") == []
    assert generate_default_times("take as needed") == []


def test_parse_duration_days():
    assert parse_duration_days("5 days") == 5
    assert parse_duration_days("x 7 d") == 7
    assert parse_duration_days("for 2 weeks") == 14
    assert parse_duration_days("1 month") == 30
    assert parse_duration_days("as needed") is None
    assert parse_duration_days("SOS") is None
    assert parse_duration_days(None) is None


def test_compute_due_dates_utc():
    now_utc = datetime.now(timezone.utc)
    times = ["08:00", "20:00"]
    due_dates = compute_due_dates_utc(
        local_times=times,
        start_date=now_utc,
        end_date=now_utc + timedelta(days=2),
        tz_str="Asia/Kolkata",
        days_ahead=2,
    )
    assert len(due_dates) > 0
    # Every date should have UTC tzinfo
    for d in due_dates:
        assert d.tzinfo is not None


def test_generate_ics_calendar():
    event_id = uuid.uuid4()
    now_utc = datetime.now(timezone.utc)
    ics = generate_ics_calendar(
        medicine_name="Amoxicillin 500mg",
        dosage_text="1 cap after food",
        events=[(event_id, now_utc)],
        tz_str="Asia/Kolkata",
    )
    assert "BEGIN:VCALENDAR" in ics
    assert "VERSION:2.0" in ics
    assert "BEGIN:VEVENT" in ics
    assert "Take Amoxicillin 500mg" in ics
    assert "BEGIN:VALARM" in ics
    assert "TRIGGER:-PT0M" in ics
    assert "END:VCALENDAR" in ics

