"""
Constants Module

This module contains constants used throughout the application.

Constants:
    - DEVICENAME (str): 
        The name of the device we will connect.
    - WRITE_CHARACTERISTIC_UUID (str): 
        A movesense UUID indicating data writing to a gatt server.
    - NOTIFY_CHARACTERISTIC_UUID (str):
        A movesense UUID indicating the recieving of notifications from a gatt server.
    - BATTERY_LEVEL_UUID (str):
        A Bluetooth UUID indicating the request for battery level from a gatt server.
    - MAGI_REQUEST_TYPES (list):
        A list of strings containing the MAGI requests types. 
        MAGI can be Magnetometer, Acceleometer, Gyroscope, Inertial Measurement Units.
        IMU can be IMU6 for acc and gyro, IMU6m for acc and magn, IMU9 for all three 
    - ECG_REQUEST_TYPE (str): A string containing the ecg type.
    - HR_REQUEST_TYPE (str): A string containing the heart rate type.
    - TEMP_REQUEST_TYPE (str): A string containing the temperature type.
    - PATH (str): A string containing the starting format of a request.
    - STOP_REQUEST_TYPE (str): A string containing the stop type.
    - MAGI_SAMPLE_RATES (list): A list of ints containing the accepted sample rates for MAGI.
    - ECG_SAMPLE_RATES (list): A list of ints containing the accepted sample rates for ECG.
    - VOLTS_PER_LSB (float): The number to multiply the sensors ecg samples to simulate real voltage.  
    - DEFAULT_FILE_PATH (str): A string containing the default path of the csv file if data will be stored to file.
"""

DEVICENAME = 'Movesense'
WRITE_CHARACTERISTIC_UUID = "34800001-7185-4d5d-b431-630e7050e8f0"
NOTIFY_CHARACTERISTIC_UUID  = "34800002-7185-4d5d-b431-630e7050e8f0"
BATTERY_LEVEL_UUID = "00002a19-0000-1000-8000-00805f9b34fb"
MAGI_REQUEST_TYPES = ["magn", "acc", "gyro", "imu6", "imu6m", "imu9"]
ECG_REQUEST_TYPE = "ecg"
HR_REQUEST_TYPE = "hr"
TEMP_REQUEST_TYPE = "temp"
PATH = "/meas/"
STOP_REQUEST_TYPE = "stop"
MAGI_SAMPLE_RATES = [13,26,52,104,208,416,833,1666]
ECG_SAMPLE_RATES = [125,128,200,250,256,500,512]
VOLTS_PER_LSB = 1.0 / 20.0 / (1 << 17)
DEFAULT_FILE_PATH = "./data_storage/" 