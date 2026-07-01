# mptcp-perf
This repository contains the entire codebase used for assessing the impact of packet scheduling and congestion control algorithms on MPTCP performance.

The respective manuscript depicting the assessment is titled: "_Evaluating the Impact of Packet Scheduling and Congestion Control Algorithms on MPTCP performance over Heterogeneous Networks_".

Repository structure:

```text
.
├── analysis
│   └── analysis_auto_new.py                        # Analyse the resulting files produced by the test execution phase 
├── iperf                                           # All files needed for test execution 
│   ├── control_minimal_iperf_auto.py               # Control script for the execution of the test scenarios in the mininet environment
│   ├── iperf3_client.py
│   ├── iperf3_server.py
│   ├── mininetenv_iperf.py                         # Mininet environment setup
│   └── test_config.csv                             # .csv file containing the set of tests to be executed (29 unique test scenarios)
├── LICENSE                                         # GPLv3 License text
├── README.md                                       # Project overview (this file)
├── Supplementary_material_Algorithms.pdf           # Contains pseudo-code of the assessed packet scheduling and congestion control algorithms
└── visualization
    └── testplot.ipynb                              # Jupyter notebook including the functions used to render the plots/figures. 

```

## Citation

If you use this software or the associated methodology in your research, please cite the software:


### Software Codebase
> Dimopoulos, D. (2026). MPTCP-performance-evaluation (Version 0.1) [Computer software]. GitHub repository: [https://github.com/ddimopou/mptcp-perf](https://github.com/ddimopou/mptcp-perf)

### BibTeX
```bibtex

@software{mptcp_perf_2026,
  author       = {Dimopoulos, Dimitris},
  title        = {MPTCP-performance-evaluation: Version 0.1},
  month        = jun,
  year         = {2026},
  publisher    = {GitHub},
  url          = {https://github.com/ddimopou/mptcp-perf}
}
```