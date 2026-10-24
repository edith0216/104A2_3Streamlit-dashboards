from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import streamlit as st

from src.views import (render_country_trade_trends, render_major_traders)


ROOT = Path(__file__).resolve().parent

SAMPLE = ROOT / "data" / "sample.csv"
PROCESSED = ROOT / "data" / "processed.csv"


@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    """Load and sort the processed crude oil trade dataset."""
    frame = pd.read_csv(path, parse_dates=["date"])

    return frame.sort_values(["country", "date"]).reset_index(drop=True)


def data_path() -> Path:
    """Choose the bundled sample or full processed dataset."""
    sample_mode = (os.getenv("DASHBOARD_SAMPLE_MODE", "0") == "1")

    if sample_mode or not PROCESSED.exists():
        return SAMPLE

    return PROCESSED


# Page
st.set_page_config(page_title="Global Crude Oil Trade", layout="wide")
st.title("Global Crude Oil Trade")
st.write("**Question:** How have the roles of major crude oil importing and exporting countries changed over time?")
st.caption("Audience: Interested non-specialists.")

# Load data
data = load_data(str(data_path()))

# View 1 — Major Importers & Exporters
with st.container(key="major_traders"):
    render_major_traders(data)

# View 2 — Country Trade Trends
with st.container(key="country_trade_trends"):
    render_country_trade_trends(data)

# Data and limitations
with st.expander("Data and limitations"):
    st.markdown("**Source:** EIA International Energy Statistics, U.S. Energy Information Administration.")
    st.markdown("The dashboard uses annual crude oil including lease condensate imports and exports reported by the EIA.")
    st.markdown("Net exports are calculated as exports minus imports.")
    st.markdown("Missing observations are retained as missing values")
    st.markdown("[EIA International Energy Statistics] (https://www.eia.gov/international/data/world)")