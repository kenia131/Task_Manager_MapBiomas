import ee
from math import pi

#
# Computes the solar position on a per-pixel basis.
#
# @param {!ee.Date} date The date for which to compute the solar angles.
# @return {!ee.Image} An image with sun_zen and sun_az bands.
#
# Converted from Fmask's landsatangles.py:
# https://bitbucket.org/chchrsc/python-fmask/downloads/, which in turn, is
# converted from the 6S POSSOL.f fortran routine:
# https://gitlab.com/satelligence/6SV1.1/blob/master/POSSOL.f
#
# The general approach is to estimate the nadir line from the "middle" of the
# scene. The satellite azimuth is assumed to be at right angles to this nadir
# line, which is only roughly correct. For the whisk-broom sensors on Landsat-5
# and Landsat-7, this angle is not 90 degrees, but is affected by earth rotation
# and is latitude dependent. For Landsat-8, the scan line is at right angles, due
# to the compensation for earth rotation, but the push-broom is made up of
# sub-modules which point in slightly different directions, giving slightly
# different satellite azimuths along the scan line. None of these effects are
# included in the current estimates. The satellite zenith is estimated based on
# the nadir point, the scan-line, and the assumed satellite altitude, and
# includes the appropriate allowance for earth curvature
#
def get_solar_position(date):
    local = ee.Image.pixelLonLat()
    lon_deg = add_expr(local, 'lon_deg = i.longitude', {'i': local})
    lat_rad = add_expr(local, 'lat_rad = i.latitude * pi / 180', {'i': local})

    # Julian date proportion in Radians
    jdpr = date.getFraction('year').multiply(2 * pi)

    mean_solar_time = add_expr(local, 'mean_solar_time = (seconds_GMT / 3600) + (lon_deg / 15)', {
        'seconds_GMT': date.getRelative('second', 'day'),
        'lon_deg': lon_deg
    })

    local_solar_diff = add_expr(local, 'local_solar_diff = (0.000075 '
        + '+ 0.001868 * cos(1 * jdpr) - 0.032077 * sin(1 * jdpr) '
        + '- 0.014615 * cos(2 * jdpr) - 0.040849 * sin(2 * jdpr))'
        + ' * 12 * 60 / pi', {'jdpr': jdpr})

    true_solar_time = add_expr(local, 'true_solar_time = mean_solar_time + local_solar_diff / 60 - 12', {
        'mean_solar_time': mean_solar_time,
        'local_solar_diff': local_solar_diff
    })

    angle_hour = add_expr(local, 'angle_hour = true_solar_time * 15 * pi / 180', {
        'true_solar_time': true_solar_time
    })

    # Solar declination, in radians.
    delta = add_expr(local, 'delta = 0.006918'
        + '- 0.399912 * cos(1 * jdpr) + 0.070257 * sin(1 * jdpr)'
        + '- 0.006758 * cos(2 * jdpr) + 0.000907 * sin(2 * jdpr)'
        + '- 0.002697 * cos(3 * jdpr) + 0.001480 * sin(3 * jdpr)', {
            'jdpr': jdpr
        })

    cos_sun_zen = add_expr(local, 'cos_sun_zen = sin(lat_rad) * sin(delta)'
        + '+ cos(lat_rad) * cos(delta) * cos(angle_hour)', {
            'lat_rad': lat_rad,
            'delta': delta,
            'angle_hour': angle_hour
        })

    sun_zen = add_expr(local, 'sun_zen = acos(cos_sun_zen)', {
        'cos_sun_zen': cos_sun_zen
    })

    sin_sun_az_SW = add_expr(local,
        'sin_sun_az_SW = clamp(cos(delta) * sin(angle_hour) / sin(sun_zen), -1, 1)', {
            'delta': delta,
            'angle_hour': angle_hour,
            'sun_zen': sun_zen
        })

    cos_sun_az_SW = add_expr(local, 'cos_sun_az_SW = (-cos(lat_rad) * sin(delta)'
        + '+ sin(lat_rad) * cos(delta) * cos(angle_hour)) / sin(sun_zen)', {
            'lat_rad': lat_rad,
            'delta': delta,
            'angle_hour': angle_hour,
            'sun_zen': sun_zen
        })

    sun_az_SW = add_expr(local, 'sun_az_SW = asin(sin_sun_az_SW)', {
        'sin_sun_az_SW': sin_sun_az_SW
    })

    sun_az_SW = add_expr(local, 'sun_az_SW = cos_sun_az_SW <= 0 ? pi - sun_az_SW : sun_az_SW', {
        'cos_sun_az_SW': cos_sun_az_SW,
        'sun_az_SW': sun_az_SW
    })

    sun_az_SW = add_expr(local, 'sun_az_SW = cos_sun_az_SW > 0 && sin_sun_az_SW <= 0 ? 2 * pi + sun_az_SW : sun_az_SW', {
        'cos_sun_az_SW': cos_sun_az_SW,
        'sin_sun_az_SW': sin_sun_az_SW,
        'sun_az_SW': sun_az_SW
    })

    sun_az = add_expr(local, 'sun_az = sun_az_SW + pi', {
        'sun_az_SW': sun_az_SW
    })

    sun_az = add_expr(local, 'sun_az = sun_az > 2 * pi ? sun_az - 2 * pi : sun_az', {
        'sun_az': sun_az
    })

    return ee.Image([sun_zen, sun_az])


# Auxiliary functinos


# Computes a string expression and adds it to the given image.
def add_expr(img, expr, args={}):
    args['pi'] = pi
    args['i'] = img

    return img.expression(expr, args)