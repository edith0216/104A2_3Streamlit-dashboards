from __future__ import annotations

import pandas as pd
import streamlit as st


# Latest year with complete country coverage in the EIA dataset.
LATEST_COMPARISON_YEAR = 2018


def render_major_traders(data: pd.DataFrame) -> None:
    """Render the major crude oil importers and exporters view."""
    st.header("Major Importers & Exporters")
    st.caption("Unit: Mb/d")

    # Show the latest observation date in the full dataset
    latest_observation = pd.to_datetime(data["date"]).max().strftime("%Y-%m-%d")
    st.caption(f"Latest observation: {latest_observation}")

    # Use 2018 as the latest comparison year because country coverage falls substantially in 2019 and 2020.
    comparison_data = data.loc[data["year"] <= LATEST_COMPARISON_YEAR].copy()
    available_years = sorted(comparison_data["year"].dropna().astype(int).unique())
    st.caption(f"Latest complete comparison year: {LATEST_COMPARISON_YEAR}")

    # Controls
    year = st.selectbox("Year", available_years, index=len(available_years) - 1, key="trade_year_filter")
    trade_flow = st.radio("Trade flow", ["Imports", "Exports"], horizontal=True, key="trade_flow_filter")
    st.write(f"Selected: {year}, {trade_flow}")

    # Filter
    filtered = comparison_data.loc[comparison_data["year"] == year].copy()

    value_column = (
        "crude_imports"
        if trade_flow == "Imports"
        else "crude_exports")

    # Remove observations where the selected trade flow is unavailable.
    chart_data = filtered.dropna(subset=[value_column]).copy()

    # Exclude the World aggregate, this view compares individual countries/entities.
    chart_data = chart_data.loc[chart_data["country"] != "World"].copy()

    # Empty state
    if chart_data.empty:
        st.info("No observations match the selected filters.")

    else:     # Metric
        st.metric("Countries with reported data", f"{chart_data['country'].nunique():,}")

        # Ranking
        top_traders = (chart_data[["country", value_column]].sort_values(value_column, ascending=False).head(10))
        top_traders = top_traders.sort_values(value_column,ascending=True)
        chart_title = (f"Top 10 Crude Oil {trade_flow} — {year}")
        st.subheader(chart_title)
        st.bar_chart(top_traders.set_index("country")[value_column], x_label="Country", y_label="Mb/d", horizontal=True)
        
    # Source
    st.caption("Source: EIA International Energy Statistics, U.S. Energy Information Administration.")

    # Download
    st.download_button(
        "Download filtered data", data=filtered.to_csv(index=False).encode("utf-8"),
        file_name="filtered_crude_oil_trade.csv", mime="text/csv", key="major_traders_download")


def render_country_trade_trends(data: pd.DataFrame) -> None:
    """Render crude oil trade trends for selected countries."""
    st.header("Country Trade Trends")
    st.caption("Unit: Mb/d")
    latest_observation = pd.to_datetime(data["date"]).max().strftime("%Y-%m-%d")
    st.caption(f"Latest observation: {latest_observation} (coverage varies by country)")
    
    # Controls
    available_countries = sorted(data.loc[data["country"] != "World", "country"].dropna().unique())

    default_countries = [
        country
        for country in ["United States", "China", "Saudi Arabia"]
        if country in available_countries]

    selected_countries = st.multiselect("Countries", available_countries, default=default_countries, key="trade_trend_country_filter")
    measure = st.radio("Measure", ["Imports", "Exports", "Net exports"], horizontal=True, key="trade_trend_measure_filter")
    measure_titles = {"Imports": "Imports", "Exports": "Exports", "Net exports": "Net Exports"}
    st.write("Selected: " + (", ".join(selected_countries)
                             if selected_countries
                             else "None") + f" | {measure}")

    # Filter
    filtered = data.loc[data["country"].isin(selected_countries)].copy()

    measure_columns = {
        "Imports": "crude_imports",
        "Exports": "crude_exports",
        "Net exports": "net_exports"}

    value_column = measure_columns[measure]

    if filtered.empty:     # Empty state
        st.info("No observations match the selected filters.")
    else:    # Keep the downloadable filtered dataset unchanged.
        plot_data = filtered.dropna(subset=[value_column]).copy()

        if plot_data.empty:
            st.info("No reported values are available for the selected measure.")
        else:    # Metric
            st.metric("Countries selected", len(selected_countries))
            # Trend chart
            st.subheader(f"Crude Oil {measure_titles[measure]} Over Time")
            chart_data = (plot_data[["year", "country", value_column]].pivot(index="year", columns="country", values=value_column).sort_index())
            st.line_chart(chart_data, x_label="Year", y_label="Mb/d")

            # Explain the interpretation of net exports.
            if measure == "Net exports":
                st.caption("Positive values indicate net exports; negative values indicate net imports.")

    st.caption("Source: EIA International Energy Statistics, U.S. Energy Information Administration.")

    st.download_button(
        "Download filtered data", data=filtered.to_csv(index=False).encode("utf-8"),
        file_name="filtered_country_trade_trends.csv", 
        mime="text/csv", key="trade_trends_download")