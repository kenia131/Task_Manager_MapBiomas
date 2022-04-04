from rsgee.imagecollection import ImageCollection
from rsgee.utils import blard
from rsgee.band import Band


class Blard(ImageCollection):

    COLLECTION_NAME = 'BLARD'

    SCALING_FACTOR = {
        0.0001: [Band.BLUE, Band.GREEN, Band.RED, Band.NIR, Band.SWIR1, Band.SWIR2],
        0.1: [Band.TIR1]
    }

    @staticmethod
    def filter_collection_by_pathrow(path, row, startDate, endDate, cloudCover, bands=blard.ALL_BANDS):
        collection = blard.get16DayProductByPathRow(path, row, startDate, endDate, cloudCover, bands)
        return Blard(collection)

    @staticmethod
    def filter_collection_by_roi(roi, startDate, endDate, cloudCover, bands=blard.ALL_BANDS):
        collection = blard.get16DayproductByROI(roi, startDate, endDate, cloudCover, bands)
        return Blard(collection)

    def mask_clouds_and_shadows(self):
        def mask(image):
            cloud_mask = image.select('QF').eq(1)
            return image.updateMask(cloud_mask)

        return self.map(mask)
