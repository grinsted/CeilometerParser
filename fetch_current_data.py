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


folder='.'
image_file = f'{folder}/ceilometer.png'
json_file = f'{folder}/ceilometer.json'

target_height = 720 #pixels
dpi = 100


if os.path.exists(image_file):
    os.remove(image_file)
if os.path.exists(json_file):
    os.remove(json_file)

class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    reader = s.makefile("r")

    output = ceilometer.parse_next_chunk(reader)
    strnow = datetime.datetime.strftime(datetime.datetime.now(),'%Y-%m-%d %H:%M:%S')
    output['time'] = strnow

    with open(json_file,'w') as file:
        file.write(json.dumps(output, cls=NumpyEncoder))

    xmax = np.max(output['profile'])
    xmax = np.max([20000,xmax])
    xmin = np.min(output['profile'])

    with plt.style.context('fivethirtyeight'):
        plt.figure(figsize=[4,8])
        plt.plot(output['profile'], output['z'])
        for level in output['cloud_base']:
            x = np.interp(level,output['z'],output['profile'])
            x = np.max([x, 10000])
            plt.plot([xmin,xmax],[level,level],'r',alpha=0.5,linewidth=1)
            plt.annotate(f'{level:.0f} m',(x,level-50),verticalalignment='top',horizontalalignment='right')
        plt.xlim([xmin,xmax])
        plt.ylim([0,output['z'][-1]])
        plt.ylabel('meters above surface')
        plt.xlabel('signal')
        plt.gca().axes.xaxis.set_ticklabels([])
        plt.title(f'EastGRIP Ceilometer\n{strnow}')
        if image_file:
            dpi=100
            plt.savefig(image_file,figsize=[target_height/2/dpi,target_height/dpi],dpi=dpi,bbox_inches='tight')

pprint(output)
