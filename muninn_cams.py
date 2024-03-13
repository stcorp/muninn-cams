import os
import re
from datetime import datetime, date

from muninn.struct import Struct
from muninn_ecmwfmars import get_core_properties as get_ecmwfmars_core_properties, extract_grib_metadata


EXP_TYPES = ['fc', 'an']

CAMS_EXP_NAME = '0001'
CAMS_CONTROL_EXP_NAMES = ['gjjh', 'gnhb', 'gsyg', 'gzhy', 'h7c4', 'hdir', 'hj7b', 'hlqd', 'ht3q', 'hylz']
CAMS_EXP_NAMES = [CAMS_EXP_NAME] + CAMS_CONTROL_EXP_NAMES

CAMS_PRODUCT_TYPE_BASE = 'cams'
CAMS_PRODUCT_TYPES = []
CAMS_PRODUCT_TYPES.append("%s_%s_%s" % (CAMS_PRODUCT_TYPE_BASE, CAMS_EXP_NAME, 'fc'))
CAMS_PRODUCT_TYPES.append("%s_%s_%s" % (CAMS_PRODUCT_TYPE_BASE, CAMS_EXP_NAME, 'an'))
for _exp_name in CAMS_CONTROL_EXP_NAMES:
    CAMS_PRODUCT_TYPES.append("%s_%s_%s" % (CAMS_PRODUCT_TYPE_BASE, _exp_name, 'fc'))

CAMS_AN_SFC_PARAM = [
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

CAMS_FC_SFC_PARAM = [
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

CAMS_AN_ML_PARAM = [
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

CAMS_FC_ML_PARAM = [
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

CAMS_EXP_AVAILABILITY = {
    # see https://confluence.ecmwf.int/display/COPSRV/Global+production+log+files
    # Each row has the following format :
    #   'exp': [model start time, strict start time, strict end time, model end time],
    # A strict time range is the time range of an expirement where that experiment is the primary experiment
    # (and therefore resulting in overlap-free time ranges for a specific set of experiments).
    # NRT production stream :
    '0001': ["2016-06-21T12:00:00", "                   ", "                   ", "                   "],
    #          started with CY41R1
    #          switch to CY43R1 on 2017-01-24
    #          switch to CY43R3 on 2017-09-26
    #          switch to CY45R1 on 2018-06-26
    #          switch to CY46R1 on 2019-07-09 (L137)
    #          switch to CY47R1 on 2020-10-06
    #          switch to CY47R2 on 2021-05-18
    #          switch to CY47R3 on 2021-10-12T12:00:00
    #          switch from Cray HPC to Atos HPC on 2022-10-18T12:00:00
    #          switch to CY48R1 on 2023-06-27T12:00:00
    # Forecast-only experiments :
    'gjjh': ["2016-06-01T00:00:00", "                   ", "2017-01-23T00:00:00", "2017-03-26T00:00:00"],  # (CY41R1)
    'gnhb': ["2017-01-10T00:00:00", "2017-01-24T00:00:00", "2017-09-25T00:00:00", "2017-11-30T00:00:00"],  # (CY43R1)
    'gsyg': ["2017-09-01T00:00:00", "2017-09-26T00:00:00", "2018-06-25T00:00:00", "2018-08-02T00:00:00"],  # (CY43R3)
    'gzhy': ["2018-06-01T00:00:00", "2018-06-26T00:00:00", "                   ", "2019-07-09T00:00:00"],  # (CY45R1)
    'h7c4': ["2018-12-01T00:00:00", "2019-07-10T00:00:00", "                   ", "2020-10-06T00:00:00"],  # (CY46R1)
    'hdir': ["2019-10-01T00:00:00", "2020-10-07T00:00:00", "                   ", "2021-05-18T00:00:00"],  # (CY47R1)
    'hj7b': ["2020-11-01T00:00:00", "2021-05-19T00:00:00", "                   ", "2021-10-12T00:00:00"],  # (CY47R2)
    'hlqd': ["2021-03-02T00:00:00", "2021-10-13T00:00:00", "                   ", "2022-10-18T00:00:00"],  # (CY47R3)
    'ht3q': ["2022-04-30T00:00:00", "2022-10-19T00:00:00", "                   ", "2023-06-27T00:00:00"],  # (CY47R3)
    'hylz': ["2022-09-01T00:00:00", "2023-06-28T00:00:00", "                   ", "                   "],  # (CY48R1)
}

CAMSGHG_FC_EXP_NAME = '0001'
CAMSGHG_AN_EXP_NAME = '0011'
CAMSGHG_CONTROL_EXP_NAMES = ['he9e', 'hllc', 'huet', 'iaiw']
CAMSGHG_AN_MC_EXP_NAMES = ['gqiq', 'gwx3', 'h72g', 'hd7v', 'hlkx', 'hues']  # old GHG models
CAMSGHG_FC_MC_EXP_NAMES = ['gqpe', 'gznv', 'h9sp', 'he9h', 'hlld', 'hueu']  # old GHG models
CAMSGHG_EXP_NAMES = [CAMSGHG_FC_EXP_NAME, CAMSGHG_AN_EXP_NAME] + CAMSGHG_CONTROL_EXP_NAMES + \
    CAMSGHG_AN_MC_EXP_NAMES + CAMSGHG_FC_MC_EXP_NAMES

CAMSGHG_PRODUCT_TYPE_BASE = 'camsghg'  # CAMS Greenhous Gases service
CAMSGHG_PRODUCT_TYPES = []
CAMSGHG_PRODUCT_TYPES.append("%s_%s_%s" % (CAMSGHG_PRODUCT_TYPE_BASE, CAMSGHG_FC_EXP_NAME, 'fc'))
CAMSGHG_PRODUCT_TYPES.append("%s_%s_%s" % (CAMSGHG_PRODUCT_TYPE_BASE, CAMSGHG_AN_EXP_NAME, 'an'))
for _exp_name in CAMSGHG_CONTROL_EXP_NAMES:
    CAMSGHG_PRODUCT_TYPES.append("%s_%s_%s" % (CAMSGHG_PRODUCT_TYPE_BASE, _exp_name, 'fc'))
for _exp_name in CAMSGHG_FC_MC_EXP_NAMES:
    CAMSGHG_PRODUCT_TYPES.append("%s_%s_%s" % (CAMSGHG_PRODUCT_TYPE_BASE, _exp_name, 'fc'))
for _exp_name in CAMSGHG_AN_MC_EXP_NAMES:
    CAMSGHG_PRODUCT_TYPES.append("%s_%s_%s" % (CAMSGHG_PRODUCT_TYPE_BASE, _exp_name, 'an'))

CAMSGHG_AN_ML_PARAM = [
    '129.128',  # Geopotential
    '130.128',  # Temperature
    '133.128',  # Specific humidity
    '61.210',   # Carbon dioxide
    '62.210',   # Methane
]

CAMSGHG_FC_ML_PARAM = [
    '129.128',  # Geopotential
    '130.128',  # Temperature
    '133.128',  # Specific humidity
    '123.210',  # Carbon monoxide
    '61.210',   # Carbon dioxide
    '62.210',   # Methane
]

CAMSGHG_EXP_AVAILABILITY = {
    # See https://confluence.ecmwf.int/pages/viewpage.action?pageId=394237962
    # forecast experiment :
    '0001': ["2024-02-26T00:00:00", "2024-02-27T00:00:00", "                   ", "                   "],  # (CY48R1)
    # analysis experiment :
    '0011': ["2024-02-18T00:00:00", "2024-02-27T00:00:00", "                   ", "                   "],  # (CY48R1)
    # old forecast experiments :
    'gqpe': ["2017-01-01T00:00:00", "2017-11-01T00:00:00", "2018-11-30T00:00:00", "2018-12-31T00:00:00"],  # (CY43R1)
    'gznv': ["2018-06-01T00:00:00", "2018-12-01T00:00:00", "2019-08-31T00:00:00", "2019-12-31T00:00:00"],  # (CY45R1)
    'h9sp': ["2019-09-01T00:00:00", "                   ", "2020-10-31T00:00:00", "2021-01-26T00:00:00"],  # (CY46R1)
    'he9h': ["2020-01-01T00:00:00", "2020-11-01T00:00:00", "2021-10-31T00:00:00", "2021-12-01T00:00:00"],  # (CY47R1)
    'hlld': ["2021-04-01T00:00:00", "2021-11-01T00:00:00", "2022-10-23T00:00:00", "2022-10-30T00:00:00"],  # (CY47R3)
    'hueu': ["2022-09-19T00:00:00", "2022-10-24T00:00:00", "2024-02-26T00:00:00", "2024-02-29T00:00:00"],  # (CY47R3)
    # old analysis experiments :
    'gqiq': ["2016-12-31T18:00:00", "2017-11-01T00:00:00", "2018-11-30T18:00:00", "2018-12-28T06:00:00"],  # (CY43R1)
    'gwx3': ["2017-11-30T18:00:00", "2018-12-01T00:00:00", "2019-08-31T18:00:00", "2020-01-22T18:00:00"],  # (CY45R1)
    'h72g': ["2018-11-27T18:00:00", "2019-09-01T00:00:00", "2020-10-31T18:00:00", "2021-01-21T18:00:00"],  # (CY46R1)
    'hd7v': ["2019-12-31T18:00:00", "2020-11-01T00:00:00", "2021-10-31T18:00:00", "2021-11-28T18:00:00"],  # (CY47R1)
    'hlkx': ["2021-03-31T18:00:00", "2021-11-01T00:00:00", "2022-10-23T18:00:00", "2022-10-27T06:00:00"],  # (CY47R3)
    'hues': ["2022-09-14T00:00:00", "2022-10-24T00:00:00", "2024-02-26T00:00:00", "2024-02-29T18:00:00"],  # (CY47R3)
    # forecast-only experiments :
    'he9e': ["2020-01-01T00:00:00", "2020-11-01T00:00:00", "2021-10-31T00:00:00", "2021-11-28T00:00:00"],  # (CY47R1)
    'hllc': ["2021-04-01T00:00:00", "2021-11-01T00:00:00", "2022-10-23T00:00:00", "2022-10-27T00:00:00"],  # (CY47R3)
    'huet': ["2022-09-15T00:00:00", "2022-10-24T00:00:00", "2024-02-26T00:00:00", "2024-02-29T00:00:00"],  # (CY47R3)
    'iaiw': ["2024-02-18T00:00:00", "2024-02-27T00:00:00", "                   ", "                   "],  # (CY48R1)
}


def get_core_properties(product_type, ecmwfmars, levtype_options):
    core = get_ecmwfmars_core_properties(product_type, ecmwfmars, levtype_options, packing='simple')
    if 'step' in ecmwfmars:
        step = ecmwfmars.step
    else:
        step = 0
    product_type_base, model, exp_type = product_type.split('_')
    assert model == ecmwfmars.expver and exp_type == ecmwfmars.type, "inconsistent product_type %s %s" % \
        (core.product_type, "%s_%s_%s" % (product_type_base, ecmwfmars.expver, ecmwfmars.type))
    core.product_type = product_type
    core.product_name = "%s_%s_%s_%s" % (product_type_base, ecmwfmars.expver,
                                         core.creation_date.strftime("%Y%m%dT%H%M%S"), ecmwfmars.type)
    if ecmwfmars.type == 'fc':
        core.product_name += "_%03d" % (step,)
    core.physical_name = "%s.grib" % (core.product_name,)
    return core


def _create_properties(ProductClass, model_date, expver='0001', type='fc', step=0, grid=None, sfc_param=None,
                       ml_param=None, levelist=None):
    product_type = "%s_%s_%s" % (ProductClass.product_type_base, expver, type)
    marsclass = ProductClass.marsclass_for_exp(expver)
    stream = ProductClass.stream_for_exp(expver)
    if grid is None:
        grid = ProductClass.default_grid_for_exp(expver)
    if isinstance(model_date, date) and not isinstance(model_date, datetime):
        model_date = datetime(model_date.year, model_date.month, model_date.day)
    if levelist is None:
        levelist = ProductClass.default_levelist_for_exp(expver, model_date)
    if sfc_param is None and ml_param is None:
        sfc_param, ml_param = ProductClass.default_param_for_exp(expver, type)

    ecmwfmars = Struct()
    ecmwfmars.marsclass = marsclass
    ecmwfmars.stream = stream
    ecmwfmars.expver = expver
    ecmwfmars.type = type
    ecmwfmars.date = model_date.strftime("%Y-%m-%d")
    ecmwfmars.time = model_date.strftime("%H:%M:%S")
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


def _exp_available(exp_availability, exp, model_datetime, strict=False):
    if strict:
        if exp_availability[exp][1].strip():
            if model_datetime < datetime.strptime(exp_availability[exp][1], "%Y-%m-%dT%H:%M:%S"):
                return False
        if exp_availability[exp][2].strip():
            if model_datetime > datetime.strptime(exp_availability[exp][2], "%Y-%m-%dT%H:%M:%S"):
                return False
    if model_datetime < datetime.strptime(exp_availability[exp][0], "%Y-%m-%dT%H:%M:%S"):
        return False
    if exp_availability[exp][3].strip():
        if model_datetime > datetime.strptime(exp_availability[exp][3], "%Y-%m-%dT%H:%M:%S"):
            return False
    return True


class CAMSProduct(object):
    product_type_base = CAMS_PRODUCT_TYPE_BASE

    @staticmethod
    def create_properties(model_date, expver='0001', type='fc', step=0, grid=None, sfc_param=None,
                          ml_param=None, levelist=None):
        return _create_properties(CAMSProduct, model_date, expver, type, step, grid, sfc_param, ml_param, levelist)

    @staticmethod
    def exp_available(exp, model_datetime, strict=False):
        return _exp_available(CAMS_EXP_AVAILABILITY, exp, model_datetime, strict)

    @staticmethod
    def marsclass_for_exp(exp):
        if exp in CAMS_CONTROL_EXP_NAMES:
            return 'rd'
        return 'mc'

    @staticmethod
    def stream_for_exp(exp):
        if exp == 'gzhy':
            # this control run was not using the default stream
            return 'lwda'
        return 'oper'

    @staticmethod
    def default_grid_for_exp(exp):
        return 'F256'

    @staticmethod
    def default_levelist_for_exp(exp, model_datetime):
        if model_datetime <= datetime(2019, 7, 9):
            return range(60)
        return range(137)

    @staticmethod
    def default_param_for_exp(exp, type):
        if type == 'an':
            return CAMS_AN_SFC_PARAM, CAMS_AN_ML_PARAM
        return CAMS_FC_SFC_PARAM, CAMS_FC_ML_PARAM

    def __init__(self, product_type):
        self.use_enclosing_directory = False
        self.use_hash = False
        self.hash_type = None
        self.product_type = product_type
        product_type_base, model, exp_type = product_type.split('_')
        pattern = [
            product_type_base,
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
        model_date = properties.core.creation_date
        prefix, exp_name, exp_type = properties.core.product_type.split('_')
        return os.path.join(
            prefix,
            exp_name,
            exp_type,
            "%04d" % model_date.year,
            "%02d" % model_date.month,
            "%02d" % model_date.day,
        )

    def analyze(self, paths):
        ecmwfmars, levtype_options = extract_grib_metadata(paths[0])
        properties = Struct()
        properties.core = get_core_properties(self.product_type, ecmwfmars, levtype_options)
        properties.ecmwfmars = ecmwfmars

        return properties

    def post_pull_hook(self, archive, properties):
        pass


class CAMSGHGProduct(CAMSProduct):
    product_type_base = CAMSGHG_PRODUCT_TYPE_BASE

    @staticmethod
    def create_properties(model_date, expver='0001', type='fc', step=0, grid=None, sfc_param=None,
                          ml_param=None, levelist=None):
        return _create_properties(CAMSGHGProduct, model_date, expver, type, step, grid, sfc_param, ml_param, levelist)

    @staticmethod
    def exp_available(exp, model_datetime, strict=False):
        return _exp_available(CAMSGHG_EXP_AVAILABILITY, exp, model_datetime, strict)

    @staticmethod
    def marsclass_for_exp(exp):
        if exp in CAMSGHG_CONTROL_EXP_NAMES + CAMSGHG_AN_MC_EXP_NAMES + CAMSGHG_FC_MC_EXP_NAMES:
            return 'rd'
        return 'gg'

    @staticmethod
    def stream_for_exp(exp):
        if exp in ['gznv', 'gqpe']:
            # the first GHG forecast runs used 'lwda', all other GHG runs use 'oper'
            return 'lwda'
        return 'oper'

    @staticmethod
    def default_grid_for_exp(exp):
        if exp in [CAMSGHG_FC_EXP_NAME] + CAMSGHG_FC_MC_EXP_NAMES:
            return 'F640'
        return 'F200'

    @staticmethod
    def default_levelist_for_exp(exp, model_datetime):
        return range(137)

    @staticmethod
    def default_param_for_exp(exp, type):
        # CAMS GHG control experiment uses 'an' parameter list
        if exp in [CAMSGHG_AN_EXP_NAME] + CAMSGHG_AN_MC_EXP_NAMES + CAMSGHG_CONTROL_EXP_NAMES:
            return None, CAMSGHG_AN_ML_PARAM
        return None, CAMSGHG_FC_ML_PARAM


def product_types():
    return CAMS_PRODUCT_TYPES + CAMSGHG_PRODUCT_TYPES


def product_type_plugin(product_type):
    if product_type in CAMS_PRODUCT_TYPES:
        return CAMSProduct(product_type=product_type)
    if product_type in CAMSGHG_PRODUCT_TYPES:
        return CAMSGHGProduct(product_type=product_type)
    return None
