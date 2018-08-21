# Import base tools

## Note, for mac osx compatability import something from shapely.geometry before importing fiona or geopandas
## https://github.com/Toblerity/Shapely/issues/553  * Import shapely before rasterio or fioana
from shapely import geometry
import rasterio
import random
from cw_tiler import main
from cw_tiler import utils
from cw_tiler import slvector_utils
import numpy as np
import os
from tqdm import tqdm
# Setting Certificate Location for Ubuntu/Mac OS locations (Rasterio looks for certs in centos locations)
os.environ['CURL_CA_BUNDLE']='/etc/ssl/certs/ca-certificates.crt'

## give location to SpaceNet 8-Band PanSharpened Geotiff on s3


#spacenetPath = "s3://spacenet-dataset/AOI_2_Vegas/srcData/rasterData/AOI_2_Vegas_MUL-PanSharpen_Cloud.tif"
geotiff_path = "/home/dlindenbaum/datastorage/spacenet_sample/AOI_2_Vegas_MUL-PanSharpen_Cloud.tif"
geojson_labels_path = "./tests/fixtures/my-bucket/spacenet_test/las-vegas_nevada_osm_buildings.geojson"

stac_item = {"geotiff": geotiff_path,
             "building_labels": geojson_labels_path}

data_location = 'dst_location'


def create_spacenet_label(data_location,
                          imagePrefix,
                          dataset_src,
                          dataset_src_profile,
                          gdf_utm,
                          cell_selection,
                          utm_crs,
                          stride_size_meters=400,  ## Each grid starting point will be spaced 400m apart
                          cell_size_meters=400,    ## Each grid cell will be 400m on a side
                          tile_size_pixels=800     ## Specify the number of pixels in a tile cell_size_meters/tile_size_pixels == Pixel_Size_Meters
                          ):
    """ll_x, ll_y, ur_x, ur_y = cell_selection


    """
    ll_x, ll_y, ur_x, ur_y = cell_selection
    label_geojson_location = os.path.join(data_location, imagePrefix.format(int(ll_x), int(ll_y)) + "_label.geojson")
    label_mask_location = os.path.join(data_location, imagePrefix.format(int(ll_x), int(ll_y)) + "_label.tif")
    tile_location = os.path.join(data_location, imagePrefix.format(int(ll_x), int(ll_y)) + "_image.tif")

    tile, mask, window_transform = main.tile_utm(dataset_src, ll_x, ll_y, ur_x, ur_y,
                                                 indexes=None,
                                                 tilesize=tile_size_pixels,
                                                 nodata=None,
                                                 alpha=None,
                                                 dst_crs=utm_crs)

    ## Get Vector Information from bounding box
    small_gdf = vector_utils.vector_tile_utm(gdf_utm, tile_bounds=[ll_x, ll_y, ur_x, ur_y])
    if not small_gdf.empty:
        small_gdf.to_file(label_geojson_location,
                          driver='GeoJSON')

    else:
        open(label_geojson_location, 'a').close()

    img = vector_utils.rasterize_gdf(small_gdf,
                                     src_shape=(tile_size_pixels, tile_size_pixels),
                                     src_transform=window_transform,
                                     )

    # update src_profile for writing new img
    dst_profile = src_profile
    dst_profile.update({'transform': window_transform,
                        'crs': utm_crs,
                        'width': tile_size_pixels,
                        'height': tile_size_pixels,
                        'count': 1,
                        'dtype': rasterio.uint8

                        })
    ## write label to tiff
    with rasterio.open(label_mask_location,
                       'w',
                       **dst_profile) as dst:

        dst.write(img, indexes=1)

    ## write image to geotiff
    dst_profile = src_profile
    dst_profile.update({'transform': window_transform,
                        'crs': utm_crs,
                        'width': tile_size_pixels,
                        'height': tile_size_pixels,
                        'count': 8,
                        'dtype': rasterio.uint16
                        })

    with rasterio.open(tile_location, 'w',
                       **dst_profile) as dst:

        dst.write(tile)

    assetDict = {'assets': {'geotiff_image': tile_location,
                            'label_geojson': label_geojson_location,
                            'label_mask': label_mask_location}
                 }

    return assetDict





def create_spacenet_labels(stac_item,
                           data_location,
                           imagePrefix="AOI_6_Atlanta_MUL_{}_{}",
                           stride_size_meters=400,  ## Each grid starting point will be spaced 400m apart
                           cell_size_meters=400,    ## Each grid cell will be 400m on a side
                           tile_size_pixels=800     ## Specify the number of pixels in a tile cell_size_meters/tile_size_pixels == Pixel_Size_Meters
                           ):

    ## Prep files for UTM
    geotiff_path = stac_item['geotiff']
    geojson_labels_path = stac_item['building_labels']




    with rasterio.open(geotiff_path) as src:

        # Get Lat, Lon bounds of the Raster (src)
        wgs_bounds = utils.get_wgs84_bounds(src)

        # Use Lat, Lon location of Image to get UTM Zone/ UTM projection
        utm_crs = utils.calculate_UTM_crs(wgs_bounds)

        # Calculate Raster bounds in UTM coordinates
        utm_bounds = utils.get_utm_bounds(src, utm_crs)

    ## read vector file

    gdf = vector_utils.read_vector_file(geojson_labels_path)
    gdf.head()
    gdf_utm = vector_utils.transformToUTM(gdf, utm_crs=utm_crs)

    ## get full bounds
    geoBounds = geometry.box(*gdf_utm.total_bounds)
    rasterBounds = geometry.box(*utm_bounds)

    interBounds = geoBounds.intersection(rasterBounds)
    interBounds.bounds
    # open s3 Location

    # Each grid starting point will be spaced 400m apart
    stride_size_meters = 400

    # Each grid cell will be 400m on a side
    cell_size_meters = 400

    # Specify the number of pixels in a tile cell_size_meters/tile_size_pixels == Pixel_Size_Meters
    tile_size_pixels = 800


    with rasterio.open(geotiff_path) as src:
        src_profile = src.profile
        # Generate list of cells to read from utm_bounds
        cells_list = main.calculate_analysis_grid(interBounds.bounds, stride_size_meters=stride_size_meters,
                                                  cell_size_meters=cell_size_meters)

        # select random cell
        assetDict_list = []
        for cell_selection in tqdm(cells_list):
            # random_cell = random.choice(cells_list)
            ll_x, ll_y, ur_x, ur_y = cell_selection

            # Get Tile from bounding box
            tile, mask, window_transform = main.tile_utm(src, ll_x, ll_y, ur_x, ur_y, indexes=None,
                                                         tilesize=tile_size_pixels, nodata=None, alpha=None,
                                                         dst_crs=utm_crs)

            # print(np.shape(tile))

            ## Get Vector Information from bounding box
            small_gdf = vector_utils.vector_tile_utm(gdf_utm, tile_bounds=[ll_x, ll_y, ur_x, ur_y])

            label_geojson_location = os.path.join(data_location, imagePrefix.format(int(ll_x), int(ll_y)) + "_label.geojson")
            label_mask_location    = os.path.join(data_location, imagePrefix.format(int(ll_x), int(ll_y)) + "_label.tif")
            tile_location          = os.path.join(data_location, imagePrefix.format(int(ll_x), int(ll_y)) + "_image.tif")
            if not small_gdf.empty:
                small_gdf.to_file(label_geojson_location,
                                  driver='GeoJSON')

            else:
                open(label_geojson_location, 'a').close()

            img = vector_utils.rasterize_gdf(small_gdf,
                                             src_shape=(tile_size_pixels, tile_size_pixels),
                                             src_transform=window_transform,
                                             )

            # update src_profile for writing new img
            dst_profile = src_profile
            dst_profile.update({'transform': window_transform,
                                'crs': utm_crs,
                                'width': tile_size_pixels,
                                'height': tile_size_pixels,
                                'count': 1,
                                'dtype': rasterio.uint8

                                })
            ## write label to tiff
            with rasterio.open(label_mask_location,
                               'w',
                               **dst_profile) as dst:

                dst.write(img, indexes=1)

            ## write image to geotiff
            dst_profile = src_profile
            dst_profile.update({'transform': window_transform,
                                'crs': utm_crs,
                                'width': tile_size_pixels,
                                'height': tile_size_pixels,
                                'count': 8,
                                'dtype': rasterio.uint16
                                })

            with rasterio.open(tile_location, 'w',
                               **dst_profile) as dst:

                dst.write(tile)

            assetDict = {'assets': {'geotiff_image': tile_location,
                                    'label_geojson': label_geojson_location,
                                    'label_mask': label_mask_location}
                         }

            assetDict_list.append(assetDict)




