import dash
from dash.dependencies import Output, Input
from dash import dcc, html
import plotly
#import plotly.express as px
import plotly.graph_objs as go
from plotly.subplots import make_subplots

from .websocket import WebSocket

RED    = '#FF0000'
BLUE   = '#483D8B'

socket = WebSocket() 
app    = dash.Dash(__name__)

app.layout = html.Div( children = [
  html.H1('Freezer Monitor'),
  html.H3(children='Real-time stats of chest freezer'),
  html.Div(id='current-temp'),
  html.Div(id='current-rh'),
  dcc.Graph(id = 'live-graph', animate = True),
  dcc.Interval(
              id          = 'graph-update',
              interval    = 60 * 1000,
              n_intervals = 0),
  ]
)
  
@app.callback(
            Output('current-temp', 'children'),
            Output('current-rh',   'children'),
            Output('live-graph',   'figure'),
            Input( 'graph-update', 'n_intervals') 
)
def update_graph_scatter( *args ):

  df   = socket.df
  x    = 'timestamp'
  y1   = 'temp'
  y2   = 'rh'
  #fig  = px.line( df, x = x, y = y1 )
  #fig.update_layout( xaxis_title = 'Date', 
  #                   yaxis_title = 'Temperature (degrees C)',
  #                   xaxis_range = [df[x ].min(), df[x ].max()],
  #                   yaxis_range = [df[y1].min(), df[y1].max()]) 


  fig  = make_subplots( specs=[[{"secondary_y" : True}]] )

  fig.add_trace( 
          go.Scatter( x = df[x], y = df[y1], name = 'Temperature', line={'color' : RED}), 
          secondary_y=False 
  )

  fig.add_trace( 
          go.Scatter( x = df[x], y = df[y2], name = 'Relative Humidity', line={'color' : BLUE}),
          secondary_y=True
  )
  
  fig.update_xaxes(
          title_text = 'Date', 
          range      = [df[x ].min(), df[x ].max()],
  )
  fig.update_yaxes(
          title_text  = '<b>Temperature (degree C)</b>',
          color       = RED,
          range       = [df[y1].min(), df[y1].max()],
          secondary_y = False
  )
  fig.update_yaxes(
          title_text  = '<b>Relative Humidity (%)</b>',
          color       = BLUE,
          range       = [df[y2].min(), df[y2].max()],
          secondary_y = True
  )


  return (f"Current temperature : {df[y1].iloc[-1]} C", 
          f"Current humidity    : {df[y2].iloc[-1]} %", 
          fig)
          
if __name__ == '__main__':
  app.run_server()
  socket.stop()
  socket.join()
  print( 'finished' )
