"""tests rio_tiler.base"""

import os
import pytest
import rasterio
import random
from cw_tiler import main
from cw_tiler import utils
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


def test_calculate_utm_epsg():

    wgs_bounds = utils.get_wgs84_bounds(ADDRESS)
    print(wgs_bounds)
    utm_EPSG = utils.calculate_UTM_EPSG(wgs_bounds)

    assert utm_EPSG=="EPSG:32613"


def test_grid_creation():

    address = spacenetPath

    with rasterio.open(address) as src:

        wgs_bounds = utils.get_wgs84_bounds(src)
        utm_EPSG = utils.calculate_UTM_EPSG(wgs_bounds)
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
        utm_EPSG = utils.calculate_UTM_EPSG(wgs_bounds)
        utm_bounds = utils.get_utm_bounds(src, utm_EPSG)

        cells_list = main.calculate_analysis_grid(utm_bounds, stride_size_meters=stride_size_meters, cell_size_meters=cell_size_meters)

        random_cell = random.choice(cells_list)
        ll_x, ll_y, ur_x, ur_y = random_cell
        tile, mask = main.tile_utm(src, ll_x, ll_y, ur_x, ur_y, indexes=None, tilesize=tile_size_pixels, nodata=None, alpha=None,
                 dst_crs=utm_EPSG)

        print(np.shape(tile))
        assert np.shape(tile) == (8, tile_size_pixels, tile_size_pixels)






