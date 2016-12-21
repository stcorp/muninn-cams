import os
import re
from datetime import datetime

from muninn.struct import Struct
from muninn.exceptions import Error

DATETIME_FMT = "%Y%m%dT%H%M"
CAMS_PRODUCT_TYPE = "CAMS-%(model)s"
_CAMS_MODELS = ["0001", "fkya", "fnyp", "fsd7", "g4e2", "gvo2", "geuh", "gjjh"]

FILENAME_FMT = re.compile(r'(?P<model>[^-]+)-(?P<val_start>[0-9T]+)-(?P<val_stop>[0-9T]+)\.grib')


class CAMSProduct(object):

    def __init__(self, model, product_type):
        self.model = model
        self.product_type = product_type

    @property
    def use_enclosing_directory(self):
        return False

    @property
    def use_hash(self):
        return False

    def archive_path(self, properties):
        md = properties.core

        return os.path.join(
            "CAMS",
            md.product_type,
            md.validity_start.strftime("%Y"),
            md.validity_start.strftime("%m"),
            md.validity_start.strftime("%d")
        )

    def identify(self, paths):
        filename = os.path.basename(paths[0])
        match = FILENAME_FMT.match(filename)

        return match and match.group('model') == self.model

    def analyze(self, paths):
        # init the metadata structs
        metadata = Struct()

        inpath = paths[0]
        filename = os.path.basename(inpath)
        match = FILENAME_FMT.match(filename)

        # populate the metadata
        core = metadata.core = Struct()
        core.product_name = filename

        # properties that can be extracted from path/os
        core.creation_date = datetime.strptime(match.group('val_start'), DATETIME_FMT)  #TODO: using val_start is wrong
        core.validity_start = datetime.strptime(match.group('val_start'), DATETIME_FMT)
        core.validity_stop = datetime.strptime(match.group('val_stop'), DATETIME_FMT)
        core.size = os.path.getsize(inpath)

        return metadata


def product_types():
    return [CAMS_PRODUCT_TYPE % {"model": m} for m in _CAMS_MODELS]


def product_type_plugin(product_type):
    return CAMSProduct(product_type, CAMS_PRODUCT_TYPE % {"model": product_type})
