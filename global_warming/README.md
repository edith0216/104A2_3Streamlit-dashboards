# Global CO2 Emissions Trends and Drivers

This Streamlit dashboard explores the question:
**Are global CO2 emissions still accelerating, and which countries and sectors drive the trend?**

The dashboard is designed for interested non-specialists and uses annual fossil CO2 emissions data from the IEA-EDGAR dataset.

## Dashboard pages

The dashboard contains three views:

1. **Global CO2 Emissions Trend**  
   Shows annual global CO2 emissions, annual emissions change, and annual acceleration.

2. **Country Drivers**  
   Shows which countries recorded the largest increases and decreases in CO2 emissions over a selected period.

3. **Sector Drivers**  
   Shows which sectors recorded the largest increases and decreases in CO2 emissions over a selected period.

## Data source

**IEA-EDGAR Fossil CO2 Emissions — EDGAR_2026_GHG**

Publisher: European Commission Joint Research Centre (JRC) and International Energy Agency (IEA).

The dashboard uses annual fossil CO2 emissions from 1970 to 2025. International aviation and shipping are included in global totals.

## Datasets

The dashboard uses two processed datasets:

- `data/processed.csv` — annual CO2 emissions by country/entity.
- `data/processed_sector.csv` — annual global CO2 emissions by sector.

The corresponding offline sample files are:

- `data/sample.csv`
- `data/sample_sector.csv`

## Run the dashboard

```bash
streamlit run app.py