import ee

from mapbiomas import processors
from rsgee.band import Band
from rsgee.db.models import TaskTypes
from rsgee.provider import Provider
from rsgee.reducer import Reducer

YEARS = [2017]

# ********** SERVICE ACCOUNT  *****************

# SERVICE_ACCOUNT = ''
# SERVICE_KEY = ''

# ********** COLLECTION SETTINGS ****************

COLLECTION_PREFIX = 'BLARD'
COLLECTION_PROVIDER = Provider.BLARD

# *********  FUSION TABLE SETTINGS

FEATURE_COLLECTION = 'users/agrosatelite_mapbiomas/COLECAO_5/GRIDS/BRASIL_COMPLETO'
FEATURE_WRS_SELECTED = {
    'AND': {'SB_WRS': 1},
    # 'OR': {'SC': 1, 'PR': 1, 'RS': 1}
}
FEATURE_WRS = 'PATHROW'
# sample these WRS after
FEATURE_WRS_FILTER = [225076, 224075]

# ********** GENERAL SETTINGS *******************

GENERATOR_CLASS = processors.SoybeanGenerator
GENERATION_BANDS = [Band.GREEN, Band.RED, Band.NIR, Band.SWIR1, Band.SWIR2,
                    Band.TIR1, Band.EVI2, Band.NDWI, Band.CAI]
GENERATION_EXTRA_BANDS = [Band.CEI]
GENERATION_REDUCERS = [Reducer.QMO, Reducer.MAX, Reducer.MIN, Reducer.MEDIAN,
                       Reducer.STDV, Reducer.MEAN]
GENERATION_VARIABLES = [
    'AC_WET_NIR_qmo', 'AC_WET_SWIR1_qmo', 'AC_WET_EVI2_qmo',
    'AC_WET_RED_max', 'AC_WET_SWIR1_max', 'AC_WET_SWIR2_max', 'AC_WET_TIR1_max', 'AC_WET_EVI2_max', 'AC_WET_NDWI_max' , 'AC_WET_CAI_max',
    'AC_WET_GREEN_min', 'AC_WET_SWIR1_min', 'AC_WET_EVI2_min', 'AC_WET_NDWI_min', 'AC_WET_CAI_min',
    'AC_WET_GREEN_median', 'AC_WET_RED_median', 'AC_WET_SWIR1_median', 'AC_WET_SWIR2_median', 'AC_WET_NDWI_median', 'AC_WET_CAI_median',
    'AC_WET_RED_stdDev', 'AC_WET_SWIR1_stdDev', 'AC_WET_SWIR2_stdDev', 'AC_WET_TIR1_stdDev', 'AC_WET_EVI2_stdDev', 'AC_WET_NDWI_stdDev', 'AC_WET_CAI_stdDev',
    'AC_DRY_NDWI_qmo', 'AC_DRY_CAI_qmo',
    'AC_DRY_RED_max', 'AC_DRY_SWIR1_max', 'AC_DRY_SWIR2_max', 'AC_DRY_NDWI_max', 'AC_DRY_CAI_max',
    'AC_DRY_RED_min', 'AC_DRY_SWIR2_min', 'AC_DRY_EVI2_min', 'AC_DRY_NDWI_min', 'AC_DRY_CAI_min',
    'AC_DRY_GREEN_median', 'AC_DRY_RED_median', 'AC_DRY_SWIR1_median', 'AC_DRY_SWIR2_median', 'AC_DRY_EVI2_median','AC_DRY_NDWI_median',
    'AC_DRY_SWIR1_stdDev', 'AC_DRY_NDWI_stdDev',
    'SB_WET_M1_RED_mean', 'SB_WET_M1_NIR_mean', 'SB_WET_M1_SWIR1_mean', 'SB_WET_M1_SWIR2_mean', 'SB_WET_M1_NDWI_mean', 'SB_WET_M1_EVI2_mean',
    'SB_WET_M2_RED_mean', 'SB_WET_M2_NIR_mean', 'SB_WET_M2_SWIR1_mean', 'SB_WET_M2_SWIR2_mean', 'SB_WET_M2_NDWI_mean', 'SB_WET_M2_EVI2_mean',
    'SB_WET_M3_RED_mean', 'SB_WET_M3_NIR_mean', 'SB_WET_M3_SWIR1_mean', 'SB_WET_M3_SWIR2_mean', 'SB_WET_M3_NDWI_mean', 'SB_WET_M3_EVI2_mean',
    'SB_WET_M4_RED_mean', 'SB_WET_M4_NIR_mean', 'SB_WET_M4_SWIR1_mean', 'SB_WET_M4_SWIR2_mean', 'SB_WET_M4_NDWI_mean', 'SB_WET_M4_EVI2_mean',
    'SB_WET_M5_RED_mean', 'SB_WET_M5_NIR_mean', 'SB_WET_M5_SWIR1_mean', 'SB_WET_M5_SWIR2_mean', 'SB_WET_M5_NDWI_mean', 'SB_WET_M5_EVI2_mean',
    'SB_WET_FT3_RED_median', 'SB_WET_FT3_NIR_median', 'SB_WET_FT3_SWIR1_median', 'SB_WET_FT3_SWIR2_median', 'SB_WET_FT3_NDWI_median', 'SB_WET_FT3_EVI2_median',
    'SB_WET_LT3_RED_median', 'SB_WET_LT3_NIR_median', 'SB_WET_LT3_SWIR1_median', 'SB_WET_LT3_SWIR2_median', 'SB_WET_LT3_NDWI_median', 'SB_WET_LT3_EVI2_median',
    'SB_WET_FT3_RED_mean', 'SB_WET_FT3_NIR_mean', 'SB_WET_FT3_SWIR1_mean', 'SB_WET_FT3_SWIR2_mean', 'SB_WET_FT3_NDWI_mean', 'SB_WET_FT3_EVI2_mean',
    'SB_WET_LT3_RED_mean', 'SB_WET_LT3_NIR_mean', 'SB_WET_LT3_SWIR1_mean', 'SB_WET_LT3_SWIR2_mean', 'SB_WET_LT3_NDWI_mean', 'SB_WET_LT3_EVI2_mean'
    ]

GENERATION_EXTRA_VARIABLES = ['ANNUAL_NIR_cei',
                              'ANNUAL_EVI2_cei',
                              'ANNUAL_NDWI_cei']

GENERATION_PERIODS = [
    'AC_WET', 'AC_DRY',
    'SB_WET_M1', 'SB_WET_M2', 'SB_WET_M3', 'SB_WET_M4', 'SB_WET_M5',
    'SB_WET_FT3', 'SB_WET_LT3'
    ]
GENERATION_EXTRA_PERIODS = ['ANNUAL']
GENERATION_OFFSET = 1
GENERATION_CLIP_GEOMETRY = True
GENERATION_APPLY_MASK = True
GENERATION_APPLY_BRDF = True
GENERATION_TYPE = 'int16'

# ********** CLASSIFICATION SETTINGS **************

CLASSIFIER_CLASS = processors.BLARDClassifier
CLASSIFICATION_TRAIN = 'users/agrosatelite_mapbiomas/COLECAO_5/REFERENCE_MAPS/SOYBEAN/GLAD_SOYBEAN_STABLE_2010_2019'
CLASSIFICATION_TREES = 100
CLASSIFICATION_POINTS = 10000
CLASSIFICATION_BUFFER = 100000

# ********** SAMPLING SETTINGS *******************
SAMPLER_CLASS = processors.SoybeanStratifiedSampler
SAMPLING_PROPORTIONS = 'users/agrosatelite_mapbiomas/COLECAO_5/REFERENCE_MAPS/SOYBEAN/GLAD'

# ********** EXPORT SETTINGS **********************

EXPORT_CLASS = ee.batch.Export.table.toDrive
EXPORT_TASKS = [
    TaskTypes.GENERATION,
    TaskTypes.SAMPLING
]
EXPORT_TYPES = []
EXPORT_BUCKET = ''
EXPORT_ASSET = ''
EXPORT_DIRECTORY = 'SOYBEAN_SAMPLES'
EXPORT_MAX_TASKS = 1
EXPORT_INTERVAL = 30
EXPORT_MAX_ERRORS = 1
EXPORT_BUFFER = -4200
EXPORT_SCALE = 30
EXPORT_SCALES = {
    1: [Band.TIR1],
    10000: [Band.GREEN, Band.RED, Band.NIR, Band.SWIR1, Band.SWIR2, Band.EVI2, Band.NDWI, Band.CAI],
}
EXPORT_MAX_PIXELS = 1.0E13
EXPORT_FILE_FORMAT = 'CSV'

# *********** EXTRA SETTINGS *********************

QUALITY_MOSAIC = Band.EVI2
MAX_IMAGES = 5000