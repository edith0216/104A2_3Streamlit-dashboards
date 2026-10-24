# COVID-19 Mortality Across Selected Countries

This Streamlit dashboard explores the question:

**How did reported COVID-19 mortality evolve across selected countries and pandemic waves?**

The dashboard is designed for interested non-specialists and uses weekly reported COVID-19 mortality data from the World Health Organization (WHO).

## Dashboard views

The dashboard contains two views:

1. **Country Comparison**  
   Compares reported COVID-19 deaths across selected countries over time.

2. **Pandemic Waves**  
   Shows weekly reported deaths and four-week rolling averages for selected countries.

## Data source

**WHO COVID-19 global data**

Publisher: World Health Organization (WHO).

The dashboard uses weekly reported COVID-19 deaths. Missing weekly observations are retained as missing values, and reported values may be revised retrospectively.

## Run in sample mode

```bash
export DASHBOARD_SAMPLE_MODE=1
streamlit run app.py