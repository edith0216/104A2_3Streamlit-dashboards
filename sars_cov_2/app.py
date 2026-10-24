from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import streamlit as st

from src.views import render_country_comparison, render_pandemic_waves


ROOT = Path(__file__).resolve().parent
SAMPLE = ROOT / "data" / "sample.csv"
PROCESSED = ROOT / "data" / "processed.csv"


@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    frame = pd.read_csv(path, parse_dates=["date"])
    return frame.sort_values(["country", "date"]).reset_index(drop=True)


def data_path() -> Path:
    sample_mode = os.getenv("DASHBOARD_SAMPLE_MODE", "0") == "1"
    if sample_mode or not PROCESSED.exists():
        return SAMPLE
    return PROCESSED


st.set_page_config(page_title="COVID-19 Mortality", layout="wide")
st.title("COVID-19 Mortality Across Selected Countries")
st.write("**Question:** How did reported COVID-19 mortality evolve across selected countries and pandemic waves?")
st.caption("Audience: interested non-specialists")

data = load_data(str(data_path()))

with st.container(key="country_comparison"):
    render_country_comparison(data)


with st.container(key="pandemic_waves"):
    render_pandemic_waves(data)


with st.expander("Data and limitations"):
    st.markdown("**Source:** WHO COVID-19 global data, published by the World Health Organization.")

    st.markdown(
        "The dashboard uses weekly reported COVID-19 deaths. \n"
        "Missing weekly observations are retained as missing values. \n"
        "Reported values may also be revised retrospectively.")

    st.markdown(
        "Comparisons between countries use reported death numbers. "
        "Therefore, when interpreting these comparisons, differences in population size and reporting practices should be considered.")

    st.markdown(
        "[WHO COVID-19 data]"
        "(https://data.who.int/dashboards/covid19/data?n=o)")