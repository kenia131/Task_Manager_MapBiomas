from abc import ABC, abstractclassmethod
from datetime import datetime

import ee

from rsgee.processors.generic.base import BaseProcessor


class BaseSampler(BaseProcessor, ABC):

    def __init__(self, batch_keys=['year', 'region_id']):
        super().__init__(batch_keys)

    def process(self, **args):
        self._run(mosaics=args['mosaics'])
        return self._batch

    @abstractclassmethod
    def _run(self, mosaics):
        pass

    def _get_training_data(self, year=None, region_id=None):
        reference = ee.ImageCollection(self._settings.SAMPLING_REFERENCE_ID)

        if year:
            reference = reference.filterMetadata('year', 'equals', year)

        if region_id:
            reference = reference.filterMetadata('region_id', 'equals', region_id)

        return reference.max().select([0], ['class'])


class DefaultSimpleSampler(BaseSampler):

    def _run(self, mosaics):
        regions_ids = self._get_regions_ids()
        sampling_buffer = self._settings.SAMPLING_BUFFER

        for year in self._settings.YEARS:
            training_reference = (ee.ImageCollection(self._settings.SAMPLING_REFERENCE_ID)
                                  .filterMetadata('year', 'equals', year)
                                  .first()
                                  .rename(['class']))

            for region_id in regions_ids:
                mosaic = mosaics.get_element(year=year, region_id=region_id)

                roi = (self._get_region_by_id(region_id)
                       .geometry())

                if (sampling_buffer):
                    roi = roi.buffer(sampling_buffer)

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

                samples = (samples.set({
                           'year': year,
                           'region_id': region_id}))

                self._add_in_batch(
                    year=year,
                    region_id=region_id,
                    data=samples)


class LoadSamplesFromAsset(BaseSampler):

    def _run(self, mosaics):
        regions_ids = self._get_regions_ids()
        sampling_buffer = self._settings.SAMPLING_BUFFER
        sampling_points = self._settings.SAMPLING_POINTS

        for year in self._settings.YEARS:
            for region_id in regions_ids:
                asset_id = (self._settings.SAMPLES_ASSET_ID
                            .format(
                               year=year,
                               region_id=region_id))

                roi = (self._get_region_by_id(region_id)
                       .geometry()
                       .buffer(sampling_buffer, 30))

                samplesCollection = (ee.FeatureCollection(asset_id)
                                     .filterBounds(roi))

                if (sampling_points > 0):
                    samplesCollection = (samplesCollection
                                         .randomColumn(
                                             columnName='RANDOM',
                                             seed=datetime.now().microsecond
                                         )
                                         .limit(sampling_points, 'RANDOM'))

                self._add_in_batch(
                    year=year,
                    region_id=region_id,
                    data=samplesCollection)


class StratifiedSampler(BaseSampler):

    def _run(self, mosaics):
        regions_ids = self._get_regions_ids()
        training_reference = ee.ImageCollection(self._settings.SAMPLING_REFERENCE_ID).max().rename('class')

        for year in self._settings.YEARS:
            for region_id in regions_ids:
                mosaic = mosaics.get_element(year=year, region_id=region_id)

                roi = self._get_region_by_id(region_id)

                coi_proportion = ee.Number(0.1)
                other_proportion = ee.Number(1).subtract(coi_proportion)

                coi_samples = coi_proportion.multiply(self._settings.SAMPLING_POINTS).int()
                other_samples = other_proportion.multiply(self._settings.SAMPLING_POINTS).int()

                samples = (mosaic
                           .addBands(training_reference)
                           .unmask()
                           .stratifiedSample(
                              numPoints=self._settings.SAMPLING_POINTS,
                              classBand='class',
                              region=roi.geometry(),
                              scale=30,
                              classValues=[0, 1],
                              classPoints=[other_samples, coi_samples], 
                              geometries=True
                           ))

                samples = (samples.set({
                           'year': year,
                           'region_id': region_id}))

                self._add_in_batch(
                    year=year,
                    region_id=region_id,
                    data=samples)
