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
    self._timer.start()

  def saveData( self ):

    with self._lock:
      dates = pandas.to_datetime( self._df['timestamp'] )       # Convert to datetime
      index = dates >= (datetime.now() - timedelta(days=30))    # Get all data within last 30 days
      self._df = self._df[index]                                # Subset dataframe
      with self._rw_lock.write_lock():
        self._df.to_csv( CSV, index=False )                     # Write dataframe to csv

  def stop(self, *args, **kwargs):

    self._running.clear()

  def _recvmsg(self, conn, length):
    """Receive entire message"""

    packets = []                                                # List to store all packets from remote
    while self._running.is_set() and (length > 0):              # While running and have NOT gotten full message (all packets)
      try:                                                      # Try to 
        packet = conn.recv( length )                            # Read in all the data from the socket
      except socket.timeout:                                    # On timeout
        self._log.debug('Failed to get data before timeout')    # log
        continue                                                # Continue to try to receive from socket again
      except Exception as err:                                  # On error
        self._log.warning(f'Failed to get data : {err}')        # log
        continue                                                # Continue to try to receive from socket again

      if packet == b'': break                                   # If packet is empty, then break loop as socket is closed

      packets.append( packet )                                  # Append packet to list of packets
      length -= len( packet )                                   # Decrement length of message by the size of the packet received

    return b''.join( packets )                                  # Join packets together and return

  def recv(self, conn, addr):

    conn.settimeout( 1.0 )
    with conn:
      self._log.debug(f"Connected by {addr}")
      while self._running.is_set():
        msgLen = self._recvmsg( conn, self._length )
        if msgLen == b'': break                                 # If no data returned, break

        msgLen = int.from_bytes(msgLen, 'little')               # Convert msgLen to integer
        data   = self._recvmsg( conn, msgLen )                  # Try to get rest of data
        if data == b'': break                                   # if no data returned, break

        data   = json.loads( data.decode() )                    # Decode data from json format
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
        self.recv(conn, addr)


    if self._timer: self._timer.cancel()
    self.saveData()
    self._log.debug( 'Thread dead' )

if __name__ == "__main__":
  import signal 
  inst = WebSocket()
  signal.signal( signal.SIGINT,  inst.stop )
  signal.signal( signal.SIGTERM, inst.stop )
  inst.join()
