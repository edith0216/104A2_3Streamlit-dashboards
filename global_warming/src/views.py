from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st


def render_global_trend_view(data: pd.DataFrame) -> None:
    """Render the global CO2 emissions trend view."""
    # View title and metadata
    st.header("Global CO2 Emissions Trend")
    st.caption("Unit: Gg CO2")
    st.caption(f"Latest observation: " f"{data['date'].max().date().isoformat()}")

    # Interactive year-range control
    min_year = int(data["year"].min())
    max_year = int(data["year"].max())

    year_range = st.slider(
        "Year range", min_value=min_year, max_value=max_year, 
        value=(min_year, max_year), key="global_year_range",)
    
    start_year, end_year = year_range
    st.write(f"Selected years: {start_year}-{end_year}")

    sector_options = sorted(data["sector"].dropna().unique().tolist())

    default_sectors = sector_options
    
    selected_sectors = st.multiselect(
        "Sectors", options=sector_options, default=default_sectors, key="global_sector_filter",)

    st.write(f"Selected sectors: {', '.join(selected_sectors)}")

    # Record-level filtered data, used for the filtered download.
    filtered = data.loc[data["year"].between(start_year, end_year) & data["sector"].isin(selected_sectors)].copy()

    if filtered.empty:
        st.info("No observations match the selected filters.")
    else:
        # Calculate global annual emissions
        # Use the full dataset first so annual change and acceleration can use observations before the selected start year.
        selected_data = data.loc[data["sector"].isin(selected_sectors)].copy()

        global_annual = (selected_data.groupby(["date", "year"], as_index=False)["emissions_gg"]
                         .sum().sort_values("year"))

        # Calculate annual change
        global_annual["annual_change_gg"] = (global_annual["emissions_gg"].diff())

        # Calculate annual acceleration
        # Acceleration is the change in annual emissions change.
        global_annual["acceleration_gg"] = (global_annual["annual_change_gg"].diff())

        # Apply the selected year range only after calculating the annual change and acceleration.
        global_filtered = global_annual.loc[global_annual["year"].between(start_year, end_year)].copy()
        latest = global_filtered.iloc[-1]

        # Key metrics
        metric_col1, metric_col2, metric_col3 = st.columns(3)

        with metric_col1:
            st.metric("Global CO2 emissions", (f"{latest['emissions_gg']:,.0f} " "Gg CO2"))

        with metric_col2:
            if pd.notna(latest["annual_change_gg"]):
                st.metric("Annual change", (f"{latest['annual_change_gg']:,.0f} " "Gg CO2"))
            else:
                st.metric("Annual change", "Not available")

        with metric_col3:
            if pd.notna(latest["acceleration_gg"]):
                st.metric("Annual acceleration", (f"{latest['acceleration_gg']:,.0f} " "Gg CO2"))
            else:
                st.metric("Annual acceleration", "Not available")
        
        # Latest-year interpretation
        if (pd.notna(latest["annual_change_gg"]) and pd.notna(latest["acceleration_gg"])):
            if (latest["annual_change_gg"] > 0 and latest["acceleration_gg"] > 0):
                interpretation = (
                    f"In {int(latest['year'])}, global CO2 emissions increased, and the annual increase was larger than in the previous year.")

            elif (latest["annual_change_gg"] > 0 and latest["acceleration_gg"] < 0):
                interpretation = (
                    f"In {int(latest['year'])}, global CO2 emissions "
                    "still increased, but the annual increase was smaller than in the previous year.")

            elif (latest["annual_change_gg"] < 0 and latest["acceleration_gg"] < 0):
                interpretation = (
                    f"In {int(latest['year'])}, global CO2 emissions "
                    "decreased, with a larger downward change than in the previous year.")

            else:
                interpretation = (
                    f"In {int(latest['year'])}, global CO2 emissions "
                    "decreased, but the annual change moved upward relative to the previous year.")

            st.info(interpretation)

        # Explain acceleration
        st.caption("Annual acceleration is calculated as the change in annual emissions change.")
        st.caption("A positive value means the annual change increased compared with the previous year.")
        st.caption("A negative value means it decreased.")

        # Global emissions trend
        st.subheader("Global Annual CO2 Emissions")

        emissions_chart = (alt.Chart(global_filtered).mark_line(point=True).encode(
            x=alt.X("year:O", title="Year"),
            y=alt.Y("emissions_gg:Q", title="CO2 emissions (Gg)"),
            tooltip=[alt.Tooltip("year:O", title="Year"),
                     alt.Tooltip("emissions_gg:Q", title="Emissions (Gg CO2)",format=",.0f")])
                     .properties(height=350))

        st.altair_chart(emissions_chart, width="stretch")

        # Annual emissions change
        st.subheader("Annual Change in Global CO2 Emissions")

        annual_change_data = global_filtered.dropna(subset=["annual_change_gg"])

        annual_change_chart = (alt.Chart(annual_change_data).mark_bar().encode(
            x=alt.X("year:O", title="Year"),
            y=alt.Y("annual_change_gg:Q", title="Annual change (Gg CO2)"),
            tooltip=[alt.Tooltip("year:O", title="Year"),
                     alt.Tooltip("annual_change_gg:Q",title="Annual change (Gg CO2)",format=",.0f")])
                     .properties(height=300))

        st.altair_chart(annual_change_chart, width="stretch")

        # Annual acceleration
        st.subheader("Annual Acceleration in Global CO2 Emissions")
        acceleration_data = global_filtered.dropna(subset=["acceleration_gg"])
        
        acceleration_chart = (alt.Chart(acceleration_data).mark_bar().encode(
            x=alt.X("year:O", title="Year"),
            y=alt.Y("acceleration_gg:Q",title="Change in annual change (Gg CO2)"),
            tooltip=[alt.Tooltip("year:O",title="Year"),
                     alt.Tooltip("acceleration_gg:Q",title="Annual acceleration (Gg CO2)",format=",.0f")])
                     .properties(height=300))

        st.altair_chart(acceleration_chart, width="stretch")

    # Source attribution
    st.caption(
    "Source: EDGAR - Emissions Database for Global Atmospheric Research — "
    "European Commission Joint Research Centre (JRC) and "
    "International Energy Agency (IEA)")

    # Download must remain available even in the empty state
    st.download_button(
        "Download filtered data", data=filtered.to_csv(index=False).encode("utf-8"),
        file_name="filtered_global_co2.csv", mime="text/csv", key="global_trend_download")

def render_country_drivers_view(data: pd.DataFrame) -> None:
    """Render country drivers of CO2 emissions change."""
    # View title and metadata
    st.header("Country Drivers of CO2 Emissions Change")
    st.caption("Unit: Gg CO2")
    st.caption(f"Latest observation: " f"{data['date'].max().date().isoformat()}")

    # Interactive year-range control
    min_year = int(data["year"].min())
    max_year = int(data["year"].max())

    year_range = st.slider("Year range", min_value=min_year, max_value=max_year, value=(min_year, max_year), key="country_year_range")
    start_year, end_year = year_range
    st.write(f"Selected years: {start_year}-{end_year}")

    entity_options = ["country", "international"]
    selected_entity_types = st.multiselect(
        "Entity type", options=entity_options, default=["country"], key="country_entity_filter",)

    st.write(f"Selected entity types: {', '.join(selected_entity_types)}")

    # Record-level filtered data, used for the download
    filtered = data.loc[data["year"].between(start_year, end_year) & data["entity_type"].isin(selected_entity_types)].copy()
    country_data = data.loc[data["entity_type"].isin(selected_entity_types)].copy()
    
    # Empty state
    if filtered.empty:
        st.info("No observations match the selected filters.")
    elif start_year == end_year:
        st.info("Select two different years to calculate changes in CO2 emissions.")
    else:
        # Extract start-year emissions
        start_data = (country_data.loc[
            country_data["year"] == start_year,
            ["country_code", "country", "emissions_gg"]].rename(columns={"emissions_gg": "start_emissions_gg"}))

        # Extract end-year emissions
        end_data = (country_data.loc[
            country_data["year"] == end_year,
            ["country_code", "country", "emissions_gg",]].rename(columns={"emissions_gg": "end_emissions_gg"}))

        # Match countries across the two selected years
        country_change = start_data.merge(end_data, on=["country_code", "country"], how="inner")

        # Calculate emissions change
        # Change = emissions in end year - emissions in start year
        country_change["change_gg"] = (country_change["end_emissions_gg"] - country_change["start_emissions_gg"])

        # Remove countries where change cannot be calculated
        country_change = country_change.dropna(subset=["change_gg"])

        # Create shorter names for chart display only
        # Original EDGAR country names remain unchanged in the
        # underlying data and download.
        country_name_map = {"Iran, Islamic Republic of": "Iran", "Korea, Republic of": "Korea", "Russian Federation": "Russia"}
        country_change["display_country"] = (country_change["country"].replace(country_name_map))

        # Handle unavailable changes
        if country_change.empty:
            st.info("No country changes can be calculated for the selected years.")
        else:
            # Sort from largest increase to largest decrease
            country_change = country_change.sort_values("change_gg", ascending=False)

            # Explain the measure
            st.caption("Change is calculated as end-year emissions minus start-year emissions.")

            # Separate increases and decreases
            increases = country_change.loc[country_change["change_gg"] > 0].copy()
            decreases = country_change.loc[country_change["change_gg"] < 0].copy()

            # Largest increase metric
            if increases.empty:
                st.info("No countries recorded an increase over the selected period.")
            else:
                largest_increase = increases.iloc[0]
                st.metric(("Largest increase — " f"{largest_increase['display_country']}"),
                          (f"{largest_increase['change_gg']:,.0f} " "Gg CO2"))

            # Largest increases chart
            st.subheader("Largest Increases in CO2 Emissions")

            top_increases = increases.nlargest(10, "change_gg")

            increase_chart = (alt.Chart(top_increases).mark_bar().encode(
                x=alt.X("change_gg:Q",title="Change in CO2 emissions (Gg)"),
                y=alt.Y("display_country:N",title=None,sort="-x",axis=alt.Axis(labelLimit=220)),
                tooltip=[alt.Tooltip("country:N",title="Country"),
                         alt.Tooltip("change_gg:Q",title="Change (Gg CO2)",format=",.0f")])
                         .properties(height=max(250,len(top_increases) * 35)))
            
            st.altair_chart(increase_chart, width="stretch")

            # Largest decreases chart
            st.subheader("Largest Decreases in CO2 Emissions")
            if decreases.empty:
                st.info("No countries recorded a decrease over the selected period.")
            else:
                top_decreases = decreases.nsmallest(10, "change_gg")
                
                decrease_chart = (
                    alt.Chart(top_decreases).mark_bar().encode(
                        x=alt.X("change_gg:Q", title="Change in CO2 emissions (Gg)"),
                        y=alt.Y("display_country:N", title=None, sort="x", axis=alt.Axis(labelLimit=220)),
                        tooltip=[
                            alt.Tooltip("country:N", title="Country"),
                            alt.Tooltip("change_gg:Q", title="Change (Gg CO2)", format=",.0f")])
                            .properties(height=max(250, len(top_decreases) * 35)))

                st.altair_chart(decrease_chart, width="stretch")

    # Source attribution
    st.caption(
        "Source: EDGAR - Emissions Database for Global Atmospheric Research — "
        "European Commission Joint Research Centre (JRC) and International Energy Agency (IEA)")
    
    # Download filtered record-level data
    st.download_button(
        "Download filtered data", data=filtered.to_csv(index=False).encode("utf-8"), 
        file_name="filtered_country_co2.csv", mime="text/csv", key="country_drivers_download")


def render_sector_drivers_view(data: pd.DataFrame) -> None:
    """Render sector drivers of global CO2 emissions change."""
    # View title and metadata
    st.header("Sector Drivers of CO2 Emissions Change")
    st.caption("Unit: Gg CO2")
    st.caption(f"Latest observation: " f"{data['date'].max().date().isoformat()}")

    # Interactive year-range control
    min_year = int(data["year"].min())
    max_year = int(data["year"].max())

    year_range = st.slider(
        "Year range",min_value=min_year,
        max_value=max_year, value=(min_year, max_year), key="sector_year_range")

    start_year, end_year = year_range
    st.write(f"Selected years: {start_year}-{end_year}")

    sector_options = sorted(data["sector"].dropna().unique().tolist())

    default_sectors = [
        "Main Activity Electricity and Heat Production",
        "Manufacturing Industries and Construction"]

    selected_sectors = st.multiselect(
        "Sectors", options=sector_options, default=default_sectors, key="sector_filter")

    st.write(f"Selected sectors: {', '.join(selected_sectors)}")

    # Record-level filtered data, used for the filtered download.
    selected_data = data.loc[data["sector"].isin(selected_sectors)].copy()
    filtered = data.loc[data["year"].between(start_year, end_year) & data["sector"].isin(selected_sectors)].copy()

    # Empty state
    if filtered.empty:
        st.info("No observations match the selected filters.")
    elif start_year == end_year:
        st.info("Select two different years to calculate changes in CO2 emissions.")
    else:
        # Extract start-year emissions
        start_data = (selected_data.loc[
            selected_data["year"] == start_year,["sector_code", "sector","emissions_gg"]]
            .rename(columns={"emissions_gg": "start_emissions_gg"}))

        # Extract end-year emissions
        end_data = (selected_data.loc[
            selected_data["year"] == end_year,["sector_code", "sector", "emissions_gg"]]
            .rename(columns={"emissions_gg": "end_emissions_gg"}))

        # Match sectors across selected years
        sector_change = start_data.merge(end_data, on=["sector_code", "sector"],how="inner")

        # Calculate emissions change
        sector_change["change_gg"] = (sector_change["end_emissions_gg"] - sector_change["start_emissions_gg"])
        sector_change = sector_change.dropna(subset=["change_gg"])

        # Shorter sector names for chart display only
        sector_name_map = {
            "Main Activity Electricity and Heat Production":
                "Electricity and Heat Production",

            "Manufacturing Industries and Construction":
                "Manufacturing and Construction",

            "Petroleum Refining - Manufacture of Solid Fuels and Other Energy Industries":
                "Petroleum Refining and Other Energy",

            "Non-Energy Products from Fuels and Solvent Use":
                "Non-Energy Fuel Products and Solvents",

            "Incineration and Open Burning of Waste":
                "Waste Incineration and Open Burning",

            "Other Process Uses of Carbonates":
                "Other Carbonate Uses",

            "Residential and other sectors":
                "Residential and Other Sectors"}

        sector_change["display_sector"] = (sector_change["sector"].replace(sector_name_map))
        
        # Check whether changes can be calculated
        if sector_change.empty:
            st.info("No sector changes can be calculated for the selected years.")
        else:
            sector_change = sector_change.sort_values("change_gg", ascending=False,)

            # Explain the measure used in this view
            st.caption("Change is calculated as end-year emissions minus start-year emissions.")

            # Largest increase metric
            increases = sector_change.loc[sector_change["change_gg"] > 0].copy()

            if increases.empty:
                st.info("No sectors recorded an increase over the selected period.")
            else:
                largest_increase = increases.iloc[0]
                st.metric(("Largest increase — " f"{largest_increase['display_sector']}"),
                          (f"{largest_increase['change_gg']:,.0f} " "Gg CO2"))

                # Top sector increases
                st.subheader("Largest Increases in CO2 Emissions")
                top_increases = increases.nlargest(10, "change_gg")
                increase_chart = (alt.Chart(top_increases).mark_bar().encode(
                    x=alt.X("change_gg:Q",title="Change in CO2 emissions (Gg)"),
                    y=alt.Y("display_sector:N",title=None,sort="-x",axis=alt.Axis(labelLimit=280)),
                    tooltip=[
                        alt.Tooltip("sector:N", title="Sector"),
                        alt.Tooltip("sector_code:N", title="Sector code"),
                        alt.Tooltip("change_gg:Q", title="Change (Gg CO2)", format=",.0f")])
                        .properties(height=max(250,len(top_increases) * 35)))

                st.altair_chart(increase_chart, width="stretch")

            # Top sector decreases
            decreases = sector_change.loc[sector_change["change_gg"] < 0].copy()
            st.subheader("Largest Decreases in CO2 Emissions")

            if decreases.empty:
                st.info("No sectors recorded a decrease over the selected period.")
            else:
                top_decreases = decreases.nsmallest(10, "change_gg")
                decrease_chart = (alt.Chart(top_decreases).mark_bar().encode(
                    x=alt.X("change_gg:Q", title="Change in CO2 emissions (Gg)"),
                    y=alt.Y("display_sector:N", title=None, sort="x", axis=alt.Axis(labelLimit=280)),
                    tooltip=[
                        alt.Tooltip("sector:N", title="Sector"),
                        alt.Tooltip("sector_code:N", title="Sector code"),
                        alt.Tooltip("change_gg:Q", title="Change (Gg CO2)", format=",.0f")])
                        .properties(height=max(180,len(top_decreases) * 45)))
                
                st.altair_chart(decrease_chart, width="stretch")

    # Source attribution
    st.caption(
        "Source: EDGAR - Emissions Database for Global Atmospheric Research — "
        "European Commission Joint Research Centre (JRC) and International Energy Agency (IEA)")

    # Download filtered record-level data
    st.download_button(
        "Download filtered data",data=filtered.to_csv(
            index=False).encode("utf-8"),
            file_name="filtered_sector_co2.csv",
            mime="text/csv", key="sector_drivers_download")