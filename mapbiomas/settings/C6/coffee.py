from rsgee.settings import SettingsManager, DefaultSettings
from rsgee.collections import Blard, SRTM
from rsgee.filter import And, Eq, Is, In, NEq
from rsgee.reducer import Reducer
from rsgee.band import Band
from rsgee.index import Index
from rsgee.image import PixelType

from rsgee.processors.generic.generator import DefaultBLARDGenerator, LoadMosaicsFromAsset, DefaultGenerator
from rsgee.processors.generic.sampler import DefaultSimpleSampler, LoadSamplesFromAsset, StratifiedSampler
from rsgee.processors.generic.classifier import DefaultClassifier
from rsgee.processors.generic.postprocessor import MergeImagesByYear

from rsgee.export import Export


class CoffeeMosaicsSettings(DefaultSettings):

    NAME = 'coffee_mosaics'

    # ************** COLLECTION SETTINGS **************
    IMAGE_COLLECTION = Blard
    GRID_COLLECTION_ID = 'users/agrosatelite_mapbiomas/COLECAO_5/GRIDS/BRASIL_COMPLETO'
    # ******************** FITLERS ********************
    YEARS = [2016]

    GRID_FEATURE_ID_FIELD = 'PATHROW'
    GRID_FILTER = In('PATHROW', [
        216069, 216070, 216071, 217068, 217069, 217071, 215071, 220068, 220069, 216073, 216074, 216075, 217072,
        217074, 215072, 215073, 215074, 219072, 219073, 219074, 219075, 219076, 222075, 222076, 222077, 220071,
        220073, 220074, 220075, 220076, 221071, 221072, 221073, 221075, 221076, 221077, 218074, 218075
        ]   
    )

    GRID_GEOMETRY_USE_CENTROID = True

    # ************** GENERATOR SETTINGS ***************
    GENERATOR_CLASS = DefaultBLARDGenerator

    GENERATION_BANDS = [Band.GREEN, Band.RED, Band.NIR, Band.SWIR1, Band.SWIR2]
    GENERATION_INDEXES = [
        Index.EVI2, Index.GNDVI, Index.MVI,
        Index.SR, Index.CAI, Index.LAI, Index.MNDWI
        ]

    GENERATION_REDUCERS = [
        Reducer.QMO(Index.EVI2), Reducer.MAX(), 
        Reducer.MEDIAN(), Reducer.STDV(), Reducer.MEAN(), Reducer.PERCENTILE([20, 90])
        ]

    GENERATION_ADDITIONAL_DATA = [SRTM.slope]

    GENERATION_VARIABLES = [
        'P1_NIR_min', 'P1_MNDWI_min', 'P1_MVI_min',
        'P1_NIR_max', 'P1_CAI_max', 
        'P1_NIR_mean', 'P1_CAI_mean', 'P1_GNDVI_mean', 'P1_MNDWI_mean', 'P1_SR_mean',
        'P1_NIR_median', 'P1_CAI_median', 'P1_GNDVI_median', 'P1_MNDWI_median',
        'P1_NDWI_stdDev',
        'P1_NIR_qmo', 'P1_GNDVI_qmo', 'P1_MNDWI_qmo',

        'P2_NIR_min', 'P2_MNDWI_min', 'P2_NDWI_min',
        'P2_NIR_max', 'P2_SWIR1_max', 'P2_GNDVI_max', 'P2_MNDWI_max',
        'P2_NIR_mean', 'P2_SWIR1_mean', 'P2_SWIR2_mean', 'P2_CAI_mean',
        'P2_EVI2_mean', 'P2_GNDVI_mean', 'P2_MNDWI_mean', 'P2_NDWI_mean',
        'P2_GREEN_median', 'P2_NIR_median', 'P2_SWIR1_median', 'P2_SWIR2_median',
        'P2_CAI_median', 'P2_GNDVI_median', 'P2_MNDWI_median',
        'P2_SWIR1_stdDev', 'P2_MVI_stdDev', 'P2_NDWI_stdDev',
        'P2_GNDVI_qmo', 'P2_MNDWI_qmo',

        'slope'
        ]

    GENERATION_PERIODS = {
        'P1': '(Y)-01-01,(Y)-07-01',
        'P2': '(Y)-07-01,(Y+1)-01-01',
    }

    GENERATION_OFFSET = 0
    GENERATION_MAX_CLOUD_COVER = 90

    # **************** EXPORT SETTINGS ****************
    EXPORT_CLASS = Export.Image.to_asset
    EXPORT_DIRECTORY = '{user_assets_root}/MAPBIOMAS/C6/AGRICULTURE/COFFEE/TEST/MOSAICS/COLLECTION'
    EXPORT_BUFFER = -4200
    EXPORT_BUFFER = 0
    EXPORT_SCALE = 30
    EXPORT_PIXEL_TYPE = PixelType.FLOAT


class CoffeeSamplesSettings(CoffeeMosaicsSettings):

    NAME = 'coffee_samples'

    # *************** SAMPLING SETTINGS ***************
    # SAMPLING_CLASS = DefaultSimpleSampler
    SAMPLING_CLASS = StratifiedSampler
    SAMPLING_REFERENCE_ID = 'users/agrosatelite_mapbiomas/REFERENCE_MAPS/AGRICULTURE/PERENNIAL_CROPS/COFFEE/COLLECTION_30M'
    SAMLPING_POINTS = 5000

    # **************** EXPORT SETTINGS ****************
    EXPORT_CLASS = Export.Table.to_asset
    EXPORT_DIRECTORY = 'users/testesMapBiomas/Teste_Cafe/SamplesPython'


class CoffeeClassificationSettings(CoffeeMosaicsSettings):

    NAME = 'coffee_classification'

    # *************** SAMPLING SETTINGS ***************
    SAMPLING_CLASS = LoadSamplesFromAsset
    SAMPLES_ASSET_ID = 'users/dgoulart/MAPBIOMAS/C6/AGRICULTURE/COFFEE/TEST/SAMPLES/COFFEE_MG_2016_SAMPLES_2'

    # ************ CLASSIFICATION SETTINGS ************
    CLASSIFICATION_CLASS = DefaultClassifier
    CLASSIFICATION_TREES = 100

    # **************** EXPORT SETTINGS ****************
    EXPORT_CLASS = Export.Image.to_asset
    EXPORT_DIRECTORY = '{user_assets_root}/MAPBIOMAS/C6/AGRICULTURE/COFFEE/TEST/RESULTS/COFFEE_MG_RAW_2'
    EXPORT_PIXEL_TYPE = PixelType.BYTE


SettingsManager.add_settings(CoffeeMosaicsSettings)
SettingsManager.add_settings(CoffeeSamplesSettings)
SettingsManager.add_settings(CoffeeClassificationSettings)
