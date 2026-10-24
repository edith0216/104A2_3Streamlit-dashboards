from __future__ import annotations

import pandas as pd
import streamlit as st


COUNTRY_LABELS = {
    "Republic of Korea": "South Korea",
    "United Kingdom of Great Britain and Northern Ireland": "U.K.",
    "United States of America": "U.S.A."}


def country_label(country: str) -> str:
    """Return a shorter display label where useful."""
    return COUNTRY_LABELS.get(country, country)


def render_country_comparison(data: pd.DataFrame) -> None:
    st.header("Country Comparison")
    st.caption("Unit: reported deaths")
    st.caption(f"Latest observation: {data['date'].max().date().isoformat()}")

    available = sorted(data["country"].unique())

    default_countries = [
        "Australia",
        "United Kingdom of Great Britain and Northern Ireland",
        "United States of America"]

    countries = st.multiselect(
        "Countries", available, default=default_countries,
        key="comparison_country_filter", format_func=country_label)

    st.write(f"Selected: {', '.join(countries) if countries else 'none'}")

    filtered = data.loc[data["country"].isin(countries)].copy()

    if filtered.empty:
        st.info("No observations match the selected filters.")
    else:
        total_deaths = (filtered.groupby("country", as_index=False)["weekly_deaths"].sum(min_count=1))
        st.metric("Countries selected", filtered["country"].nunique())
       
        trend = filtered.sort_values(["country", "date"]).copy()
    
        trend["rolling_4_week"] = (
            trend.groupby("country")["weekly_deaths"].transform(
                lambda values: values.rolling(window=4, min_periods=4).mean()))

        trend["display_country"] = trend["country"].map(country_label)

        chart_data = trend.pivot(index="date", columns="display_country", values="rolling_4_week")

        st.subheader("Reported deaths over time")
        st.caption("Four-week rolling average of weekly reported deaths.")
        st.line_chart(chart_data, y_label="Reported deaths", x_label="Date")

        st.subheader("Total reported deaths")
        st.caption("Sum of weekly reported deaths in the available observations.")

        total_deaths["display_country"] = (total_deaths["country"].map(country_label))

        bar_data = total_deaths.set_index("display_country")["weekly_deaths"]

        st.bar_chart(bar_data, y_label="Reported deaths", x_label="Country")

    st.caption("Source: WHO COVID-19 global data, World Health Organization.")

    st.download_button(
        "Download filtered data", data=filtered.to_csv(index=False).encode("utf-8"),
        file_name="filtered_country_comparison.csv",
        mime="text/csv", key="country_comparison_download")


def render_pandemic_waves(data: pd.DataFrame) -> None:
    st.header("Pandemic Waves")
    st.caption("Unit: reported deaths")
    st.caption(f"Latest observation: {data['date'].max().date().isoformat()}")

    available = sorted(data["country"].unique())

    countries = st.multiselect(
        "Country", available, default=["Australia"],
        key="waves_country_filter", format_func=country_label)

    st.write(f"Selected: {', '.join(countries) if countries else 'none'}")

    filtered = data.loc[data["country"].isin(countries)].copy()

    if filtered.empty:
        st.info("No observations match the selected filters.")
    else:
        plot_data = filtered.sort_values(["country", "date"]).copy()

        valid_deaths = plot_data.dropna(subset=["weekly_deaths"])

        if valid_deaths.empty:
            peak_deaths = None
            peak_week = "Not available"
        else:
            peak_record = valid_deaths.loc[
                valid_deaths["weekly_deaths"].idxmax()]
            peak_deaths = peak_record["weekly_deaths"]
            peak_week = peak_record["date"].date().isoformat()

        total_deaths = plot_data["weekly_deaths"].sum(min_count=1)

        metric_1, metric_2, metric_3 = st.columns(3)
        metric_1.metric("Peak weekly deaths", f"{peak_deaths:,.0f}" if peak_deaths is not None else "Not available")
        metric_2.metric("Peak week", peak_week)
        metric_3.metric("Total reported deaths", f"{total_deaths:,.0f}" if pd.notna(total_deaths) else "Not available")

        plot_data["rolling_4_week"] = (
            plot_data.groupby("country")["weekly_deaths"]
            .transform(lambda values: values.rolling(window=4, min_periods=4).mean()))

        plot_data["display_country"] = plot_data["country"].map(country_label)

        weekly_chart = plot_data.pivot(index="date", columns="display_country", values="weekly_deaths")

        rolling_chart = plot_data.pivot(index="date", columns="display_country", values="rolling_4_week")

        st.subheader("Weekly reported deaths")
        st.line_chart( weekly_chart, y_label="Reported deaths", x_label="Date")

        st.subheader("Four-week rolling average")
        st.line_chart(rolling_chart, y_label="Reported deaths", x_label="Date")

    st.caption("Source: WHO COVID-19 global data, World Health Organization.")
    st.caption("Weekly reported deaths may be missing or revised retrospectively.")

    st.download_button(
        "Download filtered data", data=filtered.to_csv(index=False).encode("utf-8"),
        file_name="filtered_pandemic_waves.csv", mime="text/csv", key="pandemic_waves_download")