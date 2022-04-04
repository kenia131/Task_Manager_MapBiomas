import ee

from rsgee.settings import SettingsManager as sm
from rsgee.image import Image


def generate_tasks_from_batch(batch, filename_sufix):
    export = sm.settings.EXPORT_CLASS

    export_dir = sm.settings.EXPORT_DIRECTORY
    filename_patters = sm.settings.EXPORT_FILENAME_PATTERN
    filename_prefix = sm.settings.EXPORT_FILENAME_PREFIX or sm.settings.NAME

    def generate(output):
        filename = filename_patters.format(
            prefix=filename_prefix,
            year=output.get("year", ""),
            region_id=output.get("region_id", ""),
            sufix=filename_sufix,
        )

        directory = export_dir.format(
            user_assets_root=Export.get_user_assets_root(),
            year=output.get("year", ""),
            region_id=output.get("region_id", ""),
        )

        export_params = {
            "directory": directory.strip("/"),
            "filename": filename,
            "data": output["data"],
        }

        if output.get("region"):
            export_params["region"] = output["region"]

        return export(**export_params)

    tasks = [generate(output) for output in batch.get_all().values()]

    return tasks


class _BaseExport:
    @staticmethod
    def _to_cloud_storage(directory, filename, ee_export, params):
        params.update(
            {
                "bucket": sm.settings.EXPORT_BUCKET,
                "fileNamePrefix": f"{directory}/{filename}",
            }
        )

        return _BaseExport.__export(ee_export, params)

    @staticmethod
    def _to_asset(directory, filename, ee_export, params):
        params.update(
            {"assetId": f"{directory}/{filename}",}
        )

        return _BaseExport.__export(ee_export, params)

    @staticmethod
    def _to_drive(directory, filename, ee_export, params):
        params.update({"folder": directory, "fileNamePrefix": filename})

        return _BaseExport.__export(ee_export, params)

    @staticmethod
    def __export(ee_export, params):
        task = ee_export(**params)

        return task


class ExportImage(_BaseExport):
    class FileFormat:
        GeoTIFF = "GeoTIFF"
        TFRecord = "TFRecord"

    @staticmethod
    def to_cloud_storage(directory, filename, data, region):
        params = ExportImage.__get_default_params(filename, data, region)
        params["fileFormat"] = ExportImage.__get_file_format()
        ee_export = ee.batch.Export.image.toCloudStorage

        return ExportImage._to_cloud_storage(directory, filename, ee_export, params)

    @staticmethod
    def to_asset(directory, filename, data, region):
        params = ExportImage.__get_default_params(filename, data, region)
        ee_export = ee.batch.Export.image.toAsset

        return ExportImage._to_asset(directory, filename, ee_export, params)

    @staticmethod
    def to_drive(directory, filename, data, region):
        params = ExportImage.__get_default_params(filename, data, region)
        params["fileFormat"] = ExportImage.__get_file_format()
        ee_export = ee.batch.Export.image.toDrive

        return ExportImage._to_drive(directory, filename, ee_export, params)

    @staticmethod
    def __get_default_params(filename, image, region):
        image = ExportImage.__cast_image_pixel_type(image)

        return {
            "image": ee.Image(image).clip(region),
            "description": filename,
            "region": region,
            "scale": sm.settings.EXPORT_SCALE,
            "maxPixels": sm.settings.EXPORT_MAX_PIXELS,
        }

    @staticmethod
    def __cast_image_pixel_type(image):
        if sm.settings.EXPORT_PIXEL_TYPE:
            image = Image(image).cast_to(sm.settings.EXPORT_PIXEL_TYPE)

        return image

    @staticmethod
    def __get_file_format():
        return sm.settings.EXPORT_FILE_FORMAT or ExportImage.FileFormat.GeoTIFF


class ExportTable(_BaseExport):
    class FileFormat:
        CSV = "CSV"
        GeoJSON = "GeoJSON"
        KML = "KML"
        KMZ = "KMZ"
        SHP = "SHP"
        TFRecord = "TFRecord"

    @staticmethod
    def to_cloud_storage(directory, filename, data):
        params = ExportTable.__get_default_params(filename, data)
        params["fileFormat"] = ExportTable.__get_file_format()
        ee_export = ee.batch.Export.table.toCloudStorage

        return ExportTable._to_cloud_storage(directory, filename, ee_export, params)

    @staticmethod
    def to_asset(directory, filename, data):
        params = ExportTable.__get_default_params(filename, data)
        ee_export = ee.batch.Export.table.toAsset

        return ExportTable._to_asset(directory, filename, ee_export, params)

    @staticmethod
    def to_drive(directory, filename, data):
        params = ExportTable.__get_default_params(filename, data)
        params["fileFormat"] = ExportTable.__get_file_format()
        ee_export = ee.batch.Export.table.toDrive

        return ExportTable._to_drive(directory, filename, ee_export, params)

    @staticmethod
    def __get_default_params(filename, collection):
        return {"collection": ee.FeatureCollection(collection), "description": filename}

    @staticmethod
    def __get_file_format():
        return sm.settings.EXPORT_FILE_FORMAT or ExportTable.FileFormat.CSV


class Export:
    Image = ExportImage
    Table = ExportTable

    @staticmethod
    def get_user_assets_root():
        roots = [root["id"] for root in ee.data.getAssetRoots()]
        start = "projects/earthengine-legacy/assets/users/"
        user_root = list(filter(lambda root: root.startswith(start), roots))[0]
        user_root = "/".join(user_root.split("/")[3:])

        return user_root
