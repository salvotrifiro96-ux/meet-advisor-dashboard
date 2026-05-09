from datetime import datetime, timezone

import pytest

from db.format import (
    format_duration_short,
    format_relative_minutes,
    format_timer_hms,
    parse_iso_utc,
)


class TestFormatTimerHms:
    def test_zero_seconds(self):
        assert format_timer_hms(0) == "00:00:00"

    def test_under_a_minute(self):
        assert format_timer_hms(45) == "00:00:45"

    def test_full_minutes(self):
        assert format_timer_hms(125) == "00:02:05"

    def test_over_an_hour(self):
        assert format_timer_hms(3725) == "01:02:05"

    def test_negative_clamped_to_zero(self):
        assert format_timer_hms(-10) == "00:00:00"


class TestFormatDurationShort:
    @pytest.mark.parametrize("value", [None, 0, -5])
    def test_empty_or_negative(self, value):
        assert format_duration_short(value) == "—"

    def test_seconds_only(self):
        assert format_duration_short(45) == "45s"

    def test_minutes_only(self):
        assert format_duration_short(180) == "3min"

    def test_hours_and_minutes(self):
        assert format_duration_short(3900) == "1h 5min"

    def test_exact_hour(self):
        assert format_duration_short(3600) == "1h 0min"


class TestParseIsoUtc:
    def test_returns_none_on_none(self):
        assert parse_iso_utc(None) is None

    def test_handles_z_suffix(self):
        result = parse_iso_utc("2026-05-09T11:30:00Z")
        assert result == datetime(2026, 5, 9, 11, 30, tzinfo=timezone.utc)

    def test_handles_offset(self):
        result = parse_iso_utc("2026-05-09T11:30:00+00:00")
        assert result.tzinfo is not None

    def test_naive_assumed_utc(self):
        result = parse_iso_utc("2026-05-09T11:30:00")
        assert result.tzinfo == timezone.utc

    def test_passthrough_datetime(self):
        original = datetime(2026, 5, 9, 11, 30, tzinfo=timezone.utc)
        assert parse_iso_utc(original) == original


class TestFormatRelativeMinutes:
    def setup_method(self):
        self.now = datetime(2026, 5, 9, 12, 0, 0, tzinfo=timezone.utc)

    def test_just_now(self):
        ref = datetime(2026, 5, 9, 11, 59, 30, tzinfo=timezone.utc)
        assert format_relative_minutes(ref, self.now) == "ultima: poco fa"

    def test_minutes_ago(self):
        ref = datetime(2026, 5, 9, 11, 35, 0, tzinfo=timezone.utc)
        assert format_relative_minutes(ref, self.now) == "ultima: 25 min fa"

    def test_hours_and_minutes_ago(self):
        ref = datetime(2026, 5, 9, 9, 45, 0, tzinfo=timezone.utc)
        assert format_relative_minutes(ref, self.now) == "ultima: 2h 15min fa"

    def test_exact_hours(self):
        ref = datetime(2026, 5, 9, 10, 0, 0, tzinfo=timezone.utc)
        assert format_relative_minutes(ref, self.now) == "ultima: 2h fa"
