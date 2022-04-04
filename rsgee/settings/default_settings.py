class DefaultSettings():

    NAME = 'default'

    # ************* COLLECTION SETTINGS *************

    IMAGE_COLLECTION = None

    GRID_COLLECTION_ID = ''

    # ******************* FITLERS *******************

    YEARS = []

    GRID_FILTER = None

    GRID_FEATURE_ID_FIELD = 'PATHROW'

    # ********** GENERATION SETTINGS *******************

    GENERATOR_CLASS = None

    GENERATION_BANDS = []

    GENERATION_INDEXES = []

    GENERATION_EXTRA_INDEXES = []

    GENERATION_INDEXES_PARAMS = {}

    GENERATION_REDUCERS = []

    GENERATION_VARIABLES = []

    GENERATION_PERIODS = []

    GENERATION_OFFSET = 0

    GENERATION_MAX_CLOUD_COVER = 90

    GENERATION_APPLY_BRDF = False

    GENERATION_APPLY_ILLUMINATION_CORRECTION = False

    GENERATION_APPLY_CLOUD_AND_SHADOW_MASK = True

    GENERATION_SCALING_FACTORS = {}

    GENERATION_BUFFER = 0

    GENERATION_USE_GEOMETRY_CENTROID = False

    GENERATION_ADDITIONAL_DATA = []

    # *********** SAMPLING SETTINGS ***********

    SAMPLING_CLASS = None

    SAMPLING_POINTS = 10000

    SAMPLING_REFERENCE_ID = ''

    SAMPLES_COLLECTION_ID = ''

    SAMPLING_MASK_ID = ''

    SAMPLING_BUFFER = 0

    # ********** CLASSIFICATION SETTINGS **************

    CLASSIFICATION_CLASS = None

    CLASSIFICATION_TRAIN = ''

    CLASSIFICATION_TREES = 100



    # *********** POST PROCESSING SETTINGS ************

    POST_PROCESSING_CLASS = None

    # POSTPROCESSING_COLLECTION = ''

    # POSTPROCESSING_FILTERS = []

    # POSTPROCESSING_TEMPORAL_FILTER_THRESHOLD = 2

    # POSTPROCESSING_TEMPORAL_FILTER_OFFSET = 2

    # POSTPROCESSING_SPATIAL_FILTER_THRESHOLD = 15

    # POSTPROCESSING_SPATIAL_FILTER_KERNEL = [
    #     [1, 1, 1, 1, 1],
    #     [1, 2, 2, 2, 1],
    #     [1, 2, 2, 2, 1],
    #     [1, 2, 2, 2, 1],
    #     [1, 1, 1, 1, 1]
    # ]

    # ********** EXPORT SETTINGS **********************

    EXPORT_CLASS = None

    EXPORT_BUCKET = ''

    EXPORT_DIRECTORY = ''

    EXPORT_MAX_TASKS = 3

    EXPORT_INTERVAL = 10

    EXPORT_MAX_ERRORS = 0

    EXPORT_SCALE = 30

    EXPORT_SCALES = {}

    EXPORT_MAX_PIXELS = 1.0E13

    EXPORT_FILE_FORMAT = None

    EXPORT_PIXEL_TYPE = None

    EXPORT_FILENAME_PATTERN = '{prefix}_{year}_{region_id}_{sufix}'

    EXPORT_FILENAME_PREFIX = None

    @classmethod
    def get_formated(clss, key, **args):
        return clss.__dict__[key].format(settings_name=clss.NAME, **args)
