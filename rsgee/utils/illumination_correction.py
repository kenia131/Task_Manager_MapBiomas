import ee
from math import pi
from rsgee.utils.solar_position import get_solar_position

#
# def to apply the Sun-Canopy-Sensor + C (SCSc) correction method to Landsat images.
# Created by Patrick Burns and Matt Macander
# Adapted from https://code.earthengine.google.com/6db5cebaccadeb6be09186cf6f464639
# Adapted by Djonathan Goulart
#

COEFFICIENTS = "users/agrosatelite_mapbiomas/BLARD/TOPOGRAPHY/BY_YEAR/COEFFICIENTS_2014"

COEFFS_FIELD = "TOPOGRAPHY_COEFFS"

JOIN_FIELD = "LANDSAT_SCENE_ID"

DEFAULT_BANDS = ["BLUE", "GREEN", "RED", "NIR", "SWIR1", "SWIR2"]


def correctImage(originalImage, bandsToCorrect=DEFAULT_BANDS, useExportedCoeffs=True):

    if useExportedCoeffs and COEFFICIENTS:
        sceneId = originalImage.getString(JOIN_FIELD)
        coeffs = (
            ee.FeatureCollection(COEFFICIENTS)
            .filterMetadata(JOIN_FIELD, "equals", sceneId)
            .first()
        )

        originalImage = originalImage.set(COEFFS_FIELD, coeffs)

    return _correctImage(originalImage, bandsToCorrect, useExportedCoeffs)


def correctCollection(collection, bandsToCorrect=DEFAULT_BANDS, useExportedCoeffs=True):

    if useExportedCoeffs and COEFFICIENTS:
        collection = joinCoefficients(collection)

    correctedCollection = collection.map(
        lambda originalImage: _correctImage(
            originalImage, bandsToCorrect, useExportedCoeffs
        )
    )

    return correctedCollection


def joinCoefficients(collection):
    collection = ee.ImageCollection(collection)

    dateField = "system:time_start"

    startDate = ee.Date(collection.aggregate_min(dateField)).advance(-1, "day")
    endDate = ee.Date(collection.aggregate_max(dateField)).advance(1, "day")

    coefficients = ee.FeatureCollection(COEFFICIENTS).filterDate(startDate, endDate)

    collection = ee.Join.saveFirst(matchKey=COEFFS_FIELD).apply(
        primary=collection,
        secondary=coefficients,
        condition=ee.Filter.equals(leftField=JOIN_FIELD, rightField=JOIN_FIELD),
    )

    return ee.ImageCollection(collection)


def _correctImage(originalImage, bandsToCorrect=DEFAULT_BANDS, useExportedCoeffs=True):

    illumCondition = getIlluminationCondition(originalImage)
    correctionMask = getCorrectionMask(originalImage, illumCondition)

    image = originalImage.select(bandsToCorrect).updateMask(correctionMask)

    illumCondition = illumCondition.updateMask(correctionMask)

    coefficients = getSCScCoefficients(image, illumCondition, useExportedCoeffs)

    correctedImage = applySCSc(image, illumCondition, coefficients).unmask(
        originalImage.select(bandsToCorrect)
    )
    return originalImage.addBands(correctedImage, None, True)


def getCorrectionMask(originalImage, illumCondition):
    slopeMask = illumCondition.select("slope").gte(5)
    ilumnMask = illumCondition.select("illumCond").gte(0)
    nirMask = originalImage.select("NIR").gt(-0.1)

    correctionMask = slopeMask.And(ilumnMask).And(nirMask)

    return correctionMask


def getIlluminationCondition(img):
    solarPosition = get_solar_position(img.date())

    sunZenith = solarPosition.select("sun_zen")
    sunAzimuth = solarPosition.select("sun_az")

    dem = ee.Image("USGS/SRTMGL1_003")

    slopeDeg = ee.Terrain.slope(dem)
    slopeRad = deg2rad(slopeDeg)
    aspetcRad = deg2rad(ee.Terrain.aspect(dem))

    cosSunZenith = img.expression(
        "cosSunZenith = cos(sunZenith)", {"sunZenith": sunZenith}
    )

    cosSlope = img.expression("cosSlope = cos(slope)", {"slope": slopeRad})

    slopeIllumination = img.expression(
        "slopeIllum = cosSunZenith * cosSlope",
        {"cosSunZenith": cosSunZenith, "cosSlope": cosSlope},
    )

    aspectIllumination = img.expression(
        "aspectIllum = sin(sunZenith) * sin(slope) * cos(sunAzimuth - aspect)",
        {
            "sunZenith": sunZenith,
            "sunAzimuth": sunAzimuth,
            "slope": slopeRad,
            "aspect": aspetcRad,
        },
    )

    illuminationCondition = img.expression(
        "illumCond = slopeIllum + aspectIllum",
        {"slopeIllum": slopeIllumination, "aspectIllum": aspectIllumination},
    )

    return (
        illuminationCondition.addBands(cosSunZenith)
        .addBands(cosSlope)
        .addBands(slopeDeg)
    )


def getSCScCoefficients(image, illumCondition, useExportedCoeffs):
    if useExportedCoeffs:
        return getCoefficientsFromProperties(image)
    else:
        return calculateCoefficients(image, illumCondition)


def getCoefficientsFromProperties(image):
    return ee.Feature(image.get(COEFFS_FIELD)).toArray(image.bandNames())


def calculateCoefficients(image, illumCondition):
    reducer = ee.Reducer.linearRegression(numX=2, numY=image.bandNames().length())

    linearFit = (
        illumCondition.select("illumCond")
        .addBands(ee.Image.constant(1))
        .addBands(image)
        .reduceRegion(
            reducer=reducer,
            geometry=image.geometry().buffer(-5000),
            scale=30,
            maxPixels=10e10,
        )
        .getArray("coefficients")
    )

    scale = linearFit.slice(0, 0, 1)
    offset = linearFit.slice(0, 1, 2)

    coef = offset.divide(scale).project([1])

    return coef


def applySCSc(image, illumCondition, coefficients):
    coefficients = ee.Image(coefficients).arrayFlatten([image.bandNames()])

    corrected = ee.Image().expression(
        "(image * (ic.cosSlope * ic.cosSunZenith + coef)) / (ic.illumCond + coef)",
        {"image": image, "ic": illumCondition, "coef": coefficients},
    )

    return corrected.rename(image.bandNames())


def addExpr(img, expr, args):
    args = args or {}
    args.pi = pi
    args.i = img

    return img.expression(expr, args)


def deg2rad(value):
    return ee.Image(value).multiply(pi).divide(180)


def getCoefficientsToExport(collection, bandsToCorrect=DEFAULT_BANDS):
    def getCoefficients(originalImage):
        illumCondition = getIlluminationCondition(originalImage)
        correctionMask = getCorrectionMask(originalImage, illumCondition)

        image = originalImage.select(bandsToCorrect).updateMask(correctionMask)

        illumCondition = illumCondition.updateMask(correctionMask)

        coeffs = getSCScCoefficients(image, illumCondition)

        geometry = originalImage.geometry().centroid(30)
        coeffs = ee.Dictionary.fromLists(bandsToCorrect, coeffs.toList())

        return ee.Feature(geometry, coeffs).copyProperties(
            originalImage,
            [
                "DATE_ACQUIRED",
                "LANDSAT_SCENE_ID",
                "system:time_start",
                "WRS_PATH",
                "WRS_ROW",
            ],
        )

    coefficients = collection.map(getCoefficients)

    return coefficients
