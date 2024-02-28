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
import torch

@task_manager.odop_task(name="example_task", time="2h", cpu="2", memory="2G", parameter1=1)
def example_task_function(parameter1):
    # The task can be an arbitrary Python function
    print("Running example task, got parameter:", parameter1)
    time.sleep(parameter1)

@task_manager.odop_task(name="heavy_work_process", time="10s", cpu="1", memory="1G", parameter1=1)
def heavy_work_process():
    result = sum(x*x for x in range(10**8)) 

@task_manager.odop_task(name="heavy_work_thread", time="5s", cpu="1", memory="1G", parameter1=1)
def heavy_work_thread():
    result = sum(x*x for x in range(10**7))

def gpu_computation():
    start = time.time()
    ndim = 20000
    random1 = torch.randn([ndim, ndim]).to("cuda")
    random2 = torch.randn([ndim, ndim]).to("cuda")
    while time.time() - start < 0.5 * 60:
        random1 = random1 * random2
        random2 = random2 * random1
    del random1, random2
    torch.cuda.empty_cache()

if __name__ == "__main__":
   config = yaml.safe_load(open("../odop_obs/odop_obs_conf.yaml"))
   odop_obs = OdopObs(config)
   odop_obs.start()
   i = 0
   for i in range(0,20):
        #print(gpu_computation())
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
        time.sleep(10)
   print("Done!!!")
   odop_obs.stop()
