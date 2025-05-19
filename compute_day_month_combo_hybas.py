import pandas as pd
import xarray as xr
import numpy as np
from pathlib import Path

# --- USER INPUT ---
start_year = 1990
end_year = 2025
output_dir = Path("/mnt/c/Users/rhuber/Downloads/monthly_classifications_duplicates_may_12")
output_dir.mkdir(parents=True, exist_ok=True)
# ------------------

# Read river ID to HYBAS_ID mapping
mapping_df = pd.read_csv('/mnt/c/Users/rhuber/Downloads/duplicated_hybas_ids_new.csv')
mapping_df = mapping_df.dropna(subset=['LINKNO', 'HYBAS_ID'])

# Group LINKNOs by HYBAS_ID
hybas_groups = mapping_df.groupby('HYBAS_ID')['LINKNO'].apply(list)

# Open GEOGloWS retrospective dataset
retro_hourly_zarr_uri = 's3://geoglows-v2/retrospective/monthly-timesteps.zarr'
storage_options = {'anon': True}
ds = xr.open_dataset(retro_hourly_zarr_uri, engine='zarr', storage_options=storage_options)

# Open flow threshold dataset (has dimension 'hybas_id' now)
flow_thresh = xr.open_dataset("/home/rhuber/development/pygeoglows/flow_cutoff_thresholds_by_hybas_may_12.nc")

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
            filtered_time = ds.sel(time=date_str)
        except KeyError:
            print(f"  Skipping {date_str}: time not found.")
            continue

        try:
            flow_data = filtered_time["Q"].mean(dim="time", skipna=True)
        except:
            print(f"  Skipping {date_str}: error in computing mean flow.")
            continue

        results = []

        for hybas_id, linknos in hybas_groups.items():
            try:
                linknos = [int(l) for l in linknos if pd.notna(l)]
                flow_values = flow_data.sel(river_id=linknos).sum(dim="river_id", skipna=True).item()
                cutoff_vals = flow_thresh.sel(month=month, hybas_id=hybas_id)["flow_cutoff"].values
                category = classify_flow(flow_values, cutoff_vals)

                results.append({
                    'year': year,
                    'month': month,
                    'hybas_id': hybas_id,
                    'flow': flow_values,
                    'class': category
                })
            except Exception as e:
                results.append({
                    'year': year,
                    'month': month,
                    'hybas_id': hybas_id,
                    'flow': pd.NA,
                    'class': pd.NA
                })

        df = pd.DataFrame(results)
        df.to_csv(output_dir / f"flow_classification_{year}_{month:02d}.csv", index=False)
