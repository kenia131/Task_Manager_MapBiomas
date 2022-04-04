from abc import ABC, abstractclassmethod
from datetime import datetime

import ee

from rsgee.processors.generic.base import BaseProcessor
from rsgee.export import Export


class BaseClassifier(BaseProcessor, ABC):

    def __init__(self, batch_keys=['year', 'region_id']):
        super().__init__(batch_keys)

    def process(self, **args):
        self._run(
            mosaics=args['mosaics'],
            samples=args['samples'])
        return self._batch

    @abstractclassmethod
    def _run(self, mosaics, samples):
        pass


class DefaultClassifier(BaseClassifier):

    def _run(self, samples, mosaics):
        regions_ids = self._get_regions_ids()

        for year in self._settings.YEARS:
            for region_id in regions_ids:
                roi = self._get_region_by_id(region_id).geometry()
                samples_bounds = roi

                mosaic = mosaics.get_element(year=year, region_id=region_id)
                training_samples = samples.get_element(year=year, region_id=region_id)

                training_samples = ee.FeatureCollection(training_samples)

                classifier = (ee.Classifier
                              .smileRandomForest(
                                  numberOfTrees=self._settings.CLASSIFICATION_TREES,
                                  seed=datetime.now().microsecond)
                              .train(
                                  features=training_samples,
                                  classProperty='class',
                                  inputProperties=mosaic.bandNames()))

                classified = (mosaic
                              .unmask()
                              .classify(classifier)
                              .set({
                                'year': year,
                                'region_id': region_id}))

                self._add_in_batch(
                    year=year,
                    region_id=region_id,
                    data=classified,
                    region=roi)
