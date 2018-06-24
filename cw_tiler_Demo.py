# Import base tools

## Note, for mac osx compatability import something from shapely.geometry before importing fiona or geopandas
## https://github.com/Toblerity/Shapely/issues/553  * Import shapely before rasterio or fioana
from shapely import geometry
import rasterio
import random
from cw_tiler import main
from cw_tiler import utils
from cw_tiler import vector_utils
import numpy as np
import os
from tqdm import tqdm
# Setting Certificate Location for Ubuntu/Mac OS locations (Rasterio looks for certs in centos locations)
os.environ['CURL_CA_BUNDLE']='/etc/ssl/certs/ca-certificates.crt'

## give location to SpaceNet 8-Band PanSharpened Geotiff on s3

#spacenetPath = "s3://spacenet-dataset/AOI_2_Vegas/srcData/rasterData/AOI_2_Vegas_MUL-PanSharpen_Cloud.tif"
spacenetPath = "/home/dlindenbaum/datastorage/spacenet_sample/AOI_2_Vegas_MUL-PanSharpen_Cloud.tif"
osm_labels_path = "./tests/fixtures/my-bucket/spacenet_test/las-vegas_nevada_osm_buildings.geojson"

## Prep files for UTM
with rasterio.open(spacenetPath) as src:

    # Get Lat, Lon bounds of the Raster (src)
    wgs_bounds = utils.get_wgs84_bounds(src)
    
    # Use Lat, Lon location of Image to get UTM Zone/ UTM projection
    utm_crs = utils.calculate_UTM_crs(wgs_bounds)
    
    # Calculate Raster bounds in UTM coordinates 
    utm_bounds = utils.get_utm_bounds(src, utm_crs)

## read vector file
gdf = vector_utils.read_vector_file(osm_labels_path)
gdf.head()
gdf_utm = vector_utils.transformToUTM(gdf, utm_crs=utm_crs)


# open s3 Location

# Each grid starting point will be spaced 400m apart
stride_size_meters = 400

# Each grid cell will be 400m on a side
cell_size_meters   = 400

# Specify the number of pixels in a tile cell_size_meters/tile_size_pixels == Pixel_Size_Meters
tile_size_pixels   = 1200


with rasterio.open(spacenetPath) as src:

    

    # Generate list of cells to read from utm_bounds 
    cells_list = main.calculate_analysis_grid(utm_bounds, stride_size_meters=stride_size_meters, cell_size_meters=cell_size_meters)

    # select random cell
    for idx in tqdm(range(100)):
        random_cell = random.choice(cells_list)
        ll_x, ll_y, ur_x, ur_y = random_cell


        # Get Tile from bounding box
        tile, mask, window_transform = main.tile_utm(src, ll_x, ll_y, ur_x, ur_y, 
                                                     indexes=None, 
                                                     tilesize=tile_size_pixels, 
                                                     nodata=None, 
                                                     alpha=None,
                                                     dst_crs=utm_crs)

        #print(np.shape(tile))

        ## Get Vector Information from bounding box
        small_gdf = vector_utils.vector_tile_utm(gdf_utm, tile_bounds=[ll_x, ll_y, ur_x, ur_y])