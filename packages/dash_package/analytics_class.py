class AnalyticClass:
    '''

    '''
    # Constractor
    def __init__(self):
        self.csv_file_name = None
        self.request_type = None
        self.rate_type = None
        self.date = None
        self.start_time = None
        # self.pi

    # Save parameters from file name.
    # Input only file_name like 'ecg_2024-04-18_16-50-24_125'
    def set_from_csv(self, file_name):
        self.csv_file_name = file_name

        parameters = file_name.split('_')

        self.request_type = parameters[0]
        self.date = parameters[1]
        self.start_time = parameters[2]
        self.rate_type = parameters[3]
    
    

    
