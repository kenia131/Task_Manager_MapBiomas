import ee


def parse_date(date_format, date_year):
    regex = '\\(.+\\)'
    expression = ee.String(date_format).match(regex).getString(0)
    parsed_year = ee.Number.expression(expression, {'Y': date_year})

    return ee.Date(ee.String(date_format).replace(regex, parsed_year.format('%.0f')))
