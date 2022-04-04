from datetime import datetime

import ee

from rsgee.processors.generic import BaseSampler, BaseClassifier


class ForestPlantationSampler(BaseSampler):

    def _run(self, mosaics):
        sampling_buffer = self._settings.SAMPLING_BUFFER
        regions_ids = self._get_regions_ids()

        training_reference = (ee.Image(self._settings.SAMPLING_REFERENCE_ID)
                              .select([0], ['class'])
                              .unmask())

        reference_buffer = (ee.Image
                            .constant(1)
                            .cumulativeCost(
                                source=training_reference,
                                maxDistance=500)
                            .expression("b(0) > 0 and b(0) < 500")
                            .unmask())

        training_reference = training_reference.updateMask(reference_buffer.eq(0))

        for year in self._settings.YEARS:
            for region_id in regions_ids:
                mosaic = mosaics.get_element(year=year, region_id=region_id)
                roi = self._get_region_by_id(region_id).geometry()

                if (sampling_buffer):
                    roi = roi.buffer(sampling_buffer)

                coi_samples_num = 0.1 * self._settings.SAMPLING_POINTS
                other_samples_num = 0.9 * self._settings.SAMPLING_POINTS

                samples = (mosaic
                           .unmask()
                           .addBands(training_reference)
                           .stratifiedSample(
                               numPoints=self._settings.SAMPLING_POINTS,
                               classBand='class',
                               region=roi,
                               scale=self._settings.EXPORT_SCALE,
                               seed=datetime.now().microsecond,
                               classValues=[0, 1],
                               classPoints=[other_samples_num, coi_samples_num],
                               tileScale=2,
                               geometries=True)
                           .set({
                               'year': year,
                               'region_id': region_id
                            }))

                self._add_in_batch(
                    year=year,
                    region_id=region_id,
                    data=samples)


class LoadSamplesFromAsset(BaseSampler):

    def _run(self, mosaics):
        allSamples = ee.FeatureCollection(self._settings.SAMPLES_ASSET_ID)
        buffer = self._settings.SAMPLING_BUFFER

        regions_ids = self._get_regions_ids()

        for year in self._settings.YEARS:
            for region_id in regions_ids:

                roi = self._get_region_by_id(region_id).geometry().buffer(buffer)

                samples = (allSamples
                           .filterBounds(roi)
                           .randomColumn('random'))

                classSamples = (samples
                                .filterMetadata('class', 'equals', 1)
                                .limit(1000, 'random'))

                othersSamples = (samples
                                 .filterMetadata('class', 'equals', 0)
                                 .limit(9000, 'random'))

                samples = classSamples.merge(othersSamples)

                self._add_in_batch(
                    year=year, 
                    region_id=region_id,
                    data=samples)
