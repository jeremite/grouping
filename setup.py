#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import os
from setuptools import setup
def package_files(directory):
    paths = []
    for (path, _, filenames) in os.walk(directory):
        for filename in filenames:
            paths.append(os.path.join("..", path, filename))
    return paths
grouping_files = package_files("grouping/")
#other_files = package_files("my_grouping/")
setup(
    name = 'grouping',
    version='0.1.6',
    license='GNU General Public License v3',
    author='Travis Li',
    author_email='weixing.li@verisk.com',
    description='Display and adjust the grouping results',
    packages=['grouping'],
    platforms='any',
    install_requires=[
        'flask',
    ],
    package_data={
    'grouping': grouping_files
},
    #data_files=[('grouping',grouping_files)],
    classifiers=[],
    include_package_data=True,
    entry_points={
        'console_scripts': ['grouping_run=grouping.cli:main']
    }
)
