from setuptools import setup

setup(
    name="muninn-cams",
    version="1.0",
    description="Muninn extension for CAMS GRIB products from the ECMWF mars archive",
    url="https://github.com/stcorp/muninn-cams",
    author="S[&]T",
    license="BSD",
    py_modules=["muninn_cams"],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering",
        "Environment :: Plugins",
    ],
    install_requires=["muninn", "muninn_ecmwfmars"],
)
