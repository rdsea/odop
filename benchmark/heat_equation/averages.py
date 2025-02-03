import matplotlib.pyplot as plt
import numpy as np

import odop


def compute_avg(data: np.ndarray):
    return np.sum(data) / np.prod(data.shape)


def compute_min(data: np.ndarray):
    return np.min(data)


def compute_max(data: np.ndarray):
    return np.max(data)


def compute_min_loc(data: np.ndarray):
    return np.unravel_index(np.argmin(data, axis=None), data.shape)


def compute_max_loc(data: np.ndarray):
    return np.unravel_index(np.argmax(data, axis=None), data.shape)


def print_stats(data: np.ndarray):
    print(
        str(compute_min(data))
        + ", "
        + str(compute_max(data))
        + ", "
        + str(compute_avg(data))
    )


def plot_temp(data: np.ndarray):
    min_loc = compute_min_loc(data)
    max_loc = compute_max_loc(data)
    plt.imshow(data)
    plt.plot(min_loc[0], min_loc[1], "wo")
    plt.plot(max_loc[0], max_loc[1], "ro")
    plt.show()


@odop.task(
    name="output_stats",
    time="10s",
    memory="1G",
    priority=10,
    trigger=odop.FileIn("data", filter=".*.txt"),
)
def output_stats(filename: str):
    # Read the comma separated temperature data from the file
    # (last column will be empty due to the trailing comma)
    data = np.loadtxt(filename, delimiter=",")
    with open("stats.txt", "a") as f:
        f.write(
            f"{filename}: {compute_min(data)}, {compute_max(data)}, {compute_avg(data)}\n"
        )


def main():
    data = np.loadtxt("data/heat_1000.png.txt", delimiter=",")
    print_stats(data)


if __name__ == "__main__":
    main()
