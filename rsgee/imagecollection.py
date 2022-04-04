import ee

from rsgee.image import Image
from rsgee.reducer import Reducer
from rsgee.utils import date


class ImageCollection(ee.ImageCollection):

    COLLECTION_NAME = ''

    # default bands and corresponding commom names
    BANDS_MAPPING = {}

    # default properties to set in the images
    DEFAULT_PROPERTIES = {}

    # bitmasks for qa bands
    QA_BITMASKS = {}

    # default bitmasks to mask cloud and shadow (names only, as is in QA_BITMASKS)
    CLOUD_AND_SHADOW_BITMASKS = []

    # default score used in bitmask.score method, order matters.
    DEFAULT_QA_SCORES = []

    # default parameters for indexes like SAFER
    DEFAULT_INDEXES_PARAMETERS = {}

    # factor to apply before calculing indexes
    # it should scale bands like red, green etc to 0..1 and termal bands to celcius
    # this default scale is needed for some indexes
    SCALING_FACTOR = {}

    def padronize_band_names(self, bands_mapping=None):
        bands_mapping = bands_mapping or self.BANDS_MAPPING

        if not bands_mapping:
            return self

        original_names = list(bands_mapping.keys())
        new_names = list(bands_mapping.values())

        return self.select(original_names, new_names)

    def padronize_band_scales(self, scaling_factors=None):
        scaling_factors = scaling_factors or self.SCALING_FACTOR

        if not scaling_factors:
            return self

        def scale(image):
            return Image(image).apply_scaling_factors(scaling_factors)

        return self.map(scale)

    def padronize_properties(self, properties=None):
        properties = properties or self.DEFAULT_PROPERTIES

        if not properties:
            return self

        def set_multi(image):
            return image.setMuli(properties)

        return self.map(set_multi)

    def calculate_indexes(self, indexes, parameters={}, set_default_params=True):

        def add_default_params(index):
            default_parameters = self.get_index_default_parameters(index)
            user_parameters = parameters.get(index.name, {})
            default_parameters.update(user_parameters)

            return default_parameters

        if set_default_params:
            parameters = {index.name: add_default_params(index) for index in indexes}

        def calculate(image):
            return Image(image).calculate_indexes(indexes, parameters)

        return self.map(calculate)

    def filter_period(self, period_start, period_end, year, offset=0):
        end_year = ee.Number(year)
        start_year = end_year.subtract(offset)

        def create_filter(period_year):
            start_date = date.parse_date(period_start, period_year)
            end_date = date.parse_date(period_end, period_year)

            return ee.Filter.date(start_date, end_date)

        filters = ee.List.sequence(start_year, end_year).map(create_filter)
        filtered = self.filter(ee.call('Filter.or', filters))

        return filtered

    def apply_reducers(self, reducers):
        # lists are not immutable, can't pop from received reducers list,
        # so we need to duplicate it
        _reducers = [*reducers]

        # verify if QMO is in the list and extract it to a new list
        qmo = [_reducers.pop(index) for index, reducer in enumerate(_reducers)
               if 'qmo' in reducer['reducer_name']]

        _reducers = [Reducer.build_ee_reducer(**reducer) for reducer in _reducers]

        reduced = ee.Image(0).select([])

        if (len(_reducers) > 0):
            def combine(reducer, combined):
                return ee.Reducer(combined).combine(reducer, sharedInputs=True)

            first = _reducers.pop(0)
            combined_reducers = ee.List(_reducers).iterate(combine, first)
            reduced = self.reduce(combined_reducers)

        # if QMO was found, apply it
        if bool(qmo):
            quality_band = qmo[0]['params'].name
            qmo = Image(self.qualityMosaic(quality_band)).compose_band_names(sufix='qmo')
            reduced = reduced.addBands(qmo)

        return Image(reduced)

    def mask_clouds_and_shadows(self):
        return self.apply_bitmasks(
            bitmasks_names=self.CLOUD_AND_SHADOW_BITMASKS,
            reverse_mask=True)

    def apply_bitmasks(self, bitmasks=None, bitmasks_names=None, reverse_mask=False):
        bitmasks = bitmasks or self.get_bitmasks(bitmasks_names)

        def apply(image):
            return Image(image).apply_bitmasks(bitmasks, reverse_mask=reverse_mask)

        return self.map(apply)

    def score_images(self, bitmasks_scores=None):
        bitmasks_scores = bitmasks_scores or self.DEFAULT_QA_SCORES

        bitmasks_scores = {
            key: self.get_bitmasks(bitmasks_names)
            for key, bitmasks_names in bitmasks_scores.items()}

        def score(image):
            return Image(image).score_image(bitmasks_scores)

        return self.map(score)

    def apply_brdf(self):
        def apply(image):
            return Image(image).apply_brdf()

        return self.map(apply)

    def get_index_default_parameters(self, index):
        return {
            **self.DEFAULT_INDEXES_PARAMETERS.get(index.name, {})
        }

    def to_bands(self):
        def add_bands(image, all_bands):
            return ee.Image(all_bands).addBands(image, None, True)

        return self.iterate(add_bands, Image(None))

    # def __map(self, method_name, params={}):
    #     params.pop('self', None)

    #     def apply(image):
    #         return getattr(Image(image), method_name)(**params)

    #     return self.map(apply)

    @classmethod
    def get_bitmasks(cls, bitmasks_names):
        return [cls.QA_BITMASKS[name] for name in bitmasks_names]
