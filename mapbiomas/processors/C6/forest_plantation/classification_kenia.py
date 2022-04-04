import ee

ee.Initialize()

from rsgee.db import DatabaseManager
from rsgee.taskmanager import TaskManager
from rsgee.utils.landsat_normalization import get_normalized_nollection
from rsgee.index import Index, calculate_indexes
import mapbiomas.settings as settings
from rsgee.collections import Blard

year = 2014
offset = 0

start_date = ee.Date.fromYMD(year, 1, 1)
end_date = ee.Date.fromYMD(year + 1, 1, 1)

max_cloud_cover = 80
indexes = [Index.NDVI]
indexes_names = [index.name for index in indexes]

bands = ["BLUE", "GREEN", "RED", "NIR", "SWIR1", "SWIR2"]
images_limit = 10

max_error = 30

grid = (
    ee.FeatureCollection("users/agrosatelite_mapbiomas/REGIONS/WRS_2_NO_OVERLAP")
    .filterMetadata("ACP_WRS", "equals", 1)
    .filter(
        ee.Filter.Or(
            ee.Filter.eq("PA", 1),
            ee.Filter.eq("MA", 1),
            ee.Filter.eq("MT", 1),
            ee.Filter.eq("RR", 1),
            ee.Filter.eq("TO", 1),
        )
    )
)


def add_sufix(sufix):
    return lambda band_name: ee.String(band_name).cat(sufix)


def add_prefix(prefix):
    return lambda band_name: ee.String(prefix).cat(band_name)


# fmt: off
feature_space = [
  'ANNUAL_GREEN_qmo', 'ANNUAL_RED_qmo', 'ANNUAL_NIR_qmo', 'ANNUAL_SWIR1_qmo', 'ANNUAL_SWIR2_qmo', 'ANNUAL_NDVI_qmo',
  'ANNUAL_GREEN_max', 'ANNUAL_RED_max', 'ANNUAL_NIR_max', 'ANNUAL_SWIR1_max', 'ANNUAL_SWIR2_max', 'ANNUAL_NDVI_max',
  'ANNUAL_GREEN_stdDev', 'ANNUAL_RED_stdDev', 'ANNUAL_NIR_stdDev', 'ANNUAL_SWIR1_stdDev', 'ANNUAL_SWIR2_stdDev', 'ANNUAL_NDVI_stdDev',
  'ANNUAL_GREEN_median', 'ANNUAL_RED_median', 'ANNUAL_NIR_median', 'ANNUAL_SWIR1_median', 'ANNUAL_SWIR2_median', 'ANNUAL_NDVI_median',
  'ANNUAL_GREEN_p20', 'ANNUAL_RED_p20', 'ANNUAL_NIR_p20', 'ANNUAL_SWIR1_p20', 'ANNUAL_SWIR2_p20', 'ANNUAL_NDVI_p20'
]
# fmt: on

all_samples = ee.FeatureCollection(
    "users/testesMapBiomas/testes_FlorestasPlantadas/NONE/Samples_limit_NONE"
)

## MOSAIC

tasks = []

for pathrow in grid.aggregate_array("PATHROW").getInfo():

    region = grid.filterMetadata("PATHROW", "equals", pathrow).first()
    geometry = region.geometry(max_error)
    centroid = geometry.centroid(30)

    def process_image(image):
        cloud_mask = image.select("QA_SCORE").eq(1)
        image = image.updateMask(cloud_mask)

        image = calculate_indexes(image, indexes)

        return image.select(ee.List(bands).cat(indexes_names)).clip(geometry)

    collection = Blard.filter_collection_by_roi(
        centroid, start_date, end_date, max_cloud_cover
    )

    collection = collection.map(process_image)

    qmo_ndvi = collection.qualityMosaic("NDVI").rename(
        collection.first().bandNames().map(add_sufix("_qmo"))
    )

    reducers = (
        ee.Reducer.median()
        .combine(ee.Reducer.max(), None, True)
        .combine(ee.Reducer.stdDev(), None, True)
        .combine(ee.Reducer.percentile([20]), None, True)
    )

    mosaic = ee.ImageCollection(collection).reduce(reducers).addBands(qmo_ndvi)

    band_names = mosaic.bandNames().map(add_prefix("ANNUAL_"))

    mosaic = mosaic.rename(band_names)

    ## sampling

    samples = all_samples
        .filterBounds(geometry.buffer(50000, 30))
        .randomColumn('RANDOM')
        .limit(10000, 'RANDOM')

    ## classification

    min_leaf_population = (
        samples.filterMetadata("class", "equals", 1).size().sqrt().int()
    )

    classifier = ee.Classifier.smileRandomForest(
        numberOfTrees=100,
        minLeafPopulation=min_leaf_population,
        seed=1,
    ).train(features=samples, classProperty="class", inputProperties=feature_space)

    result = mosaic.select(feature_space).classify(classifier).byte()

    # output_folder = "users/mapbiomas1/FOREST_PLANTATION_KENIA/"
    output_folder = "users/dgoulart/"

    file_name = f"forest_plantation_{year}_{pathrow}_raw_result".format(
        year=str(year), pathrow=str(pathrow)
    )

    task = ee.batch.Export.image.toAsset(
        image=result,
        description=file_name,
        assetId=output_folder + file_name,
        region=geometry,
        scale=30,
        maxPixels=10e10,
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
