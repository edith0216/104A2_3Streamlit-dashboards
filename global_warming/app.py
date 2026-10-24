
from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import streamlit as st

from src.views import render_global_trend_view

ROOT = Path(__file__).resolve().parent
SAMPLE_SECTOR = ROOT / "data" / "sample_sector.csv"
PROCESSED_SECTOR = ROOT / "data" / "processed_sector.csv"

@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    frame = pd.read_csv(
        path, parse_dates=["date"],
        dtype={"sector_code": str, "sector": str, "substance": str, "unit": str},
        keep_default_na=False, na_values=[""])

    return frame.sort_values(["sector_code", "date"]).reset_index(drop=True)


def sector_data_path() -> Path:
    sample_mode = os.getenv("DASHBOARD_SAMPLE_MODE", "0") == "1"
    if sample_mode or not PROCESSED_SECTOR.exists():
        return SAMPLE_SECTOR
    return PROCESSED_SECTOR


st.set_page_config(page_title="Global CO2 Emissions", layout="wide")
st.title("Global CO2 Emissions Trends and Drivers")
st.write("**Question:** Are global CO2 emissions still accelerating, and which countries and sectors drive the trend?")
st.caption("Audience: interested non-specialists exploring global CO2 emissions.")
sector_data = load_data(str(sector_data_path()))

with st.container(key="global_trend"):
    render_global_trend_view(sector_data)

with st.expander("Data and limitations"):
    st.markdown(
        """
        **Source:** IEA-EDGAR Fossil CO2 Emissions, European Commission
        Joint Research Centre (JRC) and International Energy Agency (IEA).

        **Coverage:** Annual fossil CO2 emissions from 1970 to 2025.
        International aviation and shipping are included in global totals.

        **Measures:** Emissions are reported in Gg CO2. Annual change is the
        difference in global emissions from the previous year. Annual
        acceleration is the year-to-year change in annual emissions change.

        **Limitations:** The dashboard uses historical annual emissions data.
        Annual changes can reflect short-term events as well as longer-term trends.
        """)

    st.markdown(
        "[EDGAR dataset page]"
        "(https://edgar.jrc.ec.europa.eu/dataset_ghg2026)")
