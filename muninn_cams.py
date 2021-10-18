import os
import re
import datetime

from muninn.struct import Struct
from muninn_ecmwfmars import get_core_properties as get_ecmwfmars_core_properties, extract_grib_metadata


PRODUCT_TYPE_BASE = 'cams'

CONTROL_EXP_NAMES = ['gjjh', 'gnhb', 'gsyg', 'gzhy', 'h7c4', 'hdir', 'hj7b', 'hlqd']
EXP_NAMES = ['0001'] + CONTROL_EXP_NAMES

GHG_CONTROL_EXP_NAMES = ['he9e']
GHG_AN_EXP_NAMES = ['gqiq', 'gwx3', 'h72g', 'hd7v']
GHG_FC_EXP_NAMES = ['gqpe', 'gznv', 'h9sp', 'he9h']
GHG_EXP_NAMES = GHG_AN_EXP_NAMES + GHG_FC_EXP_NAMES + GHG_CONTROL_EXP_NAMES

MC_EXP_NAMES = ['0001']  # marsclass="mc"
RD_EXP_NAMES = CONTROL_EXP_NAMES + GHG_EXP_NAMES  # marsclass="rd"
EXP_TYPES = ['fc', 'an']

PRODUCT_TYPES = []
for _exp_name in EXP_NAMES:
    for _exp_type in EXP_TYPES:
        if _exp_name in CONTROL_EXP_NAMES and _exp_type == 'an':
            continue
        PRODUCT_TYPES.append('%s_%s_%s' % (PRODUCT_TYPE_BASE, _exp_name, _exp_type))
for _exp_name in GHG_FC_EXP_NAMES:
    PRODUCT_TYPES.append('%s_%s_%s' % (PRODUCT_TYPE_BASE, _exp_name, 'fc'))
for _exp_name in GHG_CONTROL_EXP_NAMES:
    PRODUCT_TYPES.append('%s_%s_%s' % (PRODUCT_TYPE_BASE, _exp_name, 'fc'))
for _exp_name in GHG_AN_EXP_NAMES:
    PRODUCT_TYPES.append('%s_%s_%s' % (PRODUCT_TYPE_BASE, _exp_name, 'an'))

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
    '4.217',    # Methane
    '27.217',   # Nitrogen monoxide
    '130.128',  # Temperature
    '133.128',  # Specific humidity
    '121.210',  # Nitrogen dioxide
    '122.210',  # Sulphur dioxide
    '123.210',  # Carbon monoxide
    '124.210',  # Formaldehyde
    '203.210',  # GEMS Ozone
]

FC_ML_PARAM = [
    '4.217',    # Methane
    '27.217',   # Nitrogen monoxide
    '130.128',  # Temperature
    '133.128',  # Specific humidity
    '121.210',  # Nitrogen dioxide
    '122.210',  # Sulphur dioxide
    '123.210',  # Carbon monoxide
    '124.210',  # Formaldehyde
    '203.210',  # GEMS Ozone
    '182.215',  # Aerosol extinction coefficient at 1064 nm
    '188.215',  # Aerosol backscatter coefficient at 1064 nm (from ground)
]

GHG_AN_PARAM = [
    '129.128',  # Geopotential
    '130.128',  # Temperature
    '133.128',  # Specific humidity
    '61.210',   # Carbon dioxide
    '62.210',   # Methane
]

GHG_FC_PARAM = [
    '129.128',  # Geopotential
    '130.128',  # Temperature
    '133.128',  # Specific humidity
    '123.210',  # Carbon monoxide
    '61.210',   # Carbon dioxide
    '62.210',   # Methane
]


# see https://confluence.ecmwf.int/display/COPSRV/Global+production+log+files
# A strict time range is the time range of an expirement where that experiment is the primary experiment
# (and therefore resulting in overlap-free time ranges for a specific set of experiments).
# NRT production stream :
# - 0001 : 2016-06-21T12:00:00 - present
#          started with CY41R1
#          switch to CY43R1 on 2017-01-24
#          switch to CY43R3 on 2017-09-26
#          switch to CY45R1 on 2018-06-26
#          switch to CY46R1 on 2019-07-09 (L137)
#          switch to CY47R1 on 2020-10-06
#          switch to CY47R2 on 2021-05-18
#          switch to CY47R3 on 2021-10-12T12:00:00
# Forecast-only experiments :
# - gjjh :                       2016-06-01T00:00:00 - 2017-01-23T00:00:00 (2017-03-26T00:00:00) (CY41R1)
# - gnhb : (2017-01-10T00:00:00) 2017-01-24T00:00:00 - 2017-09-25T00:00:00 (2017-11-30T00:00:00) (CY43R1)
# - gsyg : (2017-09-01T00:00:00) 2017-09-26T00:00:00 - 2018-06-25T00:00:00 (2018-08-02T00:00:00) (CY43R3)
# - gzhy : (2018-06-01T00:00:00) 2018-06-26T00:00:00 - 2019-07-09T00:00:00                       (CY45R1)
# - h7c4 : (2018-12-01T00:00:00) 2019-07-10T00:00:00 - 2020-10-06T00:00:00                       (CY46R1)
# - hdir : (2019-10-01T00:00:00) 2020-10-07T00:00:00 - 2021-05-18T00:00:00                       (CY47R1)
# - hj7b : (2020-11-01T00:00:00) 2021-05-19T00:00:00 - 2021-10-12T00:00:00                       (CY47R2)
# - hlqd : (2021-03-02T00:00:00) 2021-10-13T00:00:00 - present                                   (CY47R3)
# GHG forecast experiments :
# - gqpe : (2017-01-01T00:00:00) 2017-11-01T00:00:00 - 2018-11-30T00:00:00 (2018-12-31T00:00:00) (CY43R1)
# - gznv : (2018-06-01T00:00:00) 2018-12-01T00:00:00 - 2019-08-31T00:00:00 (2019-21-31T00:00:00) (CY45R1)
# - h9sp :                       2019-09-01T00:00:00 - 2020-10-31T00:00:00 (2021-01-26T00:00:00) (CY46R1)
# - he9h : (2020-01-01T00:00:00) 2020-11-01T00:00:00 - present                                   (CY47R1)
# GHG analysis experiments :
# - gqiq : (2016-12-31T18:00:00) 2017-11-01T00:00:00 - 2018-11-30T18:00:00 (2018-12-28T06:00:00) (CY43R1)
# - gwx3 : (2017-11-30T18:00:00) 2018-12-01T00:00:00 - 2019-08-31T18:00:00 (2020-01-22T18:00:00) (CY45R1)
# - h72g : (2018-11-27T18:00:00) 2019-09-01T00:00:00 - 2020-10-31T18:00:00 (2021-01-21T18:00:00) (CY46R1)
# - hd7v : (2019-12-31T18:00:00) 2020-11-01T00:00:00 - present                                   (CY47R1)
# GHG forecast-only experiments :
# - he9e : (2020-01-01T00:00:00) 2020-11-01T00:00:00 - present                                   (CY47R1)
def exp_available(exp, model_datetime, strict=False):
    if exp == '0001':
        if model_datetime < datetime.datetime(2016, 6, 21, 12):
            return False
        return True
    if exp == 'gjjh':
        if model_datetime < datetime.datetime(2016, 6, 1):
            return False
        if strict and model_datetime > datetime.datetime(2017, 1, 23):
            return False
        if model_datetime > datetime.datetime(2017, 3, 26):
            return False
        return True
    if exp == 'gnhb':
        if strict and model_datetime < datetime.datetime(2017, 1, 24):
            return False
        if model_datetime < datetime.datetime(2017, 1, 10):
            return False
        if strict and model_datetime > datetime.datetime(2017, 9, 25):
            return False
        if model_datetime > datetime.datetime(2017, 11, 30):
            return False
        return True
    if exp == 'gsyg':
        if strict and model_datetime < datetime.datetime(2017, 9, 26):
            return False
        if model_datetime < datetime.datetime(2017, 9, 1):
            return False
        if strict and model_datetime > datetime.datetime(2018, 6, 25):
            return False
        if model_datetime > datetime.datetime(2018, 8, 2):
            return False
        return True
    if exp == 'gzhy':
        if strict and model_datetime < datetime.datetime(2018, 6, 26):
            return False
        if model_datetime < datetime.datetime(2018, 6, 1):
            return False
        if model_datetime > datetime.datetime(2019, 7, 9):
            return False
        return True
    if exp == 'h7c4':
        if strict and model_datetime < datetime.datetime(2019, 7, 10):
            return False
        if model_datetime < datetime.datetime(2018, 12, 1):
            return False
        if model_datetime > datetime.datetime(2020, 10, 6):
            return False
        return True
    if exp == 'hdir':
        if strict and model_datetime < datetime.datetime(2020, 10, 7):
            return False
        if model_datetime < datetime.datetime(2019, 10, 1):
            return False
        if model_datetime > datetime.datetime(2021, 5, 18):
            return False
        return True
    if exp == 'hj7b':
        if strict and model_datetime < datetime.datetime(2021, 5, 19):
            return False
        if model_datetime < datetime.datetime(2020, 11, 1):
            return False
        if model_datetime > datetime.datetime(2021, 10, 12):
            return False
        return True
    if exp == 'hlqd':
        if strict and model_datetime < datetime.datetime(2021, 10, 13):
            return False
        if model_datetime < datetime.datetime(2021, 3, 2):
            return False
        return True
    if exp == 'gqpe':
        if strict and model_datetime < datetime.datetime(2017, 11, 1):
            return False
        if model_datetime < datetime.datetime(2017, 1, 1):
            return False
        if strict and model_datetime > datetime.datetime(2018, 11, 30):
            return False
        if model_datetime > datetime.datetime(2018, 12, 31):
            return False
        return True
    if exp == 'gznv':
        if strict and model_datetime < datetime.datetime(2018, 12, 1):
            return False
        if model_datetime < datetime.datetime(2018, 6, 1):
            return False
        if strict and model_datetime > datetime.datetime(2019, 8, 31):
            return False
        if model_datetime > datetime.datetime(2019, 12, 31):
            return False
        return True
    if exp == 'h9sp':
        if model_datetime < datetime.datetime(2019, 9, 1):
            return False
        if strict and model_datetime > datetime.datetime(2020, 10, 31):
            return False
        if model_datetime > datetime.datetime(2021, 1, 26):
            return False
        return True
    if exp == 'he9h':
        if strict and model_datetime < datetime.datetime(2020, 11, 1):
            return False
        if model_datetime < datetime.datetime(2020, 1, 1):
            return False
        return True
    if exp == 'gqiq':
        if strict and model_datetime < datetime.datetime(2017, 11, 1):
            return False
        if model_datetime < datetime.datetime(2016, 12, 31, 18):
            return False
        if strict and model_datetime > datetime.datetime(2018, 11, 30, 18):
            return False
        if model_datetime > datetime.datetime(2018, 12, 28, 6):
            return False
        return True
    if exp == 'gwx3':
        if strict and model_datetime < datetime.datetime(2018, 12, 1):
            return False
        if model_datetime < datetime.datetime(2017, 11, 30, 18):
            return False
        if strict and model_datetime > datetime.datetime(2019, 8, 31, 18):
            return False
        if model_datetime > datetime.datetime(2020, 1, 22, 18):
            return False
        return True
    if exp == 'h72g':
        if strict and model_datetime < datetime.datetime(2019, 9, 1):
            return False
        if model_datetime < datetime.datetime(2018, 11, 27, 18):
            return False
        if strict and model_datetime > datetime.datetime(2020, 10, 31, 18):
            return False
        if model_datetime > datetime.datetime(2021, 1, 21, 18):
            return False
        return True
    if exp == 'hd7v':
        if strict and model_datetime < datetime.datetime(2020, 11, 1):
            return False
        if model_datetime < datetime.datetime(2019, 12, 31, 18):
            return False
        return True
    if exp == 'he9e':
        if strict and model_datetime < datetime.datetime(2020, 11, 1):
            return False
        if model_datetime < datetime.datetime(2020, 1, 1):
            return False
        return True
    return False


def marsclass_for_exp(exp):
    if exp in RD_EXP_NAMES:
        return 'rd'
    # the default mars class for CAMS is 'mc' (from 'MACC', which is the old name for 'CAMS')
    return 'mc'


def stream_for_exp(exp):
    if exp in ['gznv', 'gqpe']:
        # the first GHG forecast runs used 'lwda', all other GHG runs use 'oper'
        return 'lwda'
    if exp == 'gzhy':
        # this control run was not using the default stream
        return 'lwda'
    return 'oper'


def default_grid_for_exp(exp):
    if exp in GHG_AN_EXP_NAMES or exp in GHG_CONTROL_EXP_NAMES:
        return 'F200'
    if exp in GHG_FC_EXP_NAMES:
        return 'F640'
    return 'F256'


def default_levelist_for_exp(exp, model_datetime):
    if exp in GHG_EXP_NAMES:
        return range(137)
    if model_datetime > datetime.datetime(2019, 7, 9) or exp == 'h2xm':
        return range(137)
    return range(60)


def default_param_for_exp(exp, type):
    if exp in GHG_AN_EXP_NAMES or exp in GHG_CONTROL_EXP_NAMES:  # control uses 'an' parameter list
        return None, GHG_AN_PARAM
    if exp in GHG_FC_EXP_NAMES:
        return None, GHG_FC_PARAM
    if type == 'an':
        return AN_SFC_PARAM, AN_ML_PARAM
    if type == 'fc':
        return FC_SFC_PARAM, FC_ML_PARAM
    return None, None


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


def create_properties(date, expver="0001", type="fc", step=0, grid=None, sfc_param=None, ml_param=None, levelist=None):
    product_type = '%s_%s_%s' % (PRODUCT_TYPE_BASE, expver, type)

    marsclass = marsclass_for_exp(expver)
    stream = stream_for_exp(expver)
    if grid is None:
        grid = default_grid_for_exp(expver)
    if isinstance(date, datetime.date) and not isinstance(date, datetime.datetime):
        date = datetime.datetime(date.year, date.month, date.day)
    if levelist is None:
        levelist = default_levelist_for_exp(expver, date)
    if sfc_param is None and ml_param is None:
        sfc_param, ml_param = default_param_for_exp(expver, type)

    ecmwfmars = Struct()
    ecmwfmars.marsclass = marsclass
    ecmwfmars.stream = stream
    ecmwfmars.expver = expver
    ecmwfmars.type = type
    ecmwfmars.date = date.strftime("%Y-%m-%d")
    ecmwfmars.time = date.strftime("%H:%M:%S")
    if step != 0:
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
        self.hash_type = None
        self.product_type = product_type
        _, model, exp_type = product_type.split('_')
        pattern = [
            PRODUCT_TYPE_BASE,
            r"_(?P<model>%s)" % model,
            r"(?P<creation_date>[\dT]{15})",
            r"(?P<type>%s)" % exp_type,
            r"(?P<step>.{3})"
        ]
        self.filename_pattern = "_".join(pattern) + r"\.grib$"

    def parse_filename(self, filename):
        match = re.match(self.filename_pattern, os.path.basename(filename))
        if match:
            return match.groupdict()
        return None

    def identify(self, paths):
        if len(paths) != 1:
            return False
        return re.match(self.filename_pattern, os.path.basename(paths[0])) is not None

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
