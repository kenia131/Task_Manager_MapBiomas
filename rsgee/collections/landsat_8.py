from rsgee.band import Band
from rsgee.index import Index
from rsgee.imagecollection import ImageCollection
from rsgee.utils.bitmask import build_bitmasks


class _Landsat8():

    BASE_ID = 'LANDSAT/LC08/C01/{tier}_{collection}'

    DEFAULT_INDEXES_PARAMETERS = {
        Index.SAFER.name: {
            'BLUE_CV': 0.301,
            'GREEN_CV': 0.273,
            'RED_CV': 0.233,
            'NIR_CV': 0.143,
            'SWIR1_CV': 0.037,
            'SWIR2_CV': 0.013,
            'A_ALBEDO': 0.7,
            'B_ALBEDO': 0.6,
            'A_ET_ET0': 0.315,
            'B_ET_ET0': -0.0015,
        }
    }


class TOA(_Landsat8, ImageCollection):

    COLLECTION_NAME = 'L8TOA'

    BANDS_MAPPING = {
        "B1": Band.COASTAL,
        "B2": Band.BLUE,
        "B3": Band.GREEN,
        "B4": Band.RED,
        "B5": Band.NIR,
        "B6": Band.SWIR1,
        "B7": Band.SWIR2,
        "B8": Band.PAN,
        "B9": Band.CIRRUS,
        "B10": Band.TIR1,
        "B11": Band.TIR2,
        "BQA": Band.BQA
    }

    QA_BITMASKS = build_bitmasks({
        'DESIGNATED_FILL': ['NO', 'YES'],
        'TERRAIN_OCCLUSION': ['NO', 'YES'],
        'RADIOMETRIC_SATURATION': ['NO_BANDS', 'UP_TO_2', 'UP_TO_4', 'FIVE_MORE'],
        'CLOUD': ['NO', 'YES'],
        'CLOUD_CONFIDENCE': ['NO', 'LOW', 'MEDIUM', 'HIGH'],
        'CLOUD_SHADOW_CONFIDENCE': ['NO', 'LOW', 'MEDIUM', 'HIGH'],
        'SNOW_ICE_CONFIDENCE': ['NO', 'LOW', 'MEDIUM', 'HIGH'],
        'CIRRUS_CONFIDENCE': ['NO', 'LOW', 'MEDIUM', 'HIGH']
    })

    CLOUD_AND_SHADOW_BITMASKS = [
        'CLOUD_CONFIDENCE.MEDIUM',
        'CLOUD_CONFIDENCE.HIGH',
        'CLOUD_SHADOW_CONFIDENCE.MEDIUM',
        'CLOUD_SHADOW_CONFIDENCE.HIGH',
        'CIRRUS_CONFIDENCE.MEDIUM',
        'CIRRUS_CONFIDENCE.HIGH'
    ]

    DEFAULT_QA_SCORES = {
        2: ['SNOW_ICE_CONFIDENCE.HIGH'],
        3: ['TERRAIN_OCCLUSION.YES'],
        4: ['CIRRUS_CONFIDENCE.HIGH'],
        5: ['CLOUD_SHADOW_CONFIDENCE.HIGH'],
        6: ['CLOUD_CONFIDENCE.HIGH']
    }

    @staticmethod
    def Tier1():
        return TOA('T1')

    @staticmethod
    def Tier1RealTime():
        return TOA('T1_RT')

    @staticmethod
    def Tier2():
        return TOA('T2')

    def __init__(self, tier):
        super().__init__(self.BASE_ID.format(collection='TOA', tier=tier))


class Landsat8():
    TOA = TOA
    # SR = SR
