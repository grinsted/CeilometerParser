# -*- coding: utf-8 -*-
"""
Created on Wed Jul  6 22:04:06 2022

@author: ag
"""

import ceilometer
import matplotlib.pyplot as plt
import numpy as np
from tqdm import tqdm
import xarray as xr
import pandas as pd
import datetime
import os

fname = r"\\10.2.3.1\Public\ceilometer\ceilometer.log.2022-06-26"

sz = os.stat(fname).st_size
N = int(sz/(7657-50)) #This is how much is allocated.

print(f"loading first: {N*3/3600:.1f} hours of {fname}")

V = None
t = []
with open(fname, "r") as f:
    for i in tqdm(range(N)):
        data = ceilometer.parse_next_chunk(f)
        if not data:
            #EOF... so crop data matrix here:
            V=V[:,:i]
            break

        tt = f.readline().rstrip()
        t.append(pd.to_datetime(tt))

        if V is None:
            z = data["z"]
            V = np.empty((len(z), N))

        V[:, i] = data["profile"]


if np.any(np.diff(t)<=datetime.timedelta(seconds=0)):
    print('WARNING: time is not monotonously increasing?? Trying to apply crude fix.')
    t = pd.date_range(t[0], t[-1], periods=V.shape[1])


da = xr.DataArray(V, coords = [z, t], dims = ['z', 'time'])

da.plot.imshow()
# TODO: plot with axes, and flip y-direction.
