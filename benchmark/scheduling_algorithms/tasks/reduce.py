import odop


@odop.task(
    name="reduce_snapshot_data",
    trigger=odop.FileUpdated(
        "/users/anhdungn/pencil-code2/samples/gputest/data/proc0/var.dat"
    ),
    cpus=6,
)
def reduce_snapshot(filenames=None):
    import time

    import numpy as np
    import pencil as pc

    f = pc.read.var()
    uu = f.uu
    aa = f.uu
    timestamp = int(time.time())
    eta = np.random.uniform()
    rho = np.random.uniform()
    uu_xyaver = np.sum(uu, 3)
    aa_xyaver = np.sum(aa, 3)
    g = eta * uu_xyaver - rho * aa_xyaver

    np.save(
        f"/users/anhdungn/pencil-code2/samples/gputest/reduced_data/reduce_data_{timestamp}",
        g,
    )

    print("DONE\n")
