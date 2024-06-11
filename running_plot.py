# -*- coding: utf-8 -*-
"""
Created on Tue Jul  5 21:34:15 2022

@author: ag
"""


import socket
import ceilometer

# from pprint import pprint
import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter

# from matplotlib.patches import Rectangle
# from matplotlib.ticker import MultipleLocator, AutoMinorLocator
import datetime
import numpy as np
import os
import json
import time
import gc
import matplotlib
import tempfile

# from PIL import Image  # for png compressing

matplotlib.use("Agg")


class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)


HOST = "10.2.3.13"  # ceilometer fixed ip
PORT = 2001  # Port to listen on (non-privileged ports are > 1023)

dt = 3  # sample rate at every 3 seconds
Nbuffer = int(2 * 3600 / dt)  # buffer 2hours


tempfolder = tempfile.gettempdir()
folder = "/var/www/html"
# folder = "/users/ag/Downloads"  # ASLAKS TEST FOLDER

image_file = f"{folder}/ceilometer.png"
json_file = f"{folder}/ceilometer.json"
temp_image = f"{tempfolder}/ceilometer.png"
temp_json = f"{tempfolder}/ceilometer.png"


# os.remove(image_file)
# os.remove(json_file)


z = None
buffer = None
t = np.empty(Nbuffer, dtype="datetime64[s]")
bufferpos = 0

now = lambda: np.datetime64(datetime.datetime.now())
tlastfig = now()
t_reset = np.datetime64("1970-01-01T00:00:00.000000000")
t[:] = t_reset


# ------------------------CUSTOM COLORMAP ------------------
from matplotlib.colors import ListedColormap

darkblue = np.array([0, 0, 0.5, 1])
skyblue = np.array([52.9, 80.8, 92.2, 100]) / 100
white = np.array([1, 1, 1, 1])
grey = np.array([0.5, 0.5, 0.5, 1])
colors = np.vstack((darkblue, skyblue, white, grey))
x = np.linspace(-1, 1, 100)
cmap = np.vstack(
    [np.interp(x, np.array([-1, 0, 0.2, 1]), colors[:, c]) for c in range(4)]
).T
cmap = ListedColormap(cmap)
# cmap = 'seismic_r'
# ---------------------


s = None
reader = None
connected = False
while True:
    if not connected:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(dt)
            s.connect((HOST, PORT))
            reader = s.makefile("r")
            connected = True
            print("connected to Ceilometer...")
        except:
            s, reader = None, None

    try:
        output = ceilometer.parse_next_chunk(reader)
    except:
        connected = False
        reader = None
        t[bufferpos] = t_reset
        if not buffer is None:
            buffer[:, bufferpos] = np.nan
        bufferpos = (bufferpos + 1) % Nbuffer
        if s:
            s.close()
        time.sleep(dt)
        continue

    tnow = now()
    strnow = tnow.item().strftime("%Y-%m-%d %H:%M:%S")
    output["time"] = strnow

    if z is None:
        z = output["z"]
        buffer = np.empty((len(z), Nbuffer)) + np.nan
    t[bufferpos] = tnow
    buffer[:, bufferpos] = output["profile"]
    bufferpos = (bufferpos + 1) % Nbuffer
    # print("base:", output["cloud_base"])

    if tnow - tlastfig > np.timedelta64(2, "m"):
        tlastfig = tnow
        print("making figure")
        with open(json_file, "w") as file:
            file.write(json.dumps(output, cls=NumpyEncoder))

        ix = (np.arange(Nbuffer) + bufferpos) % Nbuffer
        V = buffer[:, ix]
        tt = t[ix]

        # with plt.style.context('fivethirtyeight'):
        if True:
            fig = plt.figure(figsize=[960 / 100, 540 / 100], dpi=150, num=1, clear=True)
            plt.pcolormesh(
                range(Nbuffer),
                z,
                V,
                cmap=cmap,
                vmin=-15000,
                vmax=15000,
                shading="auto",
            )
            for level in output["cloud_base"]:
                if level < 3000:
                    hlvl = plt.annotate(
                        f"  {level:.0f} m",
                        (Nbuffer + 1, level),
                        fontweight="bold",
                        va="center",
                        ha="left",
                        bbox=dict(
                            boxstyle="square,pad=0.1",
                            fc="white",
                            ec="white",
                            lw=0,
                            alpha=0.9,
                        ),
                    )
                # hlvl.set_clip_path(Rectangle((1.01,0),1,1,transform = plt.gca().transAxes))

            plt.gca().set_yscale(
                "function",
                functions=[
                    lambda x: np.sign(x + 10) * np.sqrt(np.abs(x + 10)),
                    lambda x: np.sign(x) * (x**2) - 10,
                ],
            )
            plt.grid(visible=True, color="#000000", linewidth=0.8, alpha=0.1)
            plt.gca().set_axisbelow(False)
            # plt.ylabel("meters above ground")
            plt.ylim([0, 3000])
            plt.gca().yaxis.set_major_formatter(FormatStrFormatter("%d m"))
            xticks = np.flip(range(Nbuffer - 1, 0, -int(60 * 20 / dt)))
            xticklabels = [x.item().strftime("%H:%M") for x in tt[xticks]]
            plt.gca().yaxis.tick_right()
            plt.gca().yaxis.set_minor_locator(MultipleLocator(100))
            plt.gca().yaxis.set_label_position("right")
            plt.gca().set_xticks(xticks)
            plt.gca().set_xticklabels(xticklabels)
            stnow = tnow.item().strftime("%Y-%m-%d")
            plt.text(
                0.5,
                0.99,
                f"EastGRIP Ceilometer {stnow}",
                horizontalalignment="center",
                verticalalignment="top",
                fontsize="large",
                fontweight="bold",
                alpha=0.5,
                transform=plt.gca().transAxes,
            )
            if image_file:
                plt.savefig(temp_image, bbox_inches="tight")
                # reduce the bitdepth
                # img = Image.open(temp_image)
                # img = img.convert("P", palette=Image.ADAPTIVE, colors=64)
                # img.save(temp_image, "PNG", optimize = True)
                # img = None
                # swap it on the webserver.
                os.replace(temp_image, image_file)
            plt.gca().cla()
            fig.clear()
            plt.close(fig)
            gc.collect()
if s:
    s.close()
