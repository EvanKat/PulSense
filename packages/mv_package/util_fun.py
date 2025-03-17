import numpy as np
from bleak import BleakScanner
from re import match as re_match
from asyncio import Queue
from constants import * 


async def scan_movesense_address(timeout = 5.0):
    '''
    Scan for ble Movesense devices using BleakScanner's discover method for a certain time

    Args:
        timeout: A float to set the descovering time

    Returns:
        list: A list of strings with each element [device.address, device.name]
    
     Example:
        >>> list = scan_movesense_address()
        [0C:8C:DC:41:DB:EB, Movesense 223430000019]
    '''
    if timeout <= 0:
        raise ValueError("Timeout cannot be negative.")

    devices = await BleakScanner.discover(timeout)
    # print(devices)
    movesense_devices = []
    if devices is not None:
        for d in devices:
            # Store movesense ble devices 
            if d.name and d.name.startswith(DEVICENAME):
                movesense_devices.append([str(d.address), str(d.name)])
        
        if not movesense_devices:
            raise NameError("No movesense devices.")
        return movesense_devices 
    else :
        raise NameError("No devise found.")

def is_valid_mac_address(mac : str):
    '''
    Validate the the given string has a mac address format (use of ':')

    Args:
        mac: A string type address 
    
    Returns:
        bool: If the given str matches True else False
    
    Example:
        >>> bool = is_valid_mac_address(0C:8C:DC:41:DB:EB)
        True
    '''
    # Define a regular expression pattern for a valid MAC address
    mac_pattern = r'^([0-9A-Fa-f]{2}[:]){5}([0-9A-Fa-f]{2})$'

    # Use the re.match() function to check if the string matches the pattern
    return bool(re_match(mac_pattern, mac))


def is_valid_request(request : str, hz = int):
    '''
    Check that the given strings has is one of the valid requests and return the full request to 
    write to a movesense device (/meas/request/hz) 

    Args:
        request: A string for the request type
        hz: An int for the tick rate (if needed)
    
    Returns:
        path: string with the full request
        False: Bool if wrong request given
    
    Example:
        >>> request = is_valid_request("ecg",125)
        "/meas/ecg/125"
        >>> request = is_valid_request("imu9m",11111111111)
        False
    '''
    if request.lower() in MAGI_REQUEST_TYPES:
        if hz in MAGI_SAMPLE_RATES:
            path = "/meas/" + str(request) + "/" + str(hz)
            return path 
        else:
            return False
    elif request.lower() == ECG_REQUEST_TYPE:
        if hz in ECG_SAMPLE_RATES:
            path = "/meas/" + str(request) + "/" + str(hz)
            return path
        else:
            return False
    elif  request.lower() == HR_REQUEST_TYPE:
        path = "/meas/" + str(request)
        return path
    else:
        return False

async def magi_data_format(queue : Queue()):
    '''
    Pop out one element from the input queue and formats it into a structured NumPy array. 
    The array is structured to [timestamp, x(1_n), y(1_n), z(1_n)] format.
    For rate 13 Hz, the format is [timestamp, x1, y1, z1], for rate 26 the structure is [timestamp, x1, x, y1, y2, z1, z2] etc.
    
    Args:
        queue: The asyncio fifo Queue that holds the stored data 
    
    Returns:
       magi_data: The np array holding the magi data.
    
    Example:
        >>> data = await magi_data_format(queue)
        [ time, data ]
    '''
    dt = np.dtype([('timestamp', np.uint32), ('elements', np.ndarray)])
    # magi_data = np.array([], np.ndarray)
    
    data = await queue.get()
    if data is None:
        return None
    
    data_xyz = np.array(data[1:], dtype = np.float32)
    # magi_data = np.array([ ( data[0], data_xyz )], dtype = dt)
    # magi_data = np.append(magi_data, full_data)  

    return np.array([ ( data[0], data_xyz )], dtype = dt) 

async def ecg_data_format(queue : Queue()):
# async def ecg_data_format(queue : Queue(), store_time = True):
    '''
    Pop out one element from the input queue and format it into a structured NumPy array. 
    The array is structured to [timestamp, ecg(1-16)] format.
    
    Args:
        queue: The asyncio fifo Queue that holds the stored data 
        store_time: Boolean to store timestump 
    
    Returns:
       ecg_data: The np array that holding the ecg data.
    
    Example:
        >>> data = await ecg_data_format(queue)
        [ time, ecg1, ... , ecg16 ]
        >>> data = await ecg_data_format(queue, False)
        [ ecg1, ... , ecg16 ]
    '''
    ecg_data = np.array([], dtype = np.float32)
    # start_time = store_time

    data = await queue.get()
    
    if data is None:
        return None
    
    start_time = data[0]
    ecg_data = np.array(data[1:])

    # if store_time:
    #     return [start_time, ecg_data]
    # else:
    #     return ecg_data
    return [start_time, ecg_data]
    
async def hr_data_format(queue : Queue()):
    '''
    Pop out one element from the input queue and format it into a structured NumPy array. 
    The array is structured to [heart rate, RR interval] format.
    
    Args:
        queue: The asyncio fifo Queue that holds the stored data 
    
    Returns:
       hr_data: The np array that holding the hr data.
    
    Example:
        >>> data = await hr_data_format(queue)
        [ 65.1,  923]
    '''
    dt = np.dtype([ ('beat_rate', np.float32), ('RR_int', np.uint16)])
     
    data = await queue.get()
    if data is None:
        return data
    
    data = np.array([(data[0],data[1])], dtype=dt)
    
    return data

async def temp_data_format(queue : Queue):
    '''
    Pop out one element from the input queue and format it into a structured NumPy array. 
    The array is structured to [timestamp, temp] format.
    
    Args:
        queue: The asyncio fifo Queue that holds the stored data 
    
    Returns:
       temp_data: The np array that holding the temp data.
    
    Example:
        >>> data = await hr_data_format(queue)
        [ 12124,  300]
    '''
    
    data = await queue.get()
    return data
    
async def ecg_from_queue(queue: Queue, save_timestamps: bool = False):
    '''
    Helper function to pop and store all the ecg data from the current queue
    
    Args:
        queue: The asyncio fifo Queue that holds the stored data 
    
    Returns:
       data: The np array that holding the data.
    
    Example:
        >>> data = await get_all_ecg_from_queue(queue)
        [ ,  300]
    '''
    # set up data format
    ecg_data = np.array([],dtype=np.float32)
    timestamps = np.array([], dtype=np.uint32)
    
    while queue.qsize() > 0:
        temp_timestamp, temp_ecg_data = await ecg_data_format(queue)
        ecg_data = np.append(ecg_data, np.array(temp_ecg_data, dtype=np.float32))
        timestamps = np.append(timestamps, np.uint32(temp_timestamp))

        
    if save_timestamps == True:
        return {'timestamps' : timestamps, 'ecg_data' : ecg_data}
    else:
        return ecg_data

