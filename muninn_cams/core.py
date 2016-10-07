import os
import os.path as path
import re
from datetime import datetime

import logging

from muninn.struct import Struct
from muninn.exceptions import Error

log = logging.getLogger(__name__)

DATETIME_FMT = "%Y%m%dT%H%M"
CAMS_PRODUCT_TYPE = "CAMS-%(model)s"
_CAMS_MODELS = [ "0001", "fkya", "fnyp", "fsd7", "g4e2", "gvo2", "geuh", "gjjh" ]

FILENAME_FMT = re.compile(r'(?P<model>[^-]+)-(?P<val_start>[0-8T]+)-(?P<val_stop>[0-8T]+)\.grib')

def identify_cams(filename):
    match = FILENAME_FMT.match(filename)
    return match and match.group('model') in _CAMS_MODELS

class CAMSProduct(object):

    def __init__(self, product_type):
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
            md.creation_date.strftime("%Y"),
            md.creation_date.strftime("%m"),
            md.creation_date.strftime("%d")
        )

    def identify(self, paths):
        filename = os.path.basename(paths[0])
        return identify_cams(filename)

    def analyze(self, paths):
        # init the metadata structs
        metadata = Struct()

        inpath = paths[0]
        filename = os.path.basename(inpath)
        match = FILENAME_FMT.match(filename)

        # populate the metadata
        metadata.core = core = Struct()

        # properties that can be extracted from path/os
        core.creation_date = datetime.strptime(match.group('val_start'), DATETIME_FMT)
        core.product_name = filename
        core.size = os.path.getsize(inpath)
        core.validity_start = datetime.strptime(match.group('val_start'), DATETIME_FMT)
        core.validity_stop = datetime.strptime(match.group('val_stop'), DATETIME_FMT)

        return metadata

_product_types = [
    CAMS_PRODUCT_TYPE % { "model": m } for m in _CAMS_MODELS
]

def product_types():
    return _product_types

def product_type_plugin(product_type):
    return CAMSProduct(product_type)

