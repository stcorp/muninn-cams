from __future__ import absolute_import, division, print_function
import os
import datetime

from muninn.struct import Struct
from muninn_ecmwfmars import get_core_properties as get_ecmwfmars_core_properties, extract_grib_metadata


PRODUCT_TYPE_BASE = 'cams'
MC_EXP_NAMES = ['0001']  # marsclass="mc"
CONTROL_EXP_NAMES = ['gjjh', 'gnhb', 'gsyg', 'gzhy', 'h7c4']
ESUITE_EXP_NAMES = ['h2xm']
RD_EXP_NAMES = CONTROL_EXP_NAMES + ESUITE_EXP_NAMES  # marsclass="rd"
EXP_NAMES = MC_EXP_NAMES + RD_EXP_NAMES
EXP_TYPES = ['fc', 'an']

PRODUCT_TYPES = []
for _exp_name in EXP_NAMES:
    for _exp_type in EXP_TYPES:
        PRODUCT_TYPES.append('%s_%s_%s' % (PRODUCT_TYPE_BASE, _exp_name, _exp_type))

FILENAME_PATTERN_BASE = PRODUCT_TYPE_BASE + \
    r'_(?P<model>%s)_(?P<creation_date>[\dT]{15})_(?P<type>%s)_(?P<step>.{3})\.grib'

AN_SFC_PARAM = [
    '129.128',  # Geopotential
    '73.210',   # PM2.5
    '74.210',   # PM10
    '207.210',  # Total Aerosol Optical Depth at 550nm
    '208.210',  # Sea Salt Aerosol Optical Depth at 550nm
    '209.210',  # Dust Aerosol Optical Depth at 550nm
    '210.210',  # Organic Matter Aerosol Optical Depth at 550nm
    '211.210',  # Black Carbon Aerosol Optical Depth at 550nm
    '212.210',  # Sulphate Aerosol Optical Depth at 550nm
    '213.210',  # Total Aerosol Optical Depth at 469nm
    '214.210',  # Total Aerosol Optical Depth at 670nm
    '215.210',  # Total Aerosol Optical Depth at 865nm
    '216.210',  # Total Aerosol Optical Depth at 1240nm
    '218.210',  # Total Aerosol Optical Depth at 335nm
    '221.210',  # Total Aerosol Optical Depth at 440nm
    '122.215',  # Total fine mode (r < 0.5 um) Aerosol Optical Depth at 550 nm
]

FC_SFC_PARAM = [
    '129.128',  # Geopotential
    '73.210',   # PM2.5
    '74.210',   # PM10
    '207.210',  # Total Aerosol Optical Depth at 550nm
    '208.210',  # Sea Salt Aerosol Optical Depth at 550nm
    '209.210',  # Dust Aerosol Optical Depth at 550nm
    '210.210',  # Organic Matter Aerosol Optical Depth at 550nm
    '211.210',  # Black Carbon Aerosol Optical Depth at 550nm
    '212.210',  # Sulphate Aerosol Optical Depth at 550nm
    '213.210',  # Total Aerosol Optical Depth at 469nm
    '214.210',  # Total Aerosol Optical Depth at 670nm
    '215.210',  # Total Aerosol Optical Depth at 865nm
    '216.210',  # Total Aerosol Optical Depth at 1240nm
    '218.210',  # Total Aerosol Optical Depth at 335nm
    '221.210',  # Total Aerosol Optical Depth at 440nm
    '122.215',  # Total fine mode (r < 0.5 um) Aerosol Optical Depth at 550 nm
]

AN_ML_PARAM = [
    '4.217',        # Methane
    '130.128',      # Temperature
    '133.128',      # Specific humidity
    '121.210',      # Nitrogen dioxide
    '122.210',      # Sulphur dioxide
    '123.210',      # Carbon monoxide
    '124.210',      # Formaldehyde
    '203.210',      # GEMS Ozone
]

FC_ML_PARAM = [
    '4.217',        # Methane
    '130.128',      # Temperature
    '133.128',      # Specific humidity
    '121.210',      # Nitrogen dioxide
    '122.210',      # Sulphur dioxide
    '123.210',      # Carbon monoxide
    '124.210',      # Formaldehyde
    '203.210',      # GEMS Ozone
    '182.215',      # Aerosol extinction coefficient at 1064 nm
    '188.215',      # Aerosol backscatter coefficient at 1064 nm (from ground)
]


# see https://confluence.ecmwf.int/display/COPSRV/Global+production+log+files
# NRT production stream :
# - 0001 : 2016-06-21T12:00:00 - present
#          switch to L137 on 2019-07-09T00:00:00
# Forecast-only experiments :
# - gjjh : 2016-06-01T00:00:00 - 2017-02-23T12:00:00
# - gnhb : 2017-01-24T00:00:00 - 2017-09-25T00:00:00
# - gsyg : 2017-09-26T00:00:00 - 2018-06-25T00:00:00
# - gzhy : 2018-06-26T00:00:00 - 2019-07-09T00:00:00
# - h7c4 : 2019-07-09T12:00:00 - present (L137 model)
# e-suite experiments:
# - h2xm : 2017-01-01T00:00:00 - 2017-06-14T00:00:00(?) (L137 model)
def exp_available(exp, model_datetime):
    if exp == '0001':
        if model_datetime < datetime.datetime(2016, 6, 21, 12):
            return False
        return True
    if exp == 'gjjh':
        if model_datetime < datetime.datetime(2016, 6, 1):
            return False
        # we stop when gnhb starts in order to prevent having duplicate data for the same date
        if model_datetime >= datetime.datetime(2017, 1, 24):
            return False
        return True
    if exp == 'gnhb':
        if model_datetime < datetime.datetime(2017, 1, 24):
            return False
        if model_datetime > datetime.datetime(2017, 9, 25):
            return False
        return True
    if exp == 'gsyg':
        if model_datetime < datetime.datetime(2017, 9, 26):
            return False
        if model_datetime > datetime.datetime(2018, 6, 25):
            return False
        return True
    if exp == 'gzhy':
        if model_datetime < datetime.datetime(2018, 6, 26):
            return False
        if model_datetime > datetime.datetime(2019, 7, 9):
            return False
        return True
    if exp == 'h7c4':
        if model_datetime <= datetime.datetime(2019, 7, 9):
            return False
        return True
    if exp == 'h2xm':
        if model_datetime < datetime.datetime(2017, 1, 1):
            return False
        if model_datetime > datetime.datetime(2017, 6, 14):
            return False
        return True
    return False


def default_stream_for_exp(exp):
    if exp == 'gzhy':
        return 'lwda'
    return 'oper'


def default_levelist_for_exp(exp, model_datetime):
    if model_datetime > datetime.datetime(2019, 7, 9) or exp == 'h2xm':
        return range(137)
    return range(60)


def get_core_properties(product_type, ecmwfmars, levtype_options):
    core = get_ecmwfmars_core_properties(product_type, ecmwfmars, levtype_options)
    if 'step' in ecmwfmars:
        step = ecmwfmars.step
    else:
        step = 0
    assert product_type == "%s_%s_%s" % (PRODUCT_TYPE_BASE, ecmwfmars.expver, ecmwfmars.type), \
        "inconsistent product_type %s %s" % (core.product_type, "cams_%s_%s" % (ecmwfmars.expver, ecmwfmars.type))
    core.product_type = product_type
    core.product_name = "%s_%s_%s_%s" % (PRODUCT_TYPE_BASE, ecmwfmars.expver,
                                         core.creation_date.strftime("%Y%m%dT%H%M%S"), ecmwfmars.type)
    if ecmwfmars.type == "fc":
        core.product_name += "_%03d" % (step,)
    core.physical_name = "%s.grib" % (core.product_name,)
    return core


def create_properties(date, marsclass="mc", stream=None, expver="0001", type="fc", step=0, grid="F256",
                      sfc_param=None, ml_param=None, levelist=None):
    if stream is None:
        stream = default_stream_for_exp(expver)
    product_type = '%s_%s_%s' % (PRODUCT_TYPE_BASE, expver, type)

    if isinstance(date, datetime.date) and not isinstance(date, datetime.datetime):
        date = datetime.datetime(date.year, date.month, date.day)
    levelist = levelist or default_levelist_for_exp(expver, date)

    # don't set ecmwfmars.dataset, we always use the mars interface to get the parameters
    ecmwfmars = Struct()
    ecmwfmars.marsclass = marsclass
    ecmwfmars.stream = stream
    ecmwfmars.expver = expver
    ecmwfmars.type = type
    ecmwfmars.date = date.strftime("%Y-%m-%d")
    ecmwfmars.time = date.strftime("%H:%M:%S")
    if step is not 0:
        ecmwfmars.step = step
    ecmwfmars.grid = grid

    levtype_options = {}
    if sfc_param:
        levtype_options['sfc'] = {'param': "/".join(sfc_param)}
    if ml_param:
        if '152.128' not in ml_param:
            # Make sure that the surface pressure is included
            ml_param += ['152.128']  # Logarithm of surface pressure (lnsp)
        levtype_options['ml'] = {'param': "/".join(ml_param), 'levelist': "/".join([str(x+1) for x in levelist])}

    metadata = Struct()
    metadata.core = get_core_properties(product_type, ecmwfmars, levtype_options)
    metadata.ecmwfmars = ecmwfmars

    return metadata


class CAMSProduct(object):

    def __init__(self, product_type):
        self.use_enclosing_directory = False
        self.use_hash = False
        self.product_type = product_type
        _, model, exp_type = product_type.split('_')
        pattern = [
            PRODUCT_TYPE_BASE,
            r"_(?P<model>%s)" % model,
            r"(?P<creation_date>[\dT]{15})",
            r"(?P<type>%s)" % exp_type,
            r"(?P<step>.{3})"
        ]
        self.filename_pattern = "_".join(pattern) + r"\.grib"

    def parse_filename(self, filename):
        filename = os.path.basename(filename)
        match = re.match(self.filename_pattern, filename)
        if match:
            return match.groupdict()
        return None

    def identify(self, paths):
        if len(paths) != 1:
            return False
        name_attrs = self.parse_filename(os.path.basename(paths[0]))
        return name_attrs is not None

    def archive_path(self, properties):
        date = properties.core.creation_date
        prefix, exp_name, exp_type = properties.core.product_type.split('_')
        return os.path.join(
            prefix,
            exp_name,
            exp_type,
            "%04d" % date.year,
            "%02d" % date.month,
            "%02d" % date.day,
        )

    def analyze(self, paths):
        ecmwfmars, levtype_options = extract_grib_metadata(paths[0])
        if 'dataset' in ecmwfmars:
            # we always want to use the mars interface to retrieve the data
            del ecmwfmars.dataset
        properties = Struct()
        properties.core = get_core_properties(self.product_type, ecmwfmars, levtype_options)
        properties.ecmwfmars = ecmwfmars

        return properties

    def post_pull_hook(self, archive, properties):
        pass


def product_types():
    return PRODUCT_TYPES


def product_type_plugin(product_type):
    if product_type in PRODUCT_TYPES:
        return CAMSProduct(product_type=product_type)
    return None
