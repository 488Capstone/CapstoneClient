# this file is necessary to create a package so that the webgui can import the modules ABOVE it in the directory
#   hierarchy. It's a pain, I know...
from setuptools import setup,find_packages
setup(name='CapstoneClient', version='0.1', packages=find_packages())
