"""Acquire, transform and validate the Global Warming dashboard datasets.
Data source:IEA-EDGAR CO2 emissions data, 1970-2025.
Pipeline:
1. acquire(): check that the raw EDGAR Excel workbook is available
2. transform(): reshape country-level CO2 emissions into tidy format
3. transform_sector(): reshape sector-level CO2 emissions into tidy format
4. build_global_sector_data(): aggregate sector emissions to global totals
5. validate(): check the country-level processed dataset
6. validate_sector(): check the transformed sector-level dataset
7. validate_global_sector(): check the aggregated global sector dataset
8. main(): run the complete pipeline and write dashboard-ready outputs
The pipeline produces:
1. processed.csv: annual country-level CO2 emissions
2. processed_sector.csv: annual global sector-level CO2 emissions
Presentation and visualisation logic belongs in views.py.
"""

from __future__ import annotations
import os
from pathlib import Path
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

SAMPLE = ROOT / "data" / "sample.csv"
SAMPLE_SECTOR = ROOT / "data" / "sample_sector.csv"

RAW = ROOT / "data" / "IEA_EDGAR_CO2_1970_2025.xlsx"

PROCESSED = ROOT / "data" / "processed.csv"
PROCESSED_SECTOR = ROOT / "data" / "processed_sector.csv"

REQUIRED = {"date", "year", "country_code", "country",
            "entity_type","substance","emissions_gg","unit"}

def acquire() -> None:
    """Check that the manually downloaded EDGAR source file is available."""
    if not RAW.exists():
        raise FileNotFoundError(
            f"EDGAR source file not found: {RAW}\n"
            "Download the IEA-EDGAR CO2 1970-2025 Excel file "
            "and place it in the data directory.")

    print(f"Using local EDGAR source: {RAW}")


def transform(payload_path: Path) -> pd.DataFrame:
    """Transform EDGAR country-level CO2 emissions into tidy format."""
    # Read the TOTALS BY COUNTRY sheet.
    # The actual column header is on row 9 of the Excel sheet.
    frame = pd.read_excel(payload_path, sheet_name="TOTALS BY COUNTRY", header=9,)

    # Identify annual emissions columns from Y_1970 to Y_2025.
    year_columns = [
        col
        for col in frame.columns
        if str(col).startswith("Y_")]

    # Convert the dataset from wide format to long format.
    frame = frame.melt(
        id_vars=["Country_code_A3", "Name", "Substance",],
        value_vars=year_columns, var_name="year", value_name="emissions_gg",)

    # Rename columns to simpler dashboard-friendly names.
    frame = frame.rename(columns={
        "Country_code_A3": "country_code", "Name": "country", "Substance": "substance"})

    # Convert year labels such as Y_1970 to integer years such as 1970.
    frame["year"] = (frame["year"].str.replace("Y_", "", regex=False).astype(int))

    # Ensure emissions values are numeric.
    # Missing source values remain NaN rather than being replaced with zero.
    frame["emissions_gg"] = pd.to_numeric(frame["emissions_gg"], errors="coerce")

    # Create an annual date field for dashboard/checker use
    frame["date"] = pd.to_datetime(frame["year"].astype(str) + "-12-31").dt.strftime("%Y-%m-%d")

    # Distinguish countries/territories from international transport
    frame["entity_type"] = "country"
    frame.loc[frame["country_code"].isin(["AIR", "SEA"]), "entity_type",] = "international"

    # Explicit display unit
    frame["unit"] = "Gg CO2"

    # Final column order
    frame = frame[["date", "year", "country_code", "country",
                   "entity_type", "substance", "emissions_gg", "unit",]]

    # Sort the final dataset for consistent output.
    frame = frame.sort_values(["country_code", "year"]).reset_index(drop=True)

    return frame


def transform_sector(payload_path: Path) -> pd.DataFrame:
    """Transform EDGAR sector-level CO2 emissions into tidy format."""
    # Read the IPCC 2006 sector sheet.
    frame = pd.read_excel(payload_path, sheet_name="IPCC 2006", header=9,)

    # Identify annual emissions columns from Y_1970 to Y_2025.
    year_columns = [col
                    for col in frame.columns
                    if str(col).startswith("Y_")]

    # Convert from wide format to long format.
    frame = frame.melt(
        id_vars=[
            "Country_code_A3", "Name", "ipcc_code_2006_for_standard_report",
            "ipcc_code_2006_for_standard_report_name", "Substance","fossil_bio"
            ], value_vars=year_columns, var_name="year", value_name="emissions_gg")

    # Rename columns to simpler dashboard-friendly names.
    frame = frame.rename(
        columns={
            "Country_code_A3": "country_code",
            "Name": "country",
            "ipcc_code_2006_for_standard_report": "sector_code",
            "ipcc_code_2006_for_standard_report_name": "sector",
            "Substance": "substance",})

    # Convert Y_1970 to 1970, etc.
    frame["year"] = (frame["year"].str.replace("Y_", "", regex=False).astype(int))

    # Ensure emissions values are numeric & Missing source values remain NaN.
    frame["emissions_gg"] = pd.to_numeric(frame["emissions_gg"],errors="coerce")

    # Sort for consistent output.
    frame = frame.sort_values(["country_code", "sector_code", "year"]).reset_index(drop=True)

    return frame


def build_global_sector_data(sector_frame: pd.DataFrame) -> pd.DataFrame:
    """Aggregate country-sector emissions into global sector totals."""
    global_sector = (sector_frame.groupby([
        "sector_code", "sector", "substance","year"], 
        as_index=False,)["emissions_gg"].sum(min_count=1))

    # Create an annual date field for dashboard/checker use
    global_sector["date"] = pd.to_datetime(
        global_sector["year"].astype(str) + "-12-31").dt.strftime("%Y-%m-%d")

    # Add the emissions unit explicitly
    global_sector["unit"] = "Gg CO2"

    # Set the final column order
    global_sector = global_sector[["date","year","sector_code","sector","substance","emissions_gg","unit"]]

    global_sector = global_sector.sort_values(["sector_code", "year"]).reset_index(drop=True)

    return global_sector


def validate(frame: pd.DataFrame) -> None:
    """Validate the transformed EDGAR CO2 emissions dataset."""
    # Check that all required columns are present.
    missing_columns = REQUIRED.difference(frame.columns)
    if missing_columns:
        raise ValueError(f"Missing required columns: {sorted(missing_columns)}")

    # Check that country/entity identifiers are present.
    if frame["country_code"].isna().any():
        raise ValueError("Missing country/entity codes found")
    
    if frame["country"].isna().any():
        raise ValueError("Missing country/entity names found")

    # This dataset should contain CO2 only.
    substances = set(frame["substance"].dropna().unique())
    if substances != {"CO2"}:
        raise ValueError(f"Unexpected substances found: {sorted(substances)}")

    # Check the expected year coverage.
    if frame["year"].min() != 1970 or frame["year"].max() != 2025:
        raise ValueError("Expected year range 1970-2025")

    # Each country/entity should have at most one record per year.
    if frame.duplicated(
        subset=["country_code", "year"]).any():
        raise ValueError("Duplicate country/entity-year records found")

    # Emissions must be numeric where values are available.
    non_missing_emissions = frame["emissions_gg"].dropna()

    if not pd.api.types.is_numeric_dtype(non_missing_emissions):
        raise ValueError("Emissions values must be numeric")

    # Negative emissions are not expected in this dataset.
    if (non_missing_emissions < 0).any():
        raise ValueError("Negative emissions values found")

    # Check country / international category
    if not frame["entity_type"].isin(["country", "international"]).all():
        raise ValueError("Unexpected entity_type value.")
    
    # Check unit is Gg CO2
    if not (frame["unit"] == "Gg CO2").all():
        raise ValueError("Unexpected emissions unit.")
    
    # Check that annual dates use the YYYY-12-31 format
    if not frame["date"].str.match(r"^\d{4}-12-31$").all():
        raise ValueError("Unexpected annual date format.")


def validate_sector(frame: pd.DataFrame) -> None:
    """Validate the transformed EDGAR sector-level CO2 dataset."""
    required = {"country_code", "country", "sector_code", "sector",
                "substance", "fossil_bio", "year", "emissions_gg"}

    # Check required columns
    missing_columns = required.difference(frame.columns)
    if missing_columns:
        raise ValueError(f"Missing required sector columns: {sorted(missing_columns)}")

    # Check identifiers
    identifier_columns = [
        "country_code", "country", "sector_code", "sector",
        "substance", "fossil_bio", "year"]

    if frame[identifier_columns].isna().any().any():
        raise ValueError("Missing values found in sector identifiers")

    # The dataset should contain CO2 only.
    substances = set(frame["substance"].unique())
    if substances != {"CO2"}:
        raise ValueError(f"Unexpected substances found: {sorted(substances)}")

    # The selected records should contain fossil emissions only.
    fossil_bio_values = set(frame["fossil_bio"].unique())
    if fossil_bio_values != {"fossil"}:
        raise ValueError(f"Unexpected fossil_bio values found: " f"{sorted(fossil_bio_values)}")

    # Check year coverage
    if frame["year"].min() != 1970 or frame["year"].max() != 2025:
        raise ValueError("Expected sector year range 1970-2025")

    # Check country-sector-year uniqueness.
    if frame.duplicated(subset=["country_code", "sector_code", "year",]).any():
        raise ValueError("Duplicate country-sector-year records found")

    # Emissions must be numeric.
    if not pd.api.types.is_numeric_dtype(frame["emissions_gg"]):
        raise ValueError("Sector emissions values must be numeric")


def validate_global_sector(frame: pd.DataFrame) -> None:
    """Validate the aggregated global sector dataset."""
    required = {"date", "year", "sector_code", "sector", "substance", "emissions_gg", "unit"}
    
    # Check that all required columns are present
    missing_columns = required.difference(frame.columns)
    if missing_columns:
        raise ValueError(f"Missing global sector columns: {sorted(missing_columns)}")

    # Check that key sector identifiers contain no missing values
    if frame[["sector_code", "sector", "substance", "year"]].isna().any().any():
        raise ValueError("Missing values found in global sector identifiers")

    # Check that each sector has only one observation per year
    if frame.duplicated(subset=["sector_code", "year"]).any():
        raise ValueError("Duplicate sector-year records found")

    # Check that the dataset covers the full expected time period
    if frame["year"].min() != 1970 or frame["year"].max() != 2025:
        raise ValueError("Expected global sector year range 1970-2025")

    # Check that the dataset contains CO2 emissions only
    if set(frame["substance"].unique()) != {"CO2"}:
        raise ValueError("Unexpected substance in global sector data")

    # Check that all emissions use the expected unit
    if not (frame["unit"] == "Gg CO2").all():
        raise ValueError("Unexpected emissions unit.")

    # Check that annual dates use the YYYY-12-31 format
    if not frame["date"].str.match(r"^\d{4}-12-31$").all():
        raise ValueError("Unexpected annual date format.")

    
def main() -> None:
    """Build processed EDGAR CO2 datasets."""
    # Use bundled sample data when running in offline checker mode
    sample_mode = (os.getenv("DASHBOARD_SAMPLE_MODE", "0") == "1")

    # Ensure the output directory exists
    PROCESSED.parent.mkdir(parents=True, exist_ok=True)

    if sample_mode:
        # Read the bundled country-level sample
        country_frame = pd.read_csv(SAMPLE, dtype={
            "country_code": str, "country": str,
            "entity_type": str, "substance": str, "unit": str},
            keep_default_na=False, na_values=[""])

        # Read the bundled global sector sample
        global_sector_frame = pd.read_csv(SAMPLE_SECTOR,dtype={
            "sector_code": str, "sector": str,
            "substance": str, "unit": str},
            keep_default_na=False, na_values=[""])

        # Validate the bundled samples before writing outputs
        validate(country_frame)
        validate_global_sector(global_sector_frame)

    else:
        # Check that the manually downloaded EDGAR workbook exists
        acquire()

        # Build the country-level dataset from the EDGAR workbook
        country_frame = transform(RAW)
        validate(country_frame)

        # Build country-sector data from the EDGAR workbook
        sector_frame = transform_sector(RAW)
        validate_sector(sector_frame)

        # Aggregate country-sector emissions to global sector totals
        global_sector_frame = build_global_sector_data(sector_frame)
        validate_global_sector(global_sector_frame)

    # Write the dashboard-ready country dataset
    country_frame.to_csv(PROCESSED, index=False)

    # Write the dashboard-ready global sector dataset
    global_sector_frame.to_csv(PROCESSED_SECTOR,index=False)
    print(f"Wrote {len(country_frame):,} rows " f"to {PROCESSED}")
    print(f"Wrote {len(global_sector_frame):,} rows " f"to {PROCESSED_SECTOR}")

if __name__ == "__main__":
    main()