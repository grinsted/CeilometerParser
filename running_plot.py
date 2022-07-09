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


HOST = "10.2.3.13"  # ceilometer fixed ip
PORT = 2001  # Port to listen on (non-privileged ports are > 1023)

dt = 3 #sample rate at every 3 seconds
Nbuffer = int(2*3600/dt) #buffer 2hours


z = None
buffer = None
t = np.empty(Nbuffer,dtype = 'datetime64[s]')
bufferpos = 0

now = lambda: np.datetime64(datetime.datetime.now())
tlastfig = now()
t[:]=np.datetime64('1970-01-01T00:00:00.000000000')


#------------------------

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:

    s.connect((HOST, PORT))
    reader = s.makefile("r")

    while True:
        output = ceilometer.parse_next_chunk(reader)
        tnow = now()

        if z is None:
            z = output['z']
            buffer = np.empty((len(z),Nbuffer)) + np.nan
        t[bufferpos] = tnow
        buffer[:,bufferpos] = output['profile']
        bufferpos = (bufferpos+1) % Nbuffer
        print('.')
        if tnow-tlastfig>np.timedelta64(1,'m'):
            tlastfig = tnow

            ix = (np.arange(Nbuffer)+bufferpos) % Nbuffer
            V=buffer[:,ix]
            tt= t[ix]


            #plt.imshow(V, extent=[0, Nbuffer-1, z[0], z[-1]],
            #           cmap='seismic_r',clim=[-10000, 10000],origin='lower')
            #plt.axis('auto')
            with plt.style.context('fivethirtyeight'):
                plt.pcolormesh(range(Nbuffer),z,V,
                               cmap='seismic_r', vmin=-10000, vmax=10000,
                               shading='auto')
                for level in output['cloud_base']:
                    plt.annotate(f' {level:.0f} m',(Nbuffer,level),verticalalignment='top',horizontalalignment='left')

                plt.gca().set_yscale("function", functions=[lambda x: np.sqrt(x), lambda x: x**2])
                plt.grid()
                plt.ylabel('meters above ground')

                xticks = np.flip(range(Nbuffer-1,0,-int(60*20/dt)))
                xticklabels = [x.item().strftime('%H:%M') for x in tt[xticks]]
                plt.gca().set_xticks(xticks)
                plt.gca().set_xticklabels(xticklabels)
                stnow =tnow.item().strftime('%Y-%m-%d')
                plt.title(f'EGRIP ceilometer {stnow}')
                plt.show()


