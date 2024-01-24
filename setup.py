#!/usr/bin/env python

from distutils.core import setup

setup(name='external-app',
      version='0.1',
      description='External Version of the interm-app',
      author='Loup Letac',
      author_email='l.letac@3eing.ca',
      url='https://www.3eing.ca',
      packages=['distutils', 'distutils.command'],
     )