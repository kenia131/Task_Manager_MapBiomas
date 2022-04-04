from enum import Enum

import ee


class Index(Enum):
    EVI2 = "EVI2 = 2.5 * (i.NIR - i.RED) / (i.NIR + 2.4 * i.RED + 1)"
    NDVI = "NDVI = (i.NIR - i.RED) / (i.NIR + i.RED)"
    NDWI = "NDWI = (i.NIR - i.SWIR1) / (i.NIR + i.SWIR1)"
    CAI = "CAI = i.SWIR2 / i.SWIR1"
    LAI = "LAI = (0.3977 * exp(2.5556 * (i.NIR - i.RED) / (i.NIR + i.RED)))"
    MNDWI = "MNDWI = (i.GREEN - i.SWIR1) / (i.GREEN + i.SWIR1)"
    AWEI_NSH = "AWEI_NSH = 4 * (i.GREEN - i.SWIR1) -  0.25 * i.NIR + 2.75 * i.SWIR2"
    AWEI_SH = (
        "AWEI_SH = i.BLUE + 2.5 * i.GREEN - 1.5 * (i.NIR + i.SWIR1) - 0.25 * i.SWIR2"
    )
    MSAVI2 = (
        "MSAVI2 = (2 * i.NIR + 1 - sqrt((2 * i.NIR + 1)**2 - 8 * (i.NIR - i.RED))) / 2"
    )
    BSI = "BSI = (i.SWIR2 + i.RED) - (i.SWIR2 - i.BLUE) / (i.SWIR2 + i.RED) + (i.SWIR2 - i.BLUE)"
    CEI = "(10**6 * (wet_max - dry_min) / (10**6 + wet_max + 10**6 + dry_min))"
    GNDVI = "GNDVI = ((i.NIR - i.GREEN) / (i.NIR + i.GREEN))"
    MVI = "MVI = ((i.NIR - i.SWIR1) / (i.NIR + i.SWIR1))"
    SR = "SR = i.NIR / i.RED"
    SAFER = "SAFER = (i.BLUE * BLUE_CV) + (i.GREEN * GREEN_CV) + (i.RED * RED_CV) + (i.NIR * NIR_CV) + (i.SWIR1 * SWIR1_CV) + (i.SWIR2 * SWIR2_CV)"
    CMRI = "CMRI = i.EVI2 - i.NDWI"


def __default_calculator(image, index, params={}):
    params["i"] = image
    return ee.Image(image).expression(index.value, params)


def __SAFER(image, index, params):
    planetary_albedo = __default_calculator(image, index, params)

    temperature_celsius = image.select("TIR1").add(-273.15)
    ndvi = __default_calculator(image, Index.NDVI)

    surface_albedo = planetary_albedo.multiply(params.get("A_ALBEDO")).add(
        params.get("B_ALBEDO")
    )

    safer = (
        temperature_celsius.multiply(params.get("B_ET_ET0"))
        .divide(ndvi.multiply(surface_albedo))
        .add(params.get("A_ET_ET0"))
        .exp()
    )

    safer = ndvi.expression("SAFER = b(0) < 0 ? 0 : SAFER_", {"SAFER_": safer})

    return safer


def __CEI(image, index, params):
    # default = {
    #     # 'input_prefix': '.*',
    #     # 'wet_period': 'WET',
    #     # 'dry_period': 'DRY',
    #     # 'bands': '.*',
    #     # 'max_reducer': 'qmo',
    #     # 'min_reducer': 'min',
    #     'wet_bands': None,
    #     'dry_bands': None,
    #     'output_prefix': 'ANNUAL',
    # }
    # default.update(params)
    # params = default

    # def format_input(period, band_name, reducer):
    #     return '{prefix}_{period}_{band_name}_{reducer}'.format(
    #         prefix=params.get('input_prefix'),
    #         period=params[period],
    #         band_name=band_name,
    #         reducer=params[reducer]
    #     )

    # bands = [band.name if isinstance(band, Enum) else band
    #          for band in params['bands']]

    # def get_bands(period, reducer):
    #     return [format_input(period, band_name, reducer) for band_name in bands]

    # wet_bands = params.get('wet_bands', get_bands('wet_period', 'max_reducer'))
    # dry_bands = params.get('dry_bands', get_bands('dry_period', 'min_reducer'))

    wet_bands = params["wet_bands"]
    dry_bands = params["dry_bands"]
    output_bands = params["output_bands"]

    variables = [*wet_bands, *dry_bands]
    feature_space_size = len(variables)
    zero_list = ee.List([0] * feature_space_size)

    image = (
        ee.Image.constant(zero_list)
        .rename(variables)
        .selfMask()
        .addBands(image, None, True)
    )

    index_params = {
        "wet_max": image.select(wet_bands),
        "dry_min": image.select(dry_bands),
    }

    # def format_output(prefix, band_name):
    #     return f'{prefix}_{band_name}_cei'.strip('_')

    # prefix = params.get('output_prefix')
    # output_bands = [format_output(prefix, band_name) for band_name in bands]

    cei = __default_calculator(image, index, index_params).rename(output_bands)

    return cei


__indexes_functions = {
    Index.SAFER.name: __SAFER,
    Index.CEI.name: __CEI,
}


def calculate_indexes(image, indexes, parameters={}):

    for index in indexes:
        params = parameters.get(index.name, {})
        calculate = __indexes_functions.get(index.name, __default_calculator)
        index = calculate(image, index, params)
        image = image.addBands(index)

    return image
