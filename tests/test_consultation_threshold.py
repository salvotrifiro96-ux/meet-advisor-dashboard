"""Test della logica di filtro 'consulenza reale' (>= 10 min)."""

from datetime import datetime, timedelta, timezone

import pytest

from db.queries import (
    MIN_CONSULTATION_SECONDS,
    _is_real_consultation,
    _session_duration_seconds,
)


NOW = datetime(2026, 5, 11, 12, 0, 0, tzinfo=timezone.utc)


def _started(seconds_ago: int) -> str:
    return (NOW - timedelta(seconds=seconds_ago)).isoformat()


class TestSessionDurationSeconds:
    def test_ended_session_uses_stored_duration(self):
        session = {
            "started_at": _started(1200),
            "ended_at": _started(600),
            "duration_seconds": 600,
        }
        assert _session_duration_seconds(session, NOW) == 600

    def test_ended_session_with_null_duration_returns_zero(self):
        session = {
            "started_at": _started(1200),
            "ended_at": _started(600),
            "duration_seconds": None,
        }
        assert _session_duration_seconds(session, NOW) == 0

    def test_live_session_uses_elapsed_time(self):
        session = {
            "started_at": _started(300),
            "ended_at": None,
            "duration_seconds": None,
        }
        assert _session_duration_seconds(session, NOW) == 300

    def test_live_session_without_started_at_returns_zero(self):
        session = {"started_at": None, "ended_at": None, "duration_seconds": None}
        assert _session_duration_seconds(session, NOW) == 0


class TestIsRealConsultation:
    def test_constant_is_ten_minutes(self):
        assert MIN_CONSULTATION_SECONDS == 600

    @pytest.mark.parametrize("duration_seconds", [0, 60, 300, 599])
    def test_short_ended_session_is_not_real(self, duration_seconds: int):
        session = {
            "started_at": _started(duration_seconds + 100),
            "ended_at": _started(100),
            "duration_seconds": duration_seconds,
        }
        assert _is_real_consultation(session, NOW) is False

    @pytest.mark.parametrize("duration_seconds", [600, 601, 1800, 7200])
    def test_long_ended_session_is_real(self, duration_seconds: int):
        session = {
            "started_at": _started(duration_seconds + 100),
            "ended_at": _started(100),
            "duration_seconds": duration_seconds,
        }
        assert _is_real_consultation(session, NOW) is True

    def test_live_session_below_threshold_is_not_real(self):
        session = {
            "started_at": _started(120),
            "ended_at": None,
            "duration_seconds": None,
        }
        assert _is_real_consultation(session, NOW) is False

    def test_live_session_just_at_threshold_is_real(self):
        session = {
            "started_at": _started(600),
            "ended_at": None,
            "duration_seconds": None,
        }
        assert _is_real_consultation(session, NOW) is True

    def test_live_session_above_threshold_is_real(self):
        session = {
            "started_at": _started(1500),
            "ended_at": None,
            "duration_seconds": None,
        }
        assert _is_real_consultation(session, NOW) is True

    def test_reset_session_with_zero_duration_is_not_real(self):
        # Caso del reset_advisor / sessione abbandonata: chiusa ma con
        # duration_seconds = 0
        session = {
            "started_at": _started(180_000),
            "ended_at": _started(0),
            "duration_seconds": 0,
        }
        assert _is_real_consultation(session, NOW) is False
