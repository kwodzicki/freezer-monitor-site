#!/usr/bin/env python
from setuptools import setup, find_packages, convert_path

NAME = "freezer_monitor_site"
DESC = "Dash website for displaying temperature in freezer"

main_ns  = {}
ver_path = convert_path( "{}/version.py".format(NAME) )
with open(ver_path) as ver_file:
  exec(ver_file.read(), main_ns)

setup(
  name                 = NAME,
  description          = DESC,
  url                  = "https://github.com/kwodzicki/freezer_monitor_site",
  author               = "Kyle R. Wodzicki",
  author_email         = "krwodzicki@gmail.com",
  version              = main_ns['__version__'],
  packages             = find_packages(),
  scripts              = ['bin/freezer_socket'],
  install_requires     = ['pandas', 'plotly', 'dash', 'fasteners'],
  zip_safe             = False
)


