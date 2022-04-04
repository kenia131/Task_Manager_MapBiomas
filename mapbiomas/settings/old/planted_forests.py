import ee

from mapbiomas import processors
from rsgee.band import Band
from rsgee.db.models import TaskTypes
from rsgee.imagemaker import ImageMaker
from rsgee.provider import Provider
from rsgee.reducer import Reducer

YEARS = [2019]

# ********** COLLECTION SETTINGS ****************+
COLLECTION = 'LANDSAT/LC08/C01/T1_TOA'
COLLECTION_PREFIX = 'L8_T1_TOA'
COLLECTION_PROVIDER = Provider.LC08

# *********  FUSION TABLE SETTINGS
FEATURE_COLLECTION = 'users/agrosatelite_mapbiomas/COLECAO_4/GRIDS/BRASIL_COMPLETO'
FEATURE_WRS = 'PATHROW'
FEATURE_WRS_SELECTED = {
    'AND': {'ACP_WRS': 1},
}

# ********** GENERAL SETTINGS *******************
GENERATOR_CLASS = processors.PlantedForestGenerator
GENERATION_BANDS = [Band.GREEN, Band.RED, Band.NIR, Band.SWIR1, Band.SWIR2,
                    Band.NDVI, Band.LAI]
GENERATION_EXTRA_BANDS = []
GENERATION_REDUCERS = [Reducer.QMO]
GENERATION_VARIABLES = [
    'ACP_WET1_GREEN_qmo', 'ACP_WET1_RED_qmo', 'ACP_WET1_NIR_qmo',
    'ACP_WET1_SWIR1_qmo', 'ACP_WET1_SWIR2_qmo', 'ACP_WET1_NDVI_qmo',
    'ACP_WET1_LAI_qmo',
    'ACP_WET2_GREEN_qmo', 'ACP_WET2_RED_qmo', 'ACP_WET2_NIR_qmo',
    'ACP_WET2_SWIR1_qmo', 'ACP_WET2_SWIR2_qmo', 'ACP_WET2_NDVI_qmo',
    'ACP_WET2_LAI_qmo',
    'ACP_DRY1_GREEN_qmo', 'ACP_DRY1_RED_qmo', 'ACP_DRY1_NIR_qmo',
    'ACP_DRY1_SWIR1_qmo', 'ACP_DRY1_SWIR2_qmo', 'ACP_DRY1_NDVI_qmo',
    'ACP_DRY1_LAI_qmo',
    'ACP_DRY2_GREEN_qmo', 'ACP_DRY2_RED_qmo', 'ACP_DRY2_NIR_qmo',
    'ACP_DRY2_SWIR1_qmo', 'ACP_DRY2_SWIR2_qmo', 'ACP_DRY2_NDVI_qmo',
    'ACP_DRY2_LAI_qmo',
    'ACP_DRY3_GREEN_qmo', 'ACP_DRY3_RED_qmo', 'ACP_DRY3_NIR_qmo',
    'ACP_DRY3_SWIR1_qmo', 'ACP_DRY3_SWIR2_qmo', 'ACP_DRY3_NDVI_qmo',
    'ACP_DRY3_LAI_qmo',
    'ACP_WET3_GREEN_qmo', 'ACP_WET3_RED_qmo', 'ACP_WET3_NIR_qmo',
    'ACP_WET3_SWIR1_qmo', 'ACP_WET3_SWIR2_qmo', 'ACP_WET3_NDVI_qmo',
    'ACP_WET3_LAI_qmo']
GENERATION_EXTRA_VARIABLES = []
GENERATION_PERIODS = ['ACP_WET1', 'ACP_WET2', 'ACP_DRY1', 'ACP_DRY2',
                      'ACP_DRY3', 'ACP_WET3']
GENERATION_OFFSET = 2
GENERATION_CLIP_GEOMETRY = True
GENERATION_APPLY_MASK = True
GENERATION_APPLY_BRDF = True
GENERATION_TYPE = 'int16'

# ********** CLASSIFICATION SETTINGS ***************

CLASSIFIER_CLASS = processors.Classifier
CLASSIFICATION_TRAIN = 'users/agrosatelite_mapbiomas/COLECAO_4/REFERENCE_MAPS/PLANTED_FORESTS/USED'
CLASSIFICATION_TREES = 100
CLASSIFICATION_POINTS = 10000
CLASSIFICATION_BUFFER = 50000

# ********** EXPORT SETTINGS **********************

EXPORT_CLASS = ee.batch.Export.image.toCloudStorage
EXPORT_TASKS = [TaskTypes.GENERATION, TaskTypes.CLASSIFICATION]
EXPORT_TYPES = [ImageMaker.IMAGE]
EXPORT_BUCKET = 'agrosatelite-mapbiomas'
EXPORT_DIRECTORY = 'mapbiomas_c4/classification/planted_forest/2019'
EXPORT_MAX_TASKS = 3
EXPORT_INTERVAL = 30
EXPORT_MAX_ERRORS = 1
EXPORT_BUFFER = -4200
EXPORT_SCALE = 30
EXPORT_SCALES = {
    10000: [Band.GREEN, Band.RED, Band.NIR, Band.SWIR1, Band.SWIR2, Band.NDVI,
            Band.LAI],
}
EXPORT_MAX_PIXELS = 1.0E13

# *********** EXTRA SETTINGS

QUALITY_MOSAIC = Band.NDVI
MAX_IMAGES = 5000