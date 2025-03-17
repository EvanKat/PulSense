"""
Module Name: movesense_class.py
Description: Contains the class of the bleak device and methods to communicate with it.
"""


#  Imports 
from bleak import BleakClient 
from asyncio import Event, Queue  
# from os.path import exists 
from util_fun import * 
import struct 
# Evan
# TODO: Proccess windows of 16 samples each time or more 
# TODO: Make documentation for the project using sphinx

class BLEClient:
    '''
    The bleak client class (https://bleak.readthedocs.io/en/latest/api/client.html).

    Have the main methods to connect and disconect from a BLE GATT server and communicating with it.

    Args: 
        device_address:
            The MAC addrese of the ble device.
        client:
            The bleak client object
        battery_level:
            The battery level of the device in the range of [0,100]. Need the call of set_battery_level() method to set.
        is_connected:
            Boolean arg representing connection status.
        is_notifying:
            Boolean arg representing notifying status.
        stop_capture_event:
            Asyncio type Event (https://docs.python.org/3/library/asyncio-sync.html#asyncio.Event).
        queue:
            Asyncio type FIFO queue to store capturing data (https://docs.python.org/3/library/asyncio-queue.html).
        case:
            String to hold the request type (ecg, hr, magn imu6, imu6m, imu9) and stop to write null to device 
        hz:
            Integer for the sample rate of each request
        
        TODO: set comments for file storation 
        TODO: Remove file implimentations       
    '''
    # Constractor
    def __init__(self, device_address = None):
        # self.device_address = device_address
        if device_address is not None and is_valid_mac_address(device_address):
            self.device_address = device_address
            self.client = BleakClient(self.device_address)
        else:
            self.device_address = None
            self.client = None 
        self.battery_level = None
        self.is_connected = False
        self.is_notifying = False
        self.stop_capture_event = Event()
        self.queue = Queue()
        self.case = None
        self.hz = None

    def set_device_address(self, device_address : str):
        '''
        Checks if given address is valid and set it to the class
        
        Args:   
            device_address:
                The string conteining the address of the device to connect.

        Returns: 
            True if setted.
        
        Raises:
            ValueError: if address format is wrong.
        '''
        try: 
            if is_valid_mac_address(device_address):
                self.device_address = device_address
                return True
            else:
                raise ValueError("Invalid address format.")
        except Exception as e:
            print(f"set_device_address()_E: {e}")
    
    def get_device_address(self):
        '''
        Returns:
            String with the device's mac address.
        '''
        return self.device_address
    
    
    def set_client(self):
        '''
        Set up the Bleak Client object to the class
        
        Returns: 
            True if setted.

        Raises:
            ValueError: if client allready set.
        '''
        try:
            if not self.client: 
                self.client = BleakClient(self.device_address)
                return True
            else:
                raise ValueError("Client allready set.")
        except Exception as e:
            print(f"set_client()_E: {e}")

    async def get_active_services(self):
        '''
        Gets the collection of GATT services available on the device.

        Returns:
            List of active Bleak services [UUID, Handle No, Name] 

        Raises:
            ValueError: if no device is connected.
        '''
        try:
            if self.client and self.is_connected:
                return self.client.services
            else:
                raise ValueError("Not Connected to any device.")
        except Exception as e:
            print(f"get_active_services()_E: {e}")

    async def set_battery_level(self):
        '''
        Reads and sets the battery level [0,100] of divece using bluetooth's uuid.

        Raises:
            ValueError: if no device is connected.
        '''
        try:
            if self.client and self.is_connected:
                battery_level = await self.read_characteristic(BATTERY_LEVEL_UUID)
                self.battery_level = battery_level[0]
            else:
                raise ValueError("Not Connected to any device.")
        except Exception as e:
            print(f"set_battery_level()_E: {e}")
    
    def get_battery_level(self):
        ''' 
        Returs:
            Battery level
        '''
        if self.client:
            return self.battery_level
 
    # I/O methods
    async def connect(self):
        '''
        Connect to the specified device.
        
        Returns:
            True if connected.

        Raises:
            ValueError: At unsuccessful connection.
            AttributeError: No client specified.
        '''
        if not self.client:
            raise AttributeError("No client specified.")
            
        try:
            await self.client._backend.connect()
            if self.client.is_connected:
                self.is_connected = self.client.is_connected
                return True
            else:
                raise ValueError("Unsuccessful connection.") 
        except Exception as e:
            raise ConnectionError(f"Failed to connect: {str(e)}")
        
    # Disconnect from a gatt server
    # If successful set is_connected property to False and return True 
    async def disconnect(self):
        '''
        Disconnect from the specified device and reset class parameters.

        Returns:
            True if disconection is successful 
        
        Raises:
            ValueError: At unsuccessful connection.
            ValueError: At no client connected.
            AttributeError: No client specified.
        '''
        if not self.client:
            raise AttributeError("No client specified")
        
        if not self.is_connected:
            raise ValueError("No client connected.")

        try:
            if self.case != STOP_REQUEST_TYPE:
                await self.write_characteristic("stop")
                self.case = STOP_REQUEST_TYPE
                self.hz = None

            await self.client.disconnect()

            if not self.client.is_connected:
                self.is_connected = self.client.is_connected
                return True

            else:
                raise ValueError("Unsuccessful disconnection.")

        except Exception as e:
            return ConnectionError(f"Failed to connect: {str(e)}")    


    async def read_characteristic(self, UUID_char):
        '''
        Perform a read operation on a specified characteristic to the connected device.

        Args:
            UUID_char: The UUID characteristic to read from.
        
        Returns: 
            The read data. At movesense case data will be a byte array.
        
        Raises:
            ValueError: No device connection.
            AttributeError: No client specified.
        '''
        try:            
            if self.client:
                if self.is_connected:
                    return await self.client.read_gatt_char(UUID_char)
                else:
                    raise ValueError("No device connection.") 
            else:
                raise AttributeError("No client specified")
        except Exception as e:
            print(f"read_characteristic()_E: {e}")

    async def write_characteristic(self, request = str, hz = int, response = False):
        '''
            Perform a write operation on the specified characteristic to the connected device. Depending on the response can wait for data after the request is made.
            Validates the given request type and set the case of the request type writen to the remote device.

            Args:
                request:
                    String with the wanted type.
                hz:
                    Integer for the wanted sample rate if needed.
                response:
                    Boolean for the write type. If True, will write the data and then wait for a response (request) else will queue the data to be writen (command).

            Returns:
                The data from the response if exists else True if write operation succeeded   

            Raises:
                ValueError: No device connection.
                AttributeError: No client specified.
        '''
        if not self.client:
            raise AttributeError("No client specified")
        
        if not self.is_connected:
            raise ValueError("No device connection.") 

        try:            
            # Set up request
            path = is_valid_request(request, hz)
            if path:
                bytearray_rq =  bytearray([1, 99]) + bytearray(path, "utf-8")
                self.case = request
                self.hz = hz
            elif request.lower() == STOP_REQUEST_TYPE:
                bytearray_rq = bytearray([2, 99])
                self.case = STOP_REQUEST_TYPE
                self.hz = None
            else:
                raise NameError("Wrong request.") 
            
            # set up queue if already used put none 
            if self.queue.qsize() > 0:
                await self.queue.put(None)
            # Write operation
            response_data = await self.client.write_gatt_char(WRITE_CHARACTERISTIC_UUID, bytearray_rq, response=response)
            
            return response_data if response_data else True

        except Exception as e:
            print(f"write_characteristic()_E: {e}")
    
    async def start_notify(self):
        '''
        Activate notifications from the remote device. While notifying, the captured data are handled from the :func:`_notification_handler` method.
        If notifying, parameter is_notifying is set to True.

        Raises:
            ValueError: Allready notifying.
            ValueError: No device connected.
            AttributeError: No client specified.
        '''
        try:            
            if self.client:
                if self.is_connected:
                    if not self.is_notifying:
                        await self.client.start_notify(NOTIFY_CHARACTERISTIC_UUID, self._notification_handler)
                        self.is_notifying = True
                    else:
                        raise ValueError("Allready notifying.")    
                else:
                    raise ValueError("No device connection.") 
            else:
                raise AttributeError("No client specified")
        except Exception as e:
            print(f"start_notify()_E: {e}")

    async def stop_notify(self):
        '''
        Deactivate notifications from the remote device.
        Parameter is_notifying is set to False.

        Raises:
            ValueError: Allready not notifying.
            ValueError: No device connected.
            AttributeError: No client specified.
        '''
        try:            
            if self.client:
                if self.is_connected:
                    if self.is_notifying:
                        await self.client.stop_notify(NOTIFY_CHARACTERISTIC_UUID)
                        self.is_notifying = False
                    else:
                        raise ValueError("Not notifying.")    
                else:
                    raise ValueError("No device connection.") 
            else:
                raise AttributeError("No client specified")
        except Exception as e:
            print(f"stop_notify()_E: {e}")        
    
    async def empty_queue(self):
        '''
        Emptying the asyncio type queue of the class.
        '''
        while not self.queue.empty():
            await self.queue.get()
    
    # Nonification handlers for each method

    async def _notification_handler(self, sender, data : bytearray):
        '''
        The private notification handler for the responsed data. The given data (byte array) are passed to :func:`_proccess_data` to be decoded.
        The decoded data are stored to queue or to file if parameter is_stored is true.
        
        Args:
            sender:
                BLE Device. Used at start notify method.
            data:
                Byte Array with the data to be handled
        '''
        # Decode data
        formated_data = self._proccess_data(data)
        # # Case to store to file
        # # if self.is_stored and self.file_object:
        # if self.is_stored:
        #     if self.case == ECG_REQUEST_TYPE:
        #         self._write_ecg_data_file(formated_data)
        #     else:
        #         self.file_writer.writerow(formated_data)
        # # Case store to queue
        # else:
        #     await self.queue.put(formated_data)
        await self.queue.put(formated_data)
    
    def _proccess_data(self, data):
        '''
        Check the current request case and decode given data

        Args:
            data:
                Byte Array containg the data to be decoded

        Returns:
            formated_data:
                The decoded data. 
        '''
        # Temperature
        if self.case == TEMP_REQUEST_TYPE:
            if len(data) == 10:
                formated_data = self._temp_data_handler(data)
        # Heart rate and RR interval
        elif self.case == HR_REQUEST_TYPE:
            formated_data = self._hr_data_handler(data)
        # ECG 
        elif self.case == ECG_REQUEST_TYPE:
            formated_data = self._ecg_data_handler(data)
        # MAGI format
        else:
            formated_data = self._magi_data_handler(data)
        
        return formated_data
    
    def _magi_data_handler(data : bytearray):
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

    def _ecg_data_handler(data : bytearray):
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

    def _hr_data_handler(data : bytearray):
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

    def _temp_data_handler(data : bytearray):
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


