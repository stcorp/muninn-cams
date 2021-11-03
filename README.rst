muninn-cams
===========

This python package facilitates the deployment of a muninn archive containing
data from the `Copernicus Atmospheric Monitoring Service (CAMS)
<https://atmosphere.copernicus.eu>`_.

This package only supports the CAMS *global* model data and only data in GRIB
format.

This package is build on top of (and requires) the muninn-ecmwfmars extension.

This package provides:

- a list of commonly used parameters (which is a subset of the full set of
  parameters that are available in the CAMS models).
- model identifiers and timeline information for the forecast-only (control)
  and GHG models.
- a function to create metadata records for new model times; the associated
  CAMS data can then be retrieved with muninn-pull using the remote backend of
  muninn-ecmwfmars. Note that this requires a mars account at ECMWF.
