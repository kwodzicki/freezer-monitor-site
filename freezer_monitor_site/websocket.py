import logging

import os
from datetime import datetime, timedelta
import socket
import json
from threading import Thread, Timer, Lock, Event

import pandas
import fasteners

from . import CSV, CSVLOCK

HOSTNAME = socket.gethostname()
LOCAL_IP = socket.gethostbyname(HOSTNAME)

class WebSocket( Thread ):

  def __init__(self, host=LOCAL_IP, port = 20486, **kwargs):

    super().__init__()
    self.host       = host
    self.port       = port

    self._log       = logging.getLogger(__name__)
    self._socket    = None
    self._timer     = None
    self._connected = False
    self._running   = Event()
    self._lock      = Lock()
    self._length    = 4
    self._interval  = 60.0              # Save interval for updating file

    self._rw_lock   = fasteners.InterProcessReaderWriterLock( CSVLOCK )

    if os.path.isfile( CSV ):
      with self._rw_lock.read_lock():  
        self._df = pandas.read_csv( CSV )
    else:
      self._df = pandas.DataFrame(columns=['timestamp', 'temp', 'rh'])

    self._running.set()
    self._autoSave()
    self.start()

  @property
  def df(self):
    with self._lock:
      return self._df

  def _autoSave(self):
    """Run autosaving"""

    if self._timer: self.saveData()
    self._timer = Timer( self._interval, self._autoSave )

  def saveData( self ):

    with self._lock:
      dates = pandas.to_datetime( self._df['timestamp'] )       # Convert to datetime
      index = dates >= (datetime.now() - timedelta(days=30))    # Get all data within last 30 days
      self._df = self._df[index]                                # Subset dataframe
      with self._rw_lock.write_lock():
        self._df.to_csv( CSV, index=False )                     # Write dataframe to csv

  def stop(self, *args, **kwargs):

    self._running.clear()

  def _recv(self, conn, addr):

    conn.settimeout( 1.0 )
    with conn:
      self._log.debug(f"Connected by {addr}")
      while self._running.is_set():
        try:
          dataLen = conn.recv( self._length )
        except socket.timeout:
          self._log.debug('Failed to get data before timeout')
          continue 
        except Exception as err:
          self._log.warning(f'Failed to get data : {err}')
          continue

        if dataLen == b'': break

        data = conn.recv( int.from_bytes(dataLen, 'little') )
        data = json.loads( data.decode() )
        for key, val in data.items():
          if not isinstance( val, (list, tuple) ):
            data[key] = [ val ]

        data = pandas.DataFrame.from_dict( data )
        with self._lock:
          self._df = pandas.concat( [self._df, data] )

    self._log.debug( f"Disconnected from {addr}" )



  def run(self):
    """Method run a separate thread"""

    self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)	# Set socket
    self.socket.settimeout( 1.0 )
    try:
      print( f'Attempting to bind - {self.host}:{self.port}' )
      self.socket.bind( (self.host, self.port) )
    except Exception as err:
      print( f'Failed to bind : {err}' )
      return

    self.socket.listen()

    while self._running.is_set():
      try:
        conn, addr = self.socket.accept()
      except socket.timeout:
        self._log.debug( 'Timed out waiting for connection.' )
      except Exception as err:
        self._log.warning( f'Encountered error waiting for connection : {err}' )
      else:
        self._recv(conn, addr)


    if self._timer: self._timer.cancel()
    self.saveData()
    self._log.debug( 'Thread dead' )

if __name__ == "__main__":
  import signal 
  inst = WebSocket()
  signal.signal( signal.SIGINT,  inst.stop )
  signal.signal( signal.SIGTERM, inst.stop )
  inst.join()
