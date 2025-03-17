import csv
import pickle as pkl
import pandas as pd
from datetime import datetime
import pywt
import torch
import neurokit2 as nk
import numpy as np
import os
import plotly.graph_objects as go
from plotly_resampler import FigureResampler, FigureWidgetResampler

from packages.dash_package import default_values as def_val
from packages.cwt_cnn import worker_ecg_cwt as workers
from packages.cwt_cnn import cnn_model


def create_ecg_file(path, rate):
    """
    Creates a CSV file with a header for ECG amplitudes.

    Args:
    rate (int): The rate to include in the file name.
    
    Returns:
    str: The file path of the created CSV file.
    """
    # Current date and time
    current_date_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    
    # File name format: 'ecg_<currentDateTime>_<rate>.csv'
    file_name = f"ecg_{current_date_time}_{rate}"
    
    # Path to save the file
    file_path = f"{path}{file_name}.csv"  # Specify your directory path here
    
    # Write the header to the CSV file
    with open(file_path, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['ECG Amplitude (mV)'])
    
    return file_name, file_path

def append_ecg_data(file_path, data):
    """
    Appends ECG amplitude data to an existing CSV file.

    Args:
    file_path (str): The path to the CSV file.
    data (list): A list of ECG amplitude values in millivolts to append.
    """
    with open(file_path, 'a', newline='') as file:
        writer = csv.writer(file)
        for value in data:
            writer.writerow([value])

def ensure_directory_exists(path = 'storege/csv_files/'):
    """
    Checks if a directory exists, and if not, creates it.
    
    Args:
    path (str): The path to the directory to check and potentially create.
    """
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"Directory created: {path}")
    else:
        print(f"Directory already exists: {path}")

def scan_for_pckl_files(file_name:str):
    '''
    Given file name, scan if a pickle file excist
    '''
    # Check if the file exists
    if not os.path.exists(file_name):
        # Create the file
        with open(file_name, mode='w', newline='') as file:
            writer = csv.writer(file)
            # Write a header or initial data if needed
            writer.writerow(['Column1', 'Column2', 'Column3'])  # Example header
        print(f"File '{file_name}' created.")
    else:
        print(f"File '{file_name}' already exists.")

# fan to save given data to given path and ith given name 
def save_file(file_name:str, parent_path:str, data):

    path = f'{parent_path}{file_name}.pkl'

    with open(path, 'wb') as file:
        pkl.dump(data, file)
        
    return True

# Fun to clean the given signal using nk
def clean_signal(file_name:str, f_rate:str, f_type:str, f_date:str, f_time:str, method:str):

    # load csv file and convert to numpy of type float32
    path = f'{def_val.RAW_PATH}{file_name}'
    df = pd.read_csv(path).iloc[:, 0].values.astype(np.float32)
    # df = df.iloc[:, 0].values.astype(np.float32)
    # data format to be saved
    data = {
        'type'  : f_type,
        'rate'  : f_rate,
        'date'  : f_date,
        'capture_time' : f_time,
        'method'    : method,
        'data'  : None
    }

    if method == 'raw':
        data['data'] = df
    else:
        cleaned_data = nk.ecg_clean(df, sampling_rate=f_rate, method=method)
        data['data'] = cleaned_data.astype(np.float32)
    
    return data

def calculate_rr_hr(ecg_data:np.array, f_rate:int, f_type:str, f_date:str, f_time:str, method:str):
    # data format to be saved
    data = {
        'type'  : f_type,
        'rate'  : f_rate,
        'date'  : f_date,
        'capture_time' : f_time,
        'method'    : method,
        'rpeaks_data'  : None,
        'rpeaks_indices': None,
        'rri_data'  : None,
        'rri_times'  : None,
        'hr_data'   : None
    }  

    # find peaks
    data['rpeaks_data'], info = nk.ecg_peaks(ecg_data, sampling_rate=f_rate, method=method, correct_artifacts=True)
    data['rpeaks_indices'] = info['ECG_R_Peaks']
    
    # Compute R-R intervals in milliseconds
    data['rri_data'] = (np.diff(info['ECG_R_Peaks']) / f_rate * 1000).astype(np.int32)
    # Compute R-R intervals time domain in seconds
    data['rri_times'] = (np.array(info['ECG_R_Peaks'][1:]) / f_rate).astype(np.float32)
    
    # Calculate HR
    data['hr_data'] = nk.signal_rate(data['rpeaks_data'], sampling_rate=f_rate, desired_length=len(ecg_data))[1:]
    
    return data
# TODO: Test what it rerurns
# rpeaks, info = nk.ecg_peaks(data_clean['data'], sampling_rate=250)

# ecg_rate = nk.signal_rate(rpeaks, sampling_rate=250, desired_length=len(rpeaks))

# # Get ECG Derived Respiration (EDR) and add to the data
# data = nk.ecg_rsp(ecg_rate, sampling_rate=250, method='charlton2016')



# Calculate EDR
def calculate_edr(ecg_rate:np.array, f_rate:int, f_type:str, f_date:str, f_time:str, method:str):
    # data format to be saved
    data = {
        'type'  : f_type,
        'rate'  : f_rate,
        'date'  : f_date,
        'capture_time' : f_time,
        'method'    : method,
        'edr_rate'  : None
    }  

    # calculate edr
    edr_data = nk.ecg_rsp(ecg_rate = ecg_rate, sampling_rate=f_rate, method=method) 
    
    # clean data
    cleaned = nk.rsp_clean(edr_data, sampling_rate=f_rate, method='biosppy')

    # find_peaks
    df, peaks_dict = nk.rsp_peaks(cleaned)

    # Extract rate
    # Extract rate
    data['edr_rate'] = nk.rsp_rate(cleaned, peaks_dict, sampling_rate=f_rate)
    

    return data


def calculate_hrv(ecg_peaks:np.array, f_rate:int, f_type:str, f_date:str, f_time:str,values):
    # data format to be saved
    # data = {
    #     'type'  : f_type,
    #     'rate'  : f_rate,
    #     'date'  : f_date,
    #     'capture_time' : f_time,
    #     'time_indices'  : None,
    #     'freq_indices'  : None,
    #     'nonlin_indices'  : None
    # }  

    # if 'time_domain' in values:
    #     # calculate hrv Time 
    #     data['time_indices'] = nk.hrv_time(peaks=ecg_peaks, sampling_rate=f_rate).to_dict(orient='list') 

    # if 'freq_domain' in values:
    #     # calculate hrv Freq 
    #     data['freq_indices'] = nk.hrv_frequency(peaks=ecg_peaks, sampling_rate=f_rate).to_dict(orient='list') 

    # if 'nonLinear_domain' in values:
    #     # calculate hrv nonLinear 
    #     data['nonlin_indices'] = nk.hrv_nonlinear(peaks=ecg_peaks, sampling_rate=f_rate).to_dict(orient='list') 

    # data format to be saved
    data = {
        'type'  : f_type,
        'rate'  : f_rate,
        'date'  : f_date,
        'capture_time' : f_time,
        'values' : values,
        'indices' : []
    }  

    if 'time_domain' in values:
        # calculate hrv Time 
        time = nk.hrv_time(peaks=ecg_peaks, sampling_rate=f_rate)
        data['indices'].append(time.to_dict('records')[0])

    if 'freq_domain' in values:
        # calculate hrv Freq 
        freq = nk.hrv_frequency(peaks=ecg_peaks, sampling_rate=f_rate)
        data['indices'].append(freq.to_dict('records')[0])
    
    if 'nonLinear_domain' in values:
        # calculate hrv nonLinear 
        nonlinear = nk.hrv_nonlinear(peaks=ecg_peaks, sampling_rate=f_rate)
        data['indices'].append(nonlinear.to_dict('records')[0])

    return data

def calculate_hrv_time(ecg_peaks:np.array, f_rate:int, f_type:str, f_date:str, f_time:str):
    # data format to be saved
    data = {
        'type'  : f_type,
        'rate'  : f_rate,
        'date'  : f_date,
        'capture_time' : f_time,
        'time_indices'  : None
    }  

    # calculate hrv Time 
    data['time_indices'] = nk.hrv_time(peaks=ecg_peaks, sampling_rate=f_rate).to_dict(orient='list') 

    return data

def calculate_hrv_freq(ecg_peaks:np.array, f_rate:int, f_type:str, f_date:str, f_time:str):
    # data format to be saved
    data = {
        'type'  : f_type,
        'rate'  : f_rate,
        'date'  : f_date,
        'capture_time' : f_time,
        'freq_indices'  : None
    }  

    # calculate hrv Time 
    data['freq_indices'] = nk.hrv_frequency(peaks=ecg_peaks, sampling_rate=f_rate).to_dict(orient='list') 

    return data

def calculate_hrv_nonlinear(ecg_peaks:np.array, f_rate:int, f_type:str, f_date:str, f_time:str):
    # data format to be saved
    data = {
        'type'  : f_type,
        'rate'  : f_rate,
        'date'  : f_date,
        'capture_time' : f_time,
        'nonlinear_indices'  : None
    }  

    # calculate hrv Time 
    data['nonlinear_indices'] = nk.hrv_nonlinear(peaks=ecg_peaks, sampling_rate=f_rate).to_dict(orient='list') 

    return data


def predict_arrythmias( f_rate:int, f_type:str, f_date:str, f_time:str,
                        ecg_cleaned:np.array, 
                        # sample_rate:np.array, 
                        r_peaks_index:np.array ):
    

    # set cwt parameters
    wavelet = "mexh"  # mexh, morl, gaus8, gaus4
    cwt_parameters = {
            'wavelet'   : wavelet,
            'scales'    : pywt.central_frequency(wavelet) * f_rate / np.arange(1, 256, 1),
            'sampling_period' : 1/f_rate
    }

    # load scalar
    scalar_path = 'packages/cwt_cnn/models/scaler.pkl'
    with open(scalar_path, 'rb') as file:
        loaded_scaler = pkl.load(file)

    # compute cwt of given ecg
    cwt_data = workers.worker_ecg_to_cwt(ecg_cleaned=ecg_cleaned,
                                        sample_rate = f_rate, 
                                        r_peaks_index = r_peaks_index, 
                                        cwt_parameters = cwt_parameters,
                                        scaler = loaded_scaler)

    
    # load cnn architecture
    model = cnn_model.CNN_Module()
    
    # load parameters for cnn
    model_path = 'packages/cwt_cnn/models/model_notch_mexh.pkl'
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    torch_load_dkt = torch.load(model_path, map_location = device)
    # map_location=torch.device('cpu')
    model.load_state_dict(torch_load_dkt)

    # make tensors from numpy data
    x1 = torch.from_numpy(cwt_data[0]).float() 
    x2 = torch.from_numpy(cwt_data[1]).float() 

    # predict
    with torch.no_grad():  # No gradients needed for prediction
        predictions = model(x1, x2)

    # manage the propabilities to numpy
    probabilities = torch.softmax(predictions, dim=1)
    predicted_classes = torch.argmax(probabilities, dim=1)
    predicted_classes_cpu = predicted_classes.cpu().numpy()

    data = {
        'type'  : f_type,
        'rate'  : f_rate,
        'date'  : f_date,
        'capture_time' : f_time,
        'r_peaks_indices'  : cwt_data[2],
        'predictions': predicted_classes_cpu
    }  

    return data


# Fun to scan for csv files in a given path and return the names
def scan_for_csv_files(folder_path:str):
    csv_files_names = []
    files_names = []

    for f in os.listdir(folder_path):
        file_path = os.path.join(folder_path, f)

        if os.path.isfile(file_path) and f.endswith('.csv'):
            file_name = f.split('.')[0]
            file_name = file_name.split('_')
            csv_files_names.append(file_name)

    # csv_files_names = sorted(csv_files_names, key=lambda x: datetime.strptime(x, 'ecg_%Y-%m-%d_%H-%M-%S_250.csv'))
    csv_files_names = sorted(csv_files_names, key=get_datetime, reverse=True)

    for name in csv_files_names:
        files_names.append('_'.join(name))

    return files_names


# Function to convert date and time strings to datetime objects
def get_datetime(sublist):
    if len(sublist) > 2:
        date_part = sublist[1]
        time_part = sublist[2]
        return datetime.strptime(date_part + ' ' + time_part, '%Y-%m-%d %H-%M-%S')
    # Return minimal datetime for lists that do not have date/time info
    else:
        return datetime.min  

# load a pickle file and return data
def load_pickle_data(filepath):
    filepath = f'{filepath}.pkl'
    print(filepath)
    # check if file exist
    if not os.path.exists(filepath):
        print(f"No such file: {filepath}")
        return None

    with open(filepath, 'rb') as file:
        data = pkl.load(file)
        return data

def figure_rr(rri_times, rri_data, method):
    meth = method
    title = f'RR intervals ({meth})'

    fig = go.Figure(
        data=[go.Scatter(x=rri_times, y=rri_data) ],
        layout=go.Layout(
            title=go.layout.Title(text=title, x=0.5, xanchor='center'),
            xaxis_title="Time (s)",
            yaxis_title="RR (ms)"
        )
    )

    return fig

def figure_hr(time_domain, hr_data, rate):
    title = f'Heart Rate'
    
    # print(len(time_domain), len(edr_data))
    avg_window_size = 4*rate
    hr_rate_norm = np.convolve(hr_data, np.ones(avg_window_size),  mode='valid') / avg_window_size
    
    fig = go.Figure(
        data=[go.Scatter(x=time_domain, y=hr_rate_norm) ],
        layout=go.Layout(
            title=go.layout.Title(text=title, x=0.5, xanchor='center'),
            xaxis_title="Time (s)",
            yaxis_title="HR (bpm)"
        )
    )

    return fig


def figure_density_rr(rri_data, hr_data, bins = 20):
    intervals = rri_data
    # Histogram
    counts, bins = np.histogram(intervals, bins=bins)
    bin_centers = 0.5 * (bins[1:] + bins[:-1])
    hist = go.Bar(x=bin_centers, y=counts)

    # Density Plot
    x_axis, y_axis = nk.density(intervals) 
    y_axis = nk.rescale(y_axis, to=[0, np.max(counts)])
    density_line = go.Scatter(x=x_axis, y=y_axis, mode='lines', name='Density')

    # # Scatter Points on the x-axis
    scatter_points = go.Scatter(x=intervals, y=np.full(len(intervals), np.max(counts)*0.001), mode='markers', 
                                marker=dict(color='black', symbol='line-ns-open'), name='Points')

    # Boxplot
    box = go.Box(x=intervals,  name='R-R Intervals', boxpoints=False,line=dict(color='black'),
                    fillcolor='rgba(0,0,0,0)',width=np.max(counts) / 6)

    fig = go.Figure(data=[hist, density_line, box, scatter_points])

    # Update layout
    fig.update_layout(
        title=go.layout.Title(text='Distribution of R-R Intervals', x=0.5, xanchor='center'),
        xaxis_title_text='R-R intervals (ms)',
        # margin=dict(l=40, r=40, t=40, b=40),
        yaxis=dict(
            title='',
            range=[0, np.max(counts) * 1.2]  # Set y-axis range to accommodate all elements
            # range=[-0.2 * y_max, 1.3 * y_max] 
        ),
        # bargap=0.1,  # Gap between bars of the histogram
        showlegend=False,
        boxgap=0.0001,  # Space between adjacent boxplots
        boxgroupgap=0.0001  # Space between groups of boxplots
        # template='plotly_white'  # Set a white background
    )

    fig.update_traces(line=dict(width=2), selector=dict(type='box'))
    fig.update_yaxes(range=[-1.5, np.max(counts)+3])


    return fig

def figure_edr(time_domain, rsp_rate, rate):

    # meth = method
    title = f'ECG-Derived Respiration Rate '

    
    
    # print(len(time_domain), len(edr_data))
    avg_window_size = 4*rate
    rsp_rate_norm = np.convolve(rsp_rate, np.ones(avg_window_size),  mode='valid') / avg_window_size

    time_domain_norm = np.convolve(time_domain[:-1], np.ones(avg_window_size),  mode='valid') / avg_window_size

    # print(len(time_domain_norm), len(rsp_rate_norm))


    fig = go.Figure(
        data=[go.Scatter(x = time_domain_norm, y=rsp_rate_norm) ],
        layout=go.Layout(
            title=go.layout.Title(text=title, x=0.5, xanchor='center'),
            xaxis_title='Time (s)',
            yaxis_title='Breaths Per Minute'
        )
    )

    # resample for large data samples 
    fig = FigureResampler(fig)

    return fig

def adjusted_arrhythmia_indices(predictions,rpeaks_indices):

    # count_arrythmias
    unique_numbers, counts = np.unique(np.array(predictions), return_counts=True)
    count_dict = dict(zip(unique_numbers, counts))
    # Cheat and add the missing 2 arrythmias
    count_dict[0] += 2 

    # create a list with arrythmia indexes
    arrhythmia_indexes = {}
    for value in unique_numbers:
        if value != 0:

            if value == 1:
                arr_type =  'SVEB'
            elif value == 2:
                arr_type =  'VEB'
            else:
                arr_type =  'F'

            arrhythmia_indexes[arr_type] = np.where(predictions == value)[0].tolist()

    # print(arrhythmia_indexes)


    # Map rpeaks indexes to arrhythmia indexes
    adjusted_arrhythmia_indices = {}
    for arrhythmia_type, indixes in arrhythmia_indexes.items():
        
        if arrhythmia_type not in adjusted_arrhythmia_indices:
            adjusted_arrhythmia_indices[arrhythmia_type] = []
        
        for i in indixes:
            mapped_index = rpeaks_indices[i+1]
            adjusted_arrhythmia_indices[arrhythmia_type].append(mapped_index)

    # print(adjusted_arrhythmia_indices)
    return adjusted_arrhythmia_indices

def figure_arrythmias(ecg_data, time_domain, rpeaks_indices, arrhythmia_indices):

    # Sample data simulation
    ecg_signal = ecg_data * 1000

    # rpeaks_indices = data_intervals['rpeaks_indices']  # Indices of R-peaks
    # arrhythmia_indices = adjusted_arrhythmia_indices  # Dictionary of arrhythmia indices from your setup

    # Create a trace for the ECG signal
    ecg_trace = go.Scatter(
        x=time_domain,
        y=ecg_signal,
        mode='lines',
        name='ECG Signal'
    )

    # Create a trace for R-peaks
    rpeaks_trece = go.Scatter(
        x=time_domain[rpeaks_indices],
        y=[ecg_signal[idx] for idx in rpeaks_indices],
        mode='markers',
        marker=dict(color='red', size=5),
        name='R-Peaks'
    )

    fig = go.Figure()
    fig.add_trace(ecg_trace)
    # fig=FigureResampler(fig)
    fig.add_trace(rpeaks_trece)


    arrhythmia_markers = {
        'SVEB': {'color': 'black', 'symbol': 'x'},
        'VEB': {'color': 'green', 'symbol': 'x'},
        'F': {'color': 'purple', 'symbol': 'x'},
        # Additional markers can be defined as needed
    }

    # Add markers for each arrhythmia type at the adjusted R-peak indices
    for arrhythmia_type, indices in arrhythmia_indices.items():
        
        fig.add_trace(go.Scatter(
            x=time_domain[indices],
            y=[ecg_signal[idx] for idx in indices],
            mode='markers',
            marker=dict(
                color=arrhythmia_markers[arrhythmia_type]['color'],
                symbol=arrhythmia_markers[arrhythmia_type]['symbol'],
                size=10
            ),
            name=f'{arrhythmia_type}'
        ))

    # Customize layout to show the time domain
    fig.update_layout(
        title='ECG Signal with R-Peaks and Arrhythmias',
        xaxis=dict(title='Time (s)'),
        yaxis=dict(title='mV')
    )

    # fig.update_layout(yaxis_range=[np.mean(np.min(ecg_signal)),np.mean(np.max(ecg_signal))])
    fig.update_layout(yaxis_range=[-0.003, 0.003])
    # fig.update_layout(xaxis_rangeslider_visible=True)

    return fig