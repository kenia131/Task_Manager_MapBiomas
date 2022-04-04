import ee

from rsgee.collections import Landsat5, Landsat7, Landsat8, Modis
from rsgee.band import Band

# import rsgee.utils.cloud as cloudLib

MODIS_COLLECTION = Modis.MOD09A1

NORMALIZATION_BANDS = [
    Band.BLUE,
    Band.GREEN,
    Band.RED,
    Band.NIR,
    Band.SWIR1,
    Band.SWIR2,
]

NORMALIZATION_TARGET = (
    ee.Image(
        "users/agrosatelite_mapbiomas/COLECAO_5/BLARD/MODIS_2000_2019_NORMALIZATION_TARGET"
    )
    .select(NORMALIZATION_BANDS)
    .divide(10000)
)

SPATIAL_RESOLUTION = 30
DEFAULT_MAX_CLOUD_COVER = 90

BRIGHT_OBJECTS_THRESHOLD = 0.5
CFACTOR = 0.05

MIN_PSINV_PIXELS_COUNT = 5000

COEFFICIENTS = ee.FeatureCollection(
    "users/agrosatelite_mapbiomas/BLARD/NORMALIZATION/COEFFICIENTS"
)

COEFFS_FIELD = "NORMALIZATION_COEFFICIENTS"
JOIN_FIELD = "LANDSAT_SCENE_ID"


def get_normalized_collection(
    roi,
    start_date,
    end_date,
    max_cloud_cover,
    bands=NORMALIZATION_BANDS,
    use_exported_coeffs=True,
):
    collection = get_landsat_collection(roi, start_date, end_date, max_cloud_cover)
    return apply_normalization(collection, bands, use_exported_coeffs)


def get_landsat_collection(
    roi, start_date, end_date, max_cloud_cover=DEFAULT_MAX_CLOUD_COVER
):
    def filter(collection):
        return (
            collection.filterBounds(roi)
            .filterDate(start_date, end_date)
            .filterMetadata("CLOUD_COVER", "less_than", max_cloud_cover)
            .padronize_band_names()
            .score_images()
        )

    landsat5 = filter(Landsat5.TOA.Tier1())
    landsat7 = filter(Landsat7.TOA.Tier1())
    landsat8 = filter(Landsat8.TOA.Tier1())

    collection = landsat5.merge(landsat7).merge(landsat8)

    return collection


def apply_normalization(collection, bands, use_exported_coeffs=True):

    if use_exported_coeffs and COEFFICIENTS:
        collection = join_coefficients(collection)
    else:
        collection = prepare_to_normalization(collection)
        use_exported_coeffs = False

    def normalize(image):
        return normalize_image(image, bands, use_exported_coeffs)

    corrected_collection = collection.map(normalize)

    return corrected_collection


def join_coefficients(collection):
    collection = ee.ImageCollection(collection)

    start_millis = collection.aggregate_min("system:time_start")
    start_millis = ee.List([start_millis, 0]).reduce(ee.Reducer.firstNonNull())

    end_millis = collection.aggregate_max("system:time_start")
    end_millis = ee.List([end_millis, 0]).reduce(ee.Reducer.firstNonNull())

    start_date = ee.Date(start_millis).advance(-1, "day")
    end_date = ee.Date(end_millis).advance(1, "day")

    coefficients = COEFFICIENTS.filterDate(start_date, end_date)

    collection = ee.Join.saveFirst(matchKey=COEFFS_FIELD).apply(
        primary=collection,
        secondary=coefficients,
        condition=ee.Filter.equals(leftField=JOIN_FIELD, rightField=JOIN_FIELD),
    )

    return ee.ImageCollection(collection)


def prepare_to_normalization(collection):
    return (
        collection.map(add_pseudo_invariant_objects_band)
        .map(count_pseudo_invariant_pixels)
        .filterMetadata("PSINV_PIXELS_COUNT", "not_less_than", MIN_PSINV_PIXELS_COUNT)
    )


def add_pseudo_invariant_objects_band(image):
    cloud_mask = image.select(Band.QA_SCORE).eq(1)

    normalization_target_mask = NORMALIZATION_TARGET.mask().reduce(
        ee.Reducer.allNonZero()
    )

    ps_inv_pixels_mask = (
        NORMALIZATION_TARGET.select(Band.RED, Band.SWIR1)
        .subtract(image.select(Band.RED, Band.SWIR1))
        .abs()
        .lt(CFACTOR)
        .reduce(ee.Reducer.allNonZero())
    )

    bright_objects_mask = image.select(Band.RED).lte(BRIGHT_OBJECTS_THRESHOLD)

    final_mask = (
        image.select(NORMALIZATION_BANDS)
        .mask()
        .reduce(ee.Reducer.allNonZero())
        .updateMask(ps_inv_pixels_mask)
        .updateMask(normalization_target_mask)
        .updateMask(bright_objects_mask)
        .updateMask(cloud_mask)
        .rename("PSINV_PIXELS_MASK")
    )

    return image.addBands(final_mask)


def count_pseudo_invariant_pixels(image):
    ps_inv_mask = image.select("PSINV_PIXELS_MASK")

    ps_inv_pixels_count = (
        ps_inv_mask.reduceRegion(
            reducer=ee.Reducer.count(),
            geometry=image.geometry(),
            scale=SPATIAL_RESOLUTION,
            maxPixels=10e10,
        )
        .values()
        .getNumber(0)
    )

    return image.set("PSINV_PIXELS_COUNT", ps_inv_pixels_count)


def normalize_image(image, bands=NORMALIZATION_BANDS, use_exported_coeffs=True):
    coefficients = None

    if use_exported_coeffs:
        coefficients = get_coefficients_from_properties(image, bands)
    else:
        coefficients = calculate_coefficients(image, bands)

    gain = coefficients.getArray("gain")
    offset = coefficients.getArray("offset")

    gain_img = ee.Image(gain).arrayFlatten([bands])
    offset_img = ee.Image(offset).arrayFlatten([bands])

    normalized_image = image.select(bands).multiply(gain_img).add(offset_img)

    return image.addBands(normalized_image, None, True).set(
        COEFFS_FIELD,
        {
            "gain": ee.Dictionary.fromLists(bands, gain.toList()),
            "offset": ee.Dictionary.fromLists(bands, offset.toList()),
        },
    )


def get_coefficients_from_properties(image, bands):
    sorted_bands = ee.List(NORMALIZATION_BANDS).sort()
    coeffs = ee.Feature(image.get(COEFFS_FIELD))

    gain = coeffs.select([".*_gain"], sorted_bands)
    offset = coeffs.select([".*_offset"], sorted_bands)

    return ee.Dictionary(
        {
            "gain": ee.Feature(gain).toArray(bands),
            "offset": ee.Feature(offset).toArray(bands),
        }
    )


def calculate_coefficients(image, bands):
    sorted_bands = ee.List(bands).sort()
    mask = image.select("PSINV_PIXELS_MASK")

    temp_bands_img = sorted_bands.map(compose_name("img_"))
    temp_bands_ref = sorted_bands.map(compose_name("ref_"))

    image = image.select(sorted_bands, temp_bands_img)
    target = NORMALIZATION_TARGET.select(sorted_bands, temp_bands_ref)

    reducers = ee.Reducer.mean().combine(ee.Reducer.stdDev(), None, True)

    stats = (
        image.addBands(target)
        .updateMask(mask)
        .reduceRegion(
            reducer=reducers,
            geometry=image.geometry(),
            scale=SPATIAL_RESOLUTION,
            maxPixels=1e13,
        )
    )

    stats = ee.Feature(None, stats)

    def select(pattern):
        return ee.Feature(stats.select(pattern, sorted_bands))

    image_means = select(["img_.*_mean"]).toArray(bands)
    image_std_dev = select(["img_.*_stdDev"]).toArray(bands)

    target_means = select(["ref_.*_mean"]).toArray(bands)
    target_std_dev = select(["ref_.*_stdDev"]).toArray(bands)

    gain = target_std_dev.divide(image_std_dev)
    offset = target_means.subtract(gain.multiply(image_means))

    coefficients = ee.Dictionary({"gain": gain, "offset": offset})

    return coefficients


def compose_name(prefix="", sufix=""):
    return lambda name: ee.String(prefix).cat(name).cat(sufix)
