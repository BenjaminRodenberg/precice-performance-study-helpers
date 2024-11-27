# Added setup.py to make versioneer work. Use pyproject.toml for providing all other data.

from setuptools import setup
import versioneer

setup(version=versioneer.get_version(),
      cmdclass=versioneer.get_cmdclass())
