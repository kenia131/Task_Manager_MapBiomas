import ee

ee.Initialize()

from rsgee.db import DatabaseManager
from rsgee.taskmanager import TaskManager
from rsgee.utils.landsat_normalization import get_normalized_collection
from rsgee.index import Index, calculate_indexes
from rsgee.utils.illumination_correction import correctCollection
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

# fmt: off
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

  'ANNUAL_EVI2_cei', 
  'ANNUAL_NDWI_cei', 'ANNUAL_NIR_cei'
]
# fmt: on

grid = ee.FeatureCollection(
    "users/agrosatelite_mapbiomas/COLECAO_6/GRIDS/BRASIL_COMPLETO"
).filterMetadata("AC_WRS", "equals", 1)

reference = ee.Image(
    "users/agrosatelite_mapbiomas/REFERENCE_MAPS/AGRICULTURE/AGRICULTURE_2016_30M"
).eq(1)

all_samples = ee.FeatureCollection(
    "users/dgoulart/MAPBIOMAS/C6/TEMPORARY_CROPS/SAMPLES/TEMPORARY_CROPS_2016_SIMPLE"
)

all_extra_samples = ee.FeatureCollection(
    "users/dgoulart/MAPBIOMAS/C6/TEMPORARY_CROPS/SAMPLES/TEMPORARY_CROPS_2016_EXTRA"
)

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

    collection = get_normalized_collection(
        bounds, start_date, end_date, max_cloud_cover, normalization_bands, True
    )

    return collection.toList(collection.size().add(1), 0)


def process_image(image):
    cloud_mask = image.select("QA_SCORE").eq(1)
    image = image.updateMask(cloud_mask)

    image = calculate_indexes(image, indexes)

    return image.select(ee.List(bands).cat(indexes_names))


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
        export_geometry = geometry.buffer(-4200, max_error)

        ###########################
        ## MOSAIC
        ###########################

        mosaics = []

        for period in ["AC_WET", "AC_DRY"]:

            collections = ee.List.sequence(0, offset).map(
                lambda o: get_period_collection(
                    geometry.centroid(max_error), period, ee.Number(year).subtract(o)
                )
            )

            collection = ee.ImageCollection(collections.flatten()).map(process_image)

            period_mosaic = get_mosaic(collection)

            mosaics.append(period_mosaic)

        mosaic = ee.Image(mosaics).clip(export_geometry)

        # fmt: off
        mosaic = add_cei(mosaic, 'AC_DRY_EVI2_min', 'AC_WET_EVI2_qmo', 'ANNUAL_EVI2_cei')
        mosaic = add_cei(mosaic, 'AC_DRY_NDWI_min', 'AC_WET_NDWI_qmo', 'ANNUAL_NDWI_cei')
        mosaic = add_cei(mosaic, 'AC_DRY_NIR_min', 'AC_WET_NIR_qmo', 'ANNUAL_NIR_cei')
        # fmt: on

        ###########################
        ## SAMPLING
        ###########################

        sampling_geoemtry = geometry.buffer(100000, max_error)

        samples = (
            all_samples.filterBounds(sampling_geoemtry)
            .randomColumn("RANDOM")
            .limit(10000, "RANDOM")
        )

        coi_samples = samples.filterMetadata("class", "equals", 1)
        coi_samples_num = coi_samples.size()

        extra_samples_num = ee.Number(500).subtract(coi_samples_num).max(0)

        extra_samples = all_extra_samples.filterBounds(sampling_geoemtry).limit(
            extra_samples_num, "RANDOM"
        )

        coi_samples = coi_samples.merge(extra_samples)

        others_samples_num = ee.Number(10000).subtract(coi_samples.size())
        others_samples = samples.filterMetadata("class", "equals", 0).limit(
            others_samples_num, "RANDOM"
        )

        samples = coi_samples.merge(others_samples)

        ###########################
        ## CLASSIFICATION
        ###########################

        min_leaf_population = (
            samples.filterMetadata("class", "equals", 1)
            .size()
            .sqrt()
            .int()
            .min(20)
            .max(1)
        )

        classifier = ee.Classifier.smileRandomForest(
            numberOfTrees=100, seed=1, minLeafPopulation=min_leaf_population
        ).train(features=samples, classProperty="class", inputProperties=feature_space)

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
            # assetId=f"users/dgoulart/MAPBIOMAS/C6/COFFEE/RESULTS/ES_RAW/{file_name}",
            bucket="agrosatelite-mapbiomas",
            fileNamePrefix=f"mapbiomas_c6/classification/temporary_crops/v1/{year}/{file_name}",
            fileFormat="GeoTIFF",
            # folder="TEST",
            # fileNamePrefix=f"{output_folder}/{file_name}",
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
