# -*- coding: utf-8 -*-

import ee
from rsgee.filter import build_ee_filter
from rsgee.settings import SettingsManager as sm


class FeatureCollection(ee.FeatureCollection):

    @staticmethod
    def init_grid_from_settings(settings=None, apply_api_filter=True):
        settings = settings or sm.settings

        collection_id = settings.GRID_COLLECTION_ID
        collection_id_field = settings.GRID_FEATURE_ID_FIELD
        api_filter = settings.GRID_FILTER

        collection = FeatureCollection(collection_id).set('ID_FIELD', collection_id_field)

        if (api_filter and apply_api_filter):
            collection = collection.apply_api_filter(api_filter)

        return collection

    def __init__(self, args, opt_column=None):
        super().__init__(args, opt_column)

    def apply_api_filter(self, api_filter):
        ee_filter = build_ee_filter(api_filter)
        return self.filter(ee_filter)

    def get_features_ids(self, id_field=None):
        id_field = id_field or self.get('ID_FIELD')
        return self.aggregate_array(id_field)

    def get_feature_by_id(self, feature_id, id_field=None):
        id_field = id_field or self.get('ID_FIELD')
        return ee.Feature(self.filterMetadata(id_field, 'equals', feature_id).first())
