# Benchmarking different scheduling algorithms

## Setup

- Fixed node and MHD parameter:

  - 2 node, 8 tasks
  - MHD parameter, this parameter will run for 15 mins:

  ```in
  nt=1199, it1=40, isave=200, itorder=3,
  !nt=21, it1=1, isave=100, itorder=3

  cdt=0.4, cdtv=0.3, dtmin=1e-6, dt=1.e-6

  dspec=150e-6, vel_spec=T, ab_spec=T

  dvid=1e-5

  !dsnap=8e-5
  ```

## Algorithm tested

1. Best fit
2. Fifo
3. Priority
4. Round robin
