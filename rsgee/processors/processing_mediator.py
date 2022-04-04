from rsgee.settings import SettingsManager as sm
from rsgee import export


class ProcessingMediator():

    def __init__(self):
        self.__data = {}
        self.__to_export_key = ''

    def process(self):
        generator = sm.settings.GENERATOR_CLASS
        samples = sm.settings.SAMPLING_CLASS
        classifier = sm.settings.CLASSIFICATION_CLASS
        post_processor = sm.settings.POST_PROCESSING_CLASS

        if (generator):
            self.__execute(generator, 'mosaics')

        if (samples):
            self.__execute(samples, 'samples')

        if (classifier):
            self.__execute(classifier, 'raw_results')

        if (post_processor):
            self.__execute(post_processor, 'results')

        batch = self.__data[self.__to_export_key]

        filename_sufix = {
            'mosaics': 'mosaic',
            'samples': 'samples',
            'raw_results': 'raw_result',
            'filtered_results': 'filtered_result'
        }[self.__to_export_key]

        return export.generate_tasks_from_batch(batch, filename_sufix)

    def __execute(self, processor, output_key):
        processor = processor()
        print(type(processor))

        result = processor.process(**self.__data)

        self.__data[output_key] = result
        self.__to_export_key = output_key
