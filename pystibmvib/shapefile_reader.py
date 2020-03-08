import os
import tempfile

import shapefile

from .common import LOGGER

SEP = os.sep
SHAPEFILESFOLDERPATH = tempfile.gettempdir() + SEP + "stibmvibshapefiles"
print(SHAPEFILESFOLDERPATH)
TIMESTAMPFILENAME = "timestamp"
LINES_FILENAME = "LIGNES_BRUTES"
STOPS_FILENAME = "ACTU_STOPS"
LINE_TECH_ID_INDEX = 0
STOP_ID_INDEX = 4
STOP_NAME_INDEX = 6
LINE_NUMBER_INDEX = 0
DELTA_MAX_TIMESTAMP = 1 * 60 * 60 * 24 * 7  # 1 week


class ShapefileReader():
    def __init__(self, loop, session, client_id, client_secret):
        self.loop = loop
        self.session = session
        self.client_id = client_id
        self.client_secret = client_secret

    async def _refresh_shapefiles(self):
        """ Get most recent file info if not in local cache (api for files can be called only once per minute.
        These file change only 2 or 3 times per year thus we will invalidate them after one week.
        To force update simply delete them or the timestamp file."""
        must_update = False
        import os
        import time
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

        if must_update:
            LOGGER.info("Shapefiles validity outdated, updating them...")
            with open(SHAPEFILESFOLDERPATH + SEP + TIMESTAMPFILENAME, 'w') as f:
                f.write(str(time.time()))
            from .common import APIClient
            selfcreatedsession = False
            if self.session is None:
                selfcreatedsession = True

            common = APIClient(self.loop, self.session, self.client_id, self.client_secret)

            endpointshapefiles = '/Files/2.0/Shapefiles'
            zipped_data = await common.api_call(endpointshapefiles)
            if zipped_data is not None:
                import zipfile
                zip_filename = "shapefiles.zip"
                # save data to disk
                LOGGER.info("Saving to " + str(zip_filename))
                zip_path = SHAPEFILESFOLDERPATH + SEP + zip_filename
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

                # FIXME os.remove(zip_filename)
            LOGGER.info("Finished updating Shapefiles!")

    async def get_line_info(self, line_id):
        await self._refresh_shapefiles()
        print(SHAPEFILESFOLDERPATH + SEP + LINES_FILENAME)
        sf = shapefile.Reader(SHAPEFILESFOLDERPATH + SEP + LINES_FILENAME)

        for record in sf.records():
            line_number, line_type, line_color = str(int(record[0][:-1])), record[0][-1:].upper(), record[4]
            if str(line_id) == str(line_number):
                return {"line_number": line_number, "line_type": line_type, "line_color": line_color}

    async def get_stop_info(self, stop_name, filtered_out_stop_ids=None):
        if filtered_out_stop_ids is None:
            filtered_out_stop_ids = []
        await self._refresh_shapefiles()
        print(SHAPEFILESFOLDERPATH, stop_name, filtered_out_stop_ids)

        sf = shapefile.Reader(SHAPEFILESFOLDERPATH + SEP + STOPS_FILENAME)

        possible_lines = {}
        for record in sf.records():
            print(record)
            if stop_name.upper() == str(record[STOP_NAME_INDEX]).upper() or stop_name.upper() == str(
                    record[STOP_NAME_INDEX + 1]).upper():
                stop_id = record[STOP_ID_INDEX]
                print(stop_id, filtered_out_stop_ids)
                if stop_id not in filtered_out_stop_ids:
                    if record[LINE_TECH_ID_INDEX] not in possible_lines.keys():
                        possible_lines[record[LINE_TECH_ID_INDEX]] = []
                    possible_lines[record[LINE_TECH_ID_INDEX]].append(
                        await self.get_line_info(record[LINE_NUMBER_INDEX]))
                    possible_lines[record[LINE_TECH_ID_INDEX]][-1].update({"stop_id": stop_id})

                    # for convenience we add also the correspondance between business id for line and line info
                    line_business_id = possible_lines[record[LINE_TECH_ID_INDEX]][-1]["line_number"]
                    if line_business_id not in possible_lines.keys():
                        possible_lines[line_business_id] = []
                    possible_lines[line_business_id].append(possible_lines[record[LINE_TECH_ID_INDEX]][-1])

        return possible_lines
