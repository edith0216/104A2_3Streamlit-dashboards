# Global Crude Oil Trade

This Streamlit dashboard explores the question:

**How have the roles of major crude oil importing and exporting countries changed over time？**

The dashboard is designed for interested non-specialists and uses annual crude oil import and export data from the U.S. Energy Information Administration (EIA).

## Dashboard views

The dashboard contains two views:

1. **Major Importers & Exporters**  
   Compares the major crude oil importing and exporting countries in a selected year.

2. **Country Trade Trends**  
   Shows how crude oil imports, exports and net exports changed over time for selected countries.

## Data source

**EIA International Energy Statistics**

Publisher: U.S. Energy Information Administration (EIA).

The dashboard uses annual crude oil including lease condensate imports and exports from 1980 to 2020. Country coverage falls substantially after 2018, so 2018 is used as the latest complete year for cross-country comparisons.

Net exports are calculated as exports minus imports. Missing observations are retained as missing values.

## Run in sample mode

```bash
export DASHBOARD_SAMPLE_MODE=1
streamlit run app.py