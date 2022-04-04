import ee
import math

from rsgee.conf import settings
from rsgee.imagecollection import ImageCollection
from rsgee.processors.generic.base import BaseProcessor2


class SoybeanSampler(BaseProcessor2):
    def __init__(self, mosaics, train, points, years):
        BaseProcessor2.__init__(self)
        self._mosaics = mosaics
        self._train = train
        self._points = points
        self._years = years

    def run(self):
        for year in self._years:
            train_asset = ImageCollection(self._train) \
                .filterMetadata('year', 'equals', int(year)) \
                .max() \
                .eq(1)

            for image_name, image_data in self._mosaics.items():
                if year != image_data['year']:
                    continue
                image = image_data['image']
                path = image_data['path']
                row = image_data['row']
                roi = image_data['geometry']

                train = train_asset.clip(roi) \
                    .unmask(None).rename('class')

                image = image.addBands(train).unmask()

                training = ee.FeatureCollection(image.sample(
                    region=roi,
                    numPixels=int(self._points),
                    scale=settings.EXPORT_SCALE,
                    tileScale=6,
                    geometries=True
                ))

                final_name = image_name + '_samples'

                self.add_in_batch(final_name, {
                    "element": training,
                    "year": int(year),
                    "path": int(path),
                    "row": int(row),
                    "geometry": roi
                })

class SoybeanStratifiedSampler(BaseProcessor2):
    def __init__(self, mosaics, train, points, years):
        BaseProcessor2.__init__(self)
        self._mosaics = mosaics
        self._train = train
        self._points = points
        self._years = years

    def get_area(self, image, roi):
        area = ee.Image.pixelArea().multiply(image).reduceRegion(
            reducer=ee.Reducer.sum(),
            geometry=image.geometry(),
            scale=settings.EXPORT_SCALE,
            maxPixels=10e10
        )

        return area.values().getNumber(0)

    def run(self):

        train_asset = ee.Image(self._train)

        for year in self._years:
            for image_name, image_data in self._mosaics.items():
                if year != image_data['year']:
                    continue

                image = image_data['image']
                path = image_data['path']
                row = image_data['row']
                roi = image_data['geometry']

                image = image.addBands(train_asset).unmask()

                current_year_soybean = ee.ImageCollection(settings.SAMPLING_PROPORTIONS)\
                    .filterMetadata('year', 'equals', int(year))\
                    .first()

                soybean_area = self.get_area(current_year_soybean.eq(1), roi)
                others_area = self.get_area(current_year_soybean.eq(0), roi)
                total_area = soybean_area.add(others_area)
                proportion = soybean_area.divide(total_area)

                total_points = ee.Number(self._points)
                minimum = 0.2

                soybean_points = total_points.multiply(proportion).ceil()\
                    .max(total_points.multiply(minimum))\
                    .min(total_points.multiply(1 - minimum))

                other_points = total_points.subtract(soybean_points)

                samples = ee.FeatureCollection(image.stratifiedSample(
                    numPoints=0,
                    classBand='class',
                    region=roi,
                    classValues=[0, 1, 2],  # others, stable, unstable
                    classPoints=[other_points, soybean_points, 0],
                    scale=settings.EXPORT_SCALE,
                    tileScale=6,
                    geometries=True
                ))

                final_name = image_name + '_samples'

                self.add_in_batch(final_name, {
                    "element": samples,
                    "year": int(year),
                    "path": int(path),
                    "row": int(row),
                    "geometry": roi
                })


class AnnualPerennialSampler(BaseProcessor2):
    def __init__(self, mosaics, train, points, years):
        BaseProcessor2.__init__(self)
        self._mosaics = mosaics
        self._train = train
        self._points = points
        self._years = years

    def get_area(self, image, roi):
        area = ee.Image.pixelArea().multiply(image).reduceRegion(
            reducer=ee.Reducer.sum(),
            geometry=roi,
            scale=settings.EXPORT_SCALE,
            maxPixels=10e10
        )

        return area.values().getNumber(0)

    def run(self):
        reference = ee.Image(self._train).unmask()
        annual_perennial = reference.eq(1).Or(reference.eq(3))

        reference = reference.updateMask(annual_perennial)

        for year in self._years:

            agriculture_c4 = ee.ImageCollection(settings.SAMPLING_MASK)\
                .filterMetadata('year', 'equals', year)\
                .first()\
                .unmask()\
                .eq(19)

            train_asset = reference.updateMask(agriculture_c4)

            for image_name, image_data in self._mosaics.items():
                if year != image_data['year']:
                    continue
                image = image_data['image']
                path = image_data['path']
                row = image_data['row']
                roi = image_data['geometry']

                annual_area = self.get_area(train_asset.eq(1), roi)
                perennial_area = self.get_area(train_asset.eq(3), roi)

                total_area = annual_area.add(perennial_area)
                annual_proportion = annual_area.divide(total_area)

                total_points = ee.Number(ee.Algorithms.If(
                    annual_proportion.gte(0.1).And(annual_proportion.lte(0.9)),
                    ee.Number(self._points),
                    ee.Number(self._points).divide(2)
                    ))

                minimum = 0.2

                annual_points = total_points.multiply(annual_proportion).ceil()\
                    .max(total_points.multiply(minimum))\
                    .min(total_points.multiply(1 - minimum))

                perennial_points = total_points.subtract(annual_points)

                train = train_asset.unmask(None).rename('class')
                image = image.addBands(train).unmask()

                training = ee.FeatureCollection(image.stratifiedSample(
                    numPoints=0,
                    classBand='class',
                    region=roi,
                    classValues=[1, 3],  # annual, perennial
                    classPoints=[annual_points, perennial_points],
                    scale=settings.EXPORT_SCALE,
                    tileScale=6,
                    geometries=True
                ))

                final_name = image_name + '_samples'

                self.add_in_batch(final_name, {
                    "element": training,
                    "year": int(year),
                    "path": int(path),
                    "row": int(row),
                    "geometry": roi
                })


class PlantedForestSampler(BaseProcessor2):
    def __init__(self, mosaics, train, points, years):
        BaseProcessor2.__init__(self)
        self._mosaics = mosaics
        self._train = train
        self._points = points
        self._years = years

    def run(self):

        train = ee.ImageCollection(self._train)\
            .max()\
            .eq(1)\
            .unmask()\
            .rename('class')\

        for year in self._years:
            for image_name, image_data in self._mosaics.items():
                if year != image_data['year']:
                    continue
                image = image_data['image']
                path = image_data['path']
                row = image_data['row']
                roi = image_data['geometry']

                image = image.unmask().addBands(train)
                
                training = ee.FeatureCollection(image.sample(
                    region=roi,
                    numPixels=int(self._points),
                    scale=settings.EXPORT_SCALE,
                    tileScale=6,
                    geometries=True
                ))

                final_name = image_name + '_samples'

                self.add_in_batch(final_name, {
                    "element": training,
                    "year": int(year),
                    "path": int(path),
                    "row": int(row),
                    "geometry": roi
                })
