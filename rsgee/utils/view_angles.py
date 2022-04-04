from math import pi
import ee


# Compute the viewing angles from the scene's geometry.
def get_view_angles(footprint):
    max_distance_to_scene_edge = 210000
    max_satellite_zenith = 7.5

    corners = find_corners(footprint)

    # Get a center-line by splitting the distance between the 'top' points and the 'bottom' points.
    upperCenter = point_between(corners['upper_left'], corners['upper_right'])
    lowerCenter = point_between(corners['lower_left'], corners['lower_right'])
    slope = slope_between(lowerCenter, upperCenter)

    # An empty image to hold the results.
    result = ee.Image().select()
    view_az = add_expr(result, 'view_az = pi / 2 - atan(-1 / slope)', {'slope': slope})

    left_line = to_line(corners['upper_left'], corners['lower_left'])
    right_line = to_line(corners['upper_right'], corners['lower_right'])
    left_distance = ee.FeatureCollection(left_line).distance(max_distance_to_scene_edge)
    right_distance = ee.FeatureCollection(right_line).distance(max_distance_to_scene_edge)

    view_zen = add_expr(result,
        'view_zen = ((right * max_zen * 2) / (right + left) - max_zen) * pi / 180', {
            'left': left_distance,
            'right': right_distance,
            'max_zen': max_satellite_zenith
        })

    return ee.Image([view_az, view_zen])


# Computes a string expression and adds it to the given image.
def add_expr(img, expr, args={}):
    args['pi'] = pi
    args['i'] = img

    return img.expression(expr, args)


def find_corners(footprint):
    coords = ee.Geometry(footprint).coordinates()
    x_values = coords.map(get_x)
    y_values = coords.map(get_y)

    # Get the coordinate corresponding to the item in values closest to the targetValue.
    def find_corner(target_value, values):
        diff = values.map(lambda value: ee.Number(value).subtract(target_value).abs())
        min_value = diff.reduce(ee.Reducer.min())
        return coords.get(diff.indexOf(min_value))

    # This function relies on the order of the points in geometry.bounds being constant.
    bounds = ee.List(footprint.bounds(1).coordinates().get(0))

    return {
        'upper_left': find_corner(get_y(bounds.get(3)), y_values),
        'upper_right': find_corner(get_x(bounds.get(2)), x_values),
        'lower_right': find_corner(get_y(bounds.get(1)), y_values),
        'lower_left': find_corner(get_x(bounds.get(0)), x_values)
    }


# Make a line from two points.
def to_line(point_A, point_B):
    return ee.Geometry.LineString([point_A, point_B], None, True)


# Compute the center point between two points, on the sphere
def point_between(point_A, point_B):
    return ee.Geometry.LineString([point_A, point_B], None, True).centroid().coordinates()


# Compute the slope between two points
def slope_between(point_A, point_B):
    return ee.Number.expression('(yA - yB) / (xA - xB)', {
        'yA': get_y(point_A),
        'yB': get_y(point_B),
        'xA': get_x(point_A),
        'xB': get_x(point_B)
    })


# Extract the x value from a point.
def get_x(point):
    return ee.List(point).getNumber(0)


# Extract the y value from a point.
def get_y(point):
    return ee.List(point).getNumber(1)
