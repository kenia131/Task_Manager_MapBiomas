from math import pi
import ee


def harmonize_landsat(collection, start_date, output_bands=None, harmonics=3):
    output_bands = output_bands or ee.List(['BLUE', 'GREEN', 'RED', 'NIR', 'SWIR1', 'SWIR2'])

    independents = get_independent_terms(collection, harmonics, start_date)
    dependents = collection.select(output_bands)

    harmonic_trend_coefficients = get_trend_coefficients(dependents, independents)

    fitted = fit_collection(output_bands, independents, harmonic_trend_coefficients)

    harmonic_trend_coefficients = harmonic_trend_coefficients.set('HARMONICS', ee.Number(harmonics))

    return {
        'coefficients': harmonic_trend_coefficients,
        'harmonized_collection': fitted
    }


def get_independent_terms(collection, harmonics, start_date):
    harmonic_frequencies = ee.List.sequence(1, harmonics)

    cos_names = construct_band_names('cos_', harmonic_frequencies)
    sin_names = construct_band_names('sin_', harmonic_frequencies)

    harmonic_frequencies = ee.Image.constant(harmonic_frequencies)

    def get_terms(image):
        constant = ee.Image(1)

        years = image.date().difference(start_date, 'year')
        time_radians = ee.Image(years.multiply(2 * pi)).rename('t').toFloat()

        cosines = time_radians.multiply(harmonic_frequencies).cos().rename(cos_names)
        sines = time_radians.multiply(harmonic_frequencies).sin().rename(sin_names)

        return (constant
                .addBands(time_radians)
                .addBands(cosines)
                .addBands(sines)
                .copyProperties(image, ['system:index', 'system:time_start']))

    terms = ee.ImageCollection(collection).map(get_terms)

    return terms


def construct_band_names(base, list):
    base = ee.String(base)

    return ee.List(list).map(
        lambda i: base.cat(ee.Number(i).int()))


def get_trend_coefficients(dependents, independents):
    independents_names = independents.first().bandNames()
    dependents_names = dependents.first().bandNames()

    reducer = ee.Reducer.linearRegression(independents_names.length(), dependents_names.length())

    harmonic_trend = independents.combine(dependents).reduce(reducer)

    coefficients = (harmonic_trend
                    .select('coefficients')
                    .arrayFlatten([independents_names, dependents_names]))

    return coefficients


def fit_collection(bands, independents_collection, coefficients):

    fitted_names = bands.map(
        lambda band_name: ee.String('fitted_').cat(band_name))

    fitted = independents_collection.map(
                lambda image: (
                    image
                    .toArray()
                    .toArray(1)
                    .arrayTranspose()
                    .matrixMultiply(coefficients)
                    .arrayProject([1])
                    .arrayFlatten([fitted_names])
                    .copyProperties(image, ['system:index', 'system:time_start'])))

    return fitted


def get_sazonality(harmonic_trend_coefficients):
    def compose_name(replace_for):
        return lambda name: ee.String(name).replace('(sin|cos)', replace_for)

    sin = harmonic_trend_coefficients.select('sin.*')
    cos = harmonic_trend_coefficients.select('cos.*')

    magnitude_names = sin.bandNames().map(compose_name('magnitude'))
    magnitude = sin.hypot(cos).multiply(5).rename(magnitude_names)

    phase_names = sin.bandNames().map(compose_name('phase'))
    phase = sin.atan2(cos).unitScale(-pi, pi).rename(phase_names)

    seasonality = ee.Image.cat(magnitude, phase)

    return seasonality
