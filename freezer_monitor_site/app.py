import os

import dash
from dash.dependencies import Output, Input
from dash import dcc, html

from flask import Flask

import plotly
import plotly.graph_objs as go
from plotly.subplots import make_subplots

import pandas

import fasteners

from . import CSV, CSVLOCK

RED     = '#FF0000'
BLUE    = '#483D8B'

RW_LOCK = fasteners.InterProcessReaderWriterLock( CSVLOCK )

print( 'Initializing Dash object' )
server = Flask( __name__ )
app    = dash.Dash( name = __name__, server = server )

print('Setting up layout')
app.layout = html.Div( children = [
  html.H1('Freezer Monitor'),
  html.H3(children='Real-time stats of chest freezer'),
  html.Div(id='current-time'),
  html.Div(id='current-temp'),
  html.Div(id='current-rh'),
  dcc.Graph(id = 'live-graph', animate = True, style={'height' : '85vh'}),
  dcc.Interval(
              id          = 'graph-update',
              interval    = 60 * 1000,
              n_intervals = 0),
  ]
)
  
@app.callback(
            Output('current-time', 'children'),
            Output('current-temp', 'children'),
            Output('current-rh',   'children'),
            Output('live-graph',   'figure'),
            Input( 'graph-update', 'n_intervals') 
)
def update_graph_scatter( *args ):
  x, y1, y2 = 'timestamp', 'temp', 'rh'                                                 # Specify keys for x and y axes

  with RW_LOCK.read_lock():                                                             # Grab lock for file
    if not os.path.isfile( CSV ):                                                       # If the CSV file does NOT exist, then return empty strings and DataFrame 
      return '', '', '', pandas.DataFrame( columns = [x, y1, y2] )
    df = pandas.read_csv( CSV )                                                         # Read in CSV file

  fig  = make_subplots( specs=[[{"secondary_y" : True}]] )                              # Initialize sub plots

  # First plot for temperature
  fig.add_trace( 
          go.Scatter( x = df[x], y = df[y1], name = 'Temperature', line={'color' : RED}), 
          secondary_y=False 
  )

  # Second plot for RH
  fig.add_trace( 
          go.Scatter( x = df[x], y = df[y2], name = 'Relative Humidity', line={'color' : BLUE}),
          secondary_y=True
  )

  # Update x-axis for plots
  fig.update_xaxes(
          title_text = 'Date', 
          range      = [df[x ].min(), df[x ].max()],
  )
  # Update y-axis for first plot (temperature)
  fig.update_yaxes(
          title_text  = '<b>Temperature (degree C)</b>',
          color       = RED,
          range       = [-45, 15],
          secondary_y = False
  )
  # Update second y-axis (RH)
  fig.update_yaxes(
          title_text  = '<b>Relative Humidity (%)</b>',
          color       = BLUE,
          range       = [0, 100],
          secondary_y = True
  )


  return (f"Current time        : {df[ x].iloc[-1]}", 
          f"Current temperature : {df[y1].iloc[-1]:0.1f} C", 
          f"Current humidity    : {df[y2].iloc[-1]:0.1f} %", 
          fig)


if __name__ == '__main__':
  app.run_server()
  print( 'finished' )
