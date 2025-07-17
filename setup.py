import numpy as np
from setuptools import setup
from Cython.Build import cythonize

setup(
    name="compute_T_c_extension",
    ext_modules=cythonize("compute_T.pyx"),
    include_dirs=[np.get_include()]
)