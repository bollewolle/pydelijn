import logging
import os
import tempfile

import shapefile

from pystibmvib.client import AbstractSTIBAPIClient
from pystibmvib.domain.line import LineInfo
from pystibmvib.domain.stop import StopInfo

LOGGER = logging.getLogger(__name__)

SHAPEFILES_ZIP_FILENAME = "shapefiles.zip"

ENDPOINT_SHAPEFILES = '/Files/2.0/Shapefiles'

SEP = os.sep
SHAPEFILESFOLDERPATH = tempfile.gettempdir() + SEP + "stibmvibshapefiles"
LINES_FILENAME = "ACTU_LINES"
STOPS_FILENAME = "ACTU_STOPS"
TIMESTAMPFILENAME = "timestamp"
DELTA_MAX_TIMESTAMP = 1 * 60 * 60 * 24 * 7  # 1 week


class ShapefileService:
    def __init__(self, stib_api_client: AbstractSTIBAPIClient):
        self.api_client = stib_api_client
        self.lines_cache = {}
        self.stops_cache = {}

    async def get_line_info(self, line_nr: int):
        await self._refresh_shapefiles()
        if line_nr not in self.lines_cache.keys():
            sf = shapefile.Reader(SHAPEFILESFOLDERPATH + SEP + LINES_FILENAME)
            for record in sf.records():
                record = record.as_dict()
                current_line_nr, line_type = record["LIGNE"][:-1], record["LIGNE"][-1:]
                if int(line_nr) == int(current_line_nr):
                    self.lines_cache[line_nr] = LineInfo(int(current_line_nr), line_type.upper(), record["COLOR_HEX"])
                    break
        return self.lines_cache[line_nr]

    async def get_stop_infos(self, stop_name: str):
        await self._refresh_shapefiles()
        if stop_name not in self.stops_cache.keys():
            sf = shapefile.Reader(SHAPEFILESFOLDERPATH + SEP + STOPS_FILENAME)
            res: StopInfo = StopInfo(stop_name)
            for record in sf.records():
                record = record.as_dict()
                if record["alpha_fr"].upper() == stop_name.upper() or record["alpha_nl"].upper() == stop_name.upper():
                    res.add_stop(record["stop_id"], record["numero_lig"], record["variante"], record["terminus"])
                    res.add_line_info(await self.get_line_info(record["numero_lig"]))
            self.stops_cache[stop_name] = res
        return self.stops_cache[stop_name]

    async def _refresh_shapefiles(self):
        """ Get most recent file info if not in local cache (api for files can be called only once per minute.
        These file change only 2 or 3 times per year thus we will invalidate them after one week.
        To force update simply delete the timestamp file."""
        if self._must_update_shapefiles():
            import time
            LOGGER.info("Shapefiles validity outdated, updating them...")
            with open(SHAPEFILESFOLDERPATH + SEP + TIMESTAMPFILENAME, 'w') as f:
                f.write(str(time.time()))

            zipped_data = await self.api_client.api_call(ENDPOINT_SHAPEFILES)
            if zipped_data is not None:
                import zipfile
                # save data to disk
                zip_path = SHAPEFILESFOLDERPATH + SEP + SHAPEFILES_ZIP_FILENAME
                LOGGER.info("Saving new zip of shapefiles to " + str(zip_path))
                with open(zip_path, 'wb') as output:
                    output.write(zipped_data)
                    output.close()

                # extract the data
                zfobj = zipfile.ZipFile(zip_path)
                for name in zfobj.namelist():
                    uncompressed = zfobj.read(name)
                    name = name.split('/')[-1]

                    # save uncompressed data to disk
                    output_filename = SHAPEFILESFOLDERPATH + SEP + name
                    LOGGER.info("Saving extracted file to " + str(output_filename))
                    with open(output_filename, 'wb') as output:
                        output.write(uncompressed)

                # TODO os.remove(zip_filename)
                LOGGER.info("Finished updating Shapefiles!")
                self.lines_cache = {}
                self.stops_cache = {}
            else:
                LOGGER.error("Unable to update Shapefiles...")

    def _must_update_shapefiles(self):
        import time
        must_update = False
        if not os.path.isdir(SHAPEFILESFOLDERPATH):
            LOGGER.info("Shapefile folder not existing, creating it...")
            must_update = True
            os.mkdir(SHAPEFILESFOLDERPATH)
        if not os.path.isfile(SHAPEFILESFOLDERPATH + SEP + TIMESTAMPFILENAME):
            LOGGER.info("Shapefile timestamp file not existing, creating it...")
            with open(SHAPEFILESFOLDERPATH + SEP + TIMESTAMPFILENAME, 'w') as f:
                f.write(str(time.time()))
            must_update = True
        with open(SHAPEFILESFOLDERPATH + SEP + TIMESTAMPFILENAME, 'r') as f:
            timestamp = int(f.read().split(".")[0])
            now = time.time()
            if now - timestamp > DELTA_MAX_TIMESTAMP:
                must_update = True
                LOGGER.info(
                    f"Delta since last update is {now - timestamp} which is greater than {DELTA_MAX_TIMESTAMP}. Invalidating files...")
        return must_update
