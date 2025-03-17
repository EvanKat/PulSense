# import csv
import struct
import numpy as np
from json import dumps
from bleak import BleakScanner
from re import match as re_match
from asyncio import Queue
from .constants import * 
from os.path import exists 
import datetime

# from .constants import (
#     DEVICENAME,
#     VOLTS_PER_LSB,
#     MAGI_REQUEST_TYPES,
#     MAGI_SAMPLE_RATES,
#     ECG_REQUEST_TYPE,
#     ECG_SAMPLE_RATES,
#     HR_REQUEST_TYPE
#     )


def open_csv(path:str):
    '''
    Create or/and open a csv file. 
    
    Args:
        path (str): Path of the file

    Returns:
        [writer, object]: The csv_writer and and file object

    Example:
        >>> [file_writer, file_object] = open_csv("path/to/file.csv")
    '''
    try:
        file_object = open(path, mode="w") 
        cvs_writer = csv.writer(file_object, lineterminator="\n")
        return [cvs_writer, file_object] 
    except Exception as e:
        print(f"open_csv()_E: {e}")

def close_csv(file_object = None):
    '''
    Closes the given csv file object for loccking prevent and resource management.
    Also checks if the object has an close attribute
    
    Args:
        file_object (str): the return type of a open() function

    Returns:
        True: The file object successfully closed

    Example:
        >>> bool = close_csv(file_object)
    '''
    try:
        if not file_object:
            if callable(getattr(file_object, "close", None)):
                file_object.close()
                return True
            else:
                raise ValueError("No file input.")
    except Exception as e:
        return e

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

def magi_data_handler(data : bytearray):
    '''
    Takes a byte array and reads its length. The lenght will be a multiple of 3 plus 6.
    Bytes 2:6 is the timestamp and for the bytes 6:end, eatch data will in a group of four
    The MagnAccGyroImuxx (MAGI) handler is used by the notification handler and returns data 
    to [timestamp, xn, yn, zn] format   

    Args:
        data: Bytearray to unpack
    
    Returns:
        list: A list with the timestump and xn,yn,zn data

    Examples:
        >>> $ Data length of 18 
        >>> magi_data_handler(data)
        (123, 1.25, 12.4, -2.01)
    '''
    timestamp = struct.unpack('<I', data[2:6])[0]
    x = [timestamp]
    # To access its x,y,z for each sample
    for index in range( int( (len(data) - 6) / 4) ):
        start = index * 4 + 6
        end = index * 4 + 10
        x.append(struct.unpack('<f', data[start:end])[0])  
    return x

def ecg_data_handler(data : bytearray):
    '''
    Unpack a bytearray to timestamp (bytes 2:6) and to 16 samples of 4 bytes (bytes 6:70)
    Bytes 2:6 is the timestamp and for the bytes 6:end, eatch data will in a group of four. 
    Each sample is multiplied by the VOLTS_PER_LSB constant (~= 3.81e-7) to represent a real value. 
    The ElectroCardioGram (ECG) handler is used by the notification handler and returns data 
    to [timestamp, s1, ..., s16] format.

    Args:
        data: Bytearray to unpack
    
    Returns:
        list: A list with the timestump (uint milisecond) and s1, ..., s16 data (float number)

    Examples: 
        >>> ecg_data_handler(data)
        (123, s1, ..., s16)
    '''

    timestamp = struct.unpack('<I', data[2:6])[0]
    x = [timestamp]
    # To access its x,y,z for each sample
    for index in range(16):
        sample = VOLTS_PER_LSB * struct.unpack('<i', data[(index*4 + 6):(index*4 + 10)])[0]
        x.append(sample)
    return x

def hr_data_handler(data : bytearray):
    '''
    Unpack a bytearray to average beat rate (bytes 2:6) and to interval between beats rates (RR-interval)
    (bytes 6:8). Average is a float number and RR is an uint number 
    The Heart Rate (ECG) handler is used by the notification handler and returns data 
    to [beat_rate, interval] format.

    Args:
        data: Bytearray to unpack
    
    Returns:
        list: A list with the average beat_rate(float number), and interval (uint milisecond)

    Examples: 
        >>> hr_data_handler(data)
        [75.2 ,  798]
    '''

    heart_rate = struct.unpack('<f', data[2:6])[0]
    RR_interval = struct.unpack('<H', data[6:8])[0]
    return [heart_rate, RR_interval]

def temp_data_handler(data : bytearray):
    '''
    Unpack a bytearray to timestamp (bytes 2:6) and to internal devise temperature (bytes 6:10).
    Timestamp is a uint number and temperature is float. 
    The TEMPerature (TEMP) handler is used by the notification handler and returns data 
    to [timestamp, temp] format.

    Args:
        data: Bytearray to unpack
    
    Returns:
        list: A list with the timestamp (uint number), and temerature (float number) in kelvin

    Examples: 
        >>> temp_data_handler(data)
        [1225 ,  300]
    '''
    timestamp = struct.unpack('<I', data[6:10])[0]
    temp = struct.unpack('<f', data[2:6])[0] 
    return [timestamp, temp]

# To check if request format is correct
# If correct return path to write
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


# TODO Make comments for data format methods at util_fun.py
# TODO Remove general comments
# TODO Discase on how to read data from queue. One by one or all of it?

async def magi_data_format(queue : Queue()):
    # If no elements to read
    # if queue.qsize() == 0:
    #     return None
    
    # Read queue and return data 
    # [timestamp, [xn,yn,zn]]
    dt = np.dtype([('timestamp', np.uint32), ('elements', np.ndarray)])
    magi_data = np.array([], np.ndarray)
    
    data = await queue.get()
    if data is None:
        return None
    else:
        data_xyz = np.array(data[1:], dtype = np.float32)
        full_data = np.array([ ( data[0], data_xyz )], dtype = dt)
        magi_data = np.append(magi_data, full_data)  

    # To read and return data until None

    # while True:
    #     data = await queue.get()
    #     if data is None:
    #         break
    #     else:
    #         data_xyz = np.array(data[1:], dtype = np.float32)
    #         full_data = np.array([ ( data[0], data_xyz )], dtype = dt)
    #         magi_data = np.append(magi_data, full_data)  

    return magi_data

async def ecg_data_format(queue : Queue()):
    # Empty queue and return data
    ecg_data = np.array([], dtype = np.float32)
    start_time = None

    data = await queue.get()
    if data is None:
        return data
    else:
        if not start_time:
            start_time = data[0]
            # multiply data
        ecg_data = np.array(data[1:])

    # while True:
    #     data = await queue.get()
    #     if data is None:
    #         break
    #     else:
    #         if not start_time:
    #             start_time = data[0]
    #             # multiply data
    #         ecg_data = np.concatenate( (ecg_data, np.array(data[1:])) )
    return [start_time, ecg_data]

async def hr_data_format(queue : Queue()):
    dt = np.dtype([ ('beat_rate', np.float32), ('RR_int', np.uint16)])
     
    data = await queue.get()
    if data is None:
        return data
    else:
        # data = np.array([(data[0],data[1])], dtype = dt)
        data = np.array([(data[0],data[1])], dtype=dt)
        # print(data)
        # print(type(data))
        # hr_data = np.append(hr_data, data)
        # print(hr_data)
    return data

    # # Empty queue and return data
    # dt = np.dtype([ ('beat_rate', np.float32), ('RR_int', np.uint16)])
    # # hr_data = np.array([(0.0,0)], dtype = dt)
    # hr_data = np.array([], dtype=dt)

    # while True:
    #     data = await queue.get()
    #     if data is None:
    #         break
    #     else:
    #         # data = np.array([(data[0],data[1])], dtype = dt)
    #         data = np.array([(data[0],data[1])], dtype=dt)
    #         # print(data)
    #         # print(type(data))
    #         hr_data = np.append(hr_data, data)
    #         # print(hr_data)
    # return hr_data

async def temp_data_format(queue : Queue):
    data = await queue.get()
    return data
    

# def set_file(file_path : str = None, request_case : str = None, rate = None ):
#     '''
#     Check for given path if exists and create file name. Also creates the format of the data to write. 
#     Args: 
#         file_path:
#             Path to file. If none then is DEFAULT_FILE_PATH else check if exists.
#         request_type:
#             The request type to set the header if exists.
#         rate:
#             Sampling rate.


#     Return:
#         data to write, file name
            

#     TODO: Set multiple case for requests and file name

#     ''' 

#     current_datetime = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    
#     type = "foo"

#     if request_case == "ecg":
#         type = "ECG mVolts"
    
#     # Constract Data format
#     data = {
#         "type" : type,
#         "date" : current_datetime,
#         "rate" : rate,
#         "data" : [0]
#     }
    
#     # Check Path
#     if file_path and exists(file_path):
#         path = file_path
#     else:
#         path = DEFAULT_FILE_PATH
    
#     file_name = f"{path}ecg.json"

#     with open(file_name, 'w') as file:
#         file.write(dumps(data))
    
#     return file_name



# async def store_to_file(queue:Queue, file_name:str):
#     '''
#     Read queue's data, proccess the format and store data to a file.
#     Args:
#         queue:
#             Asyncio FIFO queue with the  data to store
#         path:
#             Path to file string. If None path will be DEFAULT_FILE_PATH else the given.
#     '''
#     # Queue will be increasing so store amount of data to store
#     amount = queue.qsize()
#     # print(amount)
#     current_amount = 0
#     # Get queue data an store them to file
#     while current_amount < amount:
#         with open(file_name, mode='r+') as file:
#             # Go to end
#             file.seek(0,2)
#             # Seek possition to store data
#             position = file.tell() - 2

#             # Seek possition to see if first entry
#             # pos = file.tell() - 3
#             # file.seek(pos)
#             # deli = file.read()

#             file.seek(position)
           
#             queue_data = await queue.get()
#             # print(queue_data)
#             current_amount += 1
#             data = ""
#             for element in queue_data[1:]:
#                 data = f"{data},{np.float32(element)}"
                
#             file.write(data + "]}")


async def get_data_from_queue(queue: Queue):
    # get current queue lenght
    queue_len = queue.qsize()
    # print(queue.qsize())
    queue_data = np.array([], dtype=np.float32)

    while queue_len > 0:
        # no need to wait
        temp = await ecg_data_format(queue)
        queue_data = np.append(queue_data,temp[1])
        queue_len-=1
    # np array
    # print(queue.qsize())
    return queue_data


# async def is_queue_empty(queue: Queue):
#     # get current queue lenght
#     queue_len = queue.qsize()
    
#     queue_data = np.array([], dtype=np.float32)


#     while queue_len > 0:
#         # no need to wait
#         temp = await ecg_data_format(queue)
#         queue_data = np.append(queue_data,temp[1])
#         queue_len-=1
#     # np array
#     return queue_data