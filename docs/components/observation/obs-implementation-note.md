# OBS Implementation Notes
## Embedded database

- Current choice: tinyinflux - tiny document-based time series database
- Pros:

  - Tiny
  - Time series database is more suitable for metrics datatype
  - Already have in-memory storage and persistent storage

- Cons:
  - Can't be access from multiple process and thread
  - Query slow down as the size of dataset grows
  - Missing some core functionality: retention policy

## Probe Utils

1. CPU, Memory: currently using psutil but have encountered some problems:

- Getting the child process is slow and costly
- Metric calculation can be different on diffrerent architecture/Os (as Tri said)

2. GPU: currently only support Nvidia GPU by using pynvml - a python wrapper for Nvidia Management Library (NVML). Problems encountered:

- Higher memory usage
- Slow init time

## Probe and Local exporter

1. Communication method: local socket for an easy implementation, the latency is sub milisecond but still be optimized more by other techniques (shared memory, pipe)
2. API: currently using FastAPI with uvicorn, the latency and memory is comparable to Falcon framework

## Performance:

1. Latency(p99) in ms:

- Sending report from probe to exporter: 0.22
- Process metric: 12.244
- System metric: 0.82
- Before pydantic:

    | Operation                          |   Average |       P99 |       Min |      Max |
    |------------------------------------|-----------|-----------|-----------|----------|
    | report_latency                     |  0.282406 |  0.941594 | 0.0486374 |  1.08504 |
    | calculating_process_metric_latency | 10.5623   | 14.0485   | 4.30012   | 14.462   |
    | calculating_system_metric_latency  |  0.567949 |  1.47648  | 0.203371  |  1.65439 |
- After pydantic: sending raw pydantic object seems to hurt the performance
    | Operation                          |   Average |      P99 |       Min |      Max |
    |------------------------------------|-----------|----------|-----------|----------|
    | report_latency                     |  0.354276 |  1.01577 | 0.0607967 |  1.43266 |
    | calculating_process_metric_latency |  9.05714  | 12.6678  | 4.12917   | 14.339   |
    | calculating_system_metric_latency  |  0.545169 |  1.33612 | 0.23675   |  1.82867 |
- Test on mahti:
    | Operation                          |   Average |      P99 |       Min |      Max |
    |------------------------------------|-----------|----------|-----------|----------|
    | report_latency                     |  0.273594 | 2.22106  | 0.056982 |  2.23613 |
    | calculating_process_metric_latency |  69.2098  | 86.9995  | 54.2936   | 87.4531   |
    | calculating_system_metric_latency  |  2.88274  |  4.48537 | 2.58803    |  4.53019 |
- Mostly IO bound operation (reading from /proc) so quite hard to optimize
2. Memory usage:
- Total: after pydantic:56mb
- Process probe: applying dynamic loading 
  - HPC env: 15M Res, 106M Virt
  - Other: 24M Res, 116M Virt
- System probe: applying dynamic loading 
  - HPC env: 19M Res, 113M Virt
  - Other: 28M Res, 124M Virt
- Exporter:

3. Pydantic 

|                               | Process report size(bytes) | System report size(bytes) |   |
|-------------------------------|----------------------------|---------------------------|---|
| Directly dumps pydantic model | 600                        | 800                       |   |
| Convert to dict               | 300                        | 500                       |   |
## Probe, Aggregator, Exporter 
- When I test with the probe in the same process as the main process, the latency can goes higher than the reporting frequency when the cpu is too full => everything run in a differen process from the main process

## Monitoring CPU load in hyper-threading (Intel) and SMT (AMD)
Insightful article: [Monitoring CPU Utilization Under hyper-threading](http://perfdynamics.blogspot.com/2014/01/monitoring-cpu-utilization-under-hyper.html)

Indepth article: [Performance Insight to Inter Hyper-threading](https://web.archive.org/web/20100810110350/http://software.intel.com/en-us/articles/performance-insights-to-intel-hyper-threading-technology/)

In short, cpu utilization given from the OS is not reliable and doesn't describe the true physical core load: the reported CPU utilization is 50% even though the application can use up to 70%-100% of the execution units (physical core)

