## Build the C++ code

### LUMI

```bash
make -C solver
```

### Mahti

```bash
ml gcc/13.1.0
ml openmpi/4.1.5

make -C solver
```

## Running the simulation

`main.py` calls the C++ heat equation solver.
After running the heat equation solver, you'll have png images in the directory `pngs`.

### LUMI

```bash
ml cray-python
srun -n 4 -t 00:01:00 -p debug -A project_..... python main.py
```

### Mahti

```bash
ml python-data/3.10-24.04
srun -n 4 -t 00:01:00 -p test -A project_..... python main.py
```

## The opportunistic tasks
`averages.py` contains some data reductions and an odop tasks definition.

Didn't get it running yet on LUMI as it has a dependecy on `matplotlib`.
