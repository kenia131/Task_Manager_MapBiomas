from rsgee.settings import SettingsManager, DefaultSettings
from rsgee.collections import Landsat8
from rsgee.filter import And, Or, Is, NIs, Eq, NEq, In
from rsgee.reducer import Reducer
from rsgee.band import Band
from rsgee.index import Index
from rsgee.image import PixelType
from rsgee.export import Export

from mapbiomas.processors.C5.sugarcane import DefaultGenerator, DefaultClassifier, DefaultSimpleSampler, LoadSamplesFromAsset


class SugarcaneMosaicsSettings(DefaultSettings):

    NAME = 'sugarcane_mosaics'

    # ************** COLLECTION SETTINGS **************
    IMAGE_COLLECTION = Landsat8.TOA.Tier1
    GRID_COLLECTION_ID = 'users/agrosatelite_mapbiomas/COLECAO_5/GRIDS/BRASIL_COMPLETO'

    # ******************** FITLERS ********************
    YEARS = [2020]
    GRID_FILTER = Is('ACS_WRS')
    GRID_FEATURE_ID_FIELD = 'PATHROW'

    # ************** GENERATOR SETTINGS ***************
    GENERATOR_CLASS = DefaultGenerator
    GENERATION_BANDS = [Band.GREEN, Band.RED, Band.NIR, Band.SWIR1, Band.SWIR2]
    GENERATION_INDEXES = [Index.NDVI, Index.NDWI]

    GENERATION_REDUCERS = [Reducer.MEDIAN()]

    GENERATION_VARIABLES = [
        'ACP_WET1_GREEN_median', 'ACP_WET1_RED_median', 'ACP_WET1_NIR_median',
        'ACP_WET1_SWIR1_median', 'ACP_WET1_SWIR2_median', 'ACP_WET1_NDVI_median',
        'ACP_WET1_NDWI_median',
        'ACP_WET2_GREEN_median', 'ACP_WET2_RED_median', 'ACP_WET2_NIR_median',
        'ACP_WET2_SWIR1_median', 'ACP_WET2_SWIR2_median', 'ACP_WET2_NDVI_median',
        'ACP_WET2_NDWI_median',
        'ACP_DRY1_GREEN_median', 'ACP_DRY1_RED_median', 'ACP_DRY1_NIR_median',
        'ACP_DRY1_SWIR1_median', 'ACP_DRY1_SWIR2_median', 'ACP_DRY1_NDVI_median',
        'ACP_DRY1_NDWI_median',
        'ACP_DRY2_GREEN_median', 'ACP_DRY2_RED_median', 'ACP_DRY2_NIR_median',
        'ACP_DRY2_SWIR1_median', 'ACP_DRY2_SWIR2_median', 'ACP_DRY2_NDVI_median',
        'ACP_DRY2_NDWI_median',
        'ACP_DRY3_GREEN_median', 'ACP_DRY3_RED_median', 'ACP_DRY3_NIR_median',
        'ACP_DRY3_SWIR1_median', 'ACP_DRY3_SWIR2_median', 'ACP_DRY3_NDVI_median',
        'ACP_DRY3_NDWI_median',
        'ACP_WET3_GREEN_median', 'ACP_WET3_RED_median', 'ACP_WET3_NIR_median',
        'ACP_WET3_SWIR1_median', 'ACP_WET3_SWIR2_median', 'ACP_WET3_NDVI_median',
        'ACP_WET3_NDWI_median'
        ]

    GENERATION_PERIODS = [
        'ACP_WET1', 'ACP_WET2', 'ACP_DRY1', 'ACP_DRY2', 'ACP_DRY3', 'ACP_WET3']

    GENERATION_OFFSET = 2

    GENERATION_MAX_CLOUD_COVER = 90
    GENERATION_APPLY_BRDF = True
    GENERATION_APPLY_CLOUD_AND_SHADOW_MASK = True
    GENERATION_BUFFER = -4200

    GENERATION_SCALING_FACTORS = {
        10000: [
            Band.GREEN, Band.RED, Band.NIR, Band.SWIR1, Band.SWIR2,
            Index.NDVI.name, Index.NDWI.name
        ]
    }

    # **************** EXPORT SETTINGS ****************
    EXPORT_CLASS = Export.Image.to_asset
    # EXPORT_DIRECTORY = '{user_assets_root}/MAPBIOMAS/C6/AGRICULTURE/SUGARCANE/MOSAICS'
    EXPORT_DIRECTORY = '{user_assets_root}'
    EXPORT_MAX_TASKS = 5
    EXPORT_INTERVAL = 10
    EXPORT_MAX_ERRORS = 0
    EXPORT_SCALE = 30
    EXPORT_PIXEL_TYPE = PixelType.INT16
    EXPORT_MAX_PIXELS = 1.0E13
    EXPORT_FILENAME_PREFIX = 'sugarcane'


class SugarcaneSamplingSettings(SugarcaneMosaicsSettings):

    NAME = 'sugarcane_sampling'

    GRID_COLLECTION_ID = "users/agrosatelite_mapbiomas/REGIONS/WRS_2_NO_OVERLAP"

    # *************** SAMPLING SETTINGS ***************
    SAMPLING_CLASS = DefaultSimpleSampler
    SAMPLING_REFERENCE_ID = 'users/agrosatelite_mapbiomas/COLECAO_4/REFERENCE_MAPS/SEMI-PERENNIAL/USED'
    SAMPLING_POINTS = 10000
    SAMPLING_BUFFER = 50000

    # **************** EXPORT SETTINGS ****************
    EXPORT_CLASS = Export.Table.to_asset
    EXPORT_DIRECTORY = '{user_assets_root}/SUGARCANE_SAMPLES'


class SugarcaneClassificationSettings(SugarcaneMosaicsSettings):

    NAME = 'sugarcane_classification'

    # *************** SAMPLING SETTINGS ***************
    SAMPLING_CLASS = LoadSamplesFromAsset
    SAMPLES_ASSET_ID = 'users/agrosatelite_mapbiomas/COLECAO_6/SAMPLES/SUGARCANE/SUGARCANE_SAMPLES_2020'

    # ************ CLASSIFICATION SETTINGS ************
    CLASSIFICATION_CLASS = DefaultClassifier
    CLASSIFICATION_TREES = 100

    # **************** EXPORT SETTINGS ****************
    EXPORT_CLASS = Export.Image.to_cloud_storage
    EXPORT_BUCKET = 'agrosatelite-mapbiomas'
    EXPORT_DIRECTORY = 'mapbiomas_c6/classification/sugarcane/{year}_v2'
    EXPORT_PIXEL_TYPE = PixelType.BYTE


SettingsManager.add_settings(SugarcaneMosaicsSettings)
SettingsManager.add_settings(SugarcaneSamplingSettings)
SettingsManager.add_settings(SugarcaneClassificationSettings)
