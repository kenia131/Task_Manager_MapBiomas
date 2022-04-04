from datetime import datetime

import ee

from rsgee.processors.generic import BaseGenerator, BaseSampler
from rsgee.utils.brdf import apply_brdf_correction


class SoybeanGenerator(BaseGenerator):

    def _run(self):
        regions_ids = self._get_regions_ids()

        for year in self._settings.YEARS:
            for region_id in regions_ids:
                roi = self._get_region_by_id(region_id)

                def get_mosaic(period_name, period_interval):
                    return self._generate_mosaic(roi, year, period_name, period_interval)

                periods = self._get_periods(roi)

                mosaics = periods.map(get_mosaic).values()

                mosaic = Image(ImageCollection(mosaics).to_bands())

                if (self._settings.GENERATION_EXTRA_INDEXES):
                    mosaic = mosaic.calculate_indexes(
                        self._settings.GENERATION_EXTRA_INDEXES,
                        self._settings.GENERATION_INDEXES_PARAMS)

                feature_space = self._filter_avaliable_bands_from_mosaic(mosaic)

                mosaic = (mosaic
                          .select(feature_space)
                          .set({
                            'year': year,
                            'region_id': region_id}))

                self._add_in_batch(
                    year=year,
                    region_id=region_id,
                    data=mosaic,
                    region=roi.geometry())

    def _generate_mosaic(self, roi, year, period_name, period_interval):
        period_interval = ee.String(period_interval).split(',')
        period_start = period_interval.getString(0)
        period_end = period_interval.getString(1)

        offset = self._settings.GENERATION_OFFSET
        cloud_cover = self._settings.GENERATION_MAX_CLOUD_COVER


        images = (self._settings.IMAGE_COLLECTION()
                  .filterBounds(roi)
                  .filter_period(period_start, period_end, year, offset)
                  .filterMetadata('CLOUD_COVER', 'less_than', cloud_cover)
                  .padronize_band_names()
                  .padronize_band_scales()
                  .mask_clouds_and_shadows()
                  .map(apply_brdf_correction))

        images = self._apply_generation_buffer(images)

        images = (images
            .calculate_indexes(
                self._settings.GENERATION_INDEXES,
                self._settings.GENERATION_INDEXES_PARAMS)
            .select(self._settings.GENERATION_BANDS))

        images = self._apply_scaling_fators(images)

        mosaic = (images
                  .apply_reducers(self._settings.GENERATION_REDUCERS)
                  .compose_band_names(prefix=period_name))

        return mosaic


class SoybeanSampler(BaseSampler):

    def _run(self, mosaics):
        regions_ids = self._get_regions_ids()

        for year in self._settings.YEARS:
            training_reference = (ee.Image(self._settings.SAMPLING_REFERENCE_ID)
                                  .select('.*' + str(year))
                                  .rename(['class']))

            for region_id in regions_ids:
                mosaic = mosaics.get_element(year=year, region_id=region_id)

                roi = self._get_region_by_id(region_id).geometry()

                samples = (mosaic
                           .addBands(training_reference)
                           .unmask()
                           .sample(
                               region=roi,
                               numPixels=self._settings.SAMPLING_POINTS,
                               scale=self._settings.EXPORT_SCALE,
                               seed=datetime.now().microsecond,
                               tileScale=4,
                               geometries=True))

                samples = samples.set({
                           'year': year,
                           'region_id': region_id})

                self._add_in_batch(
                    year=year,
                    region_id=region_id,
                    data=samples)
