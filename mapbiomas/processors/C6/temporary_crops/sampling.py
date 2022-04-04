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

years = [1987]

max_cloud_cover = 80
indexes = [Index.NDWI, Index.EVI2, Index.CAI]
indexes_names = [index.name for index in indexes]

bands = ["GREEN", "RED", "NIR", "SWIR1", "SWIR2", "TIR1"]
normalization_bands = ["GREEN", "RED", "NIR", "SWIR1", "SWIR2"]

max_error = 30

grid = (
    ee.FeatureCollection("users/agrosatelite_mapbiomas/REGIONS/WRS_2_NO_OVERLAP")
    .filterMetadata("AC_WRS", "equals", 1)
    .filter(
        ee.Filter.inList(
            "PATHROW",
            [223078, 223079, 223080, 224078, 224079, 224080, 222078, 222079, 222080],
        )
    )
)


# reference = ee.Image(
#     "users/agrosatelite_mapbiomas/REFERENCE_MAPS/AGRICULTURE/AGRICULTURE_2016_30M"
# ).eq(1)

# MOSAIC


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


def get_period_mosaic(roi, period, year):
    dates = region.getString(period).split(",")
    start_date = parse_date(dates.getString(0), year)
    end_date = parse_date(dates.getString(1), year)

    bounds = roi.geometry(max_error).centroid(max_error)

    collection = get_normalized_collection(
        bounds, start_date, end_date, max_cloud_cover, normalization_bands, True
    )

    def process_image(image):
        cloud_mask = image.select("QA_SCORE").eq(1)
        image = image.updateMask(cloud_mask)

        image = calculate_indexes(image, indexes)

        return image.select(ee.List(bands).cat(indexes_names))

    collection = collection.map(process_image)

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

    return mosaic.rename(new_names)


tasks = []

for year in years:

    reference = (
        ee.ImageCollection(
            "users/agrosatelite_mapbiomas/COLECAO_5/RESULTS/ANNUAL/TRUE_RAW"
        )
        .filterMetadata("year", "equals", year)
        .first()
    )

    for pathrow in grid.aggregate_array("PATHROW").getInfo():

        region = grid.filterMetadata("PATHROW", "equals", pathrow).first()
        geometry = region.geometry(max_error)

        wet_mosaic = get_period_mosaic(region, "AC_WET", year)
        dry_mosaic = get_period_mosaic(region, "AC_DRY", year)

        mosaic = wet_mosaic.addBands(dry_mosaic)

        # fmt: off
        mosaic = add_cei(mosaic, 'AC_DRY_EVI2_min', 'AC_WET_EVI2_qmo', 'ANNUAL_EVI2_cei')
        mosaic = add_cei(mosaic, 'AC_DRY_NDWI_min', 'AC_WET_NDWI_qmo', 'ANNUAL_NDWI_cei')
        mosaic = add_cei(mosaic, 'AC_DRY_NIR_min', 'AC_WET_NIR_qmo', 'ANNUAL_NIR_cei')
        # fmt: on

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

        samples_extra = (
            mosaic.addBands(reference.rename("class"))
            .unmask()
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

        file_name = f"TEMPORARY_CROPS_SAMPLES_{year}_{pathrow}"

        task = ee.batch.Export.table.toAsset(
            collection=samples,
            description=f"{file_name}_SIMPLE",
            assetId=f"users/dgoulart/MAPBIOMAS/C6/TEMPORARY_CROPS/SAMPLES/BY_PATHROW/{file_name}",
        )
        tasks.append(task)

        task = ee.batch.Export.table.toAsset(
            collection=samples_extra,
            description=f"{file_name}_EXTRA",
            assetId=f"users/dgoulart/MAPBIOMAS/C6/TEMPORARY_CROPS/SAMPLES/BY_PATHROW_EXTRA/{file_name}",
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
