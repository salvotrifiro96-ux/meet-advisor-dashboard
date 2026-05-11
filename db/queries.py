from datetime import datetime, timezone
from typing import Any

from db.client import get_supabase
from db.format import parse_iso_utc


# Soglia minima per considerare una sessione una vera "consulenza" — sotto
# questo tempo si tratta di test, click accidentali o ingressi rapidi.
MIN_CONSULTATION_SECONDS = 10 * 60


def _today_start_iso() -> str:
    now = datetime.now(timezone.utc)
    return now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()


def _session_duration_seconds(session: dict[str, Any], now: datetime) -> int:
    """Durata effettiva della sessione in secondi.

    - Se la sessione è già chiusa, usa `duration_seconds` (può essere 0 per
      sessioni resettate).
    - Se la sessione è ancora live (no ended_at), calcola `now - started_at`.
    """
    if session.get("ended_at"):
        return int(session.get("duration_seconds") or 0)
    started = parse_iso_utc(session.get("started_at"))
    if not started:
        return 0
    return max(0, int((now - started).total_seconds()))


def _is_real_consultation(session: dict[str, Any], now: datetime) -> bool:
    """True se la sessione ha superato la soglia minima per essere una consulenza."""
    return _session_duration_seconds(session, now) >= MIN_CONSULTATION_SECONDS


def get_all_advisors() -> list[dict[str, Any]]:
    sb = get_supabase()

    advisors = (
        sb.table("advisors")
        .select("*")
        .order("display_order")
        .execute()
        .data
    ) or []

    today_start = _today_start_iso()
    sessions = (
        sb.table("consultation_sessions")
        .select("*")
        .gte("started_at", today_start)
        .execute()
        .data
    ) or []

    now = datetime.now(timezone.utc)

    sessions_by_advisor: dict[int, list[dict[str, Any]]] = {}
    for session in sessions:
        sessions_by_advisor.setdefault(session["advisor_id"], []).append(session)

    enriched: list[dict[str, Any]] = []
    for advisor in advisors:
        today_sessions = sessions_by_advisor.get(advisor["id"], [])
        real_today = [s for s in today_sessions if _is_real_consultation(s, now)]
        completed_today = [s for s in today_sessions if s.get("ended_at")]
        last_ended_at = (
            max(s["ended_at"] for s in completed_today) if completed_today else None
        )
        # Per il tempo totale "oggi" sommiamo solo le consulenze reali, così
        # il dato è coerente col conteggio "Consulenze oggi".
        total_duration_today = sum(
            _session_duration_seconds(s, now) for s in real_today
        )
        enriched.append(
            {
                **advisor,
                "sessions_today": len(real_today),
                "last_session_ended_at": last_ended_at,
                "total_duration_today_seconds": total_duration_today,
            }
        )
    return enriched


def start_session(advisor_id: int, source: str = "manual") -> None:
    sb = get_supabase()
    now_iso = datetime.now(timezone.utc).isoformat()

    sb.table("consultation_sessions").insert(
        {"advisor_id": advisor_id, "started_at": now_iso, "source": source}
    ).execute()

    sb.table("advisors").update(
        {
            "is_live": True,
            "session_started_at": now_iso,
            "last_event_source": source,
        }
    ).eq("id", advisor_id).execute()


def stop_session(advisor_id: int) -> None:
    sb = get_supabase()
    now = datetime.now(timezone.utc)
    now_iso = now.isoformat()

    advisor_rows = (
        sb.table("advisors")
        .select("session_started_at")
        .eq("id", advisor_id)
        .execute()
        .data
    )
    if not advisor_rows:
        return

    started_raw = advisor_rows[0].get("session_started_at")
    started = parse_iso_utc(started_raw)

    open_sessions = (
        sb.table("consultation_sessions")
        .select("*")
        .eq("advisor_id", advisor_id)
        .is_("ended_at", "null")
        .order("started_at", desc=True)
        .limit(1)
        .execute()
        .data
    ) or []

    if open_sessions:
        session = open_sessions[0]
        session_started = started or parse_iso_utc(session["started_at"])
        duration = (
            int((now - session_started).total_seconds()) if session_started else 0
        )
        sb.table("consultation_sessions").update(
            {"ended_at": now_iso, "duration_seconds": max(duration, 0)}
        ).eq("id", session["id"]).execute()

    sb.table("advisors").update(
        {
            "is_live": False,
            "session_started_at": None,
            "last_event_source": "manual",
        }
    ).eq("id", advisor_id).execute()


def reset_advisor(advisor_id: int) -> None:
    sb = get_supabase()
    sb.table("advisors").update(
        {"is_live": False, "session_started_at": None}
    ).eq("id", advisor_id).execute()
    sb.table("consultation_sessions").update(
        {"ended_at": datetime.now(timezone.utc).isoformat()}
    ).eq("advisor_id", advisor_id).is_("ended_at", "null").execute()


def get_today_stats() -> dict[str, Any]:
    sb = get_supabase()
    today_start = _today_start_iso()

    sessions = (
        sb.table("consultation_sessions")
        .select("*")
        .gte("started_at", today_start)
        .execute()
        .data
    ) or []
    advisors = sb.table("advisors").select("is_live").execute().data or []

    now = datetime.now(timezone.utc)
    live_now = sum(1 for a in advisors if a.get("is_live"))

    # Solo sessioni che hanno superato i 10 minuti contano come "consulenze".
    # Include sessioni ancora live se hanno gia` superato la soglia.
    real_sessions = [s for s in sessions if _is_real_consultation(s, now)]
    total_today = len(real_sessions)

    durations = [_session_duration_seconds(s, now) for s in real_sessions]
    if durations:
        avg_seconds = sum(durations) / len(durations)
        total_seconds = sum(durations)
    else:
        avg_seconds = 0.0
        total_seconds = 0

    return {
        "live_now": live_now,
        "total_today": total_today,
        "avg_duration_seconds": avg_seconds,
        "total_duration_seconds": total_seconds,
    }
