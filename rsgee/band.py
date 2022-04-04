
class Band:
    COASTAL = "COASTAL"
    BLUE = "BLUE"
    GREEN = "GREEN"
    RED = "RED"
    NIR = "NIR"
    NIR2 = "NIR2"
    SWIR1 = "SWIR1"
    SWIR2 = "SWIR2"
    TIR1 = "TIR1"
    TIR2 = "TIR2"
    PAN = "PAN"
    CIRRUS = "CIRRUS"
    BQA = "BQA"
    QA_SCORE = "QA_SCORE"

    @staticmethod
    def contains(bands):
        return [f'.*{band}.*' for band in bands]

    @staticmethod
    def start_with(bands):
        return [f'{band}.*' for band in bands]

    @staticmethod
    def end_with(bands):
        return [f'.*{band}' for band in bands]
