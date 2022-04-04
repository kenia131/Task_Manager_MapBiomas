from abc import ABC, abstractclassmethod

from rsgee.settings import SettingsManager as sm
from rsgee.featurecollection import FeatureCollection


class BaseProcessor(ABC):

    def __init__(self, batch_keys):
        self._settings = sm.settings
        self._batch = Batch(batch_keys)
        self._grid_collection = FeatureCollection.init_grid_from_settings()

    def _get_regions_ids(self):
        return self._grid_collection.get_features_ids().getInfo()

    def _get_region_by_id(self, region_id):
        return (self._grid_collection
                .get_feature_by_id(region_id))

    def _add_in_batch(self, **data):
        self._batch.add(**data)

    def _get_batch(self):
        return self._batch

    def _get_neighbor_regions_ids(self, region_id):
        id_field = self._settings.GRID_FEATURE_ID_FIELD

        region = (self._grid_collection
                  .get_feature_by_id(region_id)
                  .buffer(1))

        regions_ids = (self._grid_collection
                       .filterBounds(region)
                       .aggregate_array(id_field)
                       .getInfo())

        return regions_ids

    @abstractclassmethod
    def process(self, args):
        pass

    @abstractclassmethod
    def _run(self, **args):
        pass


class Batch():

    def __init__(self, batch_keys):
        self.__key_format = self.__get_key_format(batch_keys)
        self.__batch = {}

    def add(self, **data):
        key = self.__build_key(data)
        self.__batch[key] = data

    def get_element(self, **keys):
        return self.get(**keys)['data']

    def get(self, **keys):
        key = self.__build_key(keys)
        return self.__batch[key]

    def get_all(self):
        return self.__batch

    def __get_key_format(self, keys):
        return '_'.join([f'{{{key}}}' for key in keys])

    def __build_key(self, keys):
        return self.__key_format.format(**keys)
