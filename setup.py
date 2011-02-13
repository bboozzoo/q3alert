#!/usr/bin/env python

from distutils.core import setup

setup (
    name = 'q3alert',
    description = 'Q3 server monitoring applet',
    long_description = 'An applet to monitor Q3 server and notify the user about games in progress',
    version = '0.3.1',
    author = 'Maciek Borzecki',
    author_email = 'maciek.borzecki@gmail.com',
    license = 'GPL',
    scripts = ['q3alert'],
    data_files = [('share/q3alert', ['settings-dialog.ui']),
                  ('share/pixmaps/q3alert', ['bw.svg', 'bw-polling.svg', 'colored.svg']),
                  ('share/applications', ['desktop/q3alert.desktop'])]
    )
