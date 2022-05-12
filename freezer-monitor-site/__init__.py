import logging

LOG = logging.getLogger(__name__)
LOG.setLevel( logging.DEBUG )

STREAM = logging.StreamHandler()
STREAM.setLevel( logging.DEBUG )

LOG.addHandler( STREAM )
