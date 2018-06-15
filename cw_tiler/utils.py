"""cv_tiler.utils: utility functions."""


import numpy as np
import rasterio
from rasterio.vrt import WarpedVRT
from rasterio.enums import Resampling
from rasterio.io import DatasetReader
from rasterio.warp import transform_bounds
from rio_tiler.errors import RioTilerError

from shapely.geometry import box
import statistics

from PIL import Image

# Python 2/3
try:
    from urllib.request import urlopen
except ImportError:
    from urllib2 import urlopen


def utm_getZone(longitude):
    """Calculate UTM Zone from Longitude

    Attributes:
    ___________
    longitude: float of longitude (Degrees.decimal degrees)

    Returns:
    _______
    out: int
        returns UTM Zone number
    """
    return (int(1+(longitude+180.0)/6.0))

def utm_isNorthern(latitude):
    """Calculate UTM North/South from Latitude

    Attributes:
    ___________
    latitude: float of latitude (Deg.decimal degrees)

    Returns:
    _______
    out: int
        returns UTM Zone number
    """

    if (latitude < 0.0):
        return "S"
    else:
        return "N"


def calculate_UTM_EPSG(coords, epsgStart={"N":"EPSG:326", "S":"EPSG:327"}):
    """Calculate UTM North/South from Latitude

    Attributes:
    ___________
    coords: list, [longitude, latitude] or [min_longitude, min_latitude, max_lognitude, max_latitude
    epsgStart: dict, dictionary for precursor for UTM Zone EPSG (Default is WGS84)

    Returns:
    _______
    out: str
        returns UTM Zone EPSG
    """
    if len(coords) == 2:
        longitude, latitude = coords
    elif len(coords) == 4:
        longitude = statistics.mean([coords[0], coords[2]])
        latitude = statistics.mean([coords[1], coords[3]])

    utm_zone = utm_getZone(longitude)

    utm_direction = utm_isNorthern(latitude)


    return "{}{}".format(epsgStart[utm_direction], str(utm_zone.zfill(2)))

def tile_read_utm(source, bounds, tilesize, indexes=[1], nodata=None, alpha=None, dst_crs='EPSG:3857'):
    """Read data and mask

    Attributes
    ----------
    source : str or rasterio.io.DatasetReader
        input file path or rasterio.io.DatasetReader object
    bounds : tuple, (w, s, e, n) bounds in dst_csrs
    tilesize : Output image size
    indexes : list of ints or a single int, optional, (default: 1)
        If `indexes` is a list, the result is a 3D array, but is
        a 2D array if it is a band index number.
    nodata: int or float, optional (defaults: None)
    alpha: int, optional (defaults: None)
        Force alphaband if not present in the dataset metadata

    dst_crs: str, optional (defaults: "EPSG:3857" (Web Mercator)
        Determine output path


    Returns
    -------
    out : array, int
        returns pixel value.
    """
    w, s, e, n = bounds

    if alpha is not None and nodata is not None:
        raise RioTilerError('cannot pass alpha and nodata option')

    if isinstance(indexes, int):
        indexes = [indexes]

    out_shape = (len(indexes), tilesize, tilesize)

    vrt_params = dict(
        dst_crs=dst_crs,
        resampling=Resampling.bilinear,
        src_nodata=nodata,
        dst_nodata=nodata)

    if isinstance(source, DatasetReader):
        with WarpedVRT(source, **vrt_params) as vrt:
            window = vrt.window(w, s, e, n, precision=21)
            data = vrt.read(window=window,
                            boundless=True,
                            resampling=Resampling.bilinear,
                            out_shape=out_shape,
                            indexes=indexes)

            if nodata is not None:
                mask = np.all(data != nodata, axis=0).astype(np.uint8) * 255
            elif alpha is not None:
                mask = vrt.read(alpha, window=window,
                                out_shape=(tilesize, tilesize),
                                boundless=True,
                                resampling=Resampling.bilinear)
            else:
                mask = vrt.read_masks(1, window=window,
                                      out_shape=(tilesize, tilesize),
                                      boundless=True,
                                      resampling=Resampling.bilinear)
    else:
        with rasterio.open(source) as src:
            with WarpedVRT(src, **vrt_params) as vrt:
                window = vrt.window(w, s, e, n, precision=21)
                data = vrt.read(window=window,
                                boundless=True,
                                resampling=Resampling.bilinear,
                                out_shape=out_shape,
                                indexes=indexes)

                if nodata is not None:
                    mask = np.all(data != nodata, axis=0).astype(np.uint8) * 255
                elif alpha is not None:
                    mask = vrt.read(alpha, window=window,
                                    out_shape=(tilesize, tilesize),
                                    boundless=True,
                                    resampling=Resampling.bilinear)
                else:
                    mask = vrt.read_masks(1, window=window,
                                          out_shape=(tilesize, tilesize),
                                          boundless=True,
                                          resampling=Resampling.bilinear)

    return data, mask

def tile_exists_utm(boundsSrc, boundsTile):
    """"Check if suggested tile is within bounds

    'bounds = (w, s, e, n)'
    'box( minx, miny, maxx, maxy)'

    :param bounds:

    :return:
    """


    boundsSrcBox = box(*boundsSrc)
    boundsTileBox = box(*boundsTile)

    return boundsSrcBox.intersects(boundsTileBox)




def get_wgs84_bounds(source):
    if isinstance(source, DatasetReader):
        src = source

        wgs_bounds = transform_bounds(*[src.crs, 'epsg:4326'] + list(src.bounds), densify_pts=21)

    else:
        with rasterio.open(source) as src:

            wgs_bounds = transform_bounds(*[src.crs, 'epsg:4326'] + list(src.bounds), densify_pts=21)

    return wgs_bounds


def get_utm_bounds(source, utm_EPSG):
    if isinstance(source, DatasetReader):
        src = source

        utm_bounds = transform_bounds(*[src.crs, utm_EPSG] + list(src.bounds), densify_pts=21)

    else:
        with rasterio.open(source) as src:

            utm_bounds = transform_bounds(*[src.crs, utm_EPSG] + list(src.bounds), densify_pts=21)

    return utm_bounds



