# An example task with parameters provided using an @odop decorator
#
# The implementation of the odop parameter is trivial here and only meant
# to get around the syntax error. Although I think we can expand it to
# implement the task reading functionality.
import sys, yaml
sys.path.insert(1,"/home/nguu0123/git/research/odop/")
sys.path.insert(0,"/home/nguu0123/git/research/odop/odop/odop_obs/")
from odop import task_manager
import time, multiprocessing, threading
from odop_obs import OdopObs

# Function to perform some computation on GPU

@task_manager.odop_task(name="example_task", time="2h", cpu="2", memory="2G", parameter1=1)
def example_task_function(parameter1):
    # The task can be an arbitrary Python function
    print("Running example task, got parameter:", parameter1)
    time.sleep(parameter1)

def heavy_work_process():
    result = sum(x*x for x in range(10**8)) 
    print("Heavy work process done. Result:", result)

def heavy_work_thread():
    result = sum(x*x for x in range(10**7))
    print("Heavy work thread done. Result:", result)

if __name__ == "__main__":
   config = yaml.safe_load(open("../odop_obs/odop_obs_conf.yaml"))
   odop_obs = OdopObs(config)
   odop_obs.start()
   i = 0
   for i in range(0,2):
        processes = []
        for i in range(5):
            p = multiprocessing.Process(target=heavy_work_process)
            processes.append(p)
            p.start()

        threads = []
        for i in range(3):
            t = threading.Thread(target=heavy_work_thread)
            threads.append(t)
            t.start()

        for p in processes:
            p.join()

        for t in threads:
            t.join()
   print("Done!!!")
   odop_obs.stop()
