from rsgee.band import Band
from rsgee.index import Index
from rsgee.imagecollection import ImageCollection
from rsgee.utils.bitmask import build_bitmasks


class _Landsat5():

    BASE_ID = 'LANDSAT/LT05/C01/{tier}_{collection}'

    INDEXES_PARAMETERS = {
        Index.SAFER.name: {
            'BLUE_CV': 0.293,
            'GREEN_CV': 0.274,
            'RED_CV': 0.233,
            'NIR_CV': 0.157,
            'SWIR1_CV': 0.033,
            'SWIR2_CV': 0.011,
            'A_ALBEDO': 0.7,
            'B_ALBEDO': 0.6,
            'A_ET_ET0': 0.315,
            'B_ET_ET0': -0.0015,
        }
    }


class TOA(_Landsat5, ImageCollection):

    COLLECTION_NAME = 'LT05'

    BANDS_MAPPING = {
        "B1": Band.BLUE,
        "B2": Band.GREEN,
        "B3": Band.RED,
        "B4": Band.NIR,
        "B5": Band.SWIR1,
        "B6": Band.TIR1,
        "B7": Band.SWIR2,
        "BQA": Band.BQA
    }

    QA_BITMASKS = build_bitmasks({
        'DESIGNATED_FILL': ['NO', 'YES'],
        'DROPPED_PIXEL': ['NO', 'YES'],
        'RADIOMETRIC_SATURATION': ['NO_BANDS', 'UP_TO_2', 'UP_TO_4', 'FIVE_MORE'],
        'CLOUD': ['NO', 'YES'],
        'CLOUD_CONFIDENCE': ['NO', 'LOW', 'MEDIUM', 'HIGH'],
        'CLOUD_SHADOW_CONFIDENCE': ['NO', 'LOW', 'MEDIUM', 'HIGH'],
        'SNOW_ICE_CONFIDENCE': ['NO', 'LOW', 'MEDIUM', 'HIGH'] 
    })

    CLOUD_AND_SHADOW_BITMASKS = [
        'CLOUD_CONFIDENCE.MEDIUM',
        'CLOUD_CONFIDENCE.HIGH',
        'CLOUD_SHADOW_CONFIDENCE.MEDIUM',
        'CLOUD_SHADOW_CONFIDENCE.HIGH'
    ]

    DEFAULT_QA_SCORES = {
        2: ['SNOW_ICE_CONFIDENCE.HIGH'],
        5: ['CLOUD_SHADOW_CONFIDENCE.HIGH'],
        6: ['CLOUD_CONFIDENCE.HIGH']
    }

    @staticmethod
    def Tier1():
        return TOA('T1')

    @staticmethod
    def Tier2():
        return TOA('T2')

    def __init__(self, tier):
        super().__init__(self.BASE_ID.format(collection='TOA', tier=tier))


class Landsat5():
    TOA = TOA
