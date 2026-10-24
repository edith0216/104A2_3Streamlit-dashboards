"""Acquire, transform and validate the SARS-CoV-2 dashboard dataset.
Data source: WHO COVID-19 global weekly data.
Pipeline:
1. acquire(): download the raw WHO CSV
2. transform(): select and rename mortality-related variables
3. validate(): check the processed dataset
4. make_sample(): create a faithful offline sample for the dashboard
5. main(): run the complete pipeline
Presentation and visualisation logic belongs in views.py.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

import pandas as pd

# Dashboard root folder: sars_cov_2/
ROOT = Path(__file__).resolve().parents[1]

SAMPLE = ROOT / "data" / "sample.csv"
RAW = ROOT / "data" / "WHO-COVID-19-global-data.csv"
PROCESSED = ROOT / "data" / "processed.csv"

URL = ("https://srhdpeuwpubsa.blob.core.windows.net/whdh/COVID/WHO-COVID-19-global-data.csv")


# These columns must exist after transformation.
REQUIRED = {"date", "year", "country_code", "country", "who_region", "weekly_deaths", "cumulative_deaths", "unit"}

# Countries retained in the bundled sample
SAMPLE_COUNTRIES = [
    "Australia", "Brazil", "China", "Japan","France", "India", "Germany", "Republic of Korea",
    "United Kingdom of Great Britain and Northern Ireland", "United States of America"]


def acquire() -> None:
    """Download the raw WHO COVID-19 dataset."""
    RAW.parent.mkdir(parents=True, exist_ok=True)

    try:   
        with urlopen(URL, timeout=60) as response:
            RAW.write_bytes(response.read())

    except (URLError, TimeoutError, OSError) as error:
        sys.exit(
            f"Could not fetch {URL}: {error}. "
            "Check your connection, or rerun with DASHBOARD_SAMPLE_MODE=1 to use the bundled sample.")
    print(f"Wrote {RAW}")


def transform(payload_path: Path) -> pd.DataFrame:
    """Transform the raw WHO CSV into the tidy mortality dataset."""
    raw = pd.read_csv(payload_path)

    required_raw = {
        "Date_reported", "Country_code", "Country", "WHO_region", "New_deaths", "Cumulative_deaths"}

    # Check that WHO has not unexpectedly changed the source schema.
    missing_columns = required_raw.difference(raw.columns)

    if missing_columns:
        raise ValueError("Raw WHO data is missing columns: " f"{sorted(missing_columns)}")

    # Keep only the variables needed for this dashboard.
    frame = raw[["Date_reported", "Country_code", "Country", "WHO_region", "New_deaths", "Cumulative_deaths"]].copy()

    # Rename WHO variables into simpler dashboard-friendly names.
    frame = frame.rename(
        columns={
            "Date_reported": "date",
            "Country_code": "country_code",
            "Country": "country",
            "WHO_region": "who_region",
            "New_deaths": "weekly_deaths",
            "Cumulative_deaths": "cumulative_deaths"})

    # Correct known encoding errors in WHO country labels.
    country_name_corrections = {
        "Cura�ao": "Curaçao", 
        "C�te d'Ivoire": "Côte d'Ivoire",
        "R�union": "Réunion",
        "Saint Barth�lemy": "Saint Barthélemy",
        "T�rkiye": "Türkiye"}
    frame["country"] = frame["country"].replace(country_name_corrections)

    # Parse the weekly reporting date.
    frame["date"] = pd.to_datetime(frame["date"], errors="raise")
    frame["year"] = frame["date"].dt.year

    # Convert weekly deaths to numeric.
    # Missing values are deliberately preserved as NaN.
    frame["weekly_deaths"] = pd.to_numeric(frame["weekly_deaths"], errors="coerce")

    frame["cumulative_deaths"] = pd.to_numeric(frame["cumulative_deaths"], errors="raise")
    frame["unit"] = "reported deaths"

    return frame[["date", "year", "country_code", "country", "who_region", "weekly_deaths", "cumulative_deaths", "unit"]]


def validate(frame: pd.DataFrame) -> None:
    """Validate important expectations about the transformed dataset."""
    missing_columns = REQUIRED.difference(frame.columns)

    if missing_columns:
        raise ValueError(f"Missing columns: {sorted(missing_columns)}")

    # Dataset size
    if len(frame) < 1000:
        raise ValueError("The processed dataset contains too few observations")

    parsed_dates = pd.to_datetime(frame["date"], errors="raise")

    if parsed_dates.min() < pd.Timestamp("2020-01-01"):
        raise ValueError("Unexpected observation before 2020")
    if parsed_dates.max() < pd.Timestamp("2023-01-01"):
        raise ValueError("Dataset does not contain the expected COVID-19 period")

    # Each country should have at most one observation for a reporting date.
    if frame.duplicated(["date", "country"]).any():
        raise ValueError("Duplicate date and country keys found")

    # Country names
    if frame["country"].isna().any():
        raise ValueError("Unexpected missing country names")
    if frame["country"].astype(str).str.contains("�", regex=False).any():
        raise ValueError("Country names contain unexpected replacement characters")

    # Mortality variables
    if frame["cumulative_deaths"].isna().any():
        raise ValueError("Unexpected missing cumulative death counts")
    if (frame["cumulative_deaths"] < 0).any():
        raise ValueError("Cumulative deaths must not be negative")

    # Unit
    if set(frame["unit"].dropna()) != {"reported deaths"}:
        raise ValueError("Unexpected unit")


def make_sample(frame: pd.DataFrame) -> pd.DataFrame:
    """Create a faithful offline sample with complete weekly histories."""
    # Select complete histories for the chosen countries
    sample = frame.loc[frame["country"].isin(SAMPLE_COUNTRIES)].copy()

    # Check that every intended sample country exists in the WHO data.
    available_countries = set(sample["country"].dropna().unique())
    missing_countries = set(SAMPLE_COUNTRIES).difference(available_countries)

    if missing_countries:
        raise ValueError("Sample countries missing from processed data: " f"{sorted(missing_countries)}")

    # Keep a stable country/date ordering.
    sample = sample.sort_values(["country", "date"]).reset_index(drop=True)

    return sample


def main() -> None:
    """Run acquisition, transformation, validation and output."""
    parser = argparse.ArgumentParser(description=__doc__ )

    # Download a fresh WHO raw file and stop.
    parser.add_argument( "--acquire", action="store_true", help="Refresh the raw WHO CSV and stop")

    # Validate the existing processed.csv and stop.
    parser.add_argument("--validate", action="store_true", help="Validate data/processed.csv and stop")
    args = parser.parse_args()

    # The automated checker
    sample_mode = (os.getenv("DASHBOARD_SAMPLE_MODE", "0") == "1")

    # Acquire-only mode
    if args.acquire:
        if sample_mode:
            parser.error("Unset DASHBOARD_SAMPLE_MODE before acquiring live data")
        acquire()
        return

    # Validation-only mode
    if args.validate:
        frame = pd.read_csv(PROCESSED)
        validate(frame)
        print("Processed data valid")
        return

    # Select input data
    if sample_mode:
        frame = pd.read_csv(SAMPLE)
    else:
        if not RAW.exists():
            acquire()
        frame = transform(RAW)

    # Store dates consistently as YYYY-MM-DD.
    frame["date"] = (pd.to_datetime(frame["date"], errors="raise").dt.strftime("%Y-%m-%d"))

    frame = frame.sort_values(["country", "date"]).reset_index(drop=True)
    validate(frame)

    # Make sure data file exists.
    PROCESSED.parent.mkdir(parents=True, exist_ok=True)

    # Write processed.csv
    frame.to_csv(PROCESSED, index=False, na_rep="")
    print(f"Validated and wrote {len(frame)} rows " f"to {PROCESSED}")

    # Write sample.csv
    if not sample_mode:
        sample = make_sample(frame)
        sample.to_csv(SAMPLE, index=False, na_rep="")
        print(f"Wrote {len(sample)} rows " f"to {SAMPLE}")





if __name__ == "__main__":
    main()