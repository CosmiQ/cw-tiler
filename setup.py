
import os

from setuptools import setup, find_packages

with open('cw_tiler/__init__.py') as f:
    for line in f:
        if line.find("__version__") >= 0:
            version = line.split("=")[1].strip()
            version = version.strip('"')
            version = version.strip("'")
            continue


with open('README.rst') as f:
    readme = f.read()

# Runtime requirements.
inst_reqs = ["rio-tiler", "shapely", "geopandas" ]

extra_reqs = {
    'test': ['mock', 'pytest', 'pytest-cov', 'codecov']}

setup(name='cw_tiler',
      version=version,
      description=u"""Get UTM tiles for SpaceNet Dataset or arbitrary GeoTIffs""",
      long_description=readme,
      classifiers=[
          'Intended Audience :: Information Technology',
          'Intended Audience :: Science/Research',
          'License :: OSI Approved :: BSD License',
          'Programming Language :: Python :: 3.6',
          'Programming Language :: Python :: 2.7',
          'Topic :: Scientific/Engineering :: GIS'],
      keywords='raster aws tiler gdal rasterio spacenet machinelearning',
      author=u"David Lindenbaum",
      author_email='dlindenbaum@iqt.org',
      url='https://github.com/CosmiQ/cw-tiler',
      license='BSD',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      zip_safe=False,
      install_requires=inst_reqs,
      extras_require=extra_reqs)
