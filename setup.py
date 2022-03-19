from setuptools import setup
from Cython.Build import cythonize
import numpy
setup(
    ext_modules=cythonize(
        ['compressor_cy.pyx',           # Cython code file with primes() function
         'equalizer_cy.pyx'],           # Python code file with primes() function
        annotate=True,                  # enables generation of the html annotation file
        compiler_directives={'language_level' : "3"}),                 
        include_dirs=[numpy.get_include()]
)