from functools import reduce

import ee

from rsgee.collections import Landsat5, Landsat7, Landsat8, Modis
from rsgee.band import Band

LANDSAT_COLLECTIONS = [Landsat5.TOA.Tier1, Landsat7.TOA.Tier1, Landsat8.TOA.Tier1]

LANDSAT_GRID = "users/agrosatelite_mapbiomas/COLECAO_5/GRIDS/BRASIL_COMPLETO"

MODIS_COLLECTION = Modis.MOD09A1
MODIS_BANDS_SCALES = [0.0001, 0.0001, 0.0001, 0.0001, 0.0001, 0.0001]

BANDS = [Band.BLUE, Band.GREEN, Band.RED, Band.NIR, Band.SWIR1, Band.SWIR2]
THERMAL_BAND = Band.TIR1
ALL_BANDS = [*BANDS, THERMAL_BAND]

# NORMALIZATION_TARGET = "users/agrosatelite_mapbiomas/COLECAO_5/BLARD/MODIS_2000_2011_NORMALIZATION_TARGET";
NORMALIZATION_TARGET = (
    "users/agrosatelite_mapbiomas/COLECAO_5/BLARD/MODIS_2000_2019_NORMALIZATION_TARGET"
)

SPATIAL_RESOLUTION = 30

CFACTOR = 0.05
OUTPUT_SCALE = 10000

PSINV_PIXELS_MASK = "PSINV_PIXELS_MASK"
PSINV_PIXELS_COUNT = "PSINV_PIXELS_COUNT"
MIN_PSINV_PIXELS_COUNT = 5000


def get16DayProductByPathRow(
    path, row, start_date, end_date, cloud_cover, export_bands
):
    roi = (
        ee.FeatureCollection(LANDSAT_GRID)
        .filterMetadata("PATH", "equals", path)
        .filterMetadata("ROW", "equals", row)
        .first()
        .geometry()
        .centroid()
    )

    return get16DayproductByROI(roi, start_date, end_date, cloud_cover, export_bands)


def get16DayproductByROI(roi, start_date, end_date, cloud_cover, export_bands):
    # collection = getLandsatCollection(roi, start_date, end_date, cloud_cover)
    # normalized_collection = getLandsatNormCollection(collection, export_bands)
    normalized_collection = (
        normalize_collection(collection, start_date, end_date, roi)
        .select([Band.QA_SCORE, *export_bands])
        .map(addQualityFlag)
    )

    return build16DayProduct(
        roi, normalized_collection, start_date, end_date, export_bands
    )


def getLandsatCollection(roi, startDate, endDate, cloud_cover):
    def filter_collection(merged_collection, collection):
        filtered = (
            collection()
            .filterBounds(roi)
            .filterDate(startDate, endDate)
            .filterMetadata("CLOUD_COVER", "less_than", cloud_cover)
            .padronize_band_names()
            .score_images()
        )

        return merged_collection.merge(filtered)

    landsatCollection = reduce(
        filter_collection, LANDSAT_COLLECTIONS, ee.ImageCollection([])
    )

    return landsatCollection


def normalize_collection(collection, start_date, end_date, roi):
    # bandsRegex = ee.List(BANDS).map(lambda band: ee.String(band).cat("_.*"))
    coefficients = (
        ee.FeatureCollection(
            "users/agrosatelite_mapbiomas/BLARD/NORMALIZATION/COEFFICIENTS"
        )
        .filterDate(start_date, end_date)
        .filterBounds(roi.buffer(200000))
    )

    def add_sufix(sufix):
        return lambda band: ee.String(band).cat(sufix)

    gainBands = ee.List(BANDS).map(add_sufix("_gain"))
    offsetBands = ee.List(BANDS).map(add_sufix("_offset"))

    collection = ee.Join.saveFirst(matchKey="NORMALIZATION_COEFFS").apply(
        primary=collection,
        secondary=coefficients,
        condition=ee.Filter.equals(
            leftField="LANDSAT_SCENE_ID", rightField="LANDSAT_SCENE_ID"
        ),
    )

    def apply_normalization(image):
        img_coefs = ee.Feature(image.get("NORMALIZATION_COEFFS"))

        gain = ee.Image.constant(img_coefs.toArray(gainBands).toList())
        offset = ee.Image.constant(img_coefs.toArray(offsetBands).toList())

        normalized = ee.Image(image).select(BANDS).multiply(gain).add(offset)

        return image.addBands(normalized, None, True)

    normalized_collection = ee.ImageCollection(collection).map(apply_normalization)

    return normalized_collection


def getLandsatNormCollection(landsat_collection, bands):
    landsatNormCollection = (
        landsat_collection.map(addPseudoinvariantBand)
        .filterMetadata(PSINV_PIXELS_COUNT, "not_less_than", MIN_PSINV_PIXELS_COUNT)
        .select([Band.QA_SCORE, PSINV_PIXELS_MASK, *bands])
        .map(applyHistogramMatching)
        .map(addQualityFlag)
    )

    return landsatNormCollection


def build16DayProduct(roi, normalized_collection, start_date, end_date, export_bands):
    intervals = ee.FeatureCollection(getIntervals(start_date, end_date))

    def cross_with_periods(wrs, periods_with_pathrow):
        def set_pathrow(period):
            return period.set(
                {
                    "path": wrs.get("PATH"),
                    "row": wrs.get("ROW"),
                    "geometry": wrs.geometry(),
                }
            )

        periods = intervals.map(set_pathrow)

        return ee.FeatureCollection(periods_with_pathrow).merge(periods)

    def group_images_by_period_and_pathrow(period):
        period = ee.Feature(period)

        start_date = ee.Date(period.get("start_date"))
        end_date = ee.Date(period.get("end_date"))
        path = period.get("path")
        row = period.get("row")

        filtered_collection = (
            normalized_collection.filterDate(start_date, end_date)
            .filterMetadata("WRS_PATH", "equals", path)
            .filterMetadata("WRS_ROW", "equals", row)
        )

        return period.set(
            {
                "collection": filtered_collection,
                "size": filtered_collection.size(),
                # 'interval': period.get("interval"),
                # 'start_date': start_date.millis(),
                # 'end_date': end_date.millis(),
                # 'pathrow': pathrow
            }
        )

    def build_products(feature):
        collection = ee.ImageCollection(feature.get("collection"))
        start_date = ee.Date(feature.get("start_date"))
        end_date = ee.Date(feature.get("end_date"))
        roi = feature.get("geometry")

        mosaic = collection.qualityMosaic("INVERSE_QF")

        if THERMAL_BAND in export_bands:
            extraBands = mosaic.select(THERMAL_BAND, "QF").multiply([10, 1])
        else:
            extraBands = mosaic.select("QF")

        landsatNormMosaic = (
            mosaic.select(export_bands)
            .multiply(OUTPUT_SCALE)
            .addBands(extraBands, None, True)
            .int16()
            .set(
                {
                    "system:time_start": start_date.millis(),
                    "system:footprint": roi,
                    "WRS_PATH": feature.get("path"),
                    "WRS_ROW": feature.get("row"),
                    "SPACECRAFT_ID": "BLARD",
                    "START_DATE": start_date.millis(),
                    "END_DATE": end_date.millis(),
                    "IMAGES_COUNT": collection.size(),
                    "INTERVAL": feature.get("interval"),
                }
            )
            .clip(roi)
        )

        return landsatNormMosaic

    regionsByInterval = (
        ee.FeatureCollection(
            "users/agrosatelite_mapbiomas/COLECAO_5/GRIDS/BRASIL_COMPLETO"
        )
        .filterBounds(roi)
        .iterate(cross_with_periods, ee.FeatureCollection([]))
    )

    products = (
        ee.FeatureCollection(regionsByInterval)
        .map(group_images_by_period_and_pathrow)
        .filterMetadata("size", "greater_than", 0)
        .map(build_products)
    )

    return ee.ImageCollection(products)


def addPseudoinvariantBand(landsatImage):
    roi = landsatImage.geometry()

    normalizationTarget = ee.Image(getNormalizationTarget())
    pseudoInvariantMask = getPseudoInvariantObjects(landsatImage, normalizationTarget)

    psinvCount = (
        pseudoInvariantMask.reduceRegion(
            reducer=ee.Reducer.sum(),
            geometry=roi,
            scale=SPATIAL_RESOLUTION,
            maxPixels=10e10,
            tileScale=2,
        )
        .values()
        .getNumber(0)
    )

    return (
        ee.Image(landsatImage)
        .addBands(pseudoInvariantMask.select([0]).rename(PSINV_PIXELS_MASK))
        .set(PSINV_PIXELS_COUNT, psinvCount)
    )


def getPseudoInvariantObjects(landsatImage, normalizationTarget):
    landsatImage = ee.Image(landsatImage)
    normalizationTarget = ee.Image(normalizationTarget)

    landsatCloudMask = landsatImage.select(Band.QA_SCORE).eq(1)
    normalizationTargetMask = normalizationTarget.select(0).mask()

    differenceLandsatMODIS = (
        normalizationTarget.select(Band.RED, Band.SWIR1)
        .subtract(landsatImage.select(Band.RED, Band.SWIR1))
        .abs()
    )

    pseudoInvariantPixels = differenceLandsatMODIS.lt(CFACTOR).reduce(
        ee.Reducer.allNonZero()
    )
    brightObjects = landsatImage.select(Band.RED).gt(0.5)

    pseudoInvariantMask = (
        pseudoInvariantPixels.And(normalizationTargetMask)
        .And(brightObjects.Not())
        .And(landsatCloudMask)
    )

    return pseudoInvariantMask


def applyHistogramMatching(landsatImage):
    landsatImage = ee.Image(landsatImage)
    # qaBand = landsatImage.select(Band.QA_SCORE)
    # thermalBand = landsatImage.select(THERMAL_BAND)

    normalizationTarget = ee.Image(getNormalizationTarget())
    pseudoInvariantMask = landsatImage.select(PSINV_PIXELS_MASK)
    normalizationBands = landsatImage.bandNames().removeAll(
        [Band.QA_SCORE, THERMAL_BAND, PSINV_PIXELS_MASK]
    )

    intercalibration = ee.Image(
        intercalibrate(
            landsatImage, normalizationTarget, pseudoInvariantMask, normalizationBands
        )
    )

    return landsatImage.addBands(intercalibration, None, True)


def intercalibrate(image, reference, mask, bands):
    bands = ee.List(bands)
    temp_bands_img = bands.map(lambda band: ee.String("img_").cat(band))
    temp_bands_ref = bands.map(lambda band: ee.String("ref_").cat(band))

    image = image.select(bands, temp_bands_img)
    reference = reference.select(bands, temp_bands_ref)

    bands_mean = bands.map(lambda band: ee.String(band).cat("_mean"))
    bands_std_dev = bands.map(lambda band: ee.String(band).cat("_stdDev"))

    bandsOrder = bands.map(lambda band: ee.String(".*").cat(band).cat(".*"))

    stats = (
        image.addBands(reference)
        .updateMask(mask)
        .reduceRegion(
            reducer=ee.Reducer.mean().combine(ee.Reducer.stdDev(), None, True),
            geometry=image.geometry(),
            scale=SPATIAL_RESOLUTION,
            maxPixels=1e13,
            bestEffort=True,
            tileScale=2,
        )
        .toImage()
        .select(bandsOrder)
    )

    image_means = stats.select("img_.*_mean").rename(bands_mean)
    image_std_dev = stats.select("img_.*_stdDev").rename(bands_std_dev)

    reference_means = stats.select("ref_.*_mean").rename(bands_mean)
    reference_std_dev = stats.select("ref_.*_stdDev").rename(bands_std_dev)

    a = reference_std_dev.divide(image_std_dev)
    b = reference_means.subtract(a.multiply(image_means))
    inter = image.multiply(a).add(b).rename(bands)

    return ee.Image(inter)


def fillGap(image):
    fillgap = image.focal_median(4, "square", "pixels", 3)
    qa = fillgap.select(Band.BQA)
    fillgap = fillgap.blend(image)
    return ee.Image(
        fillgap.addBands(qa, None, True).copyProperties(image, image.propertyNames())
    )


def getNormalizationTarget():
    return ee.Image(NORMALIZATION_TARGET).select(BANDS).multiply(MODIS_BANDS_SCALES)


def getIntervals(startDateInput, endDateInput):
    startDateInput = ee.Date(startDateInput)
    endDateInput = ee.Date(endDateInput)
    days = 16

    def get_intervals(year):
        def to_date(doy):
            return ee.Date.fromYMD(year, 1, 1).advance(doy, "day")

        last_doy = ee.Date.fromYMD(year, 12, 31).getRelative("day", "year")

        intervals_indexes = ee.List.sequence(1, last_doy.divide(days).ceil())
        intervals_start = ee.List.sequence(1, last_doy, days).map(to_date)
        intervals_end = (
            ee.List.sequence(1 + days, last_doy, days).add(last_doy).map(to_date)
        )

        intervals = intervals_indexes.zip(intervals_start.zip(intervals_end))

        return intervals

    def to_feature(interval):
        interval = ee.List(interval)
        dates = ee.List(interval.get(1))

        return ee.Feature(
            None,
            {
                "start_date": ee.Date(dates.get(0)),
                "end_date": ee.Date(dates.get(1)),
                "interval": interval.getNumber(0),
            },
        )

    def flatten(dates, dates_list):
        return ee.List(dates_list).cat(dates)

    start_year = startDateInput.get("year")
    end_year = endDateInput.get("year")

    years = ee.List.sequence(start_year, end_year)
    dates_by_year = years.map(get_intervals)
    dates = dates_by_year.iterate(flatten, ee.List([]))
    features = ee.List(dates).map(to_feature)
    collection = ee.FeatureCollection(features)

    start_date = ee.Date(startDateInput)
    end_date = ee.Date(endDateInput).advance(1, "day")

    date_filter = ee.Filter.And(
        ee.Filter.gte("start_date", start_date), ee.Filter.lte("end_date", end_date)
    )

    collection = collection.filter(date_filter)

    return collection


def addQualityFlag(image):
    # qualityFlag = ee.Image(cloudLib.cloudScore(image)).rename("QF")
    qualityFlag = image.select([Band.QA_SCORE], ["QF"])

    ndvi = image.normalizedDifference([Band.NIR, Band.RED]).clamp(0, 1).rename("NDVI")

    inverseQualityFlag = (
        qualityFlag.multiply(-1)
        .add(ndvi)
        .updateMask(qualityFlag.eq(0).Not())
        .rename("INVERSE_QF")
    )

    normImage = image.addBands(qualityFlag).addBands(inverseQualityFlag)

    return normImage


# ee.Initialize(use_cloud_api=False)

# print(getIntervals("2018-01-01", "2018-12-31").getInfo())

# productsDemo = ee.ImageCollection(
#     get16Dayproduct(221, 64, "2015-12-01", "2015-12-16", 90,
#     ["NIR",  "SWIR1",  "RED"]))\
#     .first()

# centroid = productsDemo.geometry().centroid().getInfo()

# import ee.mapclient
# ee.mapclient.centerMap(centroid["coordinates"][0],
#                        centroid["coordinates"][1], 10)
# ee.mapclient.addToMap(ee.Image(productsDemo),
#                     vis_params={'min': 0, 'max': 4000})
