import pandas as pd
import numpy as np
import geoglows
from tqdm import tqdm

def calculate_monthly_flow_cutoffs_from_timeseries(start_year: int, end_year: int, flowdata: pd.DataFrame) -> pd.DataFrame:
    # Ensure correct columns
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

    # Step 3: Calculate Weibull rank percentiles
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

    return pd.DataFrame(cutoffs)

# Read matched basins
matched_basins = pd.read_csv('/mnt/c/Users/rhuber/Downloads/duplicated_hybas_ids_new.csv')

# Group by HYBAS_ID
grouped = matched_basins.groupby("HYBAS_ID")["LINKNO"].apply(list).reset_index()

# Storage for all results
all_cutoffs = []

# Loop over HYBAS_IDs and compute cutoffs
for _, row in tqdm(grouped.iterrows(), total=grouped.shape[0], desc="Computing HYBAS_ID cutoffs"):
    hybas_id = row["HYBAS_ID"]
    linknos = row["LINKNO"]

    try:
        combined_flow = None

        for linkno in linknos:
            ts = geoglows.data.retrospective(int(linkno))  # DataFrame with MultiIndex: (time, river_id)

            # Drop 'river_id' level to get time-indexed Series
            if isinstance(ts.index, pd.MultiIndex):
                ts = ts.droplevel("river_id")

            # Collapse to a Series (single column)
            ts_series = ts.squeeze()

            if combined_flow is None:
                combined_flow = ts_series.copy()
            else:
                combined_flow = combined_flow.add(ts_series, fill_value=0)

        # Compute cutoffs
        cutoffs_df = calculate_monthly_flow_cutoffs_from_timeseries(1991, 2020, combined_flow)
        cutoffs_df["hybas_id"] = hybas_id
        all_cutoffs.append(cutoffs_df)

    except Exception as e:
        print(f"Failed for HYBAS_ID {hybas_id}: {e}")

# Combine all into one DataFrame
cutoffs_all = pd.concat(all_cutoffs, ignore_index=True)

# Pivot to xarray
ds = cutoffs_all.pivot_table(
    index=['hybas_id', 'month', 'threshold'],
    values='flow_cutoff'
).to_xarray()

# Save to NetCDF
ds.to_netcdf("flow_cutoff_thresholds_by_hybas_may_12.nc")
