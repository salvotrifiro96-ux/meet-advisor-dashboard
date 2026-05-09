import os

import streamlit as st
from supabase import Client, create_client


def _get_secret(key: str) -> str:
    try:
        value = st.secrets[key]
        if value:
            return str(value)
    except (KeyError, FileNotFoundError, st.errors.StreamlitSecretNotFoundError):
        pass
    value = os.environ.get(key, "")
    if not value:
        raise RuntimeError(
            f"Missing required secret '{key}'. "
            "Set it in .streamlit/secrets.toml or as an environment variable."
        )
    return value


@st.cache_resource
def get_supabase() -> Client:
    url = _get_secret("SUPABASE_URL")
    key = _get_secret("SUPABASE_KEY")
    return create_client(url, key)
