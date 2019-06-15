# -*- coding: utf-8 -*-

from distutils.core import setup
from setuptools import find_packages

setup(name='MIDILFO',
    version='1.1',
    description='MIDI LFO',
    author='David García Goñi',
    author_email='dagargo@gmail.com',
    url='https://github.com/dagargo/midilfo',
    packages=find_packages(exclude=['tests']),
    package_data={'midilfo': ['resources/*']},
    license='GNU General Public License v3 (GPLv3)',
    install_requires=['mido>=1.2.6', 'python-rtmidi>=1.1.0']
)
