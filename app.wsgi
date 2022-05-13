path_to_site = '/path/to/website'

import os
activate_this = os.path.join( path_to_site, 'venv', 'bin', 'activate_this.py' )
with open( activate_this) as file:
  exec(file.read(), dict(__file__=activate_this))

import sys
sys.path.insert(0, path_to_site)
from freezer_monitor_site.app import server as application
