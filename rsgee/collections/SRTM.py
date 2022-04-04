import ee


class SRTM(ee.Image):

    @staticmethod
    def slope():
        return ee.Terrain.slope(SRTM())

    @staticmethod
    def aspect():
        return ee.Terrain.aspect(SRTM())

    def __init__(self):
        super().__init__('USGS/SRTMGL1_003')
