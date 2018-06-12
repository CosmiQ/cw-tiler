import rasterio
from rasterio.warp import transform_bounds
from rasterio.io import DatasetReader
import statistics
import math
import random
from rio_tiler.errors import TileOutsideBounds
from cw_tiler import utils
import numpy as np



def tile_utm_source(src, ll_x, ll_y, ur_x, ur_y, indexes=None, tilesize=256, nodata=None, alpha=None, dst_crs='epsg:4326'):
    """
    Create UTM tile from any images.

    Attributes
    ----------
    source : rasterio.Dataset
    tile_x : int
        Mercator tile X index.
    tile_y : int
        Mercator tile Y index.
    tile_z : int
        Mercator tile ZOOM level.
    indexes : tuple, int, optional (default: (1, 2, 3))
        Bands indexes for the RGB combination.
    tilesize : int, optional (default: 256)
        Output image size.
    nodata: int or float, optional
        Overwrite nodata value for mask creation.
    alpha: int, optional
        Overwrite alpha band index for mask creation.


    Returns
    -------
    data : numpy ndarray
    mask: numpy array

    """

    wgs_bounds = transform_bounds(
        *[src.crs, dst_crs] + list(src.bounds), densify_pts=21)

    indexes = indexes if indexes is not None else src.indexes
    tile_bounds = (ll_x, ll_y, ur_x, ur_y)
    if not utils.tile_exists_utm(wgs_bounds, tile_bounds):
        raise TileOutsideBounds(
            'Tile {}/{}/{}/{} is outside image bounds'.format(ll_x, ll_y, ur_x, ur_y))

    return utils.tile_read_utm(src,
                               tile_bounds,
                               tilesize,
                               indexes=indexes,
                               nodata=nodata,
                               alpha=alpha,
                               dst_crs=dst_crs)



def tile_utm(source, ll_x, ll_y, ur_x, ur_y, indexes=None, tilesize=256, nodata=None, alpha=None, dst_crs='epsg:4326'):
    """
    Create UTM tile from any images.

    Attributes
    ----------
    address : str
        file url or rasterio.Dataset.
    tile_x : int
        Mercator tile X index.
    tile_y : int
        Mercator tile Y index.
    tile_z : int
        Mercator tile ZOOM level.
    indexes : tuple, int, optional (default: (1, 2, 3))
        Bands indexes for the RGB combination.
    tilesize : int, optional (default: 256)
        Output image size.
    nodata: int or float, optional
        Overwrite nodata value for mask creation.
    alpha: int, optional
        Overwrite alpha band index for mask creation.


    Returns
    -------
    data : numpy ndarray
    mask: numpy array

    """

    if isinstance(source, DatasetReader):

        return tile_utm_source(source,
                               ll_x,
                               ll_y,
                               ur_x,
                               ur_y,
                               indexes=indexes,
                               tilesize=tilesize,
                               nodata=nodata,
                               alpha=alpha,
                               dst_crs=dst_crs)



    else:
        with rasterio.open(source) as src:

            return tile_utm_source(src,
                                   ll_x,
                                   ll_y,
                                   ur_x,
                                   ur_y,
                                   indexes=indexes,
                                   tilesize=tilesize,
                                   nodata=nodata,
                                   alpha=alpha,
                                   dst_crs=dst_crs)




def get_chip(address, ll_x, ll_y, xres, yres, downSampleRate):
    """ Get Chip From Image

    :param address:
    :param ll_x:
    :param ll_y:
    :param xres:
    :param yres:
    :param downSampleRate:
    :return:

    """

def calculate_anchor_points(utm_bounds, stride_size_meters=400):
    min_x = math.floor(utm_bounds[0])
    min_y = math.floor(utm_bounds[1])
    max_x = math.ceil(utm_bounds[2])
    max_y = math.ceil(utm_bounds[3])

    anchor_point_list = []
    for x in np.arange(min_x, max_x, stride_size_meters):
        for y in np.arange(min_y, max_y, stride_size_meters):
            anchor_point_list.append([x, y])


    return anchor_point_list


def calculate_cells(anchor_point_list, cell_size_meters):
    """ calculate Cells for splitting based on anchor points

    :param anchor_point_list:
    :param cell_size_meters:
    :return:
    cells_list [(minx, miny, maxx, maxy),
                ...]
    """
    cells_list = []
    for anchor_point in anchor_point_list:
        cells_list.append([anchor_point[0], anchor_point[1], anchor_point[0]+cell_size_meters, anchor_point[1]+cell_size_meters])

    return cells_list

def calculate_analysis_grid(utm_bounds, stride_size_meters=300, cell_size_meters=400):
    anchor_point_list = calculate_anchor_points(utm_bounds, stride_size_meters=stride_size_meters)

    cells_list = calculate_cells(anchor_point_list, cell_size_meters)

    return cells_list





if __name__ == '__main__':

    utmX, utmY = 658029, 4006947
    ll_x = utmX
    ur_x = utmX + 500
    ll_y = utmY
    ur_y = utmY + 500
    stride_size_meters = 300
    cell_size_meters = 400
    tile_size_pixels = 1600
    spacenetPath = "s3://spacenet-dataset/AOI_2_Vegas/srcData/rasterData/AOI_2_Vegas_MUL-PanSharpen_Cloud.tif"
    address = spacenetPath

    with rasterio.open(address) as src:

        wgs_bounds = utils.get_wgs84_bounds(src)
        utm_EPSG = utils.calculate_UTM_EPSG(wgs_bounds)
        utm_bounds = utils.get_utm_bounds(src, utm_EPSG)

        cells_list = calculate_analysis_grid(utm_bounds, stride_size_meters=stride_size_meters, cell_size_meters=cell_size_meters)

        random_cell = random.choice(cells_list)
        ll_x, ll_y, ur_x, ur_y = random_cell
        tile = tile_utm(src, ll_x, ll_y, ur_x, ur_y, indexes=None, tilesize=tile_size_pixels, nodata=None, alpha=None,
                 dst_crs=utm_EPSG)





