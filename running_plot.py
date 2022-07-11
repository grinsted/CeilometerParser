# -*- coding: utf-8 -*-
"""
Created on Sat Jul  9 10:51:33 2022

@author: ag
"""
# -*- coding: utf-8 -*-
"""
Created on Tue Jul  5 21:34:15 2022

@author: ag
"""


import socket
import ceilometer
from pprint import pprint
import matplotlib.pyplot as plt
import datetime
import numpy as np
import os
import json
import time
import json
import gc
import matplotlib

matplotlib.use('Agg')

class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)


HOST = "127.0.0.1"  # ceilometer fixed ip
PORT = 2001  # Port to listen on (non-privileged ports are > 1023)

dt = 3 #sample rate at every 3 seconds
Nbuffer = int(2*3600/dt) #buffer 2hours


folder='/var/www/html'
image_file = f'{folder}/ceilometer.png'
json_file = f'{folder}/ceilometer.json'


z = None
buffer = None
t = np.empty(Nbuffer,dtype = 'datetime64[s]')
bufferpos = 0

now = lambda: np.datetime64(datetime.datetime.now())
tlastfig = now()
t_reset = np.datetime64('1970-01-01T00:00:00.000000000')
t[:] = t_reset


#------------------------



connected = False
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:

    while True:
        if not connected:
            try:
                s.connect((HOST, PORT))
                reader = s.makefile("r")
                connected = True
            except:
                time.sleep(10)
                t[bufferpos] = t_reset
                buffer[:,bufferpos] = np.nan
                bufferpos = (bufferpos+1) % Nbuffer
                continue

        try:
            output = ceilometer.parse_next_chunk(reader)
        except:
            connected = False
            time.sleep(10)
            t[bufferpos] = t_reset
            buffer[:,bufferpos] = np.nan
            bufferpos = (bufferpos+1) % Nbuffer
            continue

        tnow = now()
        strnow = tnow.item().strftime('%Y-%m-%d %H:%M:%S')
        output['time'] = strnow

        if z is None:
            z = output['z']
            buffer = np.empty((len(z),Nbuffer)) + np.nan
        t[bufferpos] = tnow
        buffer[:,bufferpos] = output['profile']
        bufferpos = (bufferpos+1) % Nbuffer
        print('base:', output['cloud_base'])

        if tnow-tlastfig>np.timedelta64(2,'m'):
            tlastfig = tnow
            print('making figure')
            with open(json_file,'w') as file:
                file.write(json.dumps(output, cls=NumpyEncoder))

            ix = (np.arange(Nbuffer)+bufferpos) % Nbuffer
            V=buffer[:,ix]
            tt= t[ix]

            with plt.style.context('fivethirtyeight'):
                fig = plt.figure(figsize=[900/100,500/100], dpi=100, num=1, clear=True)
                plt.pcolormesh(range(Nbuffer),z,V,
                               cmap='seismic_r', vmin=-15000, vmax=15000,
                               shading='auto')
                for level in output['cloud_base']:
                    plt.annotate(f' {level:.0f} m',(Nbuffer,level),verticalalignment='top',horizontalalignment='left')

                plt.gca().set_yscale("function", functions=[lambda x: np.sign(x+10)*np.sqrt(np.abs(x+10)), lambda x: np.sign(x)*(x**2)-10])
                plt.grid()
                plt.ylabel('meters above ground')
                plt.ylim([0, 3000])
                xticks = np.flip(range(Nbuffer-1,0,-int(60*20/dt)))
                xticklabels = [x.item().strftime('%H:%M') for x in tt[xticks]]
                plt.gca().set_xticks(xticks)
                plt.gca().set_xticklabels(xticklabels)
                stnow =tnow.item().strftime('%Y-%m-%d')
                plt.title(f'EGRIP ceilometer {stnow}')
                if image_file:
                    plt.savefig(image_file,bbox_inches='tight')
                plt.gca().cla()
                fig.clear()
                plt.close(fig)
                gc.collect()
