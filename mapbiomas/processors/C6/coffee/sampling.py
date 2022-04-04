import ee

ee.Initialize()

from rsgee.db import DatabaseManager
from rsgee.taskmanager import TaskManager
from rsgee.utils.landsat_normalization import apply_normalization
from rsgee.index import Index, calculate_indexes
from rsgee.utils.illumination_correction import correctCollection
import mapbiomas.settings as settings
from rsgee.collections import Landsat5, Landsat7, Landsat8

years_states = {
    2019: ["BA"],
    # 2019: ["BA", "GO"],
    2018: ["DF", "GO"],
    2017: ["PR"],
    2016: ["SP", "MG"],
    2015: ["ES"],
}

max_cloud_cover = 80
indexes = [Index.NDWI, Index.EVI2]
indexes_names = [index.name for index in indexes]

bands = ["BLUE", "GREEN", "RED", "NIR", "SWIR1", "SWIR2"]
images_limit = 10

max_error = 30

grid = ee.FeatureCollection("users/agrosatelite_mapbiomas/REGIONS/WRS_2_NO_OVERLAP")

ibge_states = ee.FeatureCollection(
    "users/agrosatelite_mapbiomas/REGIONS/ibge_estados_2019"
)

reference_collection = ee.ImageCollection(
    "users/agrosatelite_mapbiomas/REFERENCE_MAPS/AGRICULTURE/PERENNIAL_CROPS/COFFEE/COLLECTION_30M"
)

# brazil = ee.Image(0).paint(ibge_states, 1)

# fmt: off
feature_space = [
    'BLUE_mean', 'GREEN_mean', 'RED_mean', 'NIR_mean', 'SWIR1_mean', 'SWIR2_mean',
    'EVI2_mean', 'NDWI_mean',

    'BLUE_stdDev', 'GREEN_stdDev', 'RED_stdDev', 'NIR_stdDev', 'SWIR1_stdDev', 'SWIR2_stdDev',
    'EVI2_stdDev', 'NDWI_stdDev',

    'BLUE_min', 'GREEN_min', 'RED_min', 'NIR_min', 'SWIR1_min', 'SWIR2_min',
    'EVI2_min', 'NDWI_min',

    'BLUE_p20', 'GREEN_p20', 'RED_p20', 'NIR_p20', 'SWIR1_p20', 'SWIR2_p20',
    'EVI2_p20', 'NDWI_p20',

    'BLUE_median', 'GREEN_median', 'RED_median', 'NIR_median', 'SWIR1_median', 'SWIR2_median',
    'EVI2_median', 'NDWI_median',

    'BLUE_p80', 'GREEN_p80', 'RED_p80', 'NIR_p80', 'SWIR1_p80', 'SWIR2_p80',
    'EVI2_p80', 'NDWI_p80',

    'BLUE_max', 'GREEN_max', 'RED_max', 'NIR_max', 'SWIR1_max', 'SWIR2_max',
    'EVI2_max', 'NDWI_max',

    'BLUE_qmo', 'GREEN_qmo', 'RED_qmo', 'NIR_qmo', 'SWIR1_qmo', 'SWIR2_qmo', 
    'EVI2_qmo', 'NDWI_qmo'
]
# fmt: on

# MOSAIC


def addSufix(sufix):
    return lambda band_name: ee.String(band_name).cat(sufix)


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


def filter_collection(collection, roi, start_date, end_date):
    return (
        collection.filterBounds(roi)
        .filterDate(start_date, end_date)
        .filterMetadata("CLOUD_COVER_LAND", "less_than", max_cloud_cover)
        .limit(images_limit, "CLOUD_COVER_LAND")
        .padronize_band_names()
        .score_images()
    )


def process_image(image):
    cloud_mask = image.select("QA_SCORE").eq(1)
    image = image.updateMask(cloud_mask)

    image = calculate_indexes(image, indexes)

    return image.select(ee.List(bands).cat(indexes_names))


tasks = []

for year, states in years_states.items():

    start_date = ee.Date.fromYMD(year, 1, 1)
    end_date = ee.Date.fromYMD(year + 1, 1, 1)

    reference = reference_collection.filter(
        ee.Filter.And(ee.Filter.eq("year", year), ee.Filter.inList("state", states))
    ).Or()

    filters = [ee.Filter.eq(state, 1) for state in states]

    regions = grid.filter(ee.Filter.Or(*filters))

    states_mask = ee.Image(0).paint(
        ibge_states.filter(ee.Filter.inList("SIGLA_UF", states)), 1
    )

    for pathrow in regions.aggregate_array("PATHROW").getInfo():

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

        samples = (
            mosaic.select(feature_space)
            .addBands(reference.rename("class"))
            .unmask()
            .updateMask(states_mask)
            .sample(
                region=geometry,
                scale=30,
                numPixels=6000,
                seed=1,
                geometries=True,
                tileScale=8,
            )
        )

        samples_extra = (
            mosaic.select(feature_space)
            .addBands(reference.rename("class"))
            .unmask()
            .updateMask(states_mask)
            .stratifiedSample(
                numPoints=2500,
                classBand="class",
                region=geometry,
                scale=30,
                classValues=[0, 1],
                classPoints=[0, 2500],
                tileScale=10,
                geometries=True,
            )
        )

        file_name = f"COFFEE_SAMPLES_{year}_{pathrow}"

        # task = ee.batch.Export.table.toAsset(
        #     collection=samples,
        #     description=f"{file_name}_SIMPLE",
        #     assetId=f"users/dgoulart/MAPBIOMAS/C6/COFFEE/SAMPLES/BY_PATHROW/{file_name}",
        # )
        # tasks.append(task)

        task = ee.batch.Export.table.toAsset(
            collection=samples_extra,
            description=f"{file_name}_EXTRA",
            assetId=f"users/dgoulart/MAPBIOMAS/C6/COFFEE/SAMPLES/BY_PATHROW_EXTRA/{file_name}",
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
