from datetime import datetime, timedelta, timezone

import pytest

from db.queries import (
    STALE_HEARTBEAT_SECONDS,
    _is_stale_auto_session,
)


NOW = datetime(2026, 5, 12, 12, 0, 0, tzinfo=timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.isoformat()


class TestIsStaleAutoSession:
    def test_not_live_is_never_stale(self):
        advisor = {
            "is_live": False,
            "last_event_source": "extension",
            "last_heartbeat_at": _iso(NOW - timedelta(hours=2)),
            "session_started_at": _iso(NOW - timedelta(hours=2)),
        }
        assert _is_stale_auto_session(advisor, NOW) is False

    def test_manual_session_never_stale(self):
        """Sessioni avviate manualmente non hanno heartbeat: non vanno
        chiuse automaticamente, l'operatore deve premere Stop."""
        advisor = {
            "is_live": True,
            "last_event_source": "manual",
            "last_heartbeat_at": None,
            "session_started_at": _iso(NOW - timedelta(hours=5)),
        }
        assert _is_stale_auto_session(advisor, NOW) is False

    def test_fresh_heartbeat_is_alive(self):
        advisor = {
            "is_live": True,
            "last_event_source": "extension",
            "last_heartbeat_at": _iso(NOW - timedelta(seconds=10)),
            "session_started_at": _iso(NOW - timedelta(minutes=30)),
        }
        assert _is_stale_auto_session(advisor, NOW) is False

    def test_heartbeat_just_below_threshold(self):
        advisor = {
            "is_live": True,
            "last_event_source": "extension",
            "last_heartbeat_at": _iso(
                NOW - timedelta(seconds=STALE_HEARTBEAT_SECONDS - 1)
            ),
            "session_started_at": _iso(NOW - timedelta(minutes=10)),
        }
        assert _is_stale_auto_session(advisor, NOW) is False

    def test_heartbeat_over_threshold_is_stale(self):
        advisor = {
            "is_live": True,
            "last_event_source": "extension",
            "last_heartbeat_at": _iso(
                NOW - timedelta(seconds=STALE_HEARTBEAT_SECONDS + 1)
            ),
            "session_started_at": _iso(NOW - timedelta(minutes=10)),
        }
        assert _is_stale_auto_session(advisor, NOW) is True

    def test_missing_heartbeat_falls_back_to_session_start(self):
        """Sessioni AUTO partite prima dell'upgrade non avranno heartbeat:
        usiamo session_started_at come ripiego. Se la sessione e` partita
        da poco, non e` stale anche senza heartbeat."""
        advisor = {
            "is_live": True,
            "last_event_source": "extension",
            "last_heartbeat_at": None,
            "session_started_at": _iso(NOW - timedelta(seconds=30)),
        }
        assert _is_stale_auto_session(advisor, NOW) is False

    def test_missing_heartbeat_and_old_start_is_stale(self):
        advisor = {
            "is_live": True,
            "last_event_source": "extension",
            "last_heartbeat_at": None,
            "session_started_at": _iso(
                NOW - timedelta(seconds=STALE_HEARTBEAT_SECONDS + 60)
            ),
        }
        assert _is_stale_auto_session(advisor, NOW) is True

    def test_no_timestamps_is_not_stale(self):
        advisor = {
            "is_live": True,
            "last_event_source": "extension",
            "last_heartbeat_at": None,
            "session_started_at": None,
        }
        assert _is_stale_auto_session(advisor, NOW) is False

    @pytest.mark.parametrize("source", ["", None, "unknown"])
    def test_unknown_source_treated_as_manual(self, source):
        advisor = {
            "is_live": True,
            "last_event_source": source,
            "last_heartbeat_at": None,
            "session_started_at": _iso(NOW - timedelta(hours=2)),
        }
        assert _is_stale_auto_session(advisor, NOW) is False
