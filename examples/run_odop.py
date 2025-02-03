# Import Odop itself
import odop

# This imports a simulated main process. Replace this with your actual
# HPC computation.
import odop.simulation

if __name__ == "__main__":
    # Start Odop. This will load task from the task folder and its
    # subfolders.
    odop.start(run_name="run_1", task_folder=".", config_file="odop_conf.yaml")
    # Replace this simulation with your actual computation
    odop.simulation.simulate_cyclical_process()

    # Stop Odop once done
    odop.stop()
