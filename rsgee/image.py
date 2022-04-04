from functools import reduce

import ee
from rsgee.index import calculate_indexes
from rsgee.band import Band
from rsgee.utils import brdf, bitmask


class PixelType:
    BYTE = 'byte'
    INT8 = 'int8'
    INT16 = 'int16'
    INT32 = 'int32'
    FLOAT = 'float'

    @staticmethod
    def cast(image, pixel_type):
        return {
            PixelType.BYTE: image.byte,
            PixelType.INT8: image.int8,
            PixelType.INT16: image.int16,
            PixelType.INT32: image.int32,
            PixelType.FLOAT: image.float
        }[pixel_type]()


class Image(ee.Image):

    def select_ignore_missing(self, bands):
        avaliable_bands = bands.filter(ee.Filter.inList('item', self.bandNames()))

        return self.select(avaliable_bands)

    def select_fill_missing(self, bands, fill_value):
        bands_size = ee.List(bands).size()
        fill_values = ee.List.repeat(fill_value, bands_size)

        fake_image = (ee.Image
                      .constant(fill_values)
                      .rename(bands)
                      .selfMask())

        return fake_image.addBands(self, None, True).select(bands)

    def calculate_indexes(self, indexes, parameters={}):
        return calculate_indexes(self, indexes, parameters)

    def apply_brdf(self):
        return brdf.apply_brdf_correction(self)

    def apply_bitmasks(self, bitmasks, quality_band=Band.BQA, reducer="or", reverse_mask=False):
        quality_band = self.select(quality_band)
        mask = bitmask.get_mask_from_bitmask_list(quality_band, bitmasks, reducer)

        if reverse_mask:
            mask = mask.Not()

        return self.updateMask(mask).addBands(quality_band, None, True)

    def score_image(self, bitmasks_scores, quality_band=Band.BQA):
        quality_band = self.select(quality_band)
        score = bitmask.get_qa_score(quality_band, bitmasks_scores)

        return self.addBands(score)

    def compose_band_names(self, prefix="", sufix="", separator="_"):
        prefix = ee.String(prefix).cat(separator) if prefix else ''
        sufix = ee.String(separator).cat(sufix) if sufix else ''

        def compose(band_name):
            return ee.String(prefix).cat(band_name).cat(sufix)

        new_names = self.bandNames().map(compose)

        return self.rename(new_names)

    def cast_to(self, pixel_type):
        return PixelType.cast(self, pixel_type)

    def apply_scaling_factors(self, scaling_factors):
        def flatten(list, value):
            factor, bands = value

            factors = [*list[0], *([factor] * len(bands))]
            bands = [*list[1], *bands]

            return [factors, bands]

        factors, bands = reduce(flatten, scaling_factors.items(), [[], []])

        scaled = self.select(bands).multiply(factors)

        return self.addBands(scaled, None, True)
