# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table as dtt
from dash.dependencies import Input, Output

import plotly.graph_objects as go

import pandas as pd

from datetime import time
from PIL import Image

import sys
import os

# Parking space data import & some processing

directory = 'smart_parking_data'
files = [os.path.join(directory, filename) for filename in os.listdir(directory) if filename.endswith('.txt')]
parking_spaces = pd.DataFrame(columns=['Date_time', 'free_parking_spaces', 'occupied_spaces'])
read_f = [pd.read_csv(file, usecols= ['Date_time', 'free_parking_spaces', 'occupied_spaces']) for file in files]
parking_spaces = pd.concat(read_f)
parking_spaces['Time'] = pd.to_datetime(parking_spaces['Date_time'])
parking_spaces.drop('Date_time', axis=1, inplace=True)
parking_spaces['Weekday'] = pd.Categorical(parking_spaces['Time'].dt.day_name(), categories=
    ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday', 'Sunday'],
    ordered=True)
days = parking_spaces.groupby('Weekday').mean().round(0).reset_index()[['Weekday', 'free_parking_spaces', 'occupied_spaces']]
hours = parking_spaces.groupby(parking_spaces['Time'].map(lambda x : x.hour)).mean().reset_index()
# Average minute by minute paking space usage
minutes = parking_spaces.groupby([parking_spaces['Time'].map(lambda x : time(x.hour, x.minute)), 'Weekday']).mean().round(0).fillna(method='backfill', axis=0).reset_index()
# For the range slider
time_options = hours['Time'].values

# Object counting data import & some processing
directory = 'object_counting_data'
files = [os.path.join(directory, filename) for filename in os.listdir(directory) if filename.endswith('.txt')]
read_f = []
for file in files:
    hold = pd.read_csv(file, header=None)
    hold.columns = ['Time', 'x-axis', 'y-axis','Class']
    read_f +=[hold]
objects = pd.concat(read_f)
classes = { 0 : 'Bicyclist', 1: 'Pedestrian'}
objects['Time'] =  pd.to_datetime(objects['Time'])
objects['Weekday'] = objects['Time'].dt.day_name()
objects['Class'] = objects['Class'].map(lambda x: classes[x])

# Get object counts by time: simple frequencies
object_counts_time = objects.groupby(['Time', 'Class']).count().reset_index()

#Speed detection data import
directory = 'speed_detection_data'
files = [os.path.join(directory, filename) for filename in os.listdir(directory) if filename.endswith('.txt')]
read_f = [pd.read_csv(file, usecols= ['Class','Direction','Speed','Time']) for file in files]
speed = pd.concat(read_f)
del read_f
speed['Time'] = pd.to_datetime(speed['Time'], format="%Y-%m-%d %H:%M")
speed['Weekday'] = speed['Time'].dt.day_name()
speed['Weekday'] =  pd.Categorical(speed['Weekday'], categories=
    ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday', 'Sunday'],
    ordered=True)
# Average speed by minutes
minutes_speed = speed.groupby([speed['Time'].map(lambda x : time(x.hour, x.minute)), 'Weekday']).mean().round(0).reset_index()
# Average speed by days and classes
days_speed = speed.groupby(['Weekday', 'Class']).mean().reset_index()

img = Image.open('background.jpg')
fig = go.Figure()

img_width = 3840
img_height = 2160

for i in objects.Class.unique():
    fig.add_trace(go.Scatter(
            x=objects[objects.Class == i]['x-axis'],
            y=objects[objects.Class == i]['y-axis'],
            name=str(i),
            mode="markers",
            marker_opacity=0.1,
        )
    )
fig.update_yaxes(
    visible=False,
    range=[img_height, 0],
    # the scaleanchor attribute ensures that the aspect ratio stays constant
    scaleanchor="x"
)
fig.update_xaxes(
    visible=False,
    range=[0, img_width]
)

fig.add_layout_image(
    dict(
        x=0,
        sizex=img_width,
        y=0,
        sizey=img_height,
        xref="x",
        yref="y",
        opacity=1.0,
        layer="below",
        sizing="stretch",
        source=img)
)

# fig.update_layout(
#     # width=img_width,
#     # height=img_height,
#     margin={"l": 0, "r": 0, "t": 0, "b": 0},
# )


external_stylesheets = ['https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/css/bootstrap.min.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = dcc.Tabs([
        dcc.Tab(label='Parking Spaces', 
        children=[
            html.Div(children=[
                html.H3(children='Parking space usage'),
                html.Div(children=[
                    html.Div(children=[
                        dcc.Graph(id='graph-hours'),
                        dcc.RangeSlider(
                            id='hour-slider',
                            min=min(hours['Time']) -1,
                            max=max(hours['Time']) +1,
                            value=[min(hours['Time']), max(hours['Time'])],
                            marks={str(hour): str(hour) for hour in hours['Time'].unique()},
                            step=None,
                        ),
                    ],
                    style={'width': '45%',
                            'margin': '15px',
                            'display': 'inline-block'}),
                    dcc.Graph(
                        id='days-graph',
                        figure={
                            'data': [
                                {'x': days['Weekday'], 
                                'y': days['occupied_spaces'], 
                                'type': 'bar', 
                                'name': u'Empty spaces'},
                                {'x': days['Weekday'], 
                                'y': days['free_parking_spaces'], 
                                'type': 'bar', 
                                'name': u'Cars'},
                            ],
                            'layout': {
                                'title': 'Daily average parking space usage'
                            }
                        },
                        style={'width': '45%',
                            'display': 'inline-block'}),
                ]),
                html.Div(children=[
                    dcc.Graph(
                        id='change-graph',
                        figure={
                            'data': [dict(
                                        x = minutes[minutes.Weekday == i]['Time'],
                                        y = minutes[minutes.Weekday == i]['occupied_spaces'], 
                                        opacity=0.5,
                                        marker={
                                            'size': 2,
                                            'line': {'width': 0.2}
                                        },
                                        name=i
                                    ) for i in minutes.Weekday.unique()],
                            'layout': {
                                'title': 'Parking space usage by times of day'
                            }
                        },
                        style={'width': '100%',
                            'display': 'inline-block'}),
                ]),
            ])
        ]),
        # Object counts & speed graphs
        dcc.Tab(label='Object detection', children=[
                html.Div(children=[
                    html.Div(children=[
                        dcc.Graph(figure=fig,
                        config={'doubleClick': 'reset'},
                        style={'width': '100%',
                                'height': '100vh',
                                'display': 'inline-block'}),
                    ]),
                    html.Div(children=[
                        dcc.Graph(
                            id='class-graph',
                            figure={
                                'data': [
                                    dict(
                                        x = object_counts_time[object_counts_time.Class == i]['Time'],
                                        y = object_counts_time[object_counts_time.Class == i]['x-axis'], 
                                        opacity=0.7,
                                        marker={
                                            'size': 2,
                                            'line': {'width': 0.5, 'color': 'white'}
                                        },
                                        name=i
                                    ) for i in object_counts_time.Class.unique()
                                ],
                                'layout': {
                                    'title': 'Object counts by time'
                                }
                            },
                            style={'width': '50%',
                                'display': 'inline-block'}),
                        dcc.Graph(
                        id='speed-days-graph',
                        figure={
                            'data': [
                                dict(
                                        x = days_speed[days_speed.Class == i]['Weekday'],
                                        y = days_speed[days_speed.Class == i]['Speed'], 
                                        #mode='line',
                                        opacity=0.7,
                                        marker={
                                            'size': 2,
                                            'line': {'width': 0.5, 'color': 'white'}
                                        },
                                        type= 'bar', 
                                        name=i
                                    ) for i in days_speed.Class.unique()
                            ],
                            'layout': {
                                'title': 'Daily average speed'
                            }
                        },
                        style={'width': '50%',
                            'display': 'inline-block'}),
                    ]),
                    dcc.Graph(
                            id='speed-graph',
                            figure={
                                'data': [
                                    dict(
                                        x = minutes_speed[minutes_speed.Weekday == i]['Time'],
                                        y = minutes_speed[minutes_speed.Weekday == i]['Speed'], 
                                        #mode='line',
                                        opacity=0.5,
                                        marker={
                                            'line': {'width': 0.3, 'color': 'white'}
                                        },
                                        name=i
                                    ) for i in minutes_speed.Weekday.unique()
                                ],
                                'layout': {
                                    'title': 'Detected speed by times of day'
                                }
                            },
                            style={'width': '100%',
                                'display': 'inline-block'}),
                    ]),
                ],
)])


@app.callback(
    Output('graph-hours', 'figure'),
    [Input('hour-slider', 'value')])
def update_figure(values):
    filtered_df = hours[hours['Time'].map(lambda x: x in range(values[0], values[1]+1))]
    traces = []
    traces.append(dict(
        x=filtered_df['Time'],
        y=filtered_df['occupied_spaces'],
        text=filtered_df['Time'],
        type='bar'
    )),

    return {
        'data': traces,
        'layout': {
            'title': 'Hourly average parking space usage'
        },
    }

if __name__ == '__main__':
    app.run_server(port=8080, host='0.0.0.0', debug=False)
