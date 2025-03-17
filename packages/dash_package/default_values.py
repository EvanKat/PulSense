MAGI_REQUEST_TYPES = ["magn", "acc", "gyro", "imu6", "imu6m", "imu9"]
ECG_REQUEST_TYPE = "ecg"
HR_REQUEST_TYPE = "hr"
TEMP_REQUEST_TYPE = "temp"
REQUEST_RATE = ["ecg", "magn", "acc", "gyro", "imu6", "imu6m", "imu9"]
REQUEST_ALL = ["ecg", "hr", "temp", "magn", "acc", "gyro", "imu6", "imu6m", "imu9"]
MAGI_SAMPLE_RATES = [13,26,52,104,208,416,833,1666]
ECG_SAMPLE_RATES = [125,128,200,250,256,500,512]
CON_STATUS = ['CONNECTED','DISCONNECTED']

RAW_PATH = 'storage/0_RAW_ecg_csv/'
CLEAN_PATH = 'storage/1_CLEAN_ecg/'
INTERVALS_PATH = 'storage/2_RR_HR_intervals/'
EDR_PATH = 'storage/3_EDR/'
HRV_PATH = 'storage/4_HRV_indices/'
HRV_NONLIN_PATH = 'storage/6_HRV_nonLinear/'
HRV_ARRYTHMIAS_PATH = 'storage/7_Arrythmias/'
HRV_TIME_PATH = 'storage/4_HRV_time/'
HRV_FREQ_PATH = 'storage/5_HRV_freq/'




