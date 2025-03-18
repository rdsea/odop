import time

import odop

N = 500


def test_start(runtime=5):
    odop.start(
        config_file="tests/odop_conf.yaml",
        task_folder="examples/example_tasks",
    )
    time.sleep(runtime)
    odop.stop()


if __name__ == "__main__":
    test_start(N)
