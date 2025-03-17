import neurokit2 as nk
import numpy as np
from pickle import load as pkl_load
import pywt
import cv2




# wavelet = "mexh"  # mexh, morl, gaus8, gaus4
# cwt_parameters = {
#           'wavelet'   : wavelet,
#           'scales'    : pywt.central_frequency(wavelet) * data['rate'] / np.arange(1, 256, 1),
#           'sampling_period' : 1/data['rate']
# }


# cwt_parameters = {
#           'wavelet'   : "mexh",
#           'scales'    : np.array
#           'samplin_period' : 1/sample_rate
# }


def worker_ecg_to_cwt(ecg_cleaned:np.array,
                        sample_rate:int,
                        r_peaks_index:np.array,
                        cwt_parameters: dict, 
                        scaler):
    # peak detaction methods
    # https://neuropsychology.github.io/NeuroKit/functions/ecg.html#ecg-peaks
    
    # to_clean methods
    # https://neuropsychology.github.io/NeuroKit/functions/ecg.html#ecg-clean
    # ['neurokit','biosppy', 'pantompkins1985', 'hamilton2002', 'elgendi2010', 'engzeemod2012', 'vg'] personal vg
    
    # print(data.keys())
    # Take data and manage parameters
    ecg_sig = ecg_cleaned*1000
    sample_rate = sample_rate

    rpeaks_indexes = r_peaks_index
    # Compute CWT
    
    # heartbeat segmentation intervals udjasted by the sampling rate
    before = np.round(sample_rate / 4).astype(np.int64)
    after = np.round( (11 * sample_rate) / 36 ).astype(np.int64)
    # before = 90
    # after = 110

    coeffs, frequencies = pywt.cwt(ecg_sig, cwt_parameters['scales'], cwt_parameters['wavelet'], cwt_parameters['sampling_period'])
    r_peaks = rpeaks_indexes

    # for remove inter-patient variation
    avg_rri = np.mean(np.diff(r_peaks))

    x1, x2 = [], []
    for i in range(len(r_peaks)):
        if i == 0 or i == len(r_peaks) - 1:
            continue

        # cv2.resize is used to sampling the scalogram to (100 x100)
        x1.append(cv2.resize(coeffs[:, r_peaks[i] - before: r_peaks[i] + after], (100, 100)))
        x2.append([
            r_peaks[i] - r_peaks[i - 1] - avg_rri,  # previous RR Interval
            r_peaks[i + 1] - r_peaks[i] - avg_rri,  # post RR Interval
            (r_peaks[i] - r_peaks[i - 1]) / (r_peaks[i + 1] - r_peaks[i]),  # ratio RR Interval
            np.mean(np.diff(r_peaks[np.maximum(i - 10, 0):i + 1])) - avg_rri  # local RR Interval
        ])
    
    # Normalize r_peaks data to according to the trained data from mitdb
    x2 = np.array(x2,dtype=np.float32)
    x2_normalized = scaler.transform(x2)
    
    # Reshape coeffs for model
    x1 = np.array(x1,dtype=np.float32)
    x1 = x1[:, np.newaxis]
    


    return x1, x2_normalized, r_peaks[1:-1]