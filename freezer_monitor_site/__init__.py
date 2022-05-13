import logging
import os
LOG = logging.getLogger(__name__)
LOG.setLevel( logging.DEBUG )

#STREAM = logging.StreamHandler()
#STREAM.setLevel( logging.DEBUG )
#
#LOG.addHandler( STREAM )

DIR     = os.path.dirname( os.path.abspath( os.path.realpath(__file__) ) )
CSV     = os.path.join( DIR, 'data.csv' )
CSVLOCK = CSV + '.lock'
