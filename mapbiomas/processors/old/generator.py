# -*- coding: utf-8 -*-
import ee
import ee.mapclient
import re

import rsgee.utils.blard as blardLib
from rsgee.conf import settings
from rsgee.image import Image
from rsgee.imagecollection import ImageCollection
from rsgee.processors.generic import GeneratorProcessor


class MapbiomasGenerator(GeneratorProcessor):
    def __init__(self, collection, feature_collection, bands, reducers, years,
                 offset, periods, clip_geometry, apply_brdf, apply_mask):
        GeneratorProcessor.__init__(self, collection, feature_collection,
                                    bands, reducers, years, offset, periods,
                                    clip_geometry, apply_brdf,
                                    apply_mask)

    def get_neighbors(self, images, path, row):
        wrs = []
        for offset_path in range(-1, 2):
            for offset_row in range(-1, 2):
                for image in images:
                    local_path = path + offset_path
                    local_row = row + offset_row
                    local_geometry = image.get('GEOMETRY')
                    if int(image.get('PATH')) == local_path and \
                            int(image.get('ROW')) == local_row:
                        wrs.append((local_path, local_row, local_geometry))
        return wrs


class AnnualGenerator(MapbiomasGenerator):
    def __init__(self, collection, feature_collection, bands, reducers, years,
                 offset, periods, clip_geometry, apply_brdf, apply_mask):
        MapbiomasGenerator.__init__(self, collection, feature_collection,
                                    bands, reducers, years, offset, periods,
                                    clip_geometry, apply_brdf,
                                    apply_mask)

    def run(self):
        features = self._feature_collection.get_features()
        for year in self._years:
            for feature in features:
                path = feature.get('PATH')
                row = feature.get('ROW')
                geometry = ee.Geometry.MultiPolygon(feature.get('GEOMETRY'))

                neighbors = self.get_neighbors(features, int(path), int(row))
                neighbors_paths = list(map(lambda x: x[0], neighbors))
                neighbors_rows = list(map(lambda x: x[1], neighbors))

                neighbors_geometry = ee.Geometry \
                    .MultiPolygon(list(map(lambda x: x[2], neighbors)))

                image_collection = self._collection \
                    .filter(ee.Filter.inList('WRS_PATH',
                        ee.List(neighbors_paths))) \
                    .filter(ee.Filter.inList('WRS_ROW',
                        ee.List(neighbors_rows))) \
                    .filterMetadata("CLOUD_COVER", "less_than", 90)

                final_image = []
                for period in self._periods:
                    period_dates = feature.get(period)

                    images_by_period = ImageCollection(image_collection) \
                        .filter_by_period(year, period_dates, self._offset)

                    if self._apply_brdf:
                        images_by_period = images_by_period.apply_brdf()

                    if self._clip_geometry:
                        images_by_period = images_by_period.clip_geometry()

                    if self._apply_mask:
                        images_by_period = images_by_period.apply_qamask()

                    if self._bands:
                        images_by_period = images_by_period \
                            .apply_bands(self._bands)

                    image_reduced = Image(images_by_period
                                          .apply_reducers(self._reducers))

                    new_band_names = image_reduced \
                        .bandNames() \
                        .map(lambda band: ee.String(period).cat('_').cat(band))

                    renamed_image = image_reduced.rename(new_band_names)

                    final_image.append(renamed_image)

                final_image = Image.cat(final_image)

                if settings.GENERATION_EXTRA_BANDS:
                    extra_bands = Image(final_image).get_bands(
                        settings.GENERATION_EXTRA_BANDS)
                    final_image = final_image.addBands(extra_bands)

                final_name = "{0}_{1}_{2}".format(settings.COLLECTION_PREFIX,
                                                  "{0}{1}".format(path, row),
                                                  str(year))

                final_image = final_image \
                    .select(settings.GENERATION_VARIABLES +
                            settings.GENERATION_EXTRA_VARIABLES) \
                    .set('year', year) \
                    .set('system:footprint', geometry)

                self.add_image_in_batch(final_name, {
                    "image": final_image,
                    "year": int(year),
                    "path": int(path),
                    "row": int(row),
                    "geometry": geometry,
                    'neighbors': neighbors_geometry
                })


class SemiPereneGenerator(MapbiomasGenerator):
    def __init__(self, collection, feature_collection, bands, reducers, years,
                 offset, periods, clip_geometry, apply_brdf, apply_mask):
        MapbiomasGenerator.__init__(self, collection, feature_collection,
                                    bands, reducers, years, offset, periods,
                                    clip_geometry, apply_brdf,
                                    apply_mask)

    def run(self):
        features = self._feature_collection.get_features()
        for year in self._years:
            for feature in features:
                path = feature.get('PATH')
                row = feature.get('ROW')
                geometry = ee.Geometry.MultiPolygon(feature.get('GEOMETRY'))

                neighbors = self.get_neighbors(features, int(path), int(row))
                neighbors_paths = list(map(lambda x: x[0], neighbors))
                neighbors_rows = list(map(lambda x: x[1], neighbors))

                neighbors_geometry = ee.Geometry \
                    .MultiPolygon(list(map(lambda x: x[2], neighbors)))

                image_collection = self._collection \
                    .filter(
                    ee.Filter.inList('WRS_PATH', ee.List(neighbors_paths))) \
                    .filter(
                    ee.Filter.inList('WRS_ROW', ee.List(neighbors_rows))) \
                    .filterMetadata("CLOUD_COVER", "less_than", 90)

                images = []
                for period in self._periods:
                    period_dates = feature.get(period)
                    images_by_period = ImageCollection([])
                    for i in range(self._offset):
                        local_images_by_period = ImageCollection(
                            image_collection).filter_by_period(year - i,
                                                               period_dates, 1)

                        if self._clip_geometry:
                            local_images_by_period = local_images_by_period.clip_geometry()

                        if self._apply_mask:
                            local_images_by_period = local_images_by_period.apply_qamask()

                        if self._bands:
                            local_images_by_period = local_images_by_period.apply_bands(
                                self._bands)

                        images_by_period = images_by_period.merge(
                            local_images_by_period)

                    reduced_image = ImageCollection(
                        images_by_period).apply_reducers(self._reducers)

                    reduced_image = reduced_image.rename(
                        reduced_image.bandNames().map(
                            lambda band: ee.String(period).cat('_').cat(band))
                    )

                    images.append(reduced_image)

                final_image = Image.cat(images)

                final_name = "{0}_{1}_{2}".format(settings.COLLECTION_PREFIX,
                                                  "{0}{1}".format(path, row),
                                                  str(year))
                final_image = final_image.select(
                    settings.GENERATION_VARIABLES + settings.GENERATION_EXTRA_VARIABLES).set(
                    'year', year)

                self.add_image_in_batch(final_name,
                                        {"image": final_image,
                                         "year": int(year), "path": int(path),
                                         "row": int(row), "geometry": geometry,
                                         'neighbors': neighbors_geometry})


class PlantedForestGenerator(MapbiomasGenerator):
    def __init__(self, collection, feature_collection, bands, reducers, years,
                 offset, periods, clip_geometry, apply_brdf, apply_mask):
        MapbiomasGenerator.__init__(self, collection, feature_collection,
                                    bands, reducers, years, offset, periods,
                                    clip_geometry, apply_brdf,
                                    apply_mask)

    def run(self):
        features = self._feature_collection.get_features()
        for year in self._years:
            for feature in features:
                path = feature.get('PATH')
                row = feature.get('ROW')
                geometry = ee.Geometry.MultiPolygon(feature.get('GEOMETRY'))

                neighbors = self.get_neighbors(features, int(path), int(row))
                neighbors_paths = list(map(lambda x: x[0], neighbors))
                neighbors_rows = list(map(lambda x: x[1], neighbors))
                neighbors_geometry = ee.Geometry.MultiPolygon(
                    list(map(lambda x: x[2], neighbors)))

                image_collection = self._collection \
                    .filter(
                    ee.Filter.inList('WRS_PATH', ee.List(neighbors_paths))) \
                    .filter(
                    ee.Filter.inList('WRS_ROW', ee.List(neighbors_rows))) \
                    .filterMetadata("CLOUD_COVER", "less_than", 90)

                images = []
                for period in self._periods:
                    period_dates = feature.get(period)
                    images_by_period = ImageCollection([])
                    for i in range(self._offset):
                        local_images_by_period = ImageCollection(
                            image_collection).filter_by_period(year - i,
                                                               period_dates, 1)

                        if self._apply_brdf:
                            images_by_period = images_by_period.apply_brdf()

                        if self._clip_geometry:
                            local_images_by_period = local_images_by_period.clip_geometry()

                        if self._apply_mask:
                            local_images_by_period = local_images_by_period.apply_qamask()

                        if self._bands:
                            local_images_by_period = local_images_by_period.apply_bands(
                                self._bands)

                        images_by_period = images_by_period.merge(
                            local_images_by_period)

                    reduced_image = ImageCollection(
                        images_by_period).apply_reducers(self._reducers)

                    reduced_image = reduced_image.rename(
                        reduced_image.bandNames().map(
                            lambda band: ee.String(period).cat('_').cat(band))
                    )

                    images.append(reduced_image)

                final_image = Image.cat(images)

                final_name = "{0}_{1}_{2}".format(settings.COLLECTION_PREFIX,
                                                  "{0}{1}".format(path, row),
                                                  str(year))
                final_image = final_image.select(
                    settings.GENERATION_VARIABLES + settings.GENERATION_EXTRA_VARIABLES).set(
                    'year', year)

                self.add_image_in_batch(final_name,
                                        {"image": final_image,
                                         "year": int(year), "path": int(path),
                                         "row": int(row), "geometry": geometry,
                                         'neighbors': neighbors_geometry})

class SoybeanGenerator(MapbiomasGenerator):
    def __init__(self, collection, feature_collection, bands, reducers, years,
                 offset, periods, clip_geometry, apply_brdf, apply_mask):
        MapbiomasGenerator.__init__(self, collection, feature_collection,
                                    bands, reducers, years, offset, periods,
                                    clip_geometry, apply_brdf,
                                    apply_mask)

    def run(self):
        features = self._feature_collection.get_features()
        for year in self._years:
            for feature in features:
                path = feature.get('PATH')
                row = feature.get('ROW')

                geometry = ee.Geometry.MultiPolygon(feature.get('GEOMETRY'))

                def parse_period(date_format, year):
                    year_format = re.match('^\((?P<year>.*)\)-(.*)$',
                                            date_format).group('year')
                    year = eval(year_format.replace('Y', str(year)))
                    date = re.sub('\((.*)\)', str(year), date_format)
                    return date

                dates = []

                for period in self._periods:
                    initial_period, final_period = feature.get(period).split(',')

                    local_initial_period = parse_period(initial_period, year - self._offset)
                    local_final_period = parse_period(final_period, year)

                    dates.append(local_initial_period)
                    dates.append(local_final_period)

                startDate = min(dates)
                endDate = max(dates)


                build_bands = map(lambda x: x.value, self._bands)
                blard_bands = list(filter(lambda band:
                                          band in blardLib.ALL_BANDS,
                                          build_bands))

                image_collection = blardLib\
                    .get16Dayproduct(int(path), int(row),
                                     startDate, endDate, 90,
                                     blard_bands)

                final_image = []
                for period in self._periods:
                    period_dates = feature.get(period)

                    images_by_period = ImageCollection(image_collection) \
                        .filter_by_period(year, period_dates, self._offset)

                    if self._apply_mask:
                        images_by_period = images_by_period.apply_qamask()

                    if self._clip_geometry:
                        images_by_period = images_by_period.clip_geometry()

                    if self._bands:
                        images_by_period = images_by_period \
                            .apply_bands(self._bands)

                    reduced_image = Image(images_by_period
                                          .apply_reducers(self._reducers))

                    new_band_names = reduced_image \
                        .bandNames() \
                        .map(lambda band: ee.String(period).cat('_').cat(band))

                    renamed_image = reduced_image.rename(new_band_names)

                    final_image.append(renamed_image)

                if settings.GENERATION_EXTRA_BANDS:
                    extra_bands = Image(final_image)\
                        .get_bands(settings.GENERATION_EXTRA_BANDS)
                    final_image.append(extra_bands)

                final_image = Image.cat(final_image)

                # centroid = final_image.geometry().centroid().getInfo()
                # ee.mapclient.centerMap(centroid["coordinates"][0],
                #                        centroid["coordinates"][1], 10)
                # ee.mapclient.addToMap(ee.Image(final_image)
                #     .select('AC_WET_NIR_qmo', 'AC_WET_SWIR1_qmo',
                #             'AC_WET_RED_qmo'),
                #     vis_params={'min': 0, 'max': 4000})


                final_name = "{0}_{1}_{2}".format(settings.COLLECTION_PREFIX,
                                                  "{0}{1}".format(path, row),
                                                  str(year))

                final_image = final_image \
                    .select(settings.GENERATION_VARIABLES +
                            settings.GENERATION_EXTRA_VARIABLES) \
                    .set('year', year) \
                    .set('system:footprint', geometry)

                self.add_image_in_batch(final_name, {
                    "image": final_image,
                    "year": int(year),
                    "path": int(path),
                    "row": int(row),
                    "geometry": geometry
                })

class AnnualPerennialGenerator(MapbiomasGenerator):
    def __init__(self, collection, feature_collection, bands, reducers, years,
                 offset, periods, clip_geometry, apply_brdf, apply_mask):
        MapbiomasGenerator.__init__(self, collection, feature_collection,
                                    bands, reducers, years, offset, periods,
                                    clip_geometry, apply_brdf,
                                    apply_mask)

    def run(self):
        features = self._feature_collection.get_features()
        for year in self._years:
            for feature in features:
                path = feature.get('PATH')
                row = feature.get('ROW')

                geometry = ee.Geometry.MultiPolygon(feature.get('GEOMETRY'))

                def parse_period(date_format, year):
                    year_format = re.match('^\((?P<year>.*)\)-(.*)$',
                                            date_format).group('year')
                    year = eval(year_format.replace('Y', str(year)))
                    date = re.sub('\((.*)\)', str(year), date_format)
                    return date

                dates = []

                for period in self._periods:
                    initial_period, final_period = feature.get(period).split(',')

                    local_initial_period = parse_period(initial_period, year - self._offset)
                    local_final_period = parse_period(final_period, year)

                    dates.append(local_initial_period)
                    dates.append(local_final_period)

                startDate = min(dates)
                endDate = max(dates)


                build_bands = map(lambda x: x.value, self._bands)
                blard_bands = list(filter(lambda band:
                                          band in blardLib.ALL_BANDS,
                                          build_bands))

                image_collection = blardLib\
                    .get16Dayproduct(int(path), int(row),
                                     startDate, endDate, 90,
                                     blard_bands)

                final_image = []
                for period in self._periods:
                    period_dates = feature.get(period)

                    images_by_period = ImageCollection(image_collection) \
                        .filter_by_period(year, period_dates, self._offset)

                    if self._apply_mask:
                        images_by_period = images_by_period.apply_qamask()

                    if self._clip_geometry:
                        images_by_period = images_by_period.clip_geometry()

                    if self._bands:
                        images_by_period = images_by_period \
                            .apply_bands(self._bands)

                    reduced_image = Image(images_by_period
                                          .apply_reducers(self._reducers))

                    new_band_names = reduced_image \
                        .bandNames() \
                        .map(lambda band: ee.String(period).cat('_').cat(band))

                    renamed_image = reduced_image.rename(new_band_names)

                    final_image.append(renamed_image)

                if settings.GENERATION_EXTRA_BANDS:
                    extra_bands = Image(final_image)\
                        .get_bands(settings.GENERATION_EXTRA_BANDS)
                    final_image.append(extra_bands)

                final_image = Image.cat(final_image)

                if settings.GENERATION_AMPLITUDE:
                    amplitude = final_image.expression(
                        'MAX - MIN',
                        {
                            'MIN': final_image.select(settings.GENERATION_AMPLITUDE.get('MIN')),
                            'MAX': final_image.select(settings.GENERATION_AMPLITUDE.get('MAX'))
                        })\
                        .rename(settings.GENERATION_AMPLITUDE.get('OUTPUT'))\
                        .int16()
                        
                    final_image = final_image.addBands(amplitude)

                # centroid = final_image.geometry().centroid().getInfo()
                # ee.mapclient.centerMap(centroid["coordinates"][0],
                #                        centroid["coordinates"][1], 10)
                # ee.mapclient.addToMap(ee.Image(final_image)
                #     .select('AC_WET_NIR_qmo', 'AC_WET_SWIR1_qmo',
                #             'AC_WET_RED_qmo'),
                #     vis_params={'min': 0, 'max': 4000})


                final_name = "{0}_{1}_{2}".format(settings.COLLECTION_PREFIX,
                                                  "{0}{1}".format(path, row),
                                                  str(year))

                final_image = final_image \
                    .select(settings.GENERATION_VARIABLES +
                            settings.GENERATION_EXTRA_VARIABLES + 
                            settings.GENERATION_AMPLITUDE.get('OUTPUT')) \
                    .set('year', year) \
                    .set('system:footprint', geometry)

                self.add_image_in_batch(final_name, {
                    "image": final_image,
                    "year": int(year),
                    "path": int(path),
                    "row": int(row),
                    "geometry": geometry
                })

class PlantedForestBlardGenerator(MapbiomasGenerator):
    def __init__(self, collection, feature_collection, bands, reducers, years,
                 offset, periods, clip_geometry, apply_brdf, apply_mask):
        MapbiomasGenerator.__init__(self, collection, feature_collection,
                                    bands, reducers, years, offset, periods,
                                    clip_geometry, apply_brdf,
                                    apply_mask)

    def run(self):
        features = self._feature_collection.get_features()
        for year in self._years:
            for feature in features:
                path = feature.get('PATH')
                row = feature.get('ROW')

                geometry = ee.Geometry.MultiPolygon(feature.get('GEOMETRY'))

                def parse_period(date_format, year):
                    year_format = re.match('^\((?P<year>.*)\)-(.*)$',
                                            date_format).group('year')
                    year = eval(year_format.replace('Y', str(year)))
                    date = re.sub('\((.*)\)', str(year), date_format)
                    return date

                dates = []

                for period in self._periods:
                    initial_period, final_period = feature.get(period).split(',')

                    local_initial_period = parse_period(initial_period, year - self._offset)
                    local_final_period = parse_period(final_period, year)

                    dates.append(local_initial_period)
                    dates.append(local_final_period)

                startDate = min(dates)
                endDate = max(dates)


                build_bands = map(lambda x: x.value, self._bands)
                blard_bands = list(filter(lambda band:
                                          band in blardLib.ALL_BANDS,
                                          build_bands))

                image_collection = blardLib\
                    .get16Dayproduct(int(path), int(row),
                                     startDate, endDate, 90,
                                     blard_bands)

                final_image = []
                for period in self._periods:
                    period_dates = feature.get(period)

                    images_by_period = ImageCollection(image_collection) \
                        .filter_by_period(year, period_dates, self._offset)

                    if self._apply_mask:
                        images_by_period = images_by_period.apply_qamask()

                    if self._clip_geometry:
                        images_by_period = images_by_period.clip_geometry()

                    if self._bands:
                        images_by_period = images_by_period \
                            .apply_bands(self._bands)

                    reduced_image = Image(images_by_period
                                          .apply_reducers(self._reducers))

                    new_band_names = reduced_image \
                        .bandNames() \
                        .map(lambda band: ee.String(period).cat('_').cat(band))

                    renamed_image = reduced_image.rename(new_band_names)

                    final_image.append(renamed_image)

                final_image = Image.cat(final_image).glcmTexture(4)

                final_name = "{0}_{1}_{2}".format(settings.COLLECTION_PREFIX,
                                                  "{0}{1}".format(path, row),
                                                  str(year))

                final_image = final_image \
                    .select(settings.GENERATION_VARIABLES +
                            settings.GENERATION_EXTRA_VARIABLES) \
                    .set('year', year) \
                    .set('system:footprint', geometry)

                self.add_image_in_batch(final_name, {
                    "image": final_image,
                    "year": int(year),
                    "path": int(path),
                    "row": int(row),
                    "geometry": geometry
                })