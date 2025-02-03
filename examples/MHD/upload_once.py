import subprocess

import odop


@odop.task(name="Upload_data_to_Allas", max_runs=1)
def main():
    result = subprocess.run(
        "swift upload 2009846-test /users/anhdungn/pencil-code2/samples/gputest/reduced_data",
        shell=True,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.stderr:
        print("Error:", result.stderr)


if __name__ == "__main__":
    main()
