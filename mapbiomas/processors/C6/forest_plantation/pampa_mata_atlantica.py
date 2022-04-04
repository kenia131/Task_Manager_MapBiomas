import ee

ee.Initialize()

from rsgee.db import DatabaseManager
from rsgee.taskmanager import TaskManager
from rsgee.utils.landsat_normalization import get_normalized_collection
from rsgee.index import Index, calculate_indexes
import mapbiomas.settings as settings

export = ["sampling", "classification"][1]

# sampling year
years = {
    "sampling": [2014],
    "classification": [1985, 1990, 1995, 2000, 2005, 2010, 2015, 2020]
    # "classification": list(range(1985, 2019))
}[export]

offset = 2

max_cloud_cover = 80

indexes = [Index.NDVI, Index.NDWI, Index.EVI2, Index.CMRI]
indexes_names = [index.name for index in indexes]

bands = ["BLUE", "GREEN", "RED", "NIR", "SWIR1", "SWIR2"]

reducers = (
    ee.Reducer.median()
    .combine(ee.Reducer.mean(), None, True)
    .combine(ee.Reducer.minMax(), None, True)
    .combine(ee.Reducer.stdDev(), None, True)
    .combine(ee.Reducer.percentile([20]), None, True)
)

qmo_band = 'EVI2'

images_limit = 10

max_error = 30

grid_id = {
    "sampling": "users/agrosatelite_mapbiomas/REGIONS/WRS_2_NO_OVERLAP",
    "classification": "users/agrosatelite_mapbiomas/COLECAO_6/GRIDS/BRASIL_COMPLETO",
}[export]

# grid = ee.FeatureCollection(grid_id).filterMetadata("FP_WRS", "equals", 1)
grid = (ee.FeatureCollection(grid_id)
    .filter(ee.Filter.inList("PATHROW", [
        222077, 221077
        # 220076, 220077, 220078, 221076, 221077, 221078, 
        # 222076, 222077, 222078, 223076, 223077, 223078, 
    ])))

reference = ee.ImageCollection("users/agrosatelite_mapbiomas/REFERENCE_MAPS/FOREST_PLANTATION/COLLECTION_30M").Or()


feature_space = [
  'EVI2_max', 'CMRI_max', 'NDWI_median',  'CMRI_median',
  'NIR_median', 'SWIR1_median', 'SWIR2_median', 
  'NIR_p20', 'SWIR1_p20', 'SWIR2_p20'
]


all_samples = ee.FeatureCollection(
    "users/dgoulart/MAPBIOMAS/C6/FOREST_PLANTATION/SAMPLES/FOREST_PLANTATION_SAMPLES_2014_SIMPLE_3"
)

all_extra_samples = ee.FeatureCollection(
    "users/dgoulart/MAPBIOMAS/C6/FOREST_PLANTATION/SAMPLES/FOREST_PLANTATION_SAMPLES_2014_EXTRA_3"
)

###########################
## FUNCTIONS
###########################


def addSufix(sufix):
    return lambda band_name: ee.String(band_name).cat(sufix)


def get_mosaic(collection):
    # collection = correctCollection(collection, bands, True)

    mosaic = ee.ImageCollection(collection).reduce(reducers)

    if (qmo_band):
        qmo = collection.qualityMosaic(qmo_band).rename(
            collection.first().bandNames().map(addSufix("_qmo"))
        )

        mosaic = mosaic.addBands(qmo)

    return mosaic.multiply(10000).toInt16()


tasks = []

for year in years:

    start_date = ee.Date.fromYMD(year - offset, 1, 1)
    end_date = ee.Date.fromYMD(year + 1, 1, 1)

    for pathrow in grid.aggregate_array("PATHROW").getInfo():

        region = grid.filterMetadata("PATHROW", "equals", pathrow).first()
        geometry = region.geometry(max_error)
        centroid = geometry.centroid(max_error)

        ###########################
        ## MOSAIC
        ###########################

        def process_image(image):
            cloud_mask = image.select("QA_SCORE").eq(1)
            image = image.updateMask(cloud_mask)

            image = calculate_indexes(image, indexes)

            return image.select(ee.List(bands).cat(indexes_names)).clip(geometry)

        collection = get_normalized_collection(centroid, start_date, end_date, max_cloud_cover)

        collection = collection.map(process_image)

        L8_collection = collection.filterMetadata(
            "SPACECRAFT_ID", "equals", "LANDSAT_8"
        ).limit(images_limit, "CLOUD_COVER_LAND")

        L7_collection = collection.filterMetadata(
            "SPACECRAFT_ID", "equals", "LANDSAT_7"
        ).limit(images_limit, "CLOUD_COVER_LAND")

        L5_collection = collection.filterMetadata(
            "SPACECRAFT_ID", "equals", "LANDSAT_5"
        ).limit(images_limit, "CLOUD_COVER_LAND")

        L8_mosaic = get_mosaic(L8_collection)
        L7_mosaic = get_mosaic(L7_collection)
        L5_mosaic = get_mosaic(L5_collection)

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

        ###########################
        ## SAMPLING: GENERATE AND EXPORT
        ###########################

        if export == "sampling":
            file_name = f"forest_plantation_{year}_{pathrow}_samples"

            samples = (
                mosaic.addBands(reference.rename("class"))
                .unmask()
                .sample(
                    region=geometry,
                    scale=30,
                    numPixels=6000,
                    seed=1,
                    geometries=True,
                    tileScale=8,
                )
            )

            task = ee.batch.Export.table.toAsset(
                collection=samples,
                description=f"{file_name}_SIMPLE",
                assetId=f"users/dgoulart/MAPBIOMAS/C6/FOREST_PLANTATION/SAMPLES/BY_PATHROW/{file_name}",
            )
            tasks.append(task)

            samples_extra = (
                mosaic.addBands(reference.rename("class"))
                .unmask()
                .stratifiedSample(
                    numPoints=2000,
                    classBand="class",
                    region=geometry,
                    scale=30,
                    classValues=[0, 1],
                    classPoints=[0, 2000],
                    tileScale=10,
                    geometries=True,
                )
            )

            task = ee.batch.Export.table.toAsset(
                collection=samples_extra,
                description=f"{file_name}_EXTRA",
                assetId=f"users/dgoulart/MAPBIOMAS/C6/FOREST_PLANTATION/SAMPLES/BY_PATHROW_EXTRA/{file_name}",
            )
            tasks.append(task)

        ###########################
        ## SAMPLING: LOAD AND FILTER
        ###########################

        if export == "classification":
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

            ###########################
            ## CLASSIFICATION
            ###########################

            min_leaf_population = (
                samples.filterMetadata("class", "equals", 1).size().sqrt().int().min(30)
            )

            classifier = ee.Classifier.smileRandomForest(
                numberOfTrees=100, minLeafPopulation=min_leaf_population, seed=1,
            ).train(features=samples, classProperty="class", inputProperties=feature_space)

            result = mosaic.select(feature_space).classify(classifier).byte()

            output_folder = (
                f"mapbiomas_c6/classification/forest_plantation/pampa_mata_atlantica/{year}"
            )

            file_name = f"forest_plantation_{year}_{pathrow}_raw_result"

            task = ee.batch.Export.image.toAsset(
                image=result,
                description=file_name,
                region=geometry,
                scale=30,
                maxPixels=10e10,
                assetId=f"users/dgoulart/MAPBIOMAS/C6/FOREST_PLANTATION/TESTS/OFFSET_2/{file_name}",
                # bucket="agrosatelite-mapbiomas",
                # fileNamePrefix=f"{output_folder}/{file_name}",
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
