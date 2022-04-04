from rsgee.settings import SettingsManager, DefaultSettings
from rsgee.collections import Landsat5, Landsat7, Landsat8
from rsgee.filter import And, Or, Is, NIs, Eq, NEq, In
from rsgee.reducer import Reducer
from rsgee.band import Band
from rsgee.index import Index
from rsgee.image import PixelType
from rsgee.export import Export

from mapbiomas.processors.C5.annual_crops import DefaultGenerator, DefaultClassifier, DefaultSimpleSampler


class TemporaryCropsCaatingaSettings(DefaultSettings):

    NAME = 'annual_crops_caatinga'

    # ************** COLLECTION SETTINGS **************
    # >= 2015
    # IMAGE_COLLECTION = Landsat8.TOA.Tier1

    # <=2014
    IMAGE_COLLECTION = Landsat7.TOA.Tier1

    # <= 2012
    # IMAGE_COLLECTION = Landsat5.TOA.Tier1

    GRID_COLLECTION_ID = 'users/agrosatelite_mapbiomas/COLECAO_5/GRIDS/BRASIL_COMPLETO'
    GRID_GEOMETRY_USE_CENTROID = False

    # ******************** FITLERS ********************
    YEARS = [2014]
    GRID_FEATURE_ID_FIELD = 'PATHROW'
    GRID_FILTER = And(Is('AC_WRS'), Or(Is('CAATINGA'), Is('MG'), Is('ES'), Is('RJ')))

    # ************** GENERATOR SETTINGS ***************
    GENERATOR_CLASS = DefaultGenerator
    GENERATION_BANDS = [Band.GREEN, Band.RED, Band.NIR, Band.SWIR1, Band.SWIR2, Band.TIR1]
    GENERATION_INDEXES = [Index.EVI2, Index.NDWI, Index.CAI]
    GENERATION_EXTRA_INDEXES = [Index.CEI]

    GENERATION_INDEXES_PARAMS = {
        Index.CEI.name: {
            'wet_bands': ['AC_WET_NIR_qmo', 'AC_WET_EVI2_qmo', 'AC_WET_NDWI_qmo'],
            'dry_bands': ['AC_DRY_NIR_min', 'AC_DRY_EVI2_min', 'AC_DRY_NDWI_min'],
            'output_bands': ['ANNUAL_NIR_cei', 'ANNUAL_EVI2_cei', 'ANNUAL_NDWI_cei'],
        }
    }

    GENERATION_REDUCERS = [Reducer.QMO(Index.EVI2), Reducer.MAX(), Reducer.MIN(),
                           Reducer.MEDIAN(), Reducer.STDV(), Reducer.MEAN()]

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

        'ANNUAL_EVI2_cei', 'ANNUAL_NDWI_cei', 'ANNUAL_NIR_cei'
        ]

    GENERATION_PERIODS = ['AC_WET', 'AC_DRY']

    GENERATION_OFFSET = 4

    GENERATION_MAX_CLOUD_COVER = 90
    GENERATION_APPLY_BRDF = True
    GENERATION_APPLY_CLOUD_AND_SHADOW_MASK = True
    GENERATION_BUFFER = -4200

    GENERATION_SCALING_FACTORS = {
        10000: [
            Band.GREEN, Band.RED, Band.NIR, Band.SWIR1, Band.SWIR2,
            Index.EVI2.name, Index.NDWI.name, Index.CAI.name
        ],
        100: [Band.TIR1]
    }
    # *************** SAMPLING SETTINGS ***************
    SAMPLING_CLASS = DefaultSimpleSampler
    # SAMPLING_REFERENCE_ID = 'users/agrosatelite_mapbiomas/REFERENCE_MAPS/AGRICULTURE/AGRICULTURE_2016_30M'
    SAMPLING_REFERENCE_ID = 'users/agrosatelite_mapbiomas/COLECAO_6/RESULTS/TEMPORARY_CROPS/PLANO_B/RAW'
    SAMLPING_POINTS = 10000
    SAMPLING_BUFFER = 30000

    # ************ CLASSIFICATION SETTINGS ************
    CLASSIFICATION_CLASS = DefaultClassifier
    CLASSIFICATION_TREES = 100

    # **************** EXPORT SETTINGS ****************
    EXPORT_CLASS = Export.Image.to_cloud_storage
    EXPORT_BUCKET = 'agrosatelite-mapbiomas'
    EXPORT_DIRECTORY = 'mapbiomas_c6/classification/temporary_crops/vC5/caatinga/{year}'
    EXPORT_FILENAME_PREFIX = 'temp_crops'
    EXPORT_MAX_TASKS = 5
    EXPORT_INTERVAL = 10
    EXPORT_MAX_ERRORS = 0
    EXPORT_BUFFER = -4200
    EXPORT_SCALE = 30
    EXPORT_PIXEL_TYPE = PixelType.INT16
    EXPORT_MAX_PIXELS = 1.0E13


SettingsManager.add_settings(TemporaryCropsCaatingaSettings)
