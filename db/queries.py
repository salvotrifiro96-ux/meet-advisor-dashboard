from datetime import datetime, timezone
from typing import Any

from db.client import get_supabase
from db.format import parse_iso_utc


def _today_start_iso() -> str:
    now = datetime.now(timezone.utc)
    return now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()


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

    sessions_by_advisor: dict[int, list[dict[str, Any]]] = {}
    for session in sessions:
        sessions_by_advisor.setdefault(session["advisor_id"], []).append(session)

    enriched: list[dict[str, Any]] = []
    for advisor in advisors:
        today_sessions = sessions_by_advisor.get(advisor["id"], [])
        completed_today = [s for s in today_sessions if s.get("ended_at")]
        last_ended_at = (
            max(s["ended_at"] for s in completed_today) if completed_today else None
        )
        total_duration_today = sum(
            int(s["duration_seconds"] or 0) for s in completed_today
        )
        enriched.append(
            {
                **advisor,
                "sessions_today": len(today_sessions),
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

    live_now = sum(1 for a in advisors if a.get("is_live"))
    total_today = len(sessions)

    completed = [s for s in sessions if s.get("duration_seconds")]
    if completed:
        durations = [int(s["duration_seconds"]) for s in completed]
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
