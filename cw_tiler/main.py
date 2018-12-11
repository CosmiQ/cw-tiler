import rasterio
from rasterio.warp import transform_bounds
from rasterio.io import DatasetReader
import math
from rio_tiler.errors import TileOutsideBounds
from cw_tiler import utils
import numpy as np


def tile_utm_source(src, ll_x, ll_y, ur_x, ur_y, indexes=None, tilesize=256,
                    nodata=None, alpha=None, dst_crs='epsg:4326'):
    """
    Create UTM tile from any images.

    Arguments
    ---------
    source : :py:class:`rasterio.Dataset`
    tile_x : int
        Mercator tile X index.
    tile_y : int
        Mercator tile Y index.
    tile_z : int
        Mercator tile ZOOM level.
    indexes : tuple, int, optional
        Bands indexes for the RGB combination. Defaults to (1, 2, 3).
    tilesize : int, optional (default: 256)
        Output image size.
    nodata : int or float, optional
        Overwrite nodata value for mask creation.
    alpha : int, optional
        Overwrite alpha band index for mask creation.
    dst_crs : str, optional
        Coordinate reference system for output. Defaults to ``"epsg:4326"``.

    Returns
    -------
    data : :py:class:`np.ndarray`
    mask : :py:class:`np.ndarray`

    """

    wgs_bounds = transform_bounds(
        *[src.crs, dst_crs] + list(src.bounds), densify_pts=21)

    indexes = indexes if indexes is not None else src.indexes
    tile_bounds = (ll_x, ll_y, ur_x, ur_y)
    if not utils.tile_exists_utm(wgs_bounds, tile_bounds):
        raise TileOutsideBounds(
            'Tile {}/{}/{}/{} is outside image bounds'.format(tile_bounds)

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


def get_chip(source, ll_x, ll_y, gsd,
             utm_crs=[],
             indexes=None,
             tile_size_pixels=512,
             nodata=None,
             alpha=None):
    """ Get Chip From Image Address"

    :param address:
    :param ll_x:
    :param ll_y:
    :param xres:
    :param yres:

    :return:

    """

    ur_x = ll_x + gsd * tile_size_pixels
    ur_y = ll_y + gsd * tile_size_pixels

    if isinstance(source, DatasetReader):

        if not utm_crs:
            wgs_bounds = utils.get_wgs84_bounds(source)
            utm_crs = utils.calculate_UTM_crs(wgs_bounds)

        return tile_utm(source, ll_x, ll_y, ur_x, ur_y,
                        indexes=indexes,
                        tilesize=tile_size_pixels,
                        nodata=nodata,
                        alpha=alpha,
                        dst_crs=utm_crs)


    else:
        with rasterio.open(source) as src:

            wgs_bounds = utils.get_wgs84_bounds(src)
            utm_crs = utils.calculate_UTM_crs(wgs_bounds)

            return tile_utm(source, ll_x, ll_y, ur_x, ur_y,
                            indexes=indexes,
                            tilesize=tile_size_pixels,
                            nodata=nodata,
                            alpha=alpha,
                            dst_crs=utm_crs)


def calculate_anchor_points(utm_bounds, stride_size_meters=400, extend=False, quad_space=False):
    if extend:
        min_x = math.floor(utm_bounds[0])
        min_y = math.floor(utm_bounds[1])
        max_x = math.ceil(utm_bounds[2])
        max_y = math.ceil(utm_bounds[3])
    else:
        print("NoExtend")
        print('UTM_Bounds: {}'.format(utm_bounds))
        min_x = math.ceil(utm_bounds[0])
        min_y = math.ceil(utm_bounds[1])
        max_x = math.floor(utm_bounds[2])
        max_y = math.floor(utm_bounds[3])


    anchor_point_list = []
    if quad_space:
        print("quad_space")
        row_cell = np.asarray([[0, 1],[2,3]])
        anchor_point_list_dict={0: [],
                               1: [],
                               2:[],
                               3:[]
                               }
    else:
        anchor_point_list_dict={0:[]}

    for rowidx, x in enumerate(np.arange(min_x, max_x, stride_size_meters)):
        for colidx, y in enumerate(np.arange(min_y, max_y, stride_size_meters)):

            if quad_space:
                anchor_point_list_dict[row_cell[rowidx % 2, colidx % 2]].append([x,y])
            else:
                anchor_point_list_dict[0].append([x, y])

    return anchor_point_list_dict


def calculate_cells(anchor_point_list_dict, cell_size_meters, utm_bounds=[]):
    """ calculate Cells for splitting based on anchor points

    :param anchor_point_list:
    :param cell_size_meters:
    :return:
    cells_list [(minx, miny, maxx, maxy),
                ...]
    """
    cells_list_dict = {}
    for anchor_point_list_id, anchor_point_list in anchor_point_list_dict.items():
        cells_list = []
        for anchor_point in anchor_point_list:

            if utm_bounds:
                if (anchor_point[0] + cell_size_meters < utm_bounds[2]) and (anchor_point[1] + cell_size_meters < utm_bounds[3]):
                    cells_list.append(
                        [anchor_point[0], anchor_point[1], anchor_point[0] + cell_size_meters, anchor_point[1] + cell_size_meters])


                else:
                    pass

        cells_list_dict[anchor_point_list_id] = cells_list



    return cells_list_dict


def calculate_analysis_grid(utm_bounds, stride_size_meters=300, cell_size_meters=400, quad_space=False, snapToGrid=False):

    anchor_point_list_dict = calculate_anchor_points(utm_bounds, stride_size_meters=stride_size_meters, quad_space=quad_space)

    cells_list_dict = calculate_cells(anchor_point_list_dict, cell_size_meters, utm_bounds=utm_bounds)

    return cells_list_dict





if __name__ == '__main__':
    utmX, utmY = 658029, 4006947
    cll_x = utmX
    cur_x = utmX + 500
    cll_y = utmY
    cur_y = utmY + 500
    stride_size_meters = 300
    cell_size_meters = 400
    ctile_size_pixels = 1600
    spacenetPath = "s3://spacenet-dataset/AOI_2_Vegas/srcData/rasterData/AOI_2_Vegas_MUL-PanSharpen_Cloud.tif"
    address = spacenetPath

    with rasterio.open(address) as src:
        cwgs_bounds = utils.get_wgs84_bounds(src)
        cutm_crs = utils.calculate_UTM_crs(cwgs_bounds)
        cutm_bounds = utils.get_utm_bounds(src, cutm_crs)

        #ccells_list = calculate_analysis_grid(cutm_bounds, stride_size_meters=stride_size_meters,
        #                                     cell_size_meters=cell_size_meters)

        #random_cell = random.choice(ccells_list)
        #cll_x, cll_y, cur_x, cur_y = random_cell
        tile, mask, window, window_transform = tile_utm(src, cll_x, cll_y, cur_x, cur_y, indexes=None, tilesize=ctile_size_pixels, nodata=None, alpha=None,
                        dst_crs=cutm_crs)
