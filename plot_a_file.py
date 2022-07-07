# -*- coding: utf-8 -*-
"""
Created on Wed Jul  6 22:04:06 2022

@author: ag
"""

import ceilometer
import matplotlib.pyplot as plt
import numpy as np
from tqdm import tqdm

fname = r"\\10.2.3.1\Public\ceilometer\ceilometer.log.2022-06-28"

N = 10000
print(f"loading first: {N*3/3600:.1f} hours of {fname}")


# TODO: add it to an xarray instead!
V = None
t = []
with open(fname, "r") as f:
    for i in tqdm(range(N)):
        chunk = ceilometer.read_next_chunk(f)
        data = ceilometer.parse_ceilometer_chunk(chunk)
        tt = f.readline().rstrip()
        t.append(np.datetime64(tt))

        if V is None:
            z = data["z"]
            V = np.empty((len(z), N))

        V[:, i] = data["profile"]

plt.imshow(V)
# TODO: plot with axes, and flip y-direction.
