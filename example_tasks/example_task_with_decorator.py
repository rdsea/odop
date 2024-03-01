# An example task with parameters provided using an @odop decorator
#
# The implementation of the odop parameter is trivial here and only meant
# to get around the syntax error. Although I think we can expand it to
# implement the task reading functionality.
import sys, yaml,os, argparse
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
from odop import task_manager
import time, multiprocessing, threading
from odop_obs.odop_obs import OdopObs

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

if __name__ == "__main__":
   parser = argparse.ArgumentParser()
   parser.add_argument(
       "-c", "--config", help="config path", default="./odop_obs_conf.yaml"
   )
   args = parser.parse_args()
   config_file = args.config
   config = yaml.safe_load(open(config_file))
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
