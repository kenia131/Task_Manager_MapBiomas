from rsgee.core.exceptions import SettingsNotFound


class SettingsManager:

    settings = None

    __all_settings = {}

    @staticmethod
    def add_settings(settings):
        SettingsManager.__all_settings[settings.NAME] = settings

    @staticmethod
    def get_settings(settings_name):
        if (settings_name in SettingsManager.__all_settings):
            return SettingsManager.__all_settings[settings_name]

        raise SettingsNotFound(settings_name)

    @staticmethod
    def set_running_settings(settings_name):
        SettingsManager.settings = SettingsManager.get_settings(settings_name)

    @staticmethod
    def get_processors():
        if SettingsManager.settings:
            processors = [
                SettingsManager.settings.GENERATOR_CLASS,
                SettingsManager.settings.SAMPLING_CLASS,
                SettingsManager.settings.CLASSIFICATION_CLASS,
                SettingsManager.settings.POST_PROCESSING_CLASS
            ]

            return [processor() for processor in processors if processor]

        return []
