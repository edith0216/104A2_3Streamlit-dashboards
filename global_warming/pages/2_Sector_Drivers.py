from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import streamlit as st
from src.views import render_sector_drivers_view

ROOT = Path(__file__).resolve().parents[1]

SAMPLE_SECTOR = ROOT / "data" / "sample_sector.csv"
PROCESSED_SECTOR = ROOT / "data" / "processed_sector.csv"


@st.cache_data
def load_sector_data(path: str) -> pd.DataFrame:
    """Load the global sector CO2 emissions dataset."""
    frame = pd.read_csv(path, parse_dates=["date"],
        dtype={
            "sector_code": str, "sector": str, "substance": str, "unit": str},
            keep_default_na=False, na_values=[""])

    return frame.sort_values(["sector_code", "date"]).reset_index(drop=True)


def sector_data_path() -> Path:
    """Return the appropriate sector dataset path."""
    sample_mode = (os.getenv("DASHBOARD_SAMPLE_MODE", "0") == "1" )

    if sample_mode or not PROCESSED_SECTOR.exists():
        return SAMPLE_SECTOR

    return PROCESSED_SECTOR


st.title("Global CO2 Emissions Trends and Drivers")

st.write("**Question:** Which sectors contributed most to changes in global fossil CO2 emissions over the selected period?")

sector_data = load_sector_data(str(sector_data_path()))

with st.container(key="sector_drivers"):
    render_sector_drivers_view(sector_data)