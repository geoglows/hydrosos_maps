import pandas as pd
import numpy as np
import geoglows
from tqdm import tqdm

def calculate_monthly_flow_cutoffs(start_year: int, end_year: int, river_id: int) -> pd.DataFrame:
    assert start_year < end_year, "start_year must be less than end_year"

    # Step 1: Retrieve and prepare data
    flowdata = geoglows.data.retrospective(river_id)
    flowdata = flowdata.reset_index()
    flowdata.columns = ['date', 'flow']
    flowdata['date'] = pd.to_datetime(flowdata['date'])

    # Filter by year range
    flowdata = flowdata[
        (flowdata['date'].dt.year >= start_year) &
        (flowdata['date'].dt.year <= end_year)
    ]

    # Add month and year columns
    flowdata['month'] = flowdata['date'].dt.month
    flowdata['year'] = flowdata['date'].dt.year

    # Step 2: Calculate mean monthly flows
    flowdata = flowdata.groupby(['month', 'year'])['flow'].mean().reset_index()

    # Step 3: Calculate Weibull rank percentiles (your original style)
    for i in range(1, 13):
        flowdata.loc[flowdata['month'] == i, 'weibell_rank'] = (
            flowdata.loc[flowdata['month'] == i, 'flow'].rank(na_option='keep') /
            (flowdata.loc[flowdata['month'] == i, 'flow'].count() + 1)
        )

    # Step 4: Interpolate cutoff values
    thresholds = [0.13, 0.28, 0.71999, 0.86999, 1]
    cutoffs = []

    for month in sorted(flowdata['month'].unique()):
        month_data = flowdata[flowdata['month'] == month].sort_values('weibell_rank')
        month_data = month_data.drop_duplicates(subset='weibell_rank')

        for t in thresholds:
            interp_flow = np.interp(t, month_data['weibell_rank'], month_data['flow'])
            cutoffs.append({'month': month, 'threshold': t, 'flow_cutoff': interp_flow})

    cutoffs_df = pd.DataFrame(cutoffs).sort_values(['month', 'threshold']).reset_index(drop=True)
    return cutoffs_df



# Read both matched basin files
#matched1 = pd.read_csv('/mnt/c/Users/rhuber/Downloads/matched_basins.csv')
#matched2 = pd.read_csv('/mnt/c/Users/rhuber/Downloads/FIXME.csv')

# Combine and drop duplicates
#matched_basins = pd.concat([matched1, matched2], ignore_index=True).drop_duplicates(subset="LINKNO")
matched_basins = pd.read_csv('/mnt/c/Users/rhuber/Downloads/unique_hybas_ids_new.csv')
# Get unique river IDs
river_ids = matched_basins["LINKNO"].dropna().unique()

# Storage for all results
all_cutoffs = []

# Loop over river IDs and compute cutoffs
for river_id in tqdm(river_ids, desc="Computing cutoffs"):
    try:
        cutoffs_df = calculate_monthly_flow_cutoffs(1991, 2020, int(river_id))
        cutoffs_df['river_id'] = int(river_id)
        all_cutoffs.append(cutoffs_df)
    except Exception as e:
        print(f"Failed for river_id {river_id}: {e}")

# Combine all into one DataFrame
cutoffs_all = pd.concat(all_cutoffs, ignore_index=True)

# Pivot to xarray
ds = cutoffs_all.pivot_table(
    index=['river_id', 'month', 'threshold'],
    values='flow_cutoff'
).to_xarray()

# Save to NetCDF
ds.to_netcdf("flow_cutoff_thresholds_may_12.nc")