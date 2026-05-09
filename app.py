import os
from datetime import datetime, timezone

import streamlit as st
from dotenv import load_dotenv
from streamlit_autorefresh import st_autorefresh

from db import (
    format_duration_short,
    format_timer_hms,
    get_all_advisors,
    get_today_stats,
    parse_iso_utc,
    reset_advisor,
    start_session,
    stop_session,
)
from db.format import format_relative_minutes

load_dotenv()


REFRESH_INTERVAL_MS = 1000


def _read_password() -> str:
    try:
        configured = st.secrets["APP_PASSWORD"]
        if configured:
            return str(configured)
    except (KeyError, FileNotFoundError, st.errors.StreamlitSecretNotFoundError):
        pass
    return os.environ.get("APP_PASSWORD", "")


def require_password() -> bool:
    expected = _read_password()
    if not expected:
        return True

    if st.session_state.get("authenticated"):
        return True

    st.title("🔒 Live Advisor Dashboard")
    st.caption("Inserisci la password per continuare.")

    with st.form("login_form", clear_on_submit=False):
        candidate = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Accedi", type="primary")

    if submitted:
        if candidate == expected:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Password errata")
    return False


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        @keyframes pulse-green {
          0%, 100% {
            background-color: #16a34a;
            box-shadow: 0 0 6px #22c55e, 0 0 14px #22c55e;
          }
          50% {
            background-color: #22c55e;
            box-shadow: 0 0 18px #22c55e, 0 0 32px #22c55e;
          }
        }
        @keyframes pulse-name {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.65; }
        }
        .status-dot {
          display: inline-block;
          width: 14px;
          height: 14px;
          border-radius: 50%;
          vertical-align: middle;
        }
        .status-live {
          animation: pulse-green 1.1s ease-in-out infinite;
        }
        .status-idle {
          background-color: #9ca3af;
        }
        .advisor-name {
          font-size: 1.05rem;
          font-weight: 500;
          vertical-align: middle;
        }
        .advisor-name-live {
          color: #16a34a;
          font-weight: 700;
          animation: pulse-name 1.6s ease-in-out infinite;
        }
        .timer-live {
          color: #16a34a;
          font-weight: 700;
          font-variant-numeric: tabular-nums;
          font-size: 1.15rem;
        }
        .timer-idle {
          color: #6b7280;
          font-style: italic;
        }
        .source-badge {
          display: inline-block;
          padding: 2px 8px;
          border-radius: 10px;
          font-size: 0.7rem;
          font-weight: 600;
          letter-spacing: 0.04em;
          margin-left: 8px;
          vertical-align: middle;
        }
        .source-auto {
          background: rgba(34, 197, 94, 0.15);
          color: #16a34a;
          border: 1px solid rgba(34, 197, 94, 0.4);
        }
        .source-manual {
          background: rgba(99, 102, 241, 0.15);
          color: #6366f1;
          border: 1px solid rgba(99, 102, 241, 0.4);
        }
        .row-divider {
          border-bottom: 1px solid rgba(150, 150, 150, 0.18);
          margin: 0.25rem 0;
        }
        .meet-link a {
          text-decoration: none;
          font-weight: 500;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header(live_count: int, total_advisors: int, stats: dict) -> None:
    st.title("🎯 Live Advisor Dashboard")
    now_str = datetime.now().strftime("%H:%M:%S")
    st.caption(f"Aggiornamento in tempo reale • orario locale: {now_str}")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Advisor live ora", f"{live_count}/{total_advisors}")
    col2.metric("Consulenze oggi", stats["total_today"])
    col3.metric(
        "Durata media", format_duration_short(stats["avg_duration_seconds"])
    )
    col4.metric(
        "Tempo totale oggi", format_duration_short(stats["total_duration_seconds"])
    )


def render_table_header() -> None:
    cols = st.columns([0.4, 2.4, 2, 1.2, 1.2, 1])
    cols[0].markdown("**•**")
    cols[1].markdown("**Advisor**")
    cols[2].markdown("**Timer / Ultima sessione**")
    cols[3].markdown("**Consulenze oggi**")
    cols[4].markdown("**Azione**")
    cols[5].markdown("**Meet**")


def render_advisor_row(advisor: dict, now: datetime) -> None:
    cols = st.columns([0.4, 2.4, 2, 1.2, 1.2, 1])
    is_live = bool(advisor.get("is_live"))

    if is_live:
        cols[0].markdown(
            '<span class="status-dot status-live"></span>',
            unsafe_allow_html=True,
        )
        source = (advisor.get("last_event_source") or "manual").lower()
        if source == "extension":
            badge_html = '<span class="source-badge source-auto">AUTO</span>'
        else:
            badge_html = '<span class="source-badge source-manual">MANUAL</span>'
        cols[1].markdown(
            f'<span class="advisor-name advisor-name-live">{advisor["name"]}</span>{badge_html}',
            unsafe_allow_html=True,
        )
        started = parse_iso_utc(advisor.get("session_started_at"))
        if started:
            elapsed = int((now - started).total_seconds())
            cols[2].markdown(
                f'<span class="timer-live">⏱ {format_timer_hms(elapsed)}</span>',
                unsafe_allow_html=True,
            )
        else:
            cols[2].markdown("—")
        cols[3].markdown(f"{advisor['sessions_today']}")
        if cols[4].button("⏹ Stop", key=f"stop_{advisor['id']}", type="primary"):
            stop_session(advisor["id"])
            st.rerun()
    else:
        cols[0].markdown(
            '<span class="status-dot status-idle"></span>',
            unsafe_allow_html=True,
        )
        cols[1].markdown(
            f'<span class="advisor-name">{advisor["name"]}</span>',
            unsafe_allow_html=True,
        )
        last_ended = parse_iso_utc(advisor.get("last_session_ended_at"))
        if last_ended:
            cols[2].markdown(
                f'<span class="timer-idle">{format_relative_minutes(last_ended, now)}</span>',
                unsafe_allow_html=True,
            )
        else:
            cols[2].markdown('<span class="timer-idle">nessuna oggi</span>',
                             unsafe_allow_html=True)
        cols[3].markdown(f"{advisor['sessions_today']}")
        if cols[4].button("▶ Start", key=f"start_{advisor['id']}"):
            start_session(advisor["id"])
            st.rerun()

    cols[5].markdown(
        f'<div class="meet-link">[ Apri ↗ ]({advisor["meet_link"]})</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="row-divider"></div>', unsafe_allow_html=True)


def render_admin_panel(advisors: list[dict]) -> None:
    with st.expander("⚙️ Pannello admin (reset stato bloccato)"):
        st.caption(
            "Usa questi pulsanti se uno stato è rimasto erroneamente in LIVE "
            "(es. l'operatore ha chiuso il browser senza cliccare Stop)."
        )
        live_advisors = [a for a in advisors if a.get("is_live")]
        if not live_advisors:
            st.info("Nessun advisor live al momento.")
            return
        for advisor in live_advisors:
            cols = st.columns([3, 1])
            cols[0].markdown(f"• **{advisor['name']}** è marcato come LIVE")
            if cols[1].button("Reset", key=f"reset_{advisor['id']}"):
                reset_advisor(advisor["id"])
                st.rerun()


def main() -> None:
    st.set_page_config(
        page_title="Live Advisor Dashboard",
        page_icon="🎯",
        layout="wide",
    )

    inject_styles()

    if not require_password():
        return

    st_autorefresh(interval=REFRESH_INTERVAL_MS, key="dashboard_refresh")

    advisors = get_all_advisors()
    stats = get_today_stats()
    now = datetime.now(timezone.utc)

    render_header(
        live_count=stats["live_now"],
        total_advisors=len(advisors),
        stats=stats,
    )

    st.divider()
    render_table_header()
    st.markdown('<div class="row-divider"></div>', unsafe_allow_html=True)

    for advisor in advisors:
        render_advisor_row(advisor, now)

    st.divider()
    render_admin_panel(advisors)
    st.caption("Live Advisor Dashboard · Leone Master School")


if __name__ == "__main__":
    main()
