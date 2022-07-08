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

HOST = "10.2.3.13"  # ceilometer fixed ip
PORT = 2001  # Port to listen on (non-privileged ports are > 1023)

image_file = ''

#os.delete(image_file)

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    reader = s.makefile("r")

    output = ceilometer.parse_next_chunk(reader)

    xmax = np.max(output['profile'])
    xmax = np.max([20000,xmax])

    with plt.style.context('fivethirtyeight'):
        plt.figure(figsize=[4,8])
        plt.plot(output['profile'], output['z'])
        for level in output['cloud_base']:
            x = np.interp(level,output['z'],output['profile'])
            plt.plot([-1000,xmax],[level,level],'r',alpha=0.5,linewidth=0)
            plt.annotate(f'{level:.0f} m',(x,level-50),verticalalignment='top',horizontalalignment='right')
        plt.xlim([-1000,xmax])
        plt.ylabel('m')
        plt.xlabel('signal')
        plt.gca().axes.xaxis.set_ticklabels([])
        strnow = datetime.datetime.strftime(datetime.datetime.now(),'%Y-%m-%d %H:%M:%S')
        plt.title(f'EastGRIP Ceilometer\n{strnow}')



    pprint(output)

