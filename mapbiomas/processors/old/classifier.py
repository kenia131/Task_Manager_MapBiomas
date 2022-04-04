import ee

from rsgee.conf import settings
from rsgee.imagecollection import ImageCollection
from rsgee.featurecollection import FeatureCollection
from rsgee.processors.generic.base import BaseProcessor


class Classifier(BaseProcessor):
    def __init__(self, mosaics, train, trees, points, years, buffer):
        BaseProcessor.__init__(self)
        self._mosaics = mosaics
        self._train = train
        self._trees = trees
        self._points = points
        self._years = years
        self._buffer = buffer

    def run(self):
        for year in self._years:
            train_asset = ImageCollection(self._train) \
                .filterMetadata('year', 'equals', int(year)) \
                .max()

            for image_name, image_data in self._mosaics.items():
                if year != image_data['year']:
                    continue
                image = image_data['image']
                path = image_data['path']
                row = image_data['row']
                geometry = image_data['geometry']
                geometry_neighbors = image_data['neighbors']

                roi = geometry
                roi_train = geometry_neighbors \
                    .intersection(geometry.buffer(self._buffer))

                neighbors = image \
                    .clip(roi_train) \
                    .set('system:footprint', roi_train) \
                    .unmask(None)

                center = neighbors.clip(roi).set('system:footprint', roi)

                train = train_asset.clip(roi_train).unmask(None) \
                    .rename('class')

                neighbors = neighbors.addBands(train)

                training = ee.FeatureCollection(neighbors.sample(
                    region=roi_train,
                    numPixels=int(self._points),
                    scale=settings.EXPORT_SCALE,
                    tileScale=4
                ))

                # coi_area = train.multiply(ee.Image.pixelArea()).reduceRegion(
                #    reducer=ee.Reducer.sum(),
                #    geometry=roi_train,
                #    scale=30,
                #    maxPixels=1E13,
                #    tileScale=4
                # )

                # othes_area = train.Not().multiply(ee.Image.pixelArea()).reduceRegion(
                #    reducer=ee.Reducer.sum(),
                #    geometry=roi_train,
                #    scale=30,
                #    maxPixels=1E13,
                #    tileScale=4
                # )

                # final_coi_area = ee.Number(coi_area.get("class"))
                # final_others_area = ee.Number(othes_area.get("class"))

                # total_area = final_coi_area.add(final_others_area)

                # coi_percentage = final_coi_area.divide(total_area)
                # others_percentage = final_others_area.divide(total_area)

                # training = ee.FeatureCollection(neighbors.stratifiedSample(
                #    region=roi_train,
                #    classBand="class",
                #    classValues=[0, 1],
                #    classPoints= ee.List([
                #       others_percentage.multiply(self._points).int16(),
                #       coi_percentage.multiply(self._points).int16()
                #    ]),
                #    numPoints=self._points,
                #    scale=settings.EXPORT_SCALE,
                #    seed=1,
                #    dropNulls=True,
                #    geometries=True,
                #    tileScale=4
                #	))

                classifier = ee.Classifier.randomForest(self._trees) \
                    .train(features=training, classProperty='class',
                           inputProperties=list(settings.GENERATION_VARIABLES +
                                                settings.GENERATION_EXTRA_VARIABLES))

                classified = center.classify(classifier)

                classified = classified.clip(roi) \
                    .set('year', year) \
                    .set('system:footprint', roi)

                final_image = classified
                final_name = image_name

                self.add_image_in_batch(final_name, {
                    "image": final_image,
                    "year": int(year),
                    "path": int(path),
                    "row": int(row),
                    "geometry": roi
                })


class BLARDClassifier(BaseProcessor):
    def __init__(self, mosaics, train, trees, points, years, buffer):
        BaseProcessor.__init__(self)
        self._mosaics = mosaics
        self._train = train
        self._trees = trees
        self._points = points
        self._years = years
        self._buffer = buffer

    def run(self):
        for year in self._years:
            train_asset = ImageCollection(self._train) \
                .filterMetadata('year', 'equals', int(year)) \
                .max()

            for image_name, image_data in self._mosaics.items():
                if year != image_data['year']:
                    continue
                image = image_data['image']
                path = image_data['path']
                row = image_data['row']
                roi = image_data['geometry']

                train = train_asset.clip(roi) \
                    .unmask(None).rename('class')

                image = image.addBands(train)

                training = ee.FeatureCollection(image.sample(
                    region=roi,
                    numPixels=int(self._points),
                    scale=settings.EXPORT_SCALE,
                    tileScale=4
                ))

                classifier = ee.Classifier.randomForest(self._trees) \
                    .train(features=training, classProperty='class',
                           inputProperties=list(settings.GENERATION_VARIABLES +
                                                settings.GENERATION_EXTRA_VARIABLES))

                classified = image.classify(classifier)
                classified = classified.clip(roi) \
                    .set('year', year) \
                    .set('system:footprint', roi)

                final_image = classified
                final_name = image_name

                self.add_image_in_batch(final_name, {
                    "image": final_image,
                    "year": int(year),
                    "path": int(path),
                    "row": int(row),
                    "geometry": roi
                })


class SoybeanBLARDClassifier(BaseProcessor):
    def __init__(self, mosaics, train, trees, points, years, buffer):
        BaseProcessor.__init__(self)
        self._mosaics = mosaics
        self._train = train
        self._trees = trees
        self._points = points
        self._years = years
        self._buffer = buffer

    def run(self):
        for year in self._years:
            train_asset = FeatureCollection(self._train)

            for image_name, image_data in self._mosaics.items():
                if year != image_data['year']:
                    continue
                image = image_data['image']
                path = image_data['path']
                row = image_data['row']
                roi = image_data['geometry']

                training = train_asset.filterBounds(roi.buffer(settings.CLASSIFICATION_BUFFER))

                classifier = ee.Classifier.randomForest(self._trees) \
                    .train(features=training, classProperty='class',
                           inputProperties=list(settings.GENERATION_VARIABLES +
                                                settings.GENERATION_EXTRA_VARIABLES))

                classified = image.classify(classifier)
                classified = classified.clip(roi) \
                    .set('year', year) \
                    .set('system:footprint', roi)

                final_image = classified
                final_name = image_name

                self.add_image_in_batch(final_name, {
                    "image": final_image,
                    "year": int(year),
                    "path": int(path),
                    "row": int(row),
                    "geometry": roi
                })


class AnnualPerennialBLARDClassifier(BaseProcessor):
    def __init__(self, mosaics, train, trees, points, years, buffer):
        BaseProcessor.__init__(self)
        self._mosaics = mosaics
        self._train = train
        self._trees = trees
        self._points = points
        self._years = years
        self._buffer = buffer

    def run(self):
        train_asset = FeatureCollection(self._train)

        for year in self._years:

            classification_mask = ee.ImageCollection(settings.CLASSIFICATION_MASK)\
                .filterMetadata('year', 'equals', year)\
                .first()\
                .unmask()\
                .eq(19)

            for image_name, image_data in self._mosaics.items():
                if year != image_data['year']:
                    continue
                image = image_data['image']
                path = image_data['path']
                row = image_data['row']
                roi = image_data['geometry']

                training = train_asset.filterBounds(roi.buffer(settings.CLASSIFICATION_BUFFER))

                classifier = ee.Classifier.randomForest(self._trees) \
                    .train(features=training, classProperty='class',
                           inputProperties=list(settings.GENERATION_VARIABLES +
                                                settings.GENERATION_EXTRA_VARIABLES))

                classified = image.updateMask(classification_mask).classify(classifier)
                classified = classified.clip(roi) \
                    .set('year', year) \
                    .set('system:footprint', roi)

                final_image = classified
                final_name = image_name

                self.add_image_in_batch(final_name, {
                    "image": final_image,
                    "year": int(year),
                    "path": int(path),
                    "row": int(row),
                    "geometry": roi
                })


class PlantedForestBLARDClassifier(BaseProcessor):
    def __init__(self, mosaics, train, trees, points, years, buffer):
        BaseProcessor.__init__(self)
        self._mosaics = mosaics
        self._train = train
        self._trees = trees
        self._points = points
        self._years = years
        self._buffer = buffer

    def run(self):
        for year in self._years:
            train_asset = FeatureCollection(self._train)

            for image_name, image_data in self._mosaics.items():
                if year != image_data['year']:
                    continue
                image = image_data['image']
                path = image_data['path']
                row = image_data['row']
                roi = image_data['geometry']

                training = train_asset.filterBounds(roi.buffer(settings.CLASSIFICATION_BUFFER))

                classifier = ee.Classifier.randomForest(self._trees) \
                    .train(features=training, classProperty='class',
                           inputProperties=list(settings.GENERATION_VARIABLES +
                                                settings.GENERATION_EXTRA_VARIABLES))

                classified = image.classify(classifier)
                classified = classified.clip(roi) \
                    .set('year', year) \
                    .set('system:footprint', roi)

                final_image = classified
                final_name = image_name

                self.add_image_in_batch(final_name, {
                    "image": final_image,
                    "year": int(year),
                    "path": int(path),
                    "row": int(row),
                    "geometry": roi
                })