from abc import ABC, abstractclassmethod

from rsgee.settings import SettingsManager as sm
from rsgee.featurecollection import FeatureCollection


class BaseProcessor(ABC):

    def __init__(self, ):
        self._settings = sm.settings
        self._regions = FeatureCollection.init_grid_from_settings(settings=self._settings)
        self._batch = Batch()

    def _get_region_id(self, region):
        id_field = self._settings.GRID_FEATURE_ID_FIELD
        return region.get(id_field)

    @abstractclassmethod
    def process(self, **args):
        pass

    @abstractclassmethod
    def _run(self, **args):
        pass


class Batch():

    def __init__(self):
        self.__batch = {}

    def add(self, year, collection):
        self.__batch[year] = collection

    def get(self, year):
        return self.__batch[year]

    def get_all(self):
        return self.__batch
