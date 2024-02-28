# Embedded database

- Current choice: tinyinflux - tiny document-based time series database
- Pros:

  - Tiny
  - Time series database is more suitable for metrics datatype
  - Already have in-memory storage and persistent storage

- Cons:
  - Can't be access from multiple process and thread
  - Query slow down as the size of dataset grows
  - Missing some core functionality: retention policy

# Probe Utils

1. CPU, Memory: currently using psutil but have encountered some problems:

- Getting the child process is slow and costly
- Metric calculation can be different on diffrerent architecture/Os (as Tri said)

2. GPU: currently only support Nvidia GPU by using pynvml - a python wrapper for Nvidia Management Library (NVML). Problems encountered:

- Higher memory usage
- Slow init time

# Probe and Local exporter

1. Communication method: local socket for an easy implementation, the latency is sub milisecond but still be optimized more by other techniques (shared memory, pipe)
2. API: currently using FastAPI with uvicorn, the latency and memory is comparable to Falcon framework

# Performance:

1. Latency(p99) in ms:

- Sending report from probe to exporter: 0.22
- Process metric: 12.244
- System metric: 0.82

2. Memory usage:

- Process probe:
- System probe:
- Exporter:

# Probe, Aggregator, Exporter 
- When I test with the probe in the same process as the main process, the latency can goes higher than the reporting frequency when the cpu is too full => everything run in a differen process from the main process
