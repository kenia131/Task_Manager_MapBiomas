import ee


class Reducer:

    def __prepare_reducer(reducer_name):
        reducer = f'Reducer.{reducer_name}'

        def prepare(params=None):
            return {'reducer_name': reducer, 'params': params}

        return prepare

    MEAN = __prepare_reducer('mean')
    MEDIAN = __prepare_reducer('median')
    MAX = __prepare_reducer('max')
    MIN = __prepare_reducer('min')
    STDV = __prepare_reducer('stdDev')
    COUNT = __prepare_reducer('count')
    PERCENTILE = __prepare_reducer('percentile')
    QMO = __prepare_reducer('qmo')

    def build_ee_reducer(reducer_name, params=None):
        return ee.call(reducer_name, params) if params else ee.call(reducer_name)
