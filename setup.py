# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

with open('requirements.txt') as f:
	install_requires = f.read().strip().split('\n')

# get version from __version__ variable in erpnextturkish/__init__.py
from erpnextturkish import __version__ as version

setup(
	name='erpnextturkish',
	version=version,
	description='E-Fatura ve diger ozel cozumler',
	author='Logedosoft Business Solutions',
	author_email='info@logedosoft.com',
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
