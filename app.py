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
GRID_COLUMNS = 3


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
        @keyframes pulse-card {
          0%, 100% { box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.25); }
          50% { box-shadow: 0 0 0 6px rgba(34, 197, 94, 0.05); }
        }
        .status-dot {
          display: inline-block;
          width: 12px;
          height: 12px;
          border-radius: 50%;
          vertical-align: middle;
        }
        .status-live {
          animation: pulse-green 1.1s ease-in-out infinite;
        }
        .status-idle {
          background-color: #9ca3af;
        }
        .source-badge {
          display: inline-block;
          padding: 2px 8px;
          border-radius: 10px;
          font-size: 0.7rem;
          font-weight: 600;
          letter-spacing: 0.04em;
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

        /* Card-based grid layout */
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.advisor-card-marker-live) {
          border-color: rgba(34, 197, 94, 0.55) !important;
          box-shadow: 0 0 0 1px rgba(34, 197, 94, 0.25), 0 8px 18px -10px rgba(34, 197, 94, 0.35) !important;
          animation: pulse-card 1.8s ease-in-out infinite;
        }
        .card-status-row {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-bottom: 4px;
          font-size: 0.72rem;
          font-weight: 700;
          letter-spacing: 0.06em;
          text-transform: uppercase;
        }
        .card-status-row.live {
          color: #16a34a;
          animation: pulse-name 1.6s ease-in-out infinite;
        }
        .card-status-row.idle {
          color: #9ca3af;
        }
        /* card-name: usa il colore di testo del tema (funziona light + dark) */
        .card-name {
          font-size: 1.25rem;
          font-weight: 700;
          line-height: 1.2;
          margin-bottom: 12px;
          color: inherit;
        }
        .card-name.live {
          color: #16a34a;
        }
        .card-timer {
          font-variant-numeric: tabular-nums;
          font-size: 1.9rem;
          font-weight: 700;
          color: #16a34a;
          margin-bottom: 4px;
        }
        .card-last-session {
          color: #6b7280;
          font-style: italic;
          font-size: 0.9rem;
          margin-bottom: 4px;
        }
        .card-sessions {
          color: #6b7280;
          font-size: 0.85rem;
          margin-top: 8px;
          margin-bottom: 12px;
        }
        .card-sessions strong {
          color: inherit;
          font-weight: 700;
        }
        .meet-link-btn {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          width: 100%;
          padding: 6px 12px;
          border: 1px solid rgba(120, 120, 120, 0.4);
          border-radius: 8px;
          text-decoration: none !important;
          font-size: 0.85rem;
          font-weight: 500;
          color: inherit !important;
          background: transparent;
          transition: all 0.15s ease;
          box-sizing: border-box;
          height: 38px;
        }
        .meet-link-btn:hover {
          border-color: rgba(34, 197, 94, 0.7);
          color: #16a34a !important;
          background: rgba(34, 197, 94, 0.06);
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


def render_advisor_card(advisor: dict, now: datetime) -> None:
    is_live = bool(advisor.get("is_live"))

    with st.container(border=True):
        # Hidden marker — used by CSS :has() to style the parent container
        # in green when the advisor is live.
        if is_live:
            st.markdown(
                '<span class="advisor-card-marker-live" style="display:none"></span>',
                unsafe_allow_html=True,
            )

        # Status row (LIVE / IDLE label + source badge)
        if is_live:
            source = (advisor.get("last_event_source") or "manual").lower()
            badge_class = "source-auto" if source == "extension" else "source-manual"
            badge_label = "AUTO" if source == "extension" else "MANUAL"
            st.markdown(
                f'<div class="card-status-row live">'
                f'<span class="status-dot status-live"></span>'
                f'<span>LIVE</span>'
                f'<span class="source-badge {badge_class}">{badge_label}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div class="card-status-row idle">'
                '<span class="status-dot status-idle"></span>'
                '<span>Idle</span>'
                '</div>',
                unsafe_allow_html=True,
            )

        # Advisor name
        name_class = "card-name live" if is_live else "card-name"
        st.markdown(
            f'<div class="{name_class}">{advisor["name"]}</div>',
            unsafe_allow_html=True,
        )

        # Timer (live) or last-session label (idle)
        if is_live:
            started = parse_iso_utc(advisor.get("session_started_at"))
            elapsed = int((now - started).total_seconds()) if started else 0
            st.markdown(
                f'<div class="card-timer">⏱ {format_timer_hms(elapsed)}</div>',
                unsafe_allow_html=True,
            )
        else:
            last_ended = parse_iso_utc(advisor.get("last_session_ended_at"))
            if last_ended:
                label = format_relative_minutes(last_ended, now)
            else:
                label = "nessuna consulenza oggi"
            st.markdown(
                f'<div class="card-last-session">{label}</div>',
                unsafe_allow_html=True,
            )

        # Sessions count today
        count = advisor["sessions_today"]
        label = "consulenza" if count == 1 else "consulenze"
        st.markdown(
            f'<div class="card-sessions">📊 <strong>{count}</strong> {label} oggi (≥10 min)</div>',
            unsafe_allow_html=True,
        )

        # Action button + Meet link side by side
        action_col, link_col = st.columns([1, 1])
        with action_col:
            if is_live:
                if st.button(
                    "⏹ Stop",
                    key=f"stop_{advisor['id']}",
                    type="primary",
                    use_container_width=True,
                ):
                    stop_session(advisor["id"])
                    st.rerun()
            else:
                if st.button(
                    "▶ Start",
                    key=f"start_{advisor['id']}",
                    use_container_width=True,
                ):
                    start_session(advisor["id"])
                    st.rerun()
        with link_col:
            st.markdown(
                f'<a href="{advisor["meet_link"]}" target="_blank" '
                f'rel="noopener noreferrer" class="meet-link-btn">Apri Meet ↗</a>',
                unsafe_allow_html=True,
            )


def render_advisor_grid(advisors: list[dict], now: datetime) -> None:
    for start in range(0, len(advisors), GRID_COLUMNS):
        row_advisors = advisors[start : start + GRID_COLUMNS]
        cols = st.columns(GRID_COLUMNS)
        for col, advisor in zip(cols, row_advisors):
            with col:
                render_advisor_card(advisor, now)


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
    render_advisor_grid(advisors, now)
    st.divider()
    render_admin_panel(advisors)
    st.caption("Live Advisor Dashboard · Leone Master School")


if __name__ == "__main__":
    main()
