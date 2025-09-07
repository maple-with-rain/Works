import imageio.v3 as iio
import matplotlib.pyplot as plt
import numpy as np

n = 100
gif_path = "test.gif"
saving_path = "pictures/"

n = 100
plt.figure(figsize=(4, 4))
for x in range(n):
    plt.scatter(x / n, x / n)
    plt.xlim(0, 1)
    plt.ylim(0, 1)
    plt.savefig(saving_path + f"{x}.jpg")

frames = np.stack([iio.imread(saving_path + f"{x}.jpg") for x in range(n)], axis=0)

iio.imwrite(saving_path + gif_path, frames)