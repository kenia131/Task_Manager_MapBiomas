import ee

from mapbiomas import processors
from rsgee.band import Band
from rsgee.db.models import TaskTypes
from rsgee.provider import Provider
from rsgee.reducer import Reducer
from rsgee.imagemaker import ImageMaker

YEARS = [2018]

# ********** SERVICE ACCOUNT  *****************

# SERVICE_ACCOUNT = 'earthengine@simfaz.iam.gserviceaccount.com'
# SERVICE_KEY = '/home/saraivaufc/simfaz-4b7c418457f3.json'

# ********** COLLECTION SETTINGS ****************

COLLECTION_PREFIX = 'BLARD'
COLLECTION_PROVIDER = Provider.BLARD

# *********  FUSION TABLE SETTINGS

FEATURE_COLLECTION = 'users/agrosatelite_mapbiomas/COLECAO_5/GRIDS/BRASIL_COMPLETO_2'
FEATURE_WRS_SELECTED = {
    'AND': {'PER_WRS': 1}
}
FEATURE_WRS = 'PATHROW'
FEATURE_WRS_FILTER = []

# ********** GENERAL SETTINGS *******************

GENERATOR_CLASS = processors.AnnualPerennialGenerator
GENERATION_BANDS = [Band.RED, Band.NIR, Band.SWIR1, Band.EVI2, Band.NDWI]
GENERATION_EXTRA_BANDS = [Band.CEI]
GENERATION_REDUCERS = [Reducer.QMO, Reducer.MAX, Reducer.MIN, Reducer.MEDIAN,
                       Reducer.STDV, Reducer.MEAN, Reducer.PERCENTILE]
GENERATION_VARIABLES = [
    'PER_ANNUAL_EVI2_stdDev', 'PER_ANNUAL_EVI2_min', 'PER_ANNUAL_EVI2_p10', 'PER_ANNUAL_EVI2_median', 
    'PER_ANNUAL_EVI2_mean', 'AC_DRY_EVI2_min',  'AC_WET_NDWI_stdDev', 'AC_WET_EVI2_stdDev', 'AC_WET_NDWI_min',
    ]

GENERATION_EXTRA_VARIABLES = [
    'ANNUAL_NIR_cei',
    'ANNUAL_EVI2_cei',
    'ANNUAL_NDWI_cei',
    ]

GENERATION_AMPLITUDE = {
    'MIN':  ['AC_DRY_EVI2_p10'],
    'MAX':  ['AC_WET_EVI2_p90'],
    'OUTPUT': ['ANNUAL_EVI2_amplitude']
}

GENERATION_PERIODS = [ 'AC_WET', 'AC_DRY', 'PER_ANNUAL' ]
GENERATION_EXTRA_PERIODS = ['ANNUAL']
GENERATION_OFFSET = 1
GENERATION_CLIP_GEOMETRY = True
GENERATION_APPLY_MASK = True
GENERATION_APPLY_BRDF = True
GENERATION_TYPE = 'int16'

# ********** CLASSIFICATION SETTINGS **************

CLASSIFIER_CLASS = processors.AnnualPerennialBLARDClassifier
CLASSIFICATION_MASK = 'projects/mapbiomas-workspace/TRANSVERSAIS/AGRICULTURA4-FT'
CLASSIFICATION_TRAIN = 'users/agrosatelite_mapbiomas/COLECAO_5/SAMPLES/ANNUAL_PERENNIAL/ANNUAL_PERENNIAL_SAMPLES_2017'
CLASSIFICATION_TREES = 100
CLASSIFICATION_POINTS = 5000
CLASSIFICATION_BUFFER = 100000

# ********** EXPORT SETTINGS **********************

EXPORT_CLASS = ee.batch.Export.image.toCloudStorage
EXPORT_TASKS = [
    TaskTypes.GENERATION,
    TaskTypes.CLASSIFICATION
]
EXPORT_TYPES = [ImageMaker.IMAGE]
EXPORT_BUCKET = 'agrosatelite-mapbiomas'
EXPORT_DIRECTORY = 'mapbiomas_c5/classification/annual_perennial/2019'
EXPORT_MAX_TASKS = 1
EXPORT_INTERVAL = 30
EXPORT_MAX_ERRORS = 2
EXPORT_BUFFER = -4200
EXPORT_SCALE = 30
EXPORT_SCALES = {
    10000: [Band.RED, Band.NIR, Band.SWIR1, Band.EVI2, Band.NDWI],
}
EXPORT_MAX_PIXELS = 1.0E13

# *********** EXTRA SETTINGS *********************

QUALITY_MOSAIC = Band.EVI2
PERCENTILES = [10, 90]

MAX_IMAGES = 5000