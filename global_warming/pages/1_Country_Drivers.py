from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import streamlit as st
from src.views import render_country_drivers_view


ROOT = Path(__file__).resolve().parents[1]

SAMPLE = ROOT / "data" / "sample.csv"
PROCESSED = ROOT / "data" / "processed.csv"


@st.cache_data
def load_country_data(path: str) -> pd.DataFrame:
    """Load the country-level CO2 emissions dataset."""
    frame = pd.read_csv(path, parse_dates=["date"],
        dtype={
            "country_code": str, "country": str,"entity_type": str, "substance": str, "unit": str},
            keep_default_na=False, na_values=[""])

    return frame.sort_values(["country_code", "date"]).reset_index(drop=True)


def country_data_path() -> Path:
    """Return the appropriate country dataset path."""
    sample_mode = (os.getenv("DASHBOARD_SAMPLE_MODE", "0") == "1")

    if sample_mode or not PROCESSED.exists():
        return SAMPLE

    return PROCESSED


st.title("Global CO2 Emissions Trends and Drivers")
st.write("**Question:** Which countries contributed most to changes in fossil CO2 emissions over the selected period?")
country_data = load_country_data(str(country_data_path()))

with st.container(key="country_drivers"):
    render_country_drivers_view(country_data)