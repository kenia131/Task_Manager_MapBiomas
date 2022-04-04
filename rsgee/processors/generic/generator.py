from abc import ABC, abstractclassmethod

import ee

from rsgee.image import Image
from rsgee.imagecollection import ImageCollection
from rsgee.band import Band
from rsgee.processors.generic.base import BaseProcessor
from rsgee.utils import date
from rsgee.collections import Blard


class BaseGenerator(BaseProcessor, ABC):
    def __init__(self, batch_keys=["year", "region_id"]):
        super().__init__(batch_keys)

    def process(self, **args):
        self._run()
        return self._batch

    @abstractclassmethod
    def _run(self):
        pass

    def _get_fake_mosaic(self, extra_bands=[]):
        variables = [*self._settings.GENERATION_VARIABLES, *extra_bands]

        feature_space_size = len(variables)
        zero_list = ee.List([0] * feature_space_size)

        fake_bands = ee.Image.constant(zero_list).rename(variables).selfMask()

        return fake_bands

    def _filter_avaliable_bands_from_mosaic(self, mosaic):
        feature_space = ee.List(self._settings.GENERATION_VARIABLES)
        avaliable_bands = mosaic.bandNames()

        return feature_space.filter(ee.Filter.inList("item", avaliable_bands))

    def _get_periods(self, feature):
        generation_periods = self._settings.GENERATION_PERIODS

        if isinstance(generation_periods, dict):
            return ee.Dictionary(generation_periods)

        return feature.toDictionary(ee.List(self._settings.GENERATION_PERIODS))

    def _apply_generation_buffer(self, images):
        buffer = self._settings.GENERATION_BUFFER

        if not buffer:
            return images

        def apply(image):
            geometry = image.geometry()
            return Image(image).clip(geometry.buffer(buffer))

        return images.map(apply)

    def _apply_scaling_fators(self, images):
        scaling_factors = self._settings.GENERATION_SCALING_FACTORS

        if not scaling_factors:
            return images

        def apply(image):
            return Image(image).apply_scaling_factors(scaling_factors)

        return images.map(apply)


class DefaultGenerator(BaseGenerator):
    def _run(self):
        regions_ids = self._get_regions_ids()
        # fake_bands = self._get_fake_mosaic(['AC_DRY_NIR_min', 'AC_WET_NDWI_qmo'])

        for year in self._settings.YEARS:
            for region_id in regions_ids:
                roi = self._get_region_by_id(region_id)

                def get_mosaic(period_name, period_interval):
                    return self._generate_mosaic(
                        roi, year, period_name, period_interval
                    )

                periods = self._get_periods(roi)

                mosaics = periods.map(get_mosaic).values()

                mosaic = Image(ImageCollection(mosaics).to_bands())
                # mosaic = Image(fake_bands.addBands(mosaic, None, True))

                if self._settings.GENERATION_EXTRA_INDEXES:
                    mosaic = mosaic.calculate_indexes(
                        self._settings.GENERATION_EXTRA_INDEXES,
                        self._settings.GENERATION_INDEXES_PARAMS,
                    )

                # feature_space = self._filter_avaliable_bands_from_mosaic(mosaic)
                feature_space = ee.List(self._settings.GENERATION_VARIABLES)

                mosaic = mosaic.select(feature_space).set(
                    {"year": year, "region_id": region_id}
                )

                self._add_in_batch(
                    year=year, region_id=region_id, data=mosaic, region=roi.geometry()
                )

    def _generate_mosaic(self, roi, year, period_name, period_interval):
        period_interval = ee.String(period_interval).split(",")
        period_start = period_interval.getString(0)
        period_end = period_interval.getString(1)

        images = self._filter_collection(roi.geometry(), period_start, period_end, year)

        images = images.padronize_band_names().padronize_band_scales()

        if self._settings.GENERATION_APPLY_BRDF:
            images = images.apply_brdf()

        if self._settings.GENERATION_APPLY_CLOUD_AND_SHADOW_MASK:
            images = images.mask_clouds_and_shadows()

        if self._settings.GENERATION_BANDS:
            images = images.select(self._settings.GENERATION_BANDS)

        images = self._apply_generation_buffer(images)

        if self._settings.GENERATION_INDEXES:
            images = images.calculate_indexes(
                self._settings.GENERATION_INDEXES,
                self._settings.GENERATION_INDEXES_PARAMS,
            )

        images = self._apply_scaling_fators(images)

        mosaic = images.apply_reducers(
            self._settings.GENERATION_REDUCERS
        ).compose_band_names(prefix=period_name)

        return mosaic

    def _filter_collection(self, roi, period_start, period_end, year):
        offset = self._settings.GENERATION_OFFSET
        cloud_cover = self._settings.GENERATION_MAX_CLOUD_COVER

        if self._settings.GENERATION_USE_GEOMETRY_CENTROID:
            roi = roi.centroid()

        return (
            self._settings.IMAGE_COLLECTION()
            .filterBounds(roi)
            .filter_period(period_start, period_end, year, offset)
            .filterMetadata("CLOUD_COVER", "less_than", cloud_cover)
        )


class DefaultBLARDGenerator(DefaultGenerator):
    def _filter_collection(self, roi, period_start, period_end, year):
        # path = roi.getNumber('PATH')
        # row = roi.getNumber('ROW')
        offset = self._settings.GENERATION_OFFSET
        cloud_cover = self._settings.GENERATION_MAX_CLOUD_COVER
        bands = self._settings.GENERATION_BANDS

        if self._settings.GENERATION_USE_GEOMETRY_CENTROID:
            roi = roi.centroid()

        start_date = date.parse_date(period_start, year).advance(-offset, "year")
        end_date = date.parse_date(period_end, year)

        collection = Blard.filter_collection_by_roi(
            roi, start_date, end_date, cloud_cover
        )

        return collection.filter_period(period_start, period_end, year, offset)


class LoadMosaicsFromAsset(BaseGenerator):
    def _run(self, **args):
        regions_ids = self._get_regions_ids()
        mosaicsCollection = ee.ImageCollection(self._settings.GENERATION_MOSAICS_ID)

        for year in self._settings.YEARS:
            for region_id in regions_ids:
                roi = self._get_region_by_id(region_id).geometry()

                if self._settings.GRID_GEOMETRY_USE_CENTROID:
                    roi = roi.centroid()

                mosaic = (
                    mosaicsCollection.filterBounds(roi)
                    .filterMetadata("year", "equals", year)
                    .mosaic()
                )

                self._add_in_batch(
                    year=year, region_id=region_id, data=mosaic, region=roi
                )
