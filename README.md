
# PulSense
**An AI-Driven Cardiovascular Monitoring and Arrhythmia Detection System**

A proposed project on heart monitoring for my thesis at the ECE Department, Technical University of Crete [[1]](#1).

---

## Getting Started

### Installation
First, install the necessary dependencies by running:

```bash
pip install -r requirements.txt
```

### Usage

1. **Connect to a Movesense Device and Capture ECG Data**  
   To connect to a Movesense device, capture raw ECG data, and process it, run:

   ```bash
   python manage.py
   ```

2. **Display Processed Data**  
   To display the processed data, use:

   ```bash
   python analytics.py
   ```

### Troubleshooting

- **No Movesense Device Available?**  
  If a Movesense device is not available, and you need to run `manage.py`, modify the code as follows:
  - **Uncomment** the `hl.*` methods.
  - **Comment** the referring `mv_blk.*` methods.

### Limitations

- Currently, the `manage.py` application can only connect to one Movesense device and process ECG data.
- The application might sometimes be a bit buggy, so please report any issues you encounter.

---

## TODO
- Update the project documentation and improve stability.

## References
<a id="1">[1]</a> 
Evangelos Katsoupis, "Development of a cardiovascular disease monitoring system", Diploma Work, School of Electrical and Computer Engineering, Technical University of Crete, Chania, Greece, 2024 https://doi.org/10.26233/heallink.tuc.100510

<a id="2">[2]</a>
E. Katsoupis, A. Karasmanoglou, M. Zervakis and M. Antonakakis, "Pulsense: An AI-Driven Cardiovascular Monitoring and Arrhythmia Detection System," 2024 IEEE 24th International Conference on Bioinformatics and Bioengineering (BIBE), Kragujevac, Serbia, 2024, pp. 1-8, https://doi.org/10.1109/BIBE63649.2024.10820493
