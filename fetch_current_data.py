# -*- coding: utf-8 -*-
"""
Created on Tue Jul  5 21:34:15 2022

@author: ag
"""


import socket
import ceilometer
from pprint import pprint
import matplotlib.pyplot as plt

HOST = "10.2.3.13"  # ceilometer fixed ip
PORT = 2001  # Port to listen on (non-privileged ports are > 1023)


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    reader = s.makefile("r")

    output = ceilometer.parse_next_chunk(reader)

    plt.plot(output['profile'], output['z'])
    plt.ylabel('m')
    plt.plot(output['cloud_base']*0,output['cloud_base'],'ro')
    pprint(output)

