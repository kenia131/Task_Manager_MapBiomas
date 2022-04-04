from abc import ABC, abstractclassmethod
from datetime import datetime
from functools import reduce

import ee

from rsgee.processors.generic.base import BaseProcessor


class BasePostProcessor(BaseProcessor, ABC):

    # OUTPUT_NAME = 'filtered_results'

    def __init__(self, batch_keys=['year', 'region_id']):
        super().__init__(batch_keys)

    def process(self, **args):
        self._run(raw_results=args['raw_resutls'])
        return self._batch

    @abstractclassmethod
    def _run(self, raw_results):
        pass


class MergeImagesByYear(BasePostProcessor):

    def __init__(self, batch_keys=['year']):
        super().__init__(batch_keys)

    def _run(self, raw_results):
        regions_ids = self._get_regions_ids()
        roi = self._get_all_regions_bounds()

        def get_raw_result(year, region_id):
            raw = raw_results.get_element(year=year, region_id=region_id)
            return ee.Image(raw).unmask()

        for year in self._settings.YEARS:
            all_results_of_year = [
                get_raw_result(year, region_id) for region_id in regions_ids]

            collection = ee.ImageCollection(all_results_of_year)
            single_image_result = collection.Or().set('year', year)

            self._add_in_batch(
                year=year,
                data=single_image_result,
                region=roi)

# class Filter(enum.Enum):
#     TEMPORAL = "TEMPORAL"
#     SPATIAL = "SPATIAL"


# class PostProcessor(BaseProcessor):
#     def __init__(self, collection, collection_prefix='', filters=[], years=[],
#                  class_of_reference=1):
#         BaseProcessor.__init__(self)
#         self.__collection = collection.filter(
#             ee.Filter.inList('year', ee.List(years))).sort('year')
#         self.__collection_prefix = collection_prefix
#         self.__filters = filters
#         self.__class_of_reference = class_of_reference
#         self.__years = years

#     def run(self):
#         for filter in self.__filters:
#             if filter == Filter.TEMPORAL:
#                 self.__collection = self.apply_temporal_filter(
#                     self.__collection,
#                     settings.POSTPROCESSING_TEMPORAL_FILTER_OFFSET,
#                     settings.POSTPROCESSING_TEMPORAL_FILTER_THRESHOLD)
#             if filter == Filter.SPATIAL:
#                 self.__collection = self.apply_spatial_filter(
#                     self.__collection,
#                     settings.POSTPROCESSING_SPATIAL_FILTER_KERNEL,
#                     settings.POSTPROCESSING_SPATIAL_FILTER_THRESHOLD)

#     def apply_temporal_filter(self, collection, offset, initial_threshold):
#         collection = collection.toList(settings.MAX_IMAGES)
#         new_collection = ImageCollection([])
#         for index in xrange(len(self.__years)):
#             left, center, right, threshold = self.__break_list(collection,
#                                                                index, offset,
#                                                                0, len(
#                     self.__years) - 1, initial_threshold)

#             year = self.__years[index]
#             roi = center.geometry()

#             filename = "{0}_{1}".format(self.__collection_prefix, str(year))

#             center = center.unmask(None).eq(self.__class_of_reference)
#             left = ImageCollection(left)
#             right = ImageCollection(right)

#             sides = ImageCollection(left.merge(right)).map(
#                 lambda image: Image(image).eq(self.__class_of_reference)).sum()
#             mask = center.add(sides.eq(0)).neq(2)
#             image = center.add(sides).gte(threshold + 1)

#             filtered_image = Image(center.add(image)).updateMask(mask).gte(1)

#             filtered_image = filtered_image \
#                 .clip(roi) \
#                 .set('system:index', filename) \
#                 .set('year', year) \
#                 .set('system:footprint', roi)

#             new_collection = new_collection.merge(
#                 ImageCollection(filtered_image))

#             final_name = filename
#             final_image = filtered_image

#             self.add_image_in_batch(final_name,
#                                     {"image": final_image, "year": int(year),
#                                      "geometry": roi})

#         return new_collection

#     def apply_spatial_filter(self, collection, kernel, threshold):
#         kernel = ee.Kernel.fixed(len(kernel[0]), len(kernel), kernel,
#                                  -(len(kernel[0]) / 2), -(len(kernel) / 2),
#                                  False)
#         new_collection = ImageCollection([])
#         for year in self.__years:
#             image = Image(collection
#                           .filter(ee.Filter.eq('year', year))
#                           .first()) \
#                 .unmask(None)

#             filename = "{0}_{1}".format(self.__collection_prefix, str(year))

#             roi = image.geometry()

#             filtered_image = image.convolve(kernel).gte(threshold)

#             filtered_image = filtered_image.clip(roi).set('system:index',
#                                                           filename).set('year',
#                                                                         year).set(
#                 'system:footprint', roi)
#             new_collection = new_collection.merge(
#                 ImageCollection(filtered_image))

#             final_name = filename
#             final_image = filtered_image
#             self.add_image_in_batch(final_name,
#                                     {"image": final_image, "year": int(year),
#                                      "geometry": roi})

#         return new_collection

#     def __break_list(self, list, index, offset, min, max, threshold):
#         start = index - offset
#         end = index + offset
#         if start < min:
#             threshold = threshold + start
#             start = min
#         if end > max:
#             threshold = threshold + (max - end)
#             end = max

#         left = list.slice(start, index)
#         center = ee.Image(list.get(index))
#         right = list.slice(index + 1, end + 1)
#         return left, center, right, threshold
