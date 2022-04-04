import ee

from rsgee.db.models import TaskTypes
from rsgee.imagemaker import ImageMaker
from rsgee.processors import generic as rsgee_processors

COLLECTION_PREFIX = 'L_T1_TOA'

YEARS = list(range(1985, 2018))

# *********** POST PROCESSING SETTINGS ************

POSTPROCESSOR_CLASS = rsgee_processors.PostProcessor
POSTPROCESSING_COLLECTION = 'users/marciano/mapbiomas/classification/merged/annual'
POSTPROCESSING_FILTERS = [rsgee_processors.Filter.TEMPORAL,
                          rsgee_processors.Filter.SPATIAL]

# ********** EXPORT SETTINGS **********************

EXPORT_CLASS = ee.batch.Export.image.toAsset
EXPORT_TASKS = [TaskTypes.POSTPROCESSING]
EXPORT_TYPES = [ImageMaker.IMAGE]
EXPORT_BUCKET = 'agrosatelite-mapbiomas'
EXPORT_ASSET = 'users/marciano'
EXPORT_DIRECTORY = 'classification/filtered/annual'
EXPORT_MAX_TASKS = 5
EXPORT_INTERVAL = 20
EXPORT_BUFFER = 1
EXPORT_SCALE = 30
EXPORT_MAX_PIXELS = 1.0E13
