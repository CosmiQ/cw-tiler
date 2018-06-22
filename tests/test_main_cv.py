"""tests rio_tiler.base"""

import os
import pytest
## Note, for mac osx compatability import something from shapely.geometry before importing fiona or geopandas
## https://github.com/Toblerity/Shapely/issues/553  * Import shapely before rasterio or fioana
from shapely import geometry
import rasterio
import random
from cw_tiler import main
from cw_tiler import utils
from cw_tiler import vector_utils
import numpy as np


utmX, utmY = 658029, 4006947
ll_x = utmX
ur_x = utmX + 500
ll_y = utmY
ur_y = utmY + 500
stride_size_meters = 300
cell_size_meters = 400
tile_size_pixels = 1600
spacenetPath = "s3://spacenet-dataset/AOI_2_Vegas/srcData/rasterData/AOI_2_Vegas_MUL-PanSharpen_Cloud.tif"

PREFIX = os.path.join(os.path.dirname(__file__), 'fixtures')

ADDRESS = '{}/my-bucket/hro_sources/colorado/201404_13SED190110_201404_0x1500m_CL_1.tif'.format(PREFIX)
ADDRESS_ALPHA = '{}/my-bucket/hro_sources/colorado/201404_13SED190110_201404_0x1500m_CL_1_alpha.tif'.format(PREFIX)
ADDRESS_NODATA = '{}/my-bucket/hro_sources/colorado/201404_13SED190110_201404_0x1500m_CL_1_nodata.tif'.format(PREFIX)
geojsonPath = "{}/my-bucket/spacenet_test/las-vegas_nevada_osm_buildings.geojson".format(PREFIX)



def test_calculate_utm_epsg():

    wgs_bounds = utils.get_wgs84_bounds(ADDRESS)
    print(wgs_bounds)
    utm_crs = utils.calculate_UTM_crs(wgs_bounds)
    print(utm_crs)
    assert utm_crs=='+proj=utm +zone=13 +north +ellps=WGS84 +datum=WGS84 +units=m +no_defs'


def test_grid_creation():

    address = spacenetPath

    with rasterio.open(address) as src:

        wgs_bounds = utils.get_wgs84_bounds(src)
        utm_EPSG = utils.calculate_UTM_crs(wgs_bounds)
        utm_bounds = utils.get_utm_bounds(src, utm_EPSG)
        print(utm_bounds)
        cells_list = main.calculate_analysis_grid(utm_bounds, stride_size_meters=stride_size_meters, cell_size_meters=cell_size_meters)
        print(len(cells_list))

    assert len(cells_list[0]) == 4
    assert ((cells_list[0][2]-cells_list[0][0]), (cells_list[0][3]-cells_list[0][1])) == (cell_size_meters, cell_size_meters)
    assert (cells_list[1][1] - cells_list[0][1]) == stride_size_meters
    assert len(cells_list) == 2592




def test_return_tile():

    address = spacenetPath

    with rasterio.open(address) as src:

        wgs_bounds = utils.get_wgs84_bounds(src)
        utm_crs = utils.calculate_UTM_crs(wgs_bounds)
        utm_bounds = utils.get_utm_bounds(src, utm_crs)

        cells_list = main.calculate_analysis_grid(utm_bounds, stride_size_meters=stride_size_meters, cell_size_meters=cell_size_meters)

        random_cell = random.choice(cells_list)
        ll_x, ll_y, ur_x, ur_y = random_cell
        print(random_cell)
        tile, mask, window_transform = main.tile_utm(src, ll_x, ll_y, ur_x, ur_y, indexes=None, tilesize=tile_size_pixels, nodata=None, alpha=None,
                 dst_crs=utm_crs)

        print(np.shape(tile))
        assert np.shape(tile) == (8, tile_size_pixels, tile_size_pixels)


def test_return_vector_gdf():

    utm_crs=utils.calculate_UTM_crs([-115.30170, 36.15604, -115.30170, 36.15604])

    gdf = vector_utils.read_vector_file(geojsonPath)
    gdf.head()
    print(utm_crs)
    gdf = vector_utils.transformToUTM(gdf, utm_crs=utm_crs)

    utmX, utmY = 658029, 4006947
    ll_x = utmX
    ur_x = utmX + 500
    ll_y = utmY
    ur_y = utmY + 500
    stride_size_meters = 300
    cell_size_meters = 400
    tile_size_pixels = 1600

    small_gdf = vector_utils.vector_tile_utm(gdf, tile_bounds=[ll_x, ll_y, ur_x, ur_y])

    print(small_gdf.head())

    assert small_gdf.shape[0]>0


def test_return_vector_tile():
    utm_crs = utils.calculate_UTM_crs([-115.30170, 36.15604, -115.30170, 36.15604])

    gdf = vector_utils.read_vector_file(geojsonPath)
    gdf.head()
    print(utm_crs)
    gdf = vector_utils.transformToUTM(gdf, utm_crs=utm_crs)

    utmX, utmY = 658029, 4006947
    ll_x = utmX
    ur_x = utmX + 500
    ll_y = utmY
    ur_y = utmY + 500
    stride_size_meters = 300
    cell_size_meters = 400
    tile_size_pixels = 1600

    small_gdf = vector_utils.vector_tile_utm(gdf, tile_bounds=[ll_x, ll_y, ur_x, ur_y])

    img = vector_utils.rasterize_gdf(small_gdf, src_shape=(tile_size_pixels, tile_size_pixels))

    print(img.shape)

    assert img.shape[0] == 1600


def test_return_tile_full():

    ## Set for specific tile in Las Vegas
    utm_crs = utils.calculate_UTM_crs([-115.30170, 36.15604, -115.30170, 36.15604])
    gdf = vector_utils.read_vector_file(geojsonPath)
    gdf.head()
    gdf = vector_utils.transformToUTM(gdf, utm_crs=utm_crs)

    utmX, utmY = 658029, 4006947
    ll_x = utmX
    ur_x = utmX + 500
    ll_y = utmY
    ur_y = utmY + 500
    stride_size_meters = 300
    cell_size_meters = 400
    tile_size_pixels = 1600

    address = spacenetPath

    with rasterio.open(address) as src:

        src_profile = src.profile


        tile, mask, window_transform = main.tile_utm(src, ll_x, ll_y, ur_x, ur_y,
                                                     indexes=None,
                                                     tilesize=tile_size_pixels,
                                                     nodata=None,
                                                     alpha=None,
                                                     dst_crs=utm_crs
                                                     )

        print(np.shape(tile))
        assert np.shape(tile) == (8, tile_size_pixels, tile_size_pixels)

        small_gdf = vector_utils.vector_tile_utm(gdf, tile_bounds=[ll_x, ll_y, ur_x, ur_y])
        print(small_gdf.shape)
        small_gdf.to_file(os.path.join(PREFIX, "testTiff_Label.geojson"), driver='GeoJSON')
        img = vector_utils.rasterize_gdf(small_gdf,
                                         src_shape=(tile_size_pixels, tile_size_pixels),
                                         src_transform=window_transform,
                                    )
        print("Label Count Burn {}:".format(np.sum(img)))
        assert img.shape == (tile_size_pixels, tile_size_pixels)


        dst_profile = src_profile
        dst_profile.update({'transform': window_transform,
                    'crs': utm_crs,
                    'width': tile_size_pixels,
                    'height': tile_size_pixels,
                            'count': 1,
                            'dtype': rasterio.uint8

                   })

        with rasterio.open(os.path.join(PREFIX, "testTiff_Label.tif"), 'w',
                                        **dst_profile) as dst:

            dst.write(img, indexes=1)

        dst_profile = src_profile
        dst_profile.update({'transform': window_transform,
                    'crs': utm_crs,
                    'width': tile_size_pixels,
                    'height': tile_size_pixels,
                            'count': 8,
                            'dtype': rasterio.uint16
                   })

        with rasterio.open(os.path.join(PREFIX, "testTiff_Image.tif"), 'w',
                           **dst_profile) as dst:

            dst.write(tile)















