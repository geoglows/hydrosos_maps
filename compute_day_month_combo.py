import pandas as pd
import xarray as xr
import numpy as np
from pathlib import Path

# --- USER INPUT ---
start_year = 1990
end_year = 2025
output_dir = Path("/mnt/c/Users/rhuber/Downloads/monthly_classifications_may_12")
output_dir.mkdir(parents=True, exist_ok=True)
# ------------------

# Read river IDs
matched_basins = pd.read_csv('/mnt/c/Users/rhuber/Downloads/unique_hybas_ids_new.csv')
river_ids = matched_basins["LINKNO"].dropna().unique()

# Open GEOGloWS retrospective dataset
retro_hourly_zarr_uri = 's3://geoglows-v2/retrospective/monthly-timesteps.zarr'
storage_options = {'anon': True}
ds = xr.open_dataset(retro_hourly_zarr_uri, engine='zarr', storage_options=storage_options)

# Filter dataset to only the matched river IDs
filtered_ds = ds.sel(river_id=xr.DataArray(river_ids, dims="river_id"))

# Open flow threshold dataset
flow_thresh = xr.open_dataset("/home/rhuber/development/pygeoglows/flow_cutoff_thresholds_may_12.nc")

# Flow classification function
def classify_flow(flow_value, cutoffs):
    if np.isnan(flow_value):
        return pd.NA
    for i, cutoff in enumerate(cutoffs):
        if flow_value <= cutoff:
            return i + 1  # 1-based class
    return 5

# Loop through each year and month
for year in range(start_year, end_year + 1):
    for month in range(1, 13):
        date_str = f"{year}-{month:02d}"
        print(f"Processing: {date_str}")

        try:
            filtered_time = filtered_ds.sel(time=date_str)
        except KeyError:
            print(f"  Skipping {date_str}: time not found.")
            continue

        # Compute mean flow
        try:
            monthly_flow = filtered_time["Q"].mean(dim="time", skipna=True).to_pandas()
        except:
            print(f"  Skipping {date_str}: error in computing mean flow.")
            continue

        # Get cutoffs for the month (1-based indexing for months in xarray)
        try:
            flow_cutoffs = flow_thresh.sel(month=month)
        except:
            print(f"  Skipping {date_str}: cutoff month not found.")
            continue

        # Classify flows
        results = []
        for rid in river_ids:
            try:
                flow_value = monthly_flow.loc[rid]
                cutoff_vals = flow_cutoffs.sel(river_id=rid)["flow_cutoff"].values
                category = classify_flow(flow_value, cutoff_vals)
                results.append({
                    'year': year,
                    'month': month,
                    'river_id': rid,
                    'flow': flow_value,
                    'class': category
                })
            except KeyError:
                results.append({
                    'year': year,
                    'month': month,
                    'river_id': rid,
                    'flow': pd.NA,
                    'class': pd.NA
                })

        # Convert to DataFrame and save
        df = pd.DataFrame(results)
        df.to_csv(output_dir / f"flow_classification_{year}_{month:02d}.csv", index=False)
