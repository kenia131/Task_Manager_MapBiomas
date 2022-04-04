import ee

ee.Initialize()

from rsgee.db import DatabaseManager
from rsgee.taskmanager import TaskManager
from rsgee.utils.landsat_normalization import apply_normalization
from rsgee.index import Index, calculate_indexes
import mapbiomas.settings as settings
from rsgee.collections import Landsat5, Landsat7, Landsat8

years = [2015]

max_cloud_cover = 80
indexes = [Index.NDWI, Index.EVI2]
indexes_names = [index.name for index in indexes]

bands = ["BLUE", "GREEN", "RED", "NIR", "SWIR1", "SWIR2"]
images_limit = 10

max_error = 30

grid = (
    ee.FeatureCollection("users/agrosatelite_mapbiomas/COLECAO_6/GRIDS/BRASIL_COMPLETO")
    .filterMetadata("COF_WRS", "equals", 1)
    .filterMetadata("ES", "equals", 1)
)

# fmt: off
feature_space = [
#   'GREEN_mean', 'RED_mean', 'NIR_mean', 'SWIR1_mean', 'SWIR2_mean', 'EVI2_mean', 'NDWI_mean',
#   'GREEN_stdDev', 'RED_stdDev', 'NIR_stdDev', 'SWIR1_stdDev', 'SWIR2_stdDev', 'EVI2_stdDev', 'NDWI_stdDev',
#   'GREEN_min', 'RED_min', 'NIR_min', 'SWIR1_min', 'SWIR2_min', 'EVI2_min', 'NDWI_min',
#   'GREEN_p20', 'RED_p20', 'NIR_p20', 'SWIR1_p20', 'SWIR2_p20', 'EVI2_p20', 'NDWI_p20',
  'GREEN_median', 'RED_median', 'NIR_median', 'SWIR1_median', 'SWIR2_median', 'EVI2_median', 'NDWI_median',
  'GREEN_p80', 'RED_p80', 'NIR_p80', 'SWIR1_p80', 'SWIR2_p80', 'EVI2_p80', 'NDWI_p80',
#   'GREEN_max', 'RED_max', 'NIR_max', 'SWIR1_max', 'SWIR2_max', 
  'EVI2_max', 'NDWI_max',
  'GREEN_qmo', 'RED_qmo', 'NIR_qmo', 'SWIR1_qmo', 'SWIR2_qmo', 'EVI2_qmo', 'NDWI_qmo',
]
# fmt: on

all_samples = ee.FeatureCollection(
    "users/dgoulart/MAPBIOMAS/C6/COFFEE/SAMPLES/COFFEE_SIMPLE"
)

all_extra_samples = ee.FeatureCollection(
    "users/dgoulart/MAPBIOMAS/C6/COFFEE/SAMPLES/COFFEE_EXTRA"
)


def addSufix(sufix):
    return lambda band_name: ee.String(band_name).cat(sufix)


## MOSAIC


def filter_collection(collection, roi, start_date, end_date):
    return (
        collection.filterBounds(roi)
        .filterDate(start_date, end_date)
        .filterMetadata("CLOUD_COVER_LAND", "less_than", max_cloud_cover)
        .limit(images_limit, "CLOUD_COVER_LAND")
        .padronize_band_names()
        .score_images()
    )


def get_mosaic(collection):
    # collection = correctCollection(collection, bands, True)

    qmo = collection.qualityMosaic("EVI2").rename(
        collection.first().bandNames().map(addSufix("_qmo"))
    )

    reducers = (
        ee.Reducer.median()
        .combine(ee.Reducer.mean(), None, True)
        .combine(ee.Reducer.max(), None, True)
        .combine(ee.Reducer.min(), None, True)
        .combine(ee.Reducer.stdDev(), None, True)
        .combine(ee.Reducer.percentile([20, 80]), None, True)
    )

    mosaic = (
        ee.ImageCollection(collection)
        .reduce(reducers)
        .addBands(qmo)
        .multiply(10000)
        .toInt16()
    )

    return mosaic


tasks = []

for year in years:

    start_date = ee.Date.fromYMD(year, 1, 1)
    end_date = ee.Date.fromYMD(year + 1, 1, 1)

    for pathrow in grid.aggregate_array("PATHROW").getInfo():

        region = grid.filterMetadata("PATHROW", "equals", pathrow).first()
        geometry = region.geometry(max_error)
        centroid = geometry.centroid(30)

        L8_collection = filter_collection(
            Landsat8.TOA.Tier1(), centroid, start_date, end_date
        )
        L7_collection = filter_collection(
            Landsat7.TOA.Tier1(), centroid, start_date, end_date
        )
        L5_collection = filter_collection(
            Landsat5.TOA.Tier1(), centroid, start_date, end_date
        )

        collection = L8_collection.merge(L7_collection).merge(L5_collection)

        def process_image(image):
            cloud_mask = image.select("QA_SCORE").eq(1)
            image = image.updateMask(cloud_mask)

            image = calculate_indexes(image, indexes)

            return image.select(ee.List(bands).cat(indexes_names)).clip(geometry)

        normalized_collection = apply_normalization(collection, bands, True).map(
            process_image
        )

        L8_mosaic = get_mosaic(
            normalized_collection.filterMetadata("SPACECRAFT_ID", "equals", "LANDSAT_8")
        )
        L7_mosaic = get_mosaic(
            normalized_collection.filterMetadata("SPACECRAFT_ID", "equals", "LANDSAT_7")
        )
        L5_mosaic = get_mosaic(
            normalized_collection.filterMetadata("SPACECRAFT_ID", "equals", "LANDSAT_5")
        )

        mosaic = None

        if year >= 2013:
            mosaic = L8_mosaic.unmask(L7_mosaic)

        if year == 2012:
            mosaic = L7_mosaic

        if year >= 2003 and year < 2012:
            mosaic = L5_mosaic.unmask(L7_mosaic)

        if year >= 2000 and year < 2003:
            mosaic = L7_mosaic.unmask(L5_mosaic)

        if year < 2000:
            mosaic = L5_mosaic

        ## sampling

        sampling_geoemtry = geometry.buffer(20000, max_error)

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

        ## classification

        # min_leaf_population = (
        #     samples.filterMetadata("class", "equals", 1).size().sqrt().int().min(20)
        # )

        classifier = ee.Classifier.smileRandomForest(numberOfTrees=100, seed=1).train(
            features=samples, classProperty="class", inputProperties=feature_space
        )

        result = mosaic.select(feature_space).classify(classifier).set("year", year)

        file_name = f"coffee_{year}_{pathrow}_raw_result"

        task = ee.batch.Export.image.toAsset(
            image=result.byte(),
            description=file_name,
            region=geometry,
            scale=30,
            maxPixels=10e10,
            assetId=f"users/dgoulart/MAPBIOMAS/C6/COFFEE/RESULTS/ES_RAW/{file_name}",
            # bucket="agrosatelite-mapbiomas",
            # fileNamePrefix=f"mapbiomas_c6/classification/coffee-2/{year}/{file_name}",
            # fileFormat="GeoTIFF",
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
