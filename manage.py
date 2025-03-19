# Import packages
from dash import Dash, html, dcc, Input, Output, State, callback, no_update, clientside_callback, DiskcacheManager
import dash_bootstrap_components as dbc
import asyncio
import logging
import numpy as np

# Options for modal
clean_options=[
       {'label': 'Raw', 'value': 'raw'},
       {'label': 'Neurokit', 'value': 'neurokit'},
    #    {'label': 'BioSPPy', 'value': 'biosppy'},
       {'label': 'Pan Tompkins', 'value': 'pantompkins1985'},
       {'label': 'Elgendi', 'value': 'elgendi2010'},
   ]

rr_hr_options=[
       {'label': 'Neurokit', 'value': 'neurokit'},
       {'label': 'Pan Tompkins', 'value': 'pantompkins1985'},
       {'label': 'Hamilton', 'value': 'hamilton2002'},
       {'label': 'Rodrigues', 'value': 'rodrigues2021'},
   ]

edr_options=[
       {'label': 'HeartPy', 'value': 'vangent2019'},
       {'label': 'Sarkar', 'value': 'sarkar2015'},
       {'label': 'Charlton', 'value': 'charlton2016'},
   ]

hrv_options=[
       {'label': 'Time Domain Indices', 'value': 'time_domain'},
       {'label': 'Frequency Domain Indices', 'value': 'freq_domain'},
       {'label': 'NonLinear Indices', 'value': 'nonLinear_domain', 'disabled': False}
   ]

hrv_time_options=[
       {'label': 'Calculate R-R intervals Distribution', 'value': 'rr_distributions'},
   ]

hrv_freq_options=[
       {'label': 'Calculate Power Spectral Density', 'value': 'power_spectral_density'},
   ]

hrv_nonlinear_options=[
       {'label': 'Calculate Nonlinear indices', 'value': 'nonlinear_indices'},
   ]

arrythmias_options=[
       {'label': 'CWT and CNN', 'value': 'cwt_cnn'},
   ]



# Custom Libraries 
from packages.dash_package import default_values as def_val
from packages.dash_package import dash_class 
from packages.dash_package import util_fun_dash 

from packages.mv_package import movesense_class as mv_pack
from packages.mv_package import util_fun as mv_util_fun

import helper as hl
import plotly.graph_objs as go


# Configure logging
logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

mac = '0C:8C:DC:41:DB:EB'

# Init the current connection
current_conection = dash_class.ConnectionStatus()

# Init the Bleak class
mv_blk = mv_pack.BLEClient()

# figures to display recieved data
# CH1
figure1 = go.Figure(
    data=[],
    layout=go.Layout(
        title='',
        xaxis=dict(
            showline=False,
            showticklabels=False,
            zeroline=False,
            visible=False 
        ),
        yaxis=dict(
            showline=False,
            showticklabels=False,
            zeroline=False,
            visible=False 
        )
    )
)

# TODO: Ch2 to display second sensor
# CH2
figure2 = go.Figure(
    data=[],
    layout=go.Layout(
        title='',
        xaxis=dict(
            showline=False,
            showticklabels=False,
            zeroline=False,
            visible=False  # Hides the axis completely
        ),
        yaxis=dict(
            showline=False,
            showticklabels=False,
            zeroline=False,
            visible=False  # Hides the axis completely
        )
    )
)


# To run asyncio function using safe threading
def run_async_function(func):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(func)
    loop.close()
    return result

# app = Dash(__name__, background_callback_manager=background_callback_manager)
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

modal_body = html.Div([
    # Info
    html.Div([
        html.Label(id = 'modal_title', style={'font-weight': 'bold'})
    ], style={'display': 'flex','justify-content': 'center'}),
    html.Br(),
    html.Div([
        html.Label(id = 'modal_label_type'),
        html.Label(id = 'modal_label_rate'),
        html.Label(id = 'modal_label_date'),
        html.Label(id = 'modal_label_time')
    ], style={'display': 'flex','justify-content': 'space-between', 'align-items': 'center'}),
    html.Hr(),
    # Clean signal
    html.Div([
        html.Label(f'Clean ECG Signal:'),
        dcc.Dropdown( id='clean_dropdown', options=clean_options, value=clean_options[0]['value'],clearable=False,  style={'width': '50%'}),
    ], style={'display': 'flex', 'justify-content': 'space-between','align-items': 'center'}),
    html.Hr(),
    # find peaks
    html.Div([
        html.Label(f'Calculate RR_intervals and Heart Rate.'),
        dcc.Dropdown( id='peaks_dropdown', options=rr_hr_options,value=rr_hr_options[0]['value'],clearable=False,  style={'width': '50%'} ),
    ], style={'display': 'flex', 'justify-content': 'space-between','align-items': 'center'}),
    # Calculate ECG-Derived Respiration 
    html.Hr(),
    html.Div([
        html.Label(f'Extract ECG-Derived Respiration.'),
        dcc.Dropdown( id='edr_dropdown', options=edr_options,value=edr_options[0]['value'],clearable=False,  style={'width': '50%'} ),
    ], style={'display': 'flex', 'justify-content': 'space-between','align-items': 'center'}),
    # Calculate HRV of the time domain
    html.Hr(),
    html.Div([
        html.Label(f'HRV indices.'),
        dcc.Dropdown( id='hrv', options=hrv_options,value=hrv_options[0]['value'],multi = True, clearable=False,  style={'width': '70%'}, searchable = False )
    ], style={'display': 'flex', 'justify-content': 'space-between','align-items': 'center'}),

    # Find arrythmias using CWT
    html.Hr(),
    html.Div([
        html.Label(f'Find Arrythmias'),
        dcc.Dropdown( id='arr_rr', options=arrythmias_options,value=arrythmias_options[0]['value'],clearable=False,  style={'width': '50%'}, searchable = False )
    ], style={'display': 'flex', 'justify-content': 'space-between','align-items': 'center'}),
    html.Hr(),
    html.Hr(),
    # html.Div([
    #     html.P(id="paragraph_id", children=["Button not clicked"]),
    #     dcc.Graph(id="progress_bar_graph", figure=make_progress_graph(0, 10)),
    # ]),
    html.Div([
        html.Button(id = 'calculate_button', children = 'Start' )
    ], style={'display': 'flex', 'justify-content': 'center','align-items': 'center'}),
    html.Br(),
    html.Div([
        html.Div(id = 'modal_display_text')
    ], style={'display': 'flex', 'justify-content': 'center','align-items': 'center'}),
    
])

# Define the app layout
app.layout = html.Div([
    # Container for both columns
    html.Div([
        # Column for controls
        html.Div([
            # Scan for device and device list
            html.Div([
                html.Label('Available Devices:'),
                html.Button('Scan', id='scan_button', n_clicks=0)
            ], style={'display': 'flex', 'align-items': 'center', 'justify-content': 'space-between'}),
            dcc.Dropdown(id='available_devices'),
            html.Br(),

            # To set the request type
            html.Div([
                html.Div([
                    html.Label('Type'),
                    dcc.Dropdown(id='request_dropdown', options= def_val.REQUEST_ALL, value=None, searchable=False, clearable=False),
                ], style={'width': '50%', 'display': 'inline-block'}),
                html.Div([
                    html.Label('Rate'),
                    dcc.Dropdown(id='rate_dropdown', searchable=False)
                ], style={'width': '50%', 'display': 'inline-block'})
            ], style={'display': 'inline-block','width': '100%'}),
            html.Br(),
            html.Br(),

            # Connection status
            html.Div([
                html.Label('Connection Status:'),
                html.Span(id='connection_status', children='Disconnected', style={'font-weight': 'bold', 'color': 'red'}),
                html.Button(id='connect_button', children='Connect', n_clicks=0, disabled=True)
            ], style={'display': 'flex', 'align-items': 'center', 'justify-content': 'space-between'}),
            html.Br(),
            html.Br(),

            # To send Request
            html.Div([
                html.Label('Request Data:'),
                html.Span(id='request_data_text', children='None', style={'font-weight': 'bold', 'color': 'red'}),
                html.Button(id='request_button', children='Request', n_clicks=0, disabled=True)
            ], style={'display': 'flex', 'align-items': 'center', 'justify-content': 'space-between'}),

            html.Br(),
            html.Br(),

            # To start captureing data
            html.Div([
                html.Button('Start Notifiyng', id='capture_data_button', n_clicks=0, disabled = True),
                html.Button('Start Recording', id='save_data_button', n_clicks=0, disabled = True),
                html.Button('Create Analytics', id='analytics_button', n_clicks=0, disabled = True)
            ], style={'display':'flex', 'justify-content': 'center' } )

        ], style={'width': '20%', 'display': 'flex', 'flex-direction': 'column'}),

        # Column for the graph
        html.Div([
            dcc.Graph(
                id='live_graph_1',
                figure=figure1,
                config={'staticPlot': True,'displayModeBar': False}
            ),
            dcc.Graph(
                id='live_graph_2',
                figure=figure2,
                config={'staticPlot': True,'displayModeBar': False}
            )
        ], style={'width': '90%', 'display': 'flex', 'flex-direction': 'column','align-items': 'stretch'}),
       
    ], style={'display': 'flex', 'justifyContent': 'center', 'alignItems': 'center', 'height': '100vh'}),

    html.Div(id = 'current_text_display'),

    # Intervals
    # Interval to update client with data that recieved every interval ms
    dcc.Interval(id = 'update_data_to_client_interval', n_intervals = 0, interval = 1*1000, max_intervals = -1, disabled = True),
    # Faster interval for plotting
    dcc.Interval(id='clienside_interval', interval=10, disabled = True, max_intervals = 0,),  # Faster interval for plotting
    
    # Store Components
    # Data to sent to client to sisplay graph
    dcc.Store(id= "store_to_client", data = [], storage_type = 'memory'),
    # Store data being used for the plot
    dcc.Store(id='req_rate_store', data=[]),  

    # Modal For storing
    dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("Create Analytics"), close_button=False),
            dbc.ModalBody([modal_body]),
            dbc.ModalFooter(
                dbc.Button("Close", id="close_modal_btn", className="ms-auto", n_clicks=0, disabled = True)
            )
        ],
        size="lg",
        id="modal",
        keyboard=False,
        backdrop="static",
        is_open=False, 
    ),
], style={'width': '100%', 'height': '100vh', 'display': 'flex', 'flex-direction': 'column'})

# Callback to pop up Modal
@app.callback(
    [Output('modal_display_text', 'children'),  # 1 msg of modal
    Output('close_modal_btn','disabled'),       # 2 close modal of modal
    Output('modal_label_type', 'children'),     # 3 label type
    Output('modal_label_rate', 'children'),     # 4 label rate
    Output('modal_label_date', 'children'),     # 5 label date
    Output('modal_label_time', 'children')      # 6 label time
    ],
    # Output('calculate_button', 'disabled')],

    # [Input('modal', 'is_open'),
    [Input('calculate_button', 'n_clicks'), # 1. Start Button
    Input('clean_dropdown', 'value'),       # 2. Cleaning method
    Input('peaks_dropdown', 'value'),       # 3. Calculate intervals
    Input('edr_dropdown', 'value'),         # 4. Calculate EDR
    Input('hrv', 'value'),                  # 5. HRV
    # Input('hrv_time', 'value'),             # 5. Calculate hrv_time
    # Input('hrv_freq', 'value'),             # 6. Calculate hrv_freq
    # Input('hrv_nonlinear', 'value'),        # 7. Calculate hrv_nonlinear
    Input('arr_rr', 'value'),               # 7. Calculate arrythmias
    ],
    State('modal', 'is_open'),
    # backgtou
    prevent_initial_call = True)
def calculate_analytics_and_save(n_clicks,cl_value,pk_value,edr_value,hrv_values, arr_rr_value, is_open):
    # Modal is closed
    if n_clicks and is_open:

        # name = f'{name}_2'
        name_csv = current_conection.file_name
        rate_type = current_conection.rate_type
        rep_type = current_conection.request_type
        c_date = name_csv.split('_')[1]
        c_time = name_csv.split('_')[2]

        # clean Signal
        data = util_fun_dash.clean_signal(file_name=f'{name_csv}.csv', f_rate=rate_type, f_type=rep_type, f_date=c_date, f_time= c_time, method=cl_value)
        cleaned_ecg = data['data']
        # save clean file
        result = util_fun_dash.save_file(file_name = name_csv, parent_path = def_val.CLEAN_PATH, data=data) 

        # Calculate RR and HR
        data = util_fun_dash.calculate_rr_hr(ecg_data= data['data'], f_rate=rate_type, f_type=rep_type, f_date=c_date, f_time= c_time, method=pk_value)
        rr_data = data['rpeaks_data']
        rr_indices_data = data['rpeaks_indices']
        # save peaks file
        result = util_fun_dash.save_file(file_name = name_csv, parent_path = def_val.INTERVALS_PATH, data=data) 

        # Calculate EDR
        data = util_fun_dash.calculate_edr(ecg_rate= data['hr_data'], f_rate=rate_type, f_type=rep_type, f_date=c_date, f_time= c_time, method=edr_value)
        # save peaks file
        result = util_fun_dash.save_file(file_name = name_csv, parent_path = def_val.EDR_PATH, data=data) 

        # Calculate HRV indices
        data = util_fun_dash.calculate_hrv(ecg_peaks= rr_data, f_rate=rate_type, f_type=rep_type, f_date=c_date, f_time= c_time, values=hrv_values)
        # save peaks file
        result = util_fun_dash.save_file(file_name = name_csv, parent_path = def_val.HRV_PATH, data=data) 
        
        # Predict arrythmias
        data = util_fun_dash.predict_arrythmias(f_rate=rate_type, f_type=rep_type, f_date=c_date, f_time= c_time, 
                                            ecg_cleaned=cleaned_ecg,
                                            r_peaks_index=rr_indices_data)
        # save peaks file
        result = util_fun_dash.save_file(file_name = name_csv, parent_path = def_val.HRV_ARRYTHMIAS_PATH, data=data) 
        
        current_conection.to_create_analitycs = False 
        # data format to be saved
        # msg = f'{cl_value}, {pk_value}, {edr_value}, {hrv_time_value}, {hrv_freq_value}, {hrv_nonlin_value}, {arr_rr_value}'
        
        msg = f'{cl_value}, {pk_value}, {edr_value}, {hrv_values}, {arr_rr_value}'  # 1
        modal_close_button_disabled = False                                         # 2
        label_type = f'Type {rep_type}'                                             # 3
        label_rate = f'Type {rate_type}'                                            # 4
        label_date = f'Type {c_date}'                                               # 5
        label_time = f'Type {c_time}'                                               # 6


    else:
        msg = no_update
        modal_close_button_disabled = no_update 
        label_type = no_update
        label_rate = no_update
        label_date = no_update
        label_time = no_update

    return msg, modal_close_button_disabled, label_type, label_rate, label_date, label_time


# Callback to pop up Modal
@app.callback(
    [Output('modal', 'is_open'),
    Output('close_modal_btn', 'disabled', allow_duplicate=True),
    Output('analytics_button', 'disabled', allow_duplicate=True)],
    # [Input("save_data_button", "n_clicks"),
    [Input('analytics_button', 'n_clicks'),
    Input('close_modal_btn', 'n_clicks')],
    State('modal', 'is_open'),
    prevent_initial_call = True
)
def toggle_modal(analytics_button_n1,close_button_n2, is_open):
    print(f'data: {analytics_button_n1} {analytics_button_n1} {is_open}')
    
    if analytics_button_n1 and current_conection.to_create_analitycs:
        is_open = True
        # capture_data_nClicks = 1
        close_modal_btn_disabled = True
        analytics_button_disabled = True
    elif close_button_n2:
        # print(f'data: {close_button_n2}')
        is_open = False
        close_modal_btn_disabled = True
        # capture_data_nClicks = 0
        analytics_button_disabled = True
    else:
        is_open = no_update
        # capture_data_nClicks = no_update
        analytics_button_disabled = no_update
    
    # return is_open, capture_data_nClicks, analytics_button_disabled
    return is_open, close_modal_btn_disabled, analytics_button_disabled

app.clientside_callback(
    """
    function(n_intervals) {
        if (n_intervals > 0 ) {
            if (!window.myGlobalVar || !window.currentData1 || !window.currentData2) {
                return;  // Ensure all data buffers are initialized
            }
            //console.log("data 1");

            // Calculate the number of points to splice based on a smaller, fixed percentage of the total
            // Adjust this value to control smoothness vs. reactivity
            const percentageToSplice = 0.05; 
            let spliceCount = Math.floor(window.myGlobalVar.length * percentageToSplice);
            
            //console.log("data 2");
            
            // Ensure at least one point is spliced
            spliceCount = Math.max(1, spliceCount);
            
            // Splice the calculated number of points
            let current_sample = window.myGlobalVar.splice(0, spliceCount);

            let f1_len = window.currentData1.length 
            let f2_len = window.currentData2.length 


            // Append sampled data to the first data queue if it has capacity
            if (f1_len < 500) {
                window.currentData1.push(...current_sample);
            } else if (f2_len < 500) {
                // If first is full, start filling the second
                window.currentData2.push(...current_sample);
            } else {
                // console.log("data 5");
                // If both are full, remove from the first, add to the first, and rotate the data
                window.currentData1 = window.currentData1.slice(spliceCount);
                window.currentData1.push(...window.currentData2.splice(0, spliceCount));
                window.currentData2.push(...current_sample);
            }

            //console.log("data 6");
            return [
                {
                    data: [
                        {x: [...Array(window.currentData1.length).keys()],
                        y: window.currentData1, type: 'line'}
                        ],
                    layout: {
                        title: '',
                        xaxis: {showline: false, showticklabels: false, zeroline: false, visible: false},
                        yaxis: {showline: false, showticklabels: false, zeroline: false, visible: false}
                    }
                },
                {
                    data: [
                        {x: [...Array(window.currentData2.length).keys()],
                        y: window.currentData2, type: 'line'}
                        ],
                    layout: {
                        title: '',
                        xaxis: {showline: false, showticklabels: false, zeroline: false, visible: false},
                        yaxis: {showline: false, showticklabels: false, zeroline: false, visible: false}
                    }
                }
            ];
        }
        else {
            return;
        }
    }
    """,
    [Output(component_id = 'live_graph_1', component_property='figure'),
    Output(component_id = 'live_graph_2', component_property='figure')],
    Input(component_id = 'clienside_interval', component_property = 'n_intervals'),
    prevent_initial_call=True
)

# clientside callback to append new data to windows var
app.clientside_callback(
    """
    // Every time foo (Input data) is changed, then save data to global variable
    function(n_intervals, incomingData) {
        if (n_intervals > 3 ) {
            // Save data to global varialbe
            // check if existed
            if (!window.myGlobalVar) {
                window.myGlobalVar = [0];
            }
            if (!window.currentData1) {
                window.currentData1 = Array.apply(null, Array(500)).map(Number.prototype.valueOf,0);
            }
            if (!window.currentData2) {
                window.currentData2 = Array.apply(null, Array(500)).map(Number.prototype.valueOf,0);
            }
           
            //if (!window.myGlobalVar && !window.currentData1 && !window.currentData2) {
            //    window.myGlobalVar = [];
            //    window.currentData1 = [];
            //    window.currentData2 = [];
            //} 
            // log the input data
            // console.log('myGlobalVar exists:', incomingData.ecg_data);

            // Append data to global var
            window.myGlobalVar = window.myGlobalVar.concat(incomingData.ecg_data);
            
            // console log the global data
            // console.log('myGlobalVar exists:', window.myGlobalVar);

            return 'Current length of global var: ' + window.myGlobalVar.length;
        }
    }
    """,
    Output(component_id = 'current_text_display', component_property='children', allow_duplicate=True),
    # Output(component_id = 'clienside_interval', component_property='disabled',  allow_duplicate=True),
    Input(component_id = 'update_data_to_client_interval', component_property = 'n_intervals'),
    State(component_id = 'store_to_client', component_property = 'data'),
    prevent_initial_call=True
)


# Callback start saving data to csv file
@callback(
    [Output(component_id = 'save_data_button', component_property = 'children'),
    Output(component_id = 'connect_button', component_property='disabled', allow_duplicate=True), # 1
    Output(component_id = 'request_button', component_property='disabled', allow_duplicate=True),  # 2
    Output(component_id = 'capture_data_button', component_property='disabled', allow_duplicate=True),
    Output(component_id = 'analytics_button', component_property = 'disabled')], #3
    Input(component_id = 'save_data_button', component_property = 'n_clicks'),
    prevent_initial_call=True
)
def save_to_csv(n_clicks):
    if n_clicks > 0:

        # Start to save
        if not current_conection.is_saving_to_file:
            # create new file
            file_name, file_path = util_fun_dash.create_ecg_file(path=def_val.RAW_PATH, rate=current_conection.rate_type)
            # change connection status
            current_conection.change_saving_to_file()
            # print(current_conection.is_saving_to_file)

            # Save file name
            current_conection.set_file_path(file_name, file_path)

            # Disable changes to app
            name_save_button = 'Stop Capturing'
            disable_connect_bt = True
            disable_request_bt = True
            disable_capture_bt = True
            disable_analitics_bt = True
            # change create analitycs
            # If csv file have already captured enable it
            current_conection.to_create_analitycs = False
        # Else create stop recoring and enable again the buttons
        else:
            current_conection.change_saving_to_file()
            # print(current_conection.is_saving_to_file)

            # Disable changes to app
            name_save_button = 'Start Capturing'
            disable_connect_bt = False
            disable_request_bt = False
            disable_capture_bt = False
            disable_analitics_bt = False
            # change create analitycs
            # If csv file have already captured enable it
            current_conection.to_create_analitycs = True

        return name_save_button, disable_connect_bt, disable_request_bt, disable_capture_bt, disable_analitics_bt


# Callback to store data from queue to dcc.Store component
@callback(
    [Output(component_id='store_to_client', component_property='data'),
    Output(component_id='clienside_interval', component_property='max_intervals')],
    [Input(component_id='update_data_to_client_interval', component_property='n_intervals'),
    Input(component_id='clienside_interval', component_property='max_intervals')],
    prevent_initial_call=True
)
def display_queue_size(n_intervals, max_intervals):
    if n_intervals > 0:
       
        # current_data =  current_conection.loop.run_until_complete(
        #                     hl.generate_sawtooth(x, y)
        #                 )
        
        current_data = current_conection.loop.run_until_complete(
                                mv_util_fun.ecg_from_queue(mv_blk.queue)
                        )

        
        # Save data to file if is_saving
        if current_conection.is_saving_to_file:
            util_fun_dash.append_ecg_data(file_path=current_conection.file_path, data = current_data)

        data = {'ecg_data' : current_data.tolist()}

        # Check if interval is desabled
        logging.info(f"Recieved new data with len: {len(current_data)}.")

        if n_intervals > 4 and max_intervals == 0:
            max_intervals = -1
        else:
            max_intervals = no_update

        return data, max_intervals

# callback to start capturing data
# Enable update_data_to_client_interval interval
# Enable clienside_interval interval
@callback(
    [Output(component_id='capture_data_button', component_property='children'), # 1
    Output(component_id='update_data_to_client_interval', component_property='disabled'), # 2
    Output(component_id='clienside_interval', component_property='disabled'), # 3
    # Output(component_id='clienside_interval', component_property='n_intervals'), # 4
    Output(component_id='save_data_button', component_property='disabled')], # 5
    # Output(component_id='clienside_interval', component_property='disabled')],
    Input(component_id='capture_data_button', component_property='n_clicks'),
    prevent_initial_call=True
)
def start_capturing(n_clicks):
    if n_clicks > 0:
        # Start notifying
        if not current_conection.is_notifiyng:
            # Change button
            change_request = 'Stop Notifiyng' # 1
            
            # Start notifying
            
            # current_conection.loop.run_until_complete(hl.start_notify())
            current_conection.loop.run_until_complete(mv_blk.start_notify())
            current_conection.change_notification_status()
            
            # stop interval
            interval_disabled = False # 2
            # clientSide interval
            clientside_interval_disabled = False # 3
            # clientside_interval_n_intervals = 0 # 4

            # Enable save button
            save_data_button_disabled = False

        # Stop notifying
        else:
            # Change button
            change_request = 'Start Notifiyng'
            
            # Start notifying
            # current_conection.loop.run_until_complete(asyncio.sleep(0.5))
            # current_conection.loop.run_until_complete(hl.stop_notify())
            
            current_conection.loop.run_until_complete(mv_blk.stop_notify())
            current_conection.change_notification_status()

            # Stop interval
            interval_disabled = True # 2
            # clientSide interval
            clientside_interval_disabled = True # 3
            # clientside_interval_n_intervals = 0 # 4

            # Disable save button
            save_data_button_disabled = True
        
        # return change_request, interval_disabled, clientside_interval_disabled, clientside_interval_n_intervals, save_data_button_disabled
        return change_request, interval_disabled, clientside_interval_disabled, save_data_button_disabled
    else:
        return no_update, no_update, no_update, no_update, no_update

# Callback to write request
# firstly write a stop request to the device to get new data 
@callback(
    [Output(component_id='request_data_text', component_property='style',allow_duplicate=True),
    Output(component_id='capture_data_button', component_property='disabled'),
    Output(component_id='current_text_display', component_property='children', allow_duplicate=True)],
    Input(component_id='request_button', component_property='n_clicks'),
    prevent_initial_call=True)
def request(n_clicks):
    if n_clicks > 0:
        if not current_conection.is_connected:
            logging.info(f"Trying to request without conection.")
            return no_update, no_update, no_update

        try:
            if current_conection.request_type:


                # result = current_conection.loop.run_until_complete(
                #                         hl.write_characteristic(
                #                             request = current_conection.request_type,
                #                             hz = current_conection.rate_type)
                #                         )

                current_conection.loop.run_until_complete(
                    mv_blk.write_characteristic(
                        request = mv_util_fun.STOP_REQUEST_TYPE,
                        hz = 1
                    )
                )
                # current_conection.loop.run_until_complete(asyncio.sleep(0.5))
                result = current_conection.loop.run_until_complete(
                            mv_blk.write_characteristic(
                                request = current_conection.request_type,
                                hz = current_conection.rate_type
                            )
                        )
            

                if result:
                    logging.info(f"Requested new data ({current_conection.request_type}{'/' + str(current_conection.rate_type) if current_conection.rate_type else ''}).")
                    new_style = {'font-weight': 'bold','color': 'green'}
                    desable_capture_batton = False
                    msg = f'Request sent'
                    return new_style, desable_capture_batton, msg

        except Exception as e:
            logging.warning(f'Request: {e}')
            return no_update
            
    else:
        return no_update

# Callback to initialise connection or disconection
@callback(
    [Output(component_id='connection_status', component_property='children'), # 1
    Output(component_id='connection_status', component_property='style'), # 2
    Output(component_id='connect_button', component_property='children'), # 3
    Output(component_id='request_button', component_property='disabled', allow_duplicate=True), # 4
    Output(component_id='update_data_to_client_interval', component_property='max_intervals'), # 5
    Output(component_id='current_text_display', component_property='children', allow_duplicate=True)], # 6
    Input(component_id='connect_button', component_property='n_clicks'),
    prevent_initial_call=True)
def connect_disconnect_to_sensor(n_clicks):
    if n_clicks > 0:
        # print(not current_conection.mac_address)
        if not current_conection.mac_address:
            logging.info(f"Trying to connect without selected device.")
            return no_update, no_update, no_update, no_update, no_update

        try:
            if not current_conection.is_connected:
                logging.info(f"Initialising Connection...")
                #  Set Device address
                mv_blk.set_device_address(current_conection.mac_address)
                # set client and Connect
                if not mv_blk.client: 
                    mv_blk.set_client()

                # Create new loop
                loop = asyncio.new_event_loop()
                # set the new loop to the feature
                current_conection.loop = loop
                
                # connect
                # result = current_conection.loop.run_until_complete(hl.connect())
                result = current_conection.loop.run_until_complete(mv_blk.connect())
                
                if result == True:
                    current_conection.change_connection_status()
                    
                    # New labels
                    new_label = 'Connected' # 1
                    new_style= {'font-weight': 'bold','color': 'green'} # 2
                    new_button = 'Disconnect' # 3 

                    # check if req is correct
                    if current_conection.is_correct_req:
                        desable_req_button = False # 4
                    else:
                        desable_req_button = True # 4

                    update_data_to_client_interval_max_intervals = -1 # 5
                    current_msg = f'Connected' # 6
            # Case is disconnected
            else:
                logging.info(f"Disconecting...")
                
                # # Disconect and close the loop
                
                # result = current_conection.loop.run_until_complete(hl.disconnect())
                result = current_conection.loop.run_until_complete(mv_blk.disconnect())
                
                current_conection.loop.close()

                if result == True:
                    current_conection.change_connection_status()
                    current_conection.reset_class()
                    # New labels
                    new_label = 'Disconnected' # 1
                    new_style= {'font-weight': 'bold','color': 'red'} # 2
                    new_button = 'Connect' # 3
                    desable_req_button = True # 4
                    update_data_to_client_interval_max_intervals = 0 # 6 to stop updating
                    current_msg = f'Disconnected' # 7

            logging.info(f"{new_label}")
            
            return new_label, new_style, new_button, desable_req_button, update_data_to_client_interval_max_intervals, current_msg
            # return new_label, new_style, desable_req_button, update_data_to_client_interval_max_intervals, current_msg


        except Exception as e:
            logging.warning(f'Connect: {e}')
            return no_update, no_update, no_update, no_update
            
    else:
        return no_update, no_update, no_update, no_update



# Callback for the full request save to the current connection class
# Checks for the changes and store them 
# store the new request to the store component
@callback(
    [Output(component_id='current_text_display', component_property='children', allow_duplicate=True),
    Output(component_id='request_data_text', component_property='children'),
    Output(component_id='request_data_text', component_property='style'),
    Output(component_id='req_rate_store', component_property='data'),
    Output(component_id='request_button', component_property='disabled')],
    [Input(component_id='request_dropdown', component_property='value'),
    Input(component_id='rate_dropdown', component_property='value')],
    prevent_initial_call=True)
def save_request_variables(req_input,rate_input):
    # save them for later
    if req_input is not current_conection.request_type:
        current_conection.set_request(req_input)
        # print(f'Saved {current_conection.request_type}')

    if rate_input is not current_conection.rate_type:
        current_conection.set_rate(rate_input)
        # print(f'Saved {current_conection.rate_type}')

    full_request = f'Requsest: {current_conection.request_type} {current_conection.rate_type}'
    
    
    # req set but no rate
    if req_input in def_val.REQUEST_RATE and current_conection.rate_type == None:
        text_to_display = f'{req_input}/{rate_input}'
        current_conection.is_correct_req = False
    # req set and rate set
    elif req_input in def_val.REQUEST_RATE and rate_input:
        text_to_display = f'{req_input}/{rate_input}'
        current_conection.is_correct_req = True
    # req set
    else:
        text_to_display = f'{req_input}'
        current_conection.is_correct_req = True

    if current_conection.is_connected and current_conection.is_correct_req:
        request_button_disabled = False
    else:
        request_button_disabled = True

    # current_conection.set_full_request(text_to_display)
    new_style = {'font-weight': 'bold','color': 'red'}
    
    # save to req_rate_store to get used by client
    req_rate_store_data = {'request' : current_conection.request_type, 'rate' : current_conection.rate_type} 

    return full_request, text_to_display, new_style, req_rate_store_data, request_button_disabled

# Callback for the rate dropdown
# Different request types have different rates
@callback(
    Output(component_id='rate_dropdown', component_property='options'),
    Input(component_id='request_dropdown', component_property='value'))
def update_rate_drop(selected_request):
    available_options = []
    if not selected_request:
        return no_update
    elif selected_request in def_val.ECG_REQUEST_TYPE:
        available_options = def_val.ECG_SAMPLE_RATES
    elif selected_request in def_val.MAGI_REQUEST_TYPES:
        available_options = def_val.MAGI_SAMPLE_RATES
 
    return available_options


# Callback to save the selected device to connect
@callback(
    [Output(component_id='current_text_display', component_property='children'),
    Output(component_id='connect_button', component_property='disabled')],
    Input(component_id='available_devices', component_property='value'),
    prevent_initial_call = True)
def save_selected_device(selected_device_mac):
    if selected_device_mac is not None:
        
        if selected_device_mac is not current_conection.mac_address:
            current_conection.set_mac(selected_device_mac)
        
            logging.info(f"Selected divice changed to [{current_conection.mac_address}].")
            msg = f'Device {current_conection.mac_address} saved'
            connect_button_disabled = False
        else:
            msg = f'No Device saved'
            connect_button_disabled = True
        
        return msg, connect_button_disabled


# Callback for scan for devices
# Will return only movsense devices
@callback(
    Output(component_id='available_devices', component_property ='options'),
    Input(component_id='scan_button', component_property = 'n_clicks'),
    prevent_initial_call=True)
def scan_devices(n_clicks):
    if n_clicks > 0:
        logging.info(f"Start scanning ble devices.")
        try:            
            devices = run_async_function(mv_pack.scan_movesense_address())
            # devices = run_async_function(hl.scan_movesense_address())

            if devices:
                device_options = [{'label' : mac_address, 'value': name} for name, mac_address in devices]
                available_options = device_options
                
                logging.info(f"Scanning complete.")
                return available_options
            else:
                return no_update

        except Exception as e:
            logging.warning(f'{e}')
            return no_update

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
