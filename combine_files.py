import geopandas as gpd
import pandas as pd
import glob
import os
from pyproj import CRS

# --- USER INPUT ---
start_year = 1990
end_year = 2025
# ------------------

# Step 1: Combine shapefiles (if not done already, this can be done outside the loop)
combined_gdf = gpd.read_file("/mnt/c/Users/rhuber/Downloads/HYBAS_LEVEL_4_combined.shp")

# Step 2: Define directories and file paths
classification_dir = "/mnt/c/Users/rhuber/Downloads/monthly_classifications_may_12"
classification_duplicates_dir = "/mnt/c/Users/rhuber/Downloads/monthly_classifications_duplicates_may_12"
matched_basins_file = "/mnt/c/Users/rhuber/Downloads/final_matchings_may_12.csv"
output_dir = "/mnt/c/Users/rhuber/Downloads/new_shapefiles"

# Load the matched basins file
matched_basins = pd.read_csv(matched_basins_file)

# Loop through years and months
for year in range(start_year, end_year + 1):
    for month in range(1, 13):
        print(f"Processing {year}-{month:02d}...")

        # Step 3: Load flow classification CSV for this month/year
        classification_file = os.path.join(classification_dir, f"flow_classification_{year}_{month:02d}.csv")
        flow_df = pd.read_csv(classification_file)
        
        # If there's a corresponding duplicates file, load it
        flow_df2 = pd.read_csv(os.path.join(classification_duplicates_dir, f"flow_classification_{year}_{month:02d}.csv"))

        # Step 4: Merge flow classification with matched basins using river_id → LINKNO
        merged_df = pd.merge(flow_df, matched_basins, left_on="river_id", right_on="LINKNO", how="left")
        
        # Standardize the HYBAS ID column
        flow_df2 = flow_df2.rename(columns={"hybas_id": "HYBAS_ID"})
        merged_df = merged_df.drop(columns=["river_id"])

        # Concatenate the two DataFrames
        combined_df = pd.concat([flow_df2, merged_df], ignore_index=True)

        # Step 5: Merge with shapefile using HYBAS_ID (keep all hydrobasins)
        final_gdf = combined_gdf.merge(merged_df, on="HYBAS_ID", how="left")

        # Step 6: Keep only selected columns
        final_gdf = final_gdf[["HYBAS_ID", "LINKNO", "flow", "class", "geometry"]]
        final_gdf['LINKNO'] = final_gdf['LINKNO'].astype('Int64') 
        # Step 7: Save the final merged shapefile for this month/year
        output_final = os.path.join(output_dir, f"flow_classification_mapped_{year}_{month:02d}_new.shp")
        final_gdf.to_file(output_final)

        print(f"Final merged shapefile saved to: {output_final}")

print("All files processed.")

