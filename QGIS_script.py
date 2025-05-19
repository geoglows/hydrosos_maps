from qgis.PyQt.QtGui import QColor
from qgis.core import (
    QgsSymbol,
    QgsRendererCategory,
    QgsCategorizedSymbolRenderer
)
import os
import glob

# === Setup ===
input_folder = "C:/Users/rhuber/Downloads/new_shapefiles"
output_base = "C:/Users/rhuber/Downloads/new_tiles_test"
field_name = 'class'

# Color map
class_color_map = {
    1.0: '#cd233f',   # red
    2.0: '#ffa885',   # peach
    3.0: '#e7e2bc',   # light yellow
    4.0: '#8eceee',   # light blue
    5.0: '#2c7dcd',   # medium blue
    # None: '#c4bfbd'   # gray for NULL
}

# === Process each shapefile ===
shapefiles = glob.glob(os.path.join(input_folder, "*.shp"))

for shapefile_path in shapefiles:
    print(f"Processing: {shapefile_path}")
    
    layer = iface.addVectorLayer(shapefile_path, '', 'ogr')
    if not layer.isValid():
        print(f"Failed to load {shapefile_path}")
        continue

    # Apply categorized renderer
    categories = []
    for class_value, hex_color in class_color_map.items():
        if class_value is None:
            continue
        symbol = QgsSymbol.defaultSymbol(layer.geometryType())
        symbol.setColor(QColor(hex_color))
        label = 'Unclassified' if class_value is None else str(int(class_value))
        category = QgsRendererCategory(class_value, symbol, label)
        categories.append(category)

    renderer = QgsCategorizedSymbolRenderer(field_name, categories)
    layer.setRenderer(renderer)
    layer.triggerRepaint()

    # Create individual output directory
    shapefile_name = os.path.splitext(os.path.basename(shapefile_path))[0]
    output_dir = os.path.join(output_base, shapefile_name)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Generate tiles
    processing.run("native:tilesxyzdirectory", {
        'EXTENT': layer.extent(),
        'ZOOM_MIN': 0,
        'ZOOM_MAX': 6,
        'DPI': 96,
        'BACKGROUND_COLOR': QColor(0, 0, 0, 0),
        'ANTIALIAS': True,
        'TILE_FORMAT': 0,  # PNG
        'QUALITY': 75,
        'METATILESIZE': 4,
        'TILE_WIDTH': 256,
        'TILE_HEIGHT': 256,
        'TMS_CONVENTION': False,
        'HTML_TITLE': '',
        'HTML_ATTRIBUTION': '',
        'HTML_OSM': False,
        'OUTPUT_DIRECTORY': output_dir,
        'OUTPUT_HTML': 'TEMPORARY_OUTPUT'
    })

    # Optionally remove the layer from project to keep things clean
    QgsProject.instance().removeMapLayer(layer)

print("Done.")
