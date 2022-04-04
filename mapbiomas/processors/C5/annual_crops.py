import ee

from datetime import datetime

from rsgee.processors.generic.classifier import BaseClassifier
from rsgee.processors.generic.generator import BaseGenerator
from rsgee.processors.generic.sampler import BaseSampler
from rsgee.image import Image
from rsgee.imagecollection import ImageCollection


class DefaultGenerator(BaseGenerator):
    def _run(self):
        regions_ids = self._get_regions_ids()

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

                if self._settings.GENERATION_EXTRA_INDEXES:
                    mosaic = mosaic.calculate_indexes(
                        self._settings.GENERATION_EXTRA_INDEXES,
                        self._settings.GENERATION_INDEXES_PARAMS,
                    )

                feature_space = ee.List(self._settings.GENERATION_VARIABLES)

                mosaic = mosaic.select(feature_space).set({
                    "year": year, 
                    "region_id": region_id
                })

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


class DefaultSimpleSampler(BaseSampler):

    def _run(self, mosaics):
        regions_ids = self._get_regions_ids()
        bounds = ee.FeatureCollection('users/agrosatelite_mapbiomas/REGIONS/BIOMAS_IBGE_250K')

        for year in self._settings.YEARS:
            ref_year = year - 1 if year > 2016 else year + 1
            print(ref_year)
            training_reference = (ee.ImageCollection(self._settings.SAMPLING_REFERENCE_ID)
                                  .filterMetadata('year', 'equals', ref_year)
                                  .max()
                                  .eq(1)
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
                               geometries=True)
                           .filterBounds(bounds))

                samples = (samples.set({
                           'year': year,
                           'region_id': region_id}))

                self._add_in_batch(
                    year=year,
                    region_id=region_id,
                    data=samples)


class DefaultClassifier(BaseClassifier):

    def _run(self, samples, mosaics):
        regions_ids = self._get_regions_ids()

        for year in self._settings.YEARS:
            for region_id in regions_ids:
                roi = self._get_region_by_id(region_id).geometry()

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
