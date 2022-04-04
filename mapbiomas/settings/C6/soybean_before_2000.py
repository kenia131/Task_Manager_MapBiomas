from rsgee.settings import SettingsManager, DefaultSettings
from rsgee.collections import Landsat5, Blard
from rsgee.filter import And, Or, Is, NIs, Eq, NEq, In
from rsgee.reducer import Reducer
from rsgee.band import Band
from rsgee.index import Index
from rsgee.image import PixelType
from rsgee.processors.generic import DefaultBLARDGenerator, LoadSamplesFromAsset, DefaultClassifier, DefaultGenerator
from rsgee.export import Export

from mapbiomas.processors.soybean_before_2000 import SoybeanSampler


class SoybeanMosaics(DefaultSettings):

    NAME = 'soybean_mosaics'

    # ************** COLLECTION SETTINGS **************
    IMAGE_COLLECTION = Landsat5.TOA.Tier1
    GRID_COLLECTION_ID = 'users/agrosatelite_mapbiomas/COLECAO_5/GRIDS/BRASIL_COMPLETO'

    # ******************** FITLERS ********************
    GRID_FEATURE_ID_FIELD = 'PATHROW'
    YEARS = [1985]
    # GRID_FILTER = Is('SB_WRS')
    GRID_FILTER = In('PATHROW', [219062])

    # ************** GENERATOR SETTINGS ***************
    GENERATOR_CLASS = DefaultGenerator
    GENERATION_BANDS = [Band.GREEN, Band.RED, Band.NIR, Band.SWIR1, Band.SWIR2, Band.TIR1]
    GENERATION_INDEXES = [Index.EVI2, Index.NDWI, Index.CAI]
    GENERATION_EXTRA_INDEXES = [Index.CEI]

    GENERATION_INDEXES_PARAMS = {
        Index.CEI.name: {
            'wet_bands': ['AC_WET_NIR_qmo', 'AC_WET_EVI2_qmo', 'AC_WET_NDWI_qmo'],
            'dry_bands': ['AC_DRY_NIR_min', 'AC_DRY_EVI2_min', 'AC_DRY_NDWI_min'],
            'output_bands': ['ANNUAL_EVI2_cei', 'ANNUAL_NDWI_cei', 'ANNUAL_NIR_cei']
        }
    }

    GENERATION_REDUCERS = [Reducer.QMO(Index.EVI2), Reducer.MAX(), Reducer.MIN(),
                           Reducer.MEDIAN(), Reducer.STDV(), Reducer.MEAN()]

    GENERATION_VARIABLES = [
        'AC_WET_NIR_qmo', 'AC_WET_SWIR1_qmo', 'AC_WET_EVI2_qmo',
        'AC_WET_RED_max', 'AC_WET_SWIR1_max', 'AC_WET_SWIR2_max', 'AC_WET_TIR1_max', 'AC_WET_EVI2_max', 'AC_WET_NDWI_max', 'AC_WET_CAI_max',
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
        'SB_WET_LT3_RED_mean', 'SB_WET_LT3_NIR_mean', 'SB_WET_LT3_SWIR1_mean', 'SB_WET_LT3_SWIR2_mean', 'SB_WET_LT3_NDWI_mean', 'SB_WET_LT3_EVI2_mean',

        'ANNUAL_EVI2_cei', 'ANNUAL_NDWI_cei', 'ANNUAL_NIR_cei'
        ]

    GENERATION_PERIODS = [
        'AC_WET', 'AC_DRY',
        'SB_WET_M1', 'SB_WET_M2', 'SB_WET_M3', 'SB_WET_M4', 'SB_WET_M5',
        'SB_WET_FT3', 'SB_WET_LT3'
        ]

    GENERATION_OFFSET = 4

    GENERATION_MAX_CLOUD_COVER = 90
    GENERATION_APPLY_CLOUD_AND_SHADOW_MASK = True

    GENERATION_APPLY_BRDF = True
    GENERATION_BUFFER = -4200

    GENERATION_USE_GEOMETRY_CENTROID = True

    GENERATION_SCALING_FACTORS = {
        10000: [Band.GREEN, Band.RED, Band.NIR, Band.SWIR1, Band.SWIR2,
                Index.EVI2.name, Index.NDWI.name, Index.CAI.name],
        10: [Band.TIR1]
    }

    # **************** EXPORT SETTINGS ****************
    # EXPORT_CLASS = Export.Image.to_cloud_storage
    # EXPORT_BUCKET = 'agrosatelite-mapbiomas'
    # EXPORT_DIRECTORY = 'mapbiomas_c6/classification/soybean/{year}'

    EXPORT_CLASS = Export.Image.to_asset
    EXPORT_DIRECTORY = '{user_assets_root}/MAPBIOMAS/C6/AGRICULTURE/SOYBEAN/TESTS_BEFORE_2000/MOSAICS'
    # EXPORT_DIRECTORY = '{user_assets_root}'
    EXPORT_FILENAME_PREFIX = 'soybean'

    EXPORT_MAX_TASKS = 5
    EXPORT_INTERVAL = 10
    EXPORT_MAX_ERRORS = 0
    EXPORT_SCALE = 30

    EXPORT_PIXEL_TYPE = PixelType.INT16
    EXPORT_MAX_PIXELS = 1.0E13


class SoybeanSampling(SoybeanMosaics):

    NAME = 'soybean_sampling'

    # ******************** FITLERS ********************
    YEARS = [2012]
    # GRID_FILTER = In('PATHROW', [224079, 223078, 224077, 221074, 222075])
    GRID_FILTER = In('PATHROW', [222062, 223062])

    # *************** SAMPLING SETTINGS ***************
    SAMPLING_CLASS = SoybeanSampler
    SAMPLING_REFERENCE_ID = 'users/agrosatelite_mapbiomas/COLECAO_5/RESULTS/SOYBEAN/SPATIAL_FILTERED'
    SAMPLING_POINTS = 10000
    SAMPLING_BUFFER = 0

    # **************** EXPORT SETTINGS ****************
    EXPORT_CLASS = Export.Table.to_asset
    EXPORT_DIRECTORY = '{user_assets_root}/MAPBIOMAS/C6/AGRICULTURE/SOYBEAN/TESTS_BEFORE_2000/SAMPLES/TEST_4'


class SoybeanClassification(SoybeanMosaics):

    NAME = 'soybean_classification'

    # ******************** FITLERS ********************
    YEARS = [1999]
    # GRID_FILTER = Is('SB_WRS')
    GRID_FILTER = In('PATHROW', [225070, 226069, 226070, 229069, 229070, 227068, 227069, 227070, 228069])

    # *************** SAMPLING SETTINGS ***************
    SAMPLING_CLASS = LoadSamplesFromAsset
    SAMPLES_ASSET_ID = 'users/agrosatelite_mapbiomas/COLECAO_6/SAMPLES/SOYBEAN/soybean_samples_2000'
    SAMPLING_BUFFER = 100000

    # ************ CLASSIFICATION SETTINGS ************
    CLASSIFICATION_CLASS = DefaultClassifier
    CLASSIFICATION_TREES = 100

    # **************** EXPORT SETTINGS ****************
    EXPORT_CLASS = Export.Image.to_asset
    EXPORT_DIRECTORY = '{user_assets_root}/MAPBIOMAS/C6/AGRICULTURE/SOYBEAN/TESTS_BEFORE_2000/RAW_4'
    EXPORT_PIXEL_TYPE = PixelType.BYTE


SettingsManager.add_settings(SoybeanMosaics)
SettingsManager.add_settings(SoybeanSampling)
SettingsManager.add_settings(SoybeanClassification)
