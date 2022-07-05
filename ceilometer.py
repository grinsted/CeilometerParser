# -*- coding: utf-8 -*-

import numpy as np
import matplotlib.pyplot as plt
import re
import socket
from pprint import pprint

HOST = "10.2.3.13"  # ceilometer fixed ip
PORT = 2001  # Port to listen on (non-privileged ports are > 1023)



def hex5_to_int(s):
    # two's complement
    b = int(s, base=16)
    if b & 0x80000:
        b = b - 0x100000
    return b





feet_per_meter=3.28084

def parse_ceilometer_chunk(chunk):

    if type(chunk) is list:
        lines = chunk
    else:
        lines = chunk.split('\n')

    #-------------------------------------
    header = lines[0]
    if header[0] != "\x01":
        raise Exception('wrong header - expected \\x01')
    output['softwarelevel'] = header[4:7]
    output['with_sky_condition_data'] = (header[7] == "2")
    samplerange = header[8]
    if samplerange == "1":
        dz, N = 10, 770
    elif samplerange == "2":
        dz, N = 20, 385
    elif samplerange == "3":
        dz, N = 5, 1500
    elif samplerange == "4":
        dz, N = 5, 770
    elif samplerange == "5":
        dz, N = None, None
    z = np.arange(0, dz * N, dz) #This is already in m.
    output['z']=z

    #--------------------------------------
    line2= lines[1].rstrip()
    output['status'] = line2[21:]
    status = int(output['status'],base=16)
    if (status & 0x80):
        #units are metres
        multiplier = 1
    else:
        #units are feet
        multiplier = 1/feet_per_meter

    output['detection_status'] = line2[0]
    output['warning_alarm'] = line2[1]
    output['cloud_base'] = np.array(line2[3:20].replace('/////','nan').split(' ')).astype(float)*multiplier


    if not output['warning_alarm'] == '0':
        print('Warning/Alarm',output['warning_alarm'],output['status'])
    if output['detection_status']=='4':
        #full obscuration
        output['vertical_visibility'] = cloud_base[0]
        output['highest_signal_detected'] = cloud_base[1]
        output['cloud_base']= np.array([np.nan,np.nan,np.nan])
    else:
        output['vertical_visibility'] = None
        output['highest_signal_detected'] = None

    #--------------------------------------
    line3 = lines[2].rstrip()
    #TODO:
    numbers3 = np.array(re.split('\s+',re.sub('/+','nan',line3[2:]))).astype(float)
    output['cloud_heights'] = numbers3[1::2]*10*multiplier
    output['cloud_octas'] = numbers3[0::2]
    output['cloud_octas'][np.isnan(output['cloud_heights'])]=np.nan
    # if (output['cloud_octas'][0]>8)|(output['cloud_octas']<-1):
    #     #not sure what cloud octa = 9 means on page 65
    #     output['cloud_octas'][:]=np.nan
    #---------------------------------
    line4 = lines[3].rstrip()
    #TODO
    #-----------------------------------
    if dz:
        datatxt = lines[4].rstrip()
    chksum = lines[5].rstrip()
    data = np.array([hex5_to_int(datatxt[i : i + 5]) for i in range(0, len(datatxt), 5)])
    data = data * 1.0
    output['profile']=data
    return output




with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    reader = s.makefile("r")

    output={}

    header = True
    while header:
        header = reader.readline()
        if header[0] == "\x01":
            break
    lines=[header]
    while True:
        line = reader.readline()
        lines.append(line)
        if line[0] == "\x03":
            break

    output = parse_ceilometer_chunk(lines)

    plt.plot(output['profile'], output['z'])
    plt.ylabel('ft')
    plt.plot(output['cloud_base']*0,output['cloud_base'],'ro')
    pprint(output)

