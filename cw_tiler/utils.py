"""cw_tiler.utils: utility functions."""


import numpy as np
import rasterio
from rasterio.vrt import WarpedVRT
from rasterio.enums import Resampling
from rasterio.io import DatasetReader
from rasterio.warp import transform_bounds
from rio_tiler.errors import RioTilerError
from rasterio import windows
from rasterio import transform
from shapely.geometry import box
import statistics

# Python 2/3
try:
    from urllib.request import urlopen
except ImportError:
    from urllib2 import urlopen


def utm_getZone(longitude):
    """Calculate UTM Zone from Longitude.

    Attributes:
    -----------
    longitude: float of longitude (Degrees.decimal degrees)

    Returns:
    -------
    out: int
        returns UTM Zone number.
    """

    return (int(1+(longitude+180.0)/6.0))


def utm_isNorthern(latitude):
    """Calculate UTM North/South from Latitude

    Attributes:
    -----------
    latitude: float of latitude (Deg.decimal degrees)

    Returns:
    -------
    out: int
        returns UTM Zone number
    """

    return (latitude > 0.0)


def calculate_UTM_crs(coords):
    """Calculate UTM Projection String

    Attributes:
    -----------
    coords: list, [longitude, latitude] or [min_longitude, min_latitude,
                                            max_longitude, max_latitude]

    Returns:
    -------
    out: str
        returns pyProj string
    """

    if len(coords) == 2:
        longitude, latitude = coords
    elif len(coords) == 4:
        longitude = statistics.mean([coords[0], coords[2]])
        latitude = statistics.mean([coords[1], coords[3]])

    utm_zone = utm_getZone(longitude)

    utm_isNorthern(latitude)

    if utm_isNorthern(latitude):
        direction_indicator = "+north"
    else:
        direction_indicator = "+south"

    utm_crs = "+proj=utm +zone={} {} +ellps=WGS84 +datum=WGS84 +units=m +no_defs".format(utm_zone,
                                                                                         direction_indicator)

    return utm_crs


def get_utm_vrt(source, crs='EPSG:3857', resampling=Resampling.bilinear,
                src_nodata=None, dst_nodata=None):
    """Get a :py:class:`rasterio.vrt.WarpedVRT` projection of a dataset.

    Attributes:
    -----------
    source : rasterio ``dataset`` instance
        The dataset to virtually warp using :py:class:`rasterio.vrt.WarpedVRT`.
    crs : :py:class:`rasterio.crs.CRS`, optional
        Coordinate reference system for the VRT. Defaults to 'EPSG:3857'
        (Web Mercator).
    resampling : :py:class:`rasterio.enums.Resampling` method, optional
        Resampling method to use. Defaults to
        ``rasterio.enums.Resampling.bilinear``. Alternatives include
        ``rasterio.enums.Resampling.average``,
        ``rasterio.enums.Resampling.cubic``, and others. See docs for
        :py:class:`rasterio.enums.Resampling` for more information.
    src_nodata : ``int`` or ``float``, optional
        Source nodata value which will be ignored for interpolation. Defaults
        to ``None`` (all data used in interpolation).
    dst_nodata : ``int`` or ``float``, optional
        Destination nodata value which will be ignored for interpolation.
        Defaults to ``None``, in which case the value of ``src_nodata`` will be
        used if provided, or ``0`` otherwise.

    Returns:
    --------
    A :py:class:`rasterio.vrt.WarpedVRT` instance with the transformation.

    """

    vrt_params = dict(
        crs=crs,
        resampling=Resampling.bilinear,
        src_nodata=src_nodata,
        dst_nodata=dst_nodata)

    return WarpedVRT(source, **vrt_params)


def get_utm_vrt_profile(source, crs='EPSG:3857',
                        resampling=Resampling.bilinear,
                        src_nodata=None, dst_nodata=None):
    """Get a :py:class:`rasterio.profiles.Profile` for projection of a VRT.

    Attributes:
    -----------
    source : rasterio ``dataset`` instance
        The dataset to virtually warp using :py:class:`rasterio.vrt.WarpedVRT`.
    crs : :py:class:`rasterio.crs.CRS`, optional
        Coordinate reference system for the VRT. Defaults to 'EPSG:3857'
        (Web Mercator).
    resampling : :py:class:`rasterio.enums.Resampling` method, optional
        Resampling method to use. Defaults to
        ``rasterio.enums.Resampling.bilinear``. Alternatives include
        ``rasterio.enums.Resampling.average``,
        ``rasterio.enums.Resampling.cubic``, and others. See docs for
        :py:class:`rasterio.enums.Resampling` for more information.
    src_nodata : ``int`` or ``float``, optional
        Source nodata value which will be ignored for interpolation. Defaults
        to ``None`` (all data used in interpolation).
    dst_nodata : ``int`` or ``float``, optional
        Destination nodata value which will be ignored for interpolation.
        Defaults to ``None``, in which case the value of ``src_nodata`` will be
        used if provided, or ``0`` otherwise.

    Returns:
    --------
    A :py:class:`rasterio.profiles.Profile` instance with the transformation
    applied.

    """

    with get_utm_vrt(source, crs=crs, resampling=resampling,
                     src_nodata=src_nodata, dst_nodata=dst_nodata) as vrt:
        vrt_profile = vrt.profile

    return vrt_profile


def tile_read_utm(source, bounds, tilesize, indexes=[1], nodata=None,
                  alpha=None, dst_crs='EPSG:3857', verbose=False,
                  boundless=False):
    """Read data and mask.

    Attributes
    ----------
    source : ``str`` or :py:class:`rasterio.io.DatasetReader`
        input file path or rasterio.io.DatasetReader object.
    bounds : ``(w, s, e, n)`` tuple
        bounds in ``dst_crs``.
    tilesize : Output image size
    indexes : ``list`` of ``int``s or ``int``, optional
        If ``indexes`` is a ``list``, the result is a 3D array, but is
        a 2D array if it is a band index number. Defaults to ``1``.
    nodata: int or float, optional
        nodata value to use in :py:class:`rasterio.vrt.WarpedVRT`.
        Defaults to ``None`` (use all data in warping).
    alpha: ``int``, optional
        Force alphaband if not present in the dataset metadata. Defaults to
        ``None``.
    dst_crs: ``str``, optional
        Destination coordinate reference system. Defaults to "EPSG:3857"
        (Web Mercator)

    Returns
    -------
    ``np.array`` of ``int``s with pixel values.

    """
    w, s, e, n = bounds
    if alpha is not None and nodata is not None:
        raise RioTilerError('cannot pass alpha and nodata option')

    if isinstance(indexes, int):
        indexes = [indexes]
    (e - w) / tilesize
    out_shape = (len(indexes), tilesize, tilesize)
    if verbose:
        print(dst_crs)
    vrt_params = dict(
        crs=dst_crs,
        resampling=Resampling.bilinear,
        src_nodata=nodata,
        dst_nodata=nodata)

    if isinstance(source, DatasetReader):
        with WarpedVRT(source, **vrt_params) as vrt:
            window = vrt.window(w, s, e, n, precision=21)
            if verbose:
                print(window)
            #window_transform = windows.transform(window, vrt.transform)
            window_transform = transform.from_bounds(w,s,e,n, tilesize, tilesize)

            data = vrt.read(window=window,
                                resampling=Resampling.bilinear,
                                out_shape=out_shape,
                                indexes=indexes,
                                boundless=boundless)
            if False: #except:
                print(bounds)
                print(window)
                print(out_shape)
                print(indexes)
                print(boundless)
                print(window_transform)

            if nodata is not None:
                mask = np.all(data != nodata, axis=0).astype(np.uint8) * 255
            elif alpha is not None:
                mask = vrt.read(alpha, window=window,
                                out_shape=(tilesize, tilesize),
                                boundless=boundless,
                                resampling=Resampling.bilinear)
            else:
                mask = vrt.read_masks(1, window=window,
                                      out_shape=(tilesize, tilesize),
                                      boundless=boundless,
                                      resampling=Resampling.bilinear)
    else:
        with rasterio.open(source) as src:
            with WarpedVRT(src, **vrt_params) as vrt:
                window = vrt.window(w, s, e, n, precision=21)
                window_transform = windows.transform(window, vrt.transform)
                window_transform = transform.from_bounds(w, s, e, n, tilesize, tilesize)

                data = vrt.read(window=window,
                                boundless=boundless,
                                resampling=Resampling.bilinear,
                                out_shape=out_shape,
                                indexes=indexes)

                if nodata is not None:
                    mask = np.all(data != nodata, axis=0).astype(np.uint8) * 255
                elif alpha is not None:
                    mask = vrt.read(alpha, window=window,
                                    out_shape=(tilesize, tilesize),
                                    boundless=boundless,
                                    resampling=Resampling.bilinear)
                else:
                    mask = vrt.read_masks(1, window=window,
                                          out_shape=(tilesize, tilesize),
                                          boundless=boundless,
                                          resampling=Resampling.bilinear)

    return data, mask, window, window_transform

def tile_exists_utm(boundsSrc, boundsTile):
    """"Check if suggested tile is within bounds.

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
