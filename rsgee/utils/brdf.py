from math import pi
import ee
from rsgee.utils.view_angles import get_view_angles
from rsgee.utils.solar_position import get_solar_position


#
# Apply a BRDF correction to a Landsat image.
# This assumes the image's bands are named using the 'common' naming scheme.
#
# @param {!Image} image The image to correct.  According to the Landsat convention, this
# function assumes that the northern-most point in the footprint is the "northwest" corner.
# @param {boolean} debug If set, all the intermediate calculations are also returned as bands.
# @return {Image} The original image with the corrected bands overwriting the originals.
#
def apply_brdf_correction(image, gain=None, debug=None):
    bands = ['BLUE', 'GREEN', 'RED', 'NIR', 'SWIR1', 'SWIR2']

    solar = get_solar_position(image.date())
    view = get_view_angles(ee.Geometry(image.get('system:footprint')))

    result = adjust_brdf(image.select(bands),
                         solar.select('sun_zen'),
                         view.select('view_zen'),
                         solar.select('sun_az'),
                         view.select('view_az'),
                         gain, 
                         debug)

    return image.addBands(result, None, True)


# Adjusts the BRDFs of Landsat images to nadir observations.
def adjust_brdf(image, sun_zen, view_zen, sun_az, view_az, gain=None, debug=False):
    gain = gain or 2.5

    relative_az = view_az.subtract(sun_az)

    view_zen_norm = deg_2_rad(0)
    sun_zen_norm = deg_2_rad(ee.Image.pixelLonLat().select('latitude').polynomial(
            [31.0076, -0.1272, 0.01187, 2.4e-5, -9.48e-7, -1.95e-9, 6.15e-11]))

    relative_az_norm = deg_2_rad(180)

    # ==================== BRDF parameters  ====================
    #    band     BLUE    GREEN   RED     NIR     SWIR1   SWIR2
    dict = {
        'f_iso': [0.0774, 0.1306, 0.1690, 0.3093, 0.3430, 0.2658],
        'f_vol': [0.0372, 0.0580, 0.0574, 0.1535, 0.1154, 0.0639],
        'f_geo': [0.0079, 0.0178, 0.0227, 0.0330, 0.0453, 0.0387],
        'pi': pi,
        'gain': gain
    }

    # ======== calculate the kernel ========
    sensor = kernel(sun_zen, view_zen, relative_az)
    norm = kernel(sun_zen_norm, view_zen_norm, relative_az_norm)

    # ======== calculate correcting parameter  ========
    formula = 'gain * b("k_geo") * f_geo + gain * b("k_vol") * f_vol + f_iso'
    P1 = norm.expression(formula, dict)
    P2 = sensor.expression(formula, dict)

    norm = add_band_suffix(norm, '_norm')
    sensor = add_band_suffix(sensor, '_sensor')
    c_factor = add_band_suffix(P1.divide(P2), '_c_factor')
    corrected = image.multiply(c_factor)  # corrected reflectance

    if (debug):
        corrected = (corrected
                     .addBands(norm)
                     .addBands(sensor)
                     .addBands(add_band_suffix(P1, '_brdf_norm'))
                     .addBands(add_band_suffix(P2, '_brdf_sensor'))
                     .addBands(c_factor))

    return corrected


# Computes the kgeo and kvol kernels.
def kernel(theta_I, theta_V, azimuth):
    b = 1
    r = 1
    h = 2

    theta_I = theta_I.rename('theta_I')
    theta_V = theta_V.rename('theta_V')
    azimuth = azimuth.rename('azimuth')

    local = ee.Image.cat(theta_I, theta_V, azimuth).rename(['theta_I', 'theta_V', 'azimuth'])

    # ================ calculate kVol  ================

    cos_g = add_expr(local, 'cos_g = cos(theta_I) * cos(theta_V) + sin(theta_I) * sin(theta_V) * cos(azimuth)', {
        'theta_I': theta_I,
        'theta_V': theta_V,
        'azimuth': azimuth.rename('azimuth')
    })

    g = add_expr(local, 'g = acos(clamp(cos_g, -1, 1))', {
        'cos_g': cos_g
    })

    k_vol = add_expr(local, 'k_vol = ((pi/2 - g) * cos(g) + sin(g)) / (cos(theta_I) + cos(theta_V)) - (pi/4)', {
        'g': g,
        'theta_I': theta_I,
        'theta_V': theta_V
    })

    # ================ calculate k_geo  ================

    theta_I1 = add_expr(local, 'theta_I1 = atan(max(b / r * tan(theta_I), 0))', {
        'b': b,
        'r': r,
        'theta_I': theta_I
    })

    theta_V1 = add_expr(local, 'theta_V1 = atan(max(b / r * tan(theta_V), 0))', {
        'b': b,
        'r': r,
        'theta_V': theta_V
    })

    g1 = add_expr(local, 'g1 = cos(theta_I1) * cos(theta_V1) + sin(theta_I1) * sin(theta_V1) * cos(azimuth)', {
        'theta_I1': theta_I1,
        'theta_V1': theta_V1,
        'azimuth': azimuth
    })

    g1 = add_expr(local, 'g1 = acos(clamp(g1, -1, 1))', {
        'g1': g1
    })

    D = add_expr(local, 'D = tan(theta_I1)**2 + tan(theta_V1)**2 - (2 * tan(theta_I1) * tan(theta_V1) * cos(azimuth))', {
        'theta_I1': theta_I1,
        'theta_V1': theta_V1,
        'azimuth': azimuth
    })

    D = add_expr(local, 'D = sqrt(max(D, 0))', {
        'D': D
    })

    tmp = add_expr(local, 'tmp = (tan(theta_I1) * tan(theta_V1) * sin(azimuth))', {
        'theta_I1': theta_I1,
        'theta_V1': theta_V1,
        'azimuth': azimuth
    })

    tmp_2 = add_expr(local, 'tmp_2 = 1/cos(theta_I1) + 1/cos(theta_V1)', {
        'theta_I1': theta_I1,
        'theta_V1': theta_V1
    })

    cos_t = add_expr(local, 'cos_t = h / b * (sqrt(D ** 2 + tmp ** 2)) / tmp_2', {
        'h': h,
        'b': b,
        'D': D,
        'tmp': tmp,
        'tmp_2': tmp_2
    })

    t = add_expr(local, 't = acos(clamp(cos_t, -1, 1))', {
        'cos_t': cos_t
    })

    o = add_expr(local, 'O = 1/pi * (t - sin(t) * cos(t)) * tmp_2', {
        't': t,
        'tmp_2': tmp_2
    })

    o = add_expr(local, 'o = max(0, o)', {
        'o': o
    })

    k_geo = add_expr(local, 'k_geo = o - tmp_2 + (1 + cos(g1)) * (1/cos(theta_I1)) * (1/cos(theta_V1)) / 2', {
        'o': o,
        'tmp_2': tmp_2,
        'g1': g1,
        'theta_I1': theta_I1,
        'theta_V1': theta_V1
    })

    return ee.Image([k_geo, k_vol])


# Rename the bands of image by adding a suffix.
def add_band_suffix(image, suffix):
    bandNames = image.bandNames().map(lambda name: ee.String(name).cat(suffix))
    return image.rename(bandNames)


# Computes a string expression and adds it to the given image.
def add_expr(img, expr, args={}):
    args['pi'] = pi
    args['i'] = img

    return img.expression(expr, args)


def deg_2_rad(value):
    return ee.Image(value).multiply(pi).divide(180)