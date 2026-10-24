"""Acquire, transform and validate the Global Crude Oil Trade dashboard datasets.
Data source:U.S. Energy Information Administration (EIA), International Energy Statistics.
Pipeline:
1. acquire(): obtain annual crude oil imports and exports data
2. transform(): reshape both datasets into tidy country-year format
3. merge: combine imports and exports by country and year
4. derive: calculate net crude oil exports
5. validate(): check the processed dataset
6. main(): run the complete pipeline and write dashboard-ready output

The pipeline produces:
1. processed.csv: annual country-level crude oil imports, exports and net exports
2. sample.csv: bundled offline sample for reproducible grading
Presentation and visualisation logic belongs in views.py.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

RAW_IMPORTS = ROOT / "data" / "Annual crude and lease condensate imports.csv"
RAW_EXPORTS = ROOT / "data" / "Annual crude and lease condensate exports.csv"

SAMPLE = ROOT / "data" / "sample.csv"
PROCESSED = ROOT / "data" / "processed.csv"

IMPORTS_URL = ("https://www.eia.gov/international/data/world/petroleum-and-other-liquids/annual-crude-and-lease-condensate-imports")

EXPORTS_URL = ("https://www.eia.gov/international/data/world/petroleum-and-other-liquids/annual-crude-and-lease-condensate-exports")

# Dataset contract
REQUIRED = {"date", "year", "country", "crude_imports", "crude_exports", "net_exports", "unit"}

# Countries used in the bundled offline sample.
SAMPLE_COUNTRIES = ["Australia", "Canada", "China", "India", "Japan", "Saudi Arabia", "United States"]

def acquire() -> None:
    """Download the raw source to data/raw.json."""
    try:
        with urlopen(URL, timeout=30) as response:
            payload = json.load(response)
    except (URLError, TimeoutError, json.JSONDecodeError) as error:
        sys.exit(
            f"Could not fetch {URL}: {error}. "
            "Check your connection, or rerun with DASHBOARD_SAMPLE_MODE=1 to use the bundled sample.")
        
    RAW.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {RAW}")


def transform(imports_path: Path, exports_path: Path) -> pd.DataFrame:
    """Transform EIA crude oil imports and exports into tidy country-year data."""
    # Read the EIA CSV files
    imports = pd.read_csv(imports_path, skiprows=1)
    exports = pd.read_csv(exports_path, skiprows=1)

    # The first remaining row contains the indicator description.
    imports = imports.iloc[1:].copy()
    exports = exports.iloc[1:].copy()

    # Rename the identifier columns.
    imports = imports.rename(columns={"API": "imports_series_code", "Unnamed: 1": "country"})
    exports = exports.rename(columns={"API": "exports_series_code", "Unnamed: 1": "country"})

    # Identify annual value columns.
    import_year_columns = [
        column
        for column in imports.columns
        if str(column).isdigit()]

    export_year_columns = [
        column
        for column in exports.columns
        if str(column).isdigit()]

    # Reshape imports from wide to long format.
    imports = imports.melt(
        id_vars=["imports_series_code","country"],
        value_vars=import_year_columns, var_name="year", value_name="crude_imports")

    # Reshape exports from wide to long format.
    exports = exports.melt(
        id_vars=["exports_series_code", "country"],
        value_vars=export_year_columns, var_name="year", value_name="crude_exports")

    # Convert year to integer.
    imports["year"] = imports["year"].astype(int)
    exports["year"] = exports["year"].astype(int)

    # Convert observations to numeric & Missing or unavailable EIA values remain NaN
    imports["crude_imports"] = pd.to_numeric(imports["crude_imports"], errors="coerce")
    exports["crude_exports"] = pd.to_numeric(exports["crude_exports"], errors="coerce")

    # Clean country names.
    imports["country"] = imports["country"].astype(str).str.strip()
    exports["country"] = exports["country"].astype(str).str.strip()

    # Combine imports and exports by country and year.
    frame = imports.merge(exports, on=["country", "year"], how="outer", validate="one_to_one")

    # Calculate net exports only when both imports and exports are available for the same country-year.
    frame["net_exports"] = (frame["crude_exports"] - frame["crude_imports"])

    # Create an annual date field.
    frame["date"] = pd.to_datetime(frame["year"].astype(str) + "-12-31", errors="raise")

    # Unit used by the EIA source files.
    frame["unit"] = "Mb/d"

    # Keep a stable output schema.
    frame = frame[["date", "year", "country", "imports_series_code", "exports_series_code", "crude_imports", "crude_exports", "net_exports", "unit"]]

    return frame


def validate(frame: pd.DataFrame) -> None:
    """Validate the transformed EIA crude oil trade dataset."""
    # Check required columns.
    missing_columns = REQUIRED.difference(frame.columns)

    if missing_columns:
        raise ValueError(f"Missing columns: {sorted(missing_columns)}")
    if frame.empty:
        raise ValueError("Dataset contains no observations")

    # Country, year and date are required identifiers.
    if frame["country"].isna().any():
        raise ValueError("Unexpected missing country values")
    if frame["year"].isna().any():
        raise ValueError("Unexpected missing year values")
    if frame["date"].isna().any():
        raise ValueError("Unexpected missing date values")

    # Each country-year observation must be unique.
    if frame.duplicated(["country", "year"]).any():
        raise ValueError("Duplicate country-year observations found")

    # Validate the documented source period.
    years = pd.to_numeric(frame["year"], errors="raise")
    if years.min() < 1980 or years.max() > 2020:
        raise ValueError("Year outside the documented EIA period")

    # Date and year must agree.
    dates = pd.to_datetime(frame["date"], errors="raise")
    if not (dates.dt.year.to_numpy() == years.to_numpy()).all():
        raise ValueError("Date does not match year")

    # Imports and exports may be missing in the EIA source, but reported observations cannot be negative.
    for column in ["crude_imports", "crude_exports"]:
        values = pd.to_numeric(frame[column], errors="coerce")
        if (values.dropna() < 0).any():
            raise ValueError(f"{column} contains negative values")

    # Net exports = exports - imports whenever both source observations are available.
    complete = (frame["crude_imports"].notna() & frame["crude_exports"].notna())
    expected = (frame.loc[complete, "crude_exports"] - frame.loc[complete, "crude_imports"])
    actual = frame.loc[complete, "net_exports"]
    if not (actual.round(6).to_numpy() == expected.round(6).to_numpy()).all():
        raise ValueError("Net exports do not equal exports minus imports")

    # Check the documented unit.
    if set(frame["unit"].dropna()) != {"Mb/d"}:
        raise ValueError("Unexpected unit")


def make_sample(frame: pd.DataFrame) -> pd.DataFrame:
    """Create a representative offline sample for reproducible grading."""
    sample = frame[frame["country"].isin(SAMPLE_COUNTRIES)].copy()
    sample = sample.sort_values(["country", "year"]).reset_index(drop=True)

    if sample.empty:
        raise ValueError("Sample dataset contains no observations")

    return sample


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validate", action="store_true", help="Validate data/processed.csv and stop")
    args = parser.parse_args()
    sample_mode = (os.getenv("DASHBOARD_SAMPLE_MODE", "0") == "1")

    # Validate an existing processed dataset.
    if args.validate:
        frame = pd.read_csv(PROCESSED)
        validate(frame)
        print("Processed data valid")
        return

    # Offline / grader mode.
    if sample_mode:
        if not SAMPLE.exists():
            raise FileNotFoundError(f"Missing sample file: {SAMPLE}")
        frame = pd.read_csv(SAMPLE)

    # Full local EIA dataset.
    else:
        if not RAW_IMPORTS.exists():
            raise FileNotFoundError(f"Missing raw imports file: {RAW_IMPORTS}")
        if not RAW_EXPORTS.exists():
            raise FileNotFoundError(f"Missing raw exports file: {RAW_EXPORTS}")
        frame = transform(RAW_IMPORTS, RAW_EXPORTS)

    # Standardise date format.
    frame["date"] = pd.to_datetime(frame["date"], errors="raise").dt.strftime("%Y-%m-%d")
    frame = frame.sort_values(["country", "year"]).reset_index(drop=True)

    # Validate before writing.
    validate(frame)
    PROCESSED.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(PROCESSED, index=False)

    # Refresh the bundled sample only when processing the full raw EIA datasets.
    if not sample_mode:
        sample = make_sample(frame)
        sample.to_csv(SAMPLE, index=False)
        print(f"Wrote {len(sample)} sample rows to {SAMPLE}")

    print(f"Validated and wrote {len(frame)} rows " f"to {PROCESSED}")


if __name__ == "__main__":
    main()
