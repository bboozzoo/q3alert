#!/usr/bin/env python

from distutils.core import setup

setup (
    name = 'q3alert',
    description = 'Q3 server monitoring applet',
    long_description = 'An applet to monitor Q3 server and notify the user about games in progress',
    version = '0.3.4',
    author = 'Maciek Borzecki',
    author_email = 'maciek.borzecki@gmail.com',
    license = 'GPLv3',
    scripts = ['q3alert'],
    url = 'http://github.com/bboozzoo/q3alert',
    data_files = [('share/q3alert', ['settings-dialog.ui']),
                  ('share/pixmaps/q3alert', ['icons/bw.svg', 
                                             'icons/bw-polling.svg', 
                                             'icons/colored.svg']),
                  ('share/applications', ['desktop/q3alert.desktop'])]
    )
