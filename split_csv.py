import pandas as pd

matched_basins = pd.read_csv('/mnt/c/Users/rhuber/Downloads/final_matchings_may_12.csv')
print(matched_basins)
duplicate_linknos = matched_basins[matched_basins.duplicated(subset='LINKNO', keep=False)]

print(duplicate_linknos)
# Identify duplicated HYBAS_IDs
duplicated_mask = matched_basins['HYBAS_ID'].duplicated(keep=False)

# Create DataFrame with duplicated HYBAS_IDs
dupes_df = matched_basins[duplicated_mask]

# Create DataFrame with unique HYBAS_IDs
unique_df = matched_basins[~duplicated_mask]

print("Unique HYBAS_IDs:")
print(unique_df)
unique_df.to_csv('/mnt/c/Users/rhuber/Downloads/unique_hybas_ids_new.csv', index=False)

print("\nDuplicated HYBAS_IDs:")
print(dupes_df)
dupes_df.to_csv('/mnt/c/Users/rhuber/Downloads/duplicated_hybas_ids_new.csv', index=False)