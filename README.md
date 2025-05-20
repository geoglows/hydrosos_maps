There are 2 csv files with the matched link numbers.. One represents the hydrobasins with with a unique link number and the other represents hydrobasins that have multiple link number outlets. There is one netcdf file to go with each of these. Then there is one python script that goes with each of these.

Once you have gotten a csv file out of each python script then you can run the combine script. That will output a singuar shapefile for each month.

This shapefile can be used in the qgis script which is used to generate the maptiles. It was run in QGIS itself as a python script.

You will also need to combined hydro basin level 4 file. You can download the level 4 hydro basins and combine them into one shapefile so the script does not need to be run in segments.

The scripts also exist to compute the netcdf files which are the precomputed thresholds for hydrosos levels. If matches or hydro basins changes, this netcdf file will need to be updated.
