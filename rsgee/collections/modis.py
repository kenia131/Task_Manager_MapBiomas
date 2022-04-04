from rsgee.band import Band
from rsgee.imagecollection import ImageCollection
from rsgee.utils.bitmask import build_bitmasks


class _Modis:
    BASE_ID = 'MODIS/{product}'


class MOD09A1(_Modis, ImageCollection):

    COLLECTION_NAME = 'MOD09A1'

    BANDS_MAPPING = {
        "sur_refl_b01": Band.RED,
        "sur_refl_b02": Band.NIR,
        "sur_refl_b03": Band.BLUE,
        "sur_refl_b04": Band.GREEN,
        "sur_refl_b05": Band.NIR2,
        "sur_refl_b06": Band.SWIR1,
        "sur_refl_b07": Band.SWIR2,
        "StateQA": Band.BQA,
        "SolarZenith": "SolarZenith",
        "ViewZenith": "ViewZenith",
        "RelativeAzimuth": "RelativeAzimuth",
        "QA": "QA",
        "DayOfYear": "DayOfYear"
    }

    QA_BITMASKS = build_bitmasks({
        'CLOUD_STATE': ['CLEAR', 'CLOUDY', 'MIXED', 'NOT_SET'],
        'CLOUD_SHADOW': ['NO', 'YES'],
        'LAND_WATER': ['SHALLOW_OCEAN', 'LAND', 'OCEAN_COASTLINE_AND_LAKE_SHORELINES',
                       'SHALLOW_INLAND_WATER', 'EPHEMERAL_WATER', 'DEEP_INLAND_WATER',
                       'CONTINENTAL_OCEAN', 'DEEP_OCEAN'],
        'AEROSOL_QUALITY': ['CLIMATOLOGY', 'LOW', 'AVERAGE', 'HIGH'],
        'CIRRUS_DETECTED': ['NONE', 'SMALL', 'AVERAGE', 'HIGH'],
        'INTERNAL_CLOUD': ['NO', 'YES'],
        'INTERNAL_FIRE': ['NO', 'YES'],
        'SNOW_ICE': ['NO', 'YES'],
        'ADJACENT_TO_CLOUD': ['NO', 'YES'],
        'BRDF_CORRECTED': ['NO', 'YES'],
        'INTERNAL_SNOW': ['NO', 'YES'],
    })

    CLOUD_AND_SHADOW_BITMASKS = [
        'CLOUD_STATE.CLOUDY',
        'CLOUD_STATE.MIXED',
        'CLOUD_SHADOW',
        'CIRRUS',
        'TERRAIN_OCCLUSION'
        ]

    SCALING_FACTOR = {
        0.0001: [Band.RED, Band.NIR, Band.BLUE, Band.GREEN, Band.NIR2, Band.SWIR1, Band.SWIR2]
    }

    def __init__(self):
        super().__init__(self.BASE_ID.format(product='006/MOD09A1'))


class Modis():
    MOD09A1 = MOD09A1
