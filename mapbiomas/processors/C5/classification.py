import ee

ee.Initialize()

from rsgee.db import DatabaseManager
from rsgee.taskmanager import TaskManager
from rsgee.index import Index, calculate_indexes
import mapbiomas.settings as settings
from rsgee.collections import Landsat5, Landsat7, Landsat8
from rsgee.utils.date import parse_date

years = [1986]

offset = 4

max_cloud_cover = 90
indexes = [Index.NDWI, Index.EVI2, Index.CAI]
indexes_names = [index.name for index in indexes]

bands = ["GREEN", "RED", "NIR", "SWIR1", "SWIR2", "TIR1"]
normalization_bands = ["GREEN", "RED", "NIR", "SWIR1", "SWIR2"]

max_error = 30

feature_space = [
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

  'ANNUAL_EVI2_cei', 'ANNUAL_NDWI_cei', 'ANNUAL_NIR_cei'
]


grid = ee.FeatureCollection(
    "users/agrosatelite_mapbiomas/COLECAO_6/GRIDS/BRASIL_COMPLETO"
).filterMetadata("AC_WRS", "equals", 1)

reference = ee.Image(
    "users/agrosatelite_mapbiomas/REFERENCE_MAPS/AGRICULTURE/AGRICULTURE_2016_30M"
).eq(1)

# FUNCTIONS


def add_prefix(prefix):
    return lambda band_name: ee.String(prefix).cat("_").cat(band_name)


def add_sufix(sufix):
    return lambda band_name: ee.String(band_name).cat("_").cat(sufix)


def add_cei(image, dry_band, wet_band, output):
    selected_bands = image.select([dry_band, wet_band], ["dry_min", "wet_max"])

    cei = selected_bands.expression(
        f"{output} = (10**6 * (b('wet_max') - b('dry_min')) / (10**6 + b('wet_max') + 10**6 + b('dry_min')))"
    )

    return image.addBands(cei)


def get_period_collection(bounds, period, year):
    dates = region.getString(period).split(",")
    start_date = ee.Date(parse_date(dates.getString(0), year))
    end_date = ee.Date(parse_date(dates.getString(1), year))

    collection = Landsat8

    if (year <= 2014):
        collection = Landsat7

    if (year <= 2012):
        collection = Landsat5

    def clip(image):
        return image.clip(image.geometry(max_error).buffer(-4200, max_error))

    collection = (collection()
                  .filterBounds(bounds)
                  .filterDate(start_date, end_date)
                  .filterMetadata("CLOUD_COVER", "less_than", 90)
                  .padronize_band_names()
                  .apply_brdf()
                  .mask_clouds_and_shadows()
                  .select(bands)
                  .map(clip)
                  .calculate_indexes(indexes))

    return collection.toList(collection.size().add(1), 0)

def get_mosaic(collection):

    qmo = collection.qualityMosaic("EVI2").rename(
        collection.first().bandNames().map(add_sufix("qmo"))
    )

    reducers = (
        ee.Reducer.median()
        .combine(ee.Reducer.max(), None, True)
        .combine(ee.Reducer.min(), None, True)
        .combine(ee.Reducer.stdDev(), None, True)
        .combine(ee.Reducer.percentile([10]), None, True)
    )

    mosaic = ee.ImageCollection(collection).reduce(reducers).addBands(qmo)
    tir1 = mosaic.select(".*TIR1.*").multiply(10)

    mosaic = mosaic.multiply(10000).addBands(tir1, None, True).toInt16()

    new_names = mosaic.bandNames().map(add_prefix(period))

    return mosaic.rename(new_names).set("year", year)


tasks = []

for year in years:
    for pathrow in grid.aggregate_array("PATHROW").getInfo():

        region = grid.filterMetadata("PATHROW", "equals", pathrow).first()
        geometry = region.geometry(max_error)

        ###########################
        ## MOSAIC
        ###########################

        mosaics = []

        for period in ["AC_WET", "AC_DRY"]:

            collections = ee.List.sequence(0, offset).map(
                lambda o: get_period_collection(
                    geometry, period, ee.Number(year).subtract(o)
                )
            )

            collection = ee.ImageCollection(collections.flatten())

            period_mosaic = get_mosaic(collection)

            mosaics.append(period_mosaic)

        mosaic = ee.Image(mosaics)

        mosaic = mosaic.calculate_indexes(['CEI'], {
            'wet_bands': ['AC_WET_NIR_qmo', 'AC_WET_EVI2_qmo', 'AC_WET_NDWI_qmo'],
            'dry_bands': ['AC_DRY_NIR_min', 'AC_DRY_EVI2_min', 'AC_DRY_NDWI_min'],
            'output_bands': ['ANNUAL_NIR_cei', 'ANNUAL_EVI2_cei', 'ANNUAL_NDWI_cei'],
        })

        ###########################
        ## SAMPLING
        ###########################

        sampling_geoemtry = geometry.buffer(100000, max_error)

        samples = (
            mosaic.addBands(reference.rename("class"))
            .unmask()
            .sample(
                region=geometry,
                scale=30,
                numPixels=10000,
                seed=1,
                geometries=False,
                tileScale=8,
            )
        )

        ###########################
        ## CLASSIFICATION
        ###########################

        classifier = (ee.Classifier
                      .smileRandomForest(numberOfTrees=100, seed=1)
                      .train(features=samples, classProperty="class", inputProperties=feature_space))

        result = (
            mosaic.select(feature_space).unmask().classify(classifier).set("year", year)
        )

        file_name = f"temporary_crops_{year}_{pathrow}_raw_result"

        task = ee.batch.Export.image.toCloudStorage(
            image=result.byte(),
            description=file_name,
            region=geometry,
            scale=30,
            maxPixels=10e10,

            bucket="agrosatelite-mapbiomas",
            fileNamePrefix=f"mapbiomas_c6/classification/temporary_crops/vC5/{year}/{file_name}",
            fileFormat="GeoTIFF",

        )

        tasks.append(task)


db_settings = settings.global_settings.DATABASE


class Settings:
    EXPORT_MAX_TASKS = 5
    EXPORT_INTERVAL = 20
    EXPORT_MAX_ERRORS = 0


session = DatabaseManager(db_settings).get_session()
task_manager = TaskManager(session, Settings)

task_manager.add_tasks(tasks)
task_manager.start()
task_manager.join()

session.close()
