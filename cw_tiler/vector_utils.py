## Note, for mac osx compatability import something from shapely.geometry before importing fiona or geopandas
## https://github.com/Toblerity/Shapely/issues/553
from shapely import geometry
from shapely.geometry import box
###
import geopandas as gpd
from spacenet_utilties import geoTools
from rasterio import features
from rasterio import Affine
import numpy as np


def read_vector_file(geoFileName):
    """read in all Fiona Supported Files into geo DataFrame"""
    gdf = gpd.read_file(geoFileName)

    return gdf

def transformToUTM(gdf, utm_crs, estimate=True, calculate_sindex=True):


    gdf = gdf.to_crs(utm_crs)

    if calculate_sindex:
        sindex = gdf.sindex


    return gdf


def search_gdf_bounds(gdf, tile_bounds):
    tile_polygon = box(tile_bounds)

    smallGdf = search_gdf_polygon(gdf, tile_polygon)

    return smallGdf


def search_gdf_polygon(gdf, tile_polygon):

    spatial_index = gdf.sindex
    possible_matches_index = list(spatial_index.intersection(tile_polygon.bounds))
    possible_matches = gdf.iloc[possible_matches_index]
    precise_matches = possible_matches[possible_matches.intersects(tile_polygon)]

    if precise_matches.empty:
        precise_matches=gpd.GeoDataFrame(geometry=[])
    
    return precise_matches

def vector_tile_utm(gdf, tile_bounds, min_partial_perc=0.1, geom_type="Polygon", use_sindex=True):

    tile_polygon = box(*tile_bounds)
    small_gdf = clip_gdf(gdf, tile_polygon,
                         min_partial_perc=min_partial_perc,
                         geom_type=geom_type
                         )

    return small_gdf



def getCenterOfGeoFile(gdf, estimate=True):

    #TODO implement calculate UTM from gdf  see osmnx implementation

    pass


def clip_gdf(geodf, poly_to_cut, min_partial_perc=0.0, geom_type="Polygon", use_sindex=True):
    """clip geoDDF to a provided polygon.  Will add four (4) for additional columns
    origarea.  If the geoDF is a set of Polygons, This is the original area of the polygons
    origlen. If the geoDF is a set of LineStrings, this is the original length of the polygons
    partialDec. This is the % of the polygon or line that was truncated.  So NewArea/OrigArea.
                Can be used to filter out on very small slivers
    truncated.  Binary Flag that specified if the polygon or line string has been modified
                1=Truncated, 0=Not modified

    params:
    ______
    geoDF, a geopandas Dataframe
    polyToCut: shapely polygon to cut geodataFrame By
    minpartialPerc: Defined as the minimum % of a polygon that should be included
    geom_type: is the geo Data Frame a polygon or LineString



    returns clippedGeoDF


    """

    # check if geoDF has origAreaField

    if use_sindex:
        gdf = search_gdf_polygon(geodf, poly_to_cut)
    else:
        gdf = geodf.copy()

    
    if geom_type == "LineString":

        if 'origarea' in gdf.columns:
            pass
        else:
            gdf['origarea'] = 0

        if 'origlen' in gdf.columns:
            pass
        else:
            gdf['origlen'] = gdf.length

    else:
        if 'origarea' in gdf.columns:
            pass
        else:
            gdf['origarea'] = gdf.area

        if 'origlen' in gdf.columns:
            pass
        else:
            gdf['origlen'] = 0

    #TODO must implement different case for lines and for spatialIndex  (Assume RTree is already performed)


    cutGeoDF = gdf.copy()
    cutGeoDF.geometry=gdf.intersection(poly_to_cut)

    if geom_type== 'Polygon':
        cutGeoDF['partialDec'] = cutGeoDF.area / cutGeoDF['origarea']
        cutGeoDF = cutGeoDF.loc[cutGeoDF['partialDec'] > min_partial_perc].copy()
        cutGeoDF['truncated'] = (cutGeoDF['partialDec']!=1.0).astype(int)
    else:
        #
        cutGeoDF = cutGeoDF[cutGeoDF.geom_type != "GeometryCollection"]
        cutGeoDF['partialDec']=1
        cutGeoDF['truncated']=0

    return cutGeoDF




def rasterize_gdf(gdf, burn_value=1, src_shape=None, src_transform=Affine(1.0, 0.0, 0.0, 0.0, 1.0, 0.0)):
    
    if not gdf.empty:
        img = features.rasterize(
            ((geom, burn_value) for geom in gdf.geometry),
            out_shape=src_shape,
            transform=src_transform,

        )
    else:
        img = np.zeros(src_shape).astype(np.uint8)
        

    return img

def gdf_to_coco(gdf, image_dict, annotation_list=[]):
    annodation_dict_base = {}
    annodation_dict_base.update({'category_id': 1},
                           {'ignore': 0},
                           {'iscrowd': 0},
                            {'image_id': image_dict['id']}
                           )

    for objid, geom in enumerate(gdf.geometry):
        tmp_annotation = annodation_dict_base.copy()
        tmp_annotation.update({'id': objid+1})

        bbox, area = create_bbox(geom)
        tmp_annotation.update({'bbox': bbox})
        tmp_annotation.update({'area': area})

        segment = create_segmentation(geom)
        tmp_annotation.update({'segmentation': segment})

        annotation_list.append(tmp_annotation)

    return annotation_list


def create_image_dict(file_name, image_id, src_shape):

    image_dict = {'file_name': file_name,
                  'id': image_id,
                  'height': src_shape[1],
                  'width': src_shape[0]
                  }

    return image_dict













def create_bbox(geom):

    pass

def create_segmentation(geom):

    pass







