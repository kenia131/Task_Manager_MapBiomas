import ee


# class _EEFilterBuider():

#     def __init__(self, filter_name, field, value):
#         self.filter_name = filter_name
#         self.field = field
#         self.value = value

#     def build(self):
#         args = {'rightField': self.field, 'leftValue': self.value}
#         return ee.apply(f'Filter.{self.filter_name}', args)

# class _EENestedFilterBuider():

#     def __init__(self, filter_name, inner_filters: _EEFilterBuider[]):
#         self.filter_name = filter_name
#         self.inner_filters = inner_filters

#     def build(self):
#         args = {'filters': [filter.build() for filter in inner_filters]}
#         return ee.apply(f'Filter.{self.filter_name}', args)

# class _EENegateFilterBuider():

#     def __init__(self, filter_to_negate: _EEFilterBuider):
#         self.filter_to_negate = filter_to_negate

#     def build(self):
#         return self.filter_to_negate.build().Not()


def _recursive(query):
    return {'rec': query}


def _build_filter(filter_name, field, value):
    return {filter_name: {'rightField': field, 'leftValue': value}}


def And(*query):
    return {'and': _recursive(list(query))}


def Or(*query):
    return {'or': _recursive(list(query))}


def In(field, values):
    return _build_filter('inList', field, values)


def Eq(field, value):
    return _build_filter('eq', field, value)


def NEq(field, value):
    return _build_filter('neq', field, value)


def Is(field):
    return Eq(field, 1)


def NIs(field):
    return Eq(field, 0)


def Gt(field, value):
    return _build_filter('gt', field, value)


def Gte(field, value):
    return _build_filter('gte', field, value)


def Lt(field, value):
    return _build_filter('lt', field, value)


def Lte(field, value):
    return _build_filter('lte', field, value)


def Not(query):
    return {'not': _recursive(query)}

# build ee filter based on the filter created with the functions above
def build_ee_filter(query):
    def build(filter_name, args):
        if (args.get('rec')):
            args = {'filters': [build_ee_filter(arg) for arg in args['rec']]}

        if (args.get('not')):
            return ee.Filter(build_ee_filter(arg['not'])).Not()

        return ee.apply(f'Filter.{filter_name}', args)

    filter_name, args = list(query.items())[0]
    ee_filter = build(filter_name, args)

    return ee_filter
