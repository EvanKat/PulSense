import asyncio
import csv

class ConnectionStatus:
    '''
    A simple class that holds the connection status and variables for the app and the sensor.

    Args: 
        is_connected:
            Bool arg that holds the current connection status.
        is_notifiyng:
            Bool arg that holds the current notification status.
        # device_name:
        #     String arg that holds the selected device name to connect.
        mac_address:
            String arg that holds the selected mac address to connect.
        request_type:
            String arg representing the selected request type.
        rate_type:
            String arg representing  the selected rate type.
    '''
    # Constractor
    def __init__(self):
        self.is_connected = False
        self.is_notifiyng = False
        self.is_requested = False
        self.is_saving_to_file = False
        self.is_correct_req = False        
        self.file_name = None
        self.file_path = None
        # self.device_name = None
        self.mac_address = None
        self.request_type = None
        self.rate_type = None
        self.loop = None
        self.to_create_analitycs = False
    
    def reset_class(self):
        self.is_connected = False
        self.is_notifiyng = False
        self.is_requested = False
        self.is_saving_to_file = False
        self.is_correct_req = False        
        self.file_name = None
        self.file_path = None
        # self.device_name = None
        self.mac_address = None
        self.request_type = None
        self.rate_type = None
        self.loop = None
        self.to_create_analitycs = False



    def set_file_path (self, file_name, file_path):
        self.file_name = file_name
        self.file_path = file_path
        print(file_name)
        print(file_path)
        # return  self.file_name, self.file_path


    def set_mac(self, mac : str):
        '''
        Set the mac address

        Args:   
            mac:
                The string taht holds the address of the requested mac address.
        Returns: 
            True if setted or Value error.
        Raises:
            ValueError: if address is not setted.
        '''

        try: 
            if mac:
                self.mac_address = mac
                return True
            else:
                raise ValueError("Invalid address.")
        except Exception as e:
            return e
    
    def set_request(self, request : str):
        '''
        Set the request type. For simplicity if the request tyoe changes, the rate is setted to None

        Args:   
            request:
                The string that holds the address of the requested mac address.
        Returns: 
            True if setted or Value error.
        Raises:
            ValueError: if address is not setted.
        '''

        try: 
            if request:
                self.request_type = request
                self.rate_type = None
                return True
            else:
                raise ValueError("Invalid request.")
        except Exception as e:
            return e

    def set_rate(self, rate : str):
        '''
        Set the request type. For simplicity if the request tyoe changes, the rate is setted to None

        Args:   
            request:
                The string that holds the address of the requested mac address.
        Returns: 
            True if setted or Value error.
        Raises:
            ValueError: if address is not setted or requested is not setted.
        '''

        try: 
            if self.request_type:
                if rate:
                    self.rate_type = rate
                    return True
                else:
                    raise ValueError("Request is not setted")    
            else:
                raise ValueError("Invalid rate.")
        except Exception as e:
            return e
    
    # def set_full_request(self, full_request : str):
    #     '''
    #     to remove later on. Is used for visual propuses only. 
    #     '''
    #     self.current_full_request = full_request
        

    def change_connection_status(self):
        '''
        Change the connection status

        Returns: 
            The new connection status (is_connected).
        '''
        self.is_connected = not self.is_connected
        return self.is_connected
    
    def change_notification_status(self):
        '''
        Change the notification status

        Returns: 
            The new notification status (is_notifying).
        '''
        self.is_notifiyng = not self.is_notifiyng
        return self.is_notifiyng
    
    def change_saving_to_file(self):
        '''
        Change the saving status

        Returns: 
            The new notification status (is_notifying).
        '''
        self.is_saving_to_file = not self.is_saving_to_file
        return self.is_saving_to_file